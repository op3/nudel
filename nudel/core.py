#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2019 O. Papst.
#
# This file is part of nudel.
#
# nudel is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# nudel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with nudel.  If not, see <http://www.gnu.org/licenses/>.

"""Python interface for ENSDF nuclear data"""

from datetime import datetime
import re
from typing import Iterator, List, Optional, Tuple, Union
import warnings

from .provider import ENSDFProvider, ENSDFFileProvider
from .util import nucid_from_az, az_from_nucid, Quantity


class ENSDF:
    active_ensdf = None

    def __init__(self, provider: Optional["ENSDFProvider"] = None):
        """Create ENSDF instance

        Args:
            provider: provider for ENSDF database
        """
        self.provider = provider or ENSDFFileProvider()
        self.datasets = dict.fromkeys(self.provider.index)
        self._old_active = None

    def get_dataset(self, nuclide: Tuple[int, Optional[int]], name: str) -> "Dataset":
        """Returns specified dataset.

        Args:
            nuclide: Nuclide given in (nucleons, protons) format.
                Use protons=None for generic mass-specific dataset.
            name: Name of the ENSDF dataset

        Returns:
            Dataset that was requested.
        """
        if (nuclide, name) not in self.datasets:
            raise KeyError("Dataset not found")
        # TODO: activate cache
        if self.datasets[(nuclide, name)] is None or True:
            res = self.provider.get_dataset(nuclide, name)
            self.datasets[(nuclide, name)] = Dataset(res)
        return self.datasets[(nuclide, name)]

    def get_adopted_levels(self, nuclide: Tuple[int, int]) -> "Dataset":
        """Get adopted levels dataset of a nuclide

        Args:
            nuclide: Nuclide given in (nucleons, protons) format

        Returns:
            Dataset "ADOPTED LEVELS[…]" of given nuclide
        """
        # TODO: activate cache
        if (nuclide, "ADOPTED LEVELS") not in self.datasets or True:
            res = Dataset(self.provider.get_adopted_levels(nuclide))
            self.datasets[(nuclide, "ADOPTED LEVELS")] = res
        return self.datasets[(nuclide, "ADOPTED LEVELS")]

    def get_datasets_by_nuclide(self, nuclide: Tuple[int, Optional[int]]) -> List[str]:
        """Get names of all datasets of a nuclide

        Args:
            nuclide: Nuclide given in (nucleons, protons) format.
                Use protons=None for generic mass-specific dataset.

        Returns:
            List of dataset identifier names for given nuclide
        """
        res = []
        for dnuclide, name in self.datasets.keys():
            if dnuclide == nuclide:
                res.append(name)
        return res

    def get_indexed_nuclides(self) -> List[Tuple[int, int]]:
        """Get all nuclides with corresponding adopted levels datasets.

        Returns:
            A list of tuples, each containing the nucleon number and
            proton number of an indexed nuclide.
        """
        return self.provider.adopted_levels.keys()

    def __enter__(self):
        self._old_active = ENSDF.active_ensdf
        ENSDF.active_ensdf = self

    def __exit__(self, type, value, traceback):
        ENSDF.active_ensdf = self._old_active
        self._old_active = None


class Dataset:
    def __init__(self, dataset_plain: str):
        self.jpi_index = dict()
        self.ensdf = get_active_ensdf()
        self.header, *self.raw = dataset_plain.split("\n")
        self.nucid = self.header[0:5].strip()
        self.dataset_id = self.header[9:39].strip()
        self.dataset_ref = self.header[39:65].strip()
        self.publication = self.header[65:74].strip()
        try:
            self.date = datetime.strptime(self.header[74:80].strip(), "%Y%m")
        except ValueError:
            self.date = None
        self.records = []
        self.levels = []
        self.history = {}
        self.qrecords = []
        self.normalization_records = []
        self.comments = []
        self.parents = []
        self.references = []
        self.cross_references = []
        self._parse_dataset()

    def _add_record(self, record, comments, xref, level=None):
        rec_type = get_record_type(record)
        rec = rec_type(self, record, comments, xref, level)
        self.records.append(rec)
        return rec

    def _add_level(self, record, comments, xref):
        lvl = LevelRecord(self, record, comments, xref)
        self.levels.append(lvl)
        lvl.state_num = len(self.levels) - 1
        return lvl

    def _parse_dataset(self):
        comments = []
        record = []
        xref = []
        level = None
        history = ""
        header = True

        for line in self.raw[:-1]:
            flag_cont, flag_com, flag_rectype, flag_particle = line[5:9]
            if header:
                if flag_com.lower() in "cdt":
                    if flag_cont != " ":
                        self.comments[-1].append(line)
                    else:
                        self.comments.append([line])
                else:
                    if flag_rectype in "BAGEL" or (
                        flag_rectype in " D" and flag_particle in "PAN"
                    ):
                        header = False
                    elif flag_rectype == "X":
                        self.cross_references.append(CrossReferenceRecord(self, line))
                    elif flag_rectype == "P":
                        self.parents.append(ParentRecord(self, line))
                    elif flag_rectype == "R":
                        self.references.append(ReferenceRecord(self, line))
                    elif flag_rectype.upper() == "Q":
                        self.qrecords.append(QValueRecord(self, line))
                    elif flag_rectype.upper() == "H":
                        history += line[9:80] + " "
                    elif flag_rectype.upper() == "N" and flag_cont == flag_com == " ":
                        self.normalization_records.append(
                            NormalizationRecord(self, line)
                        )
            if header:
                continue

            try:
                if (
                    flag_rectype in "BAGEL"
                    or (flag_rectype in " D" and flag_particle in "PAN")
                ) and line[5:7] == "  ":
                    if record:
                        if record[0][7] == "L":
                            level = self._add_level(record, comments, xref)
                        else:
                            self._add_record(record, comments, xref, level)
                    comments = []
                    record = []
                    xref = []
                    record.append(line)
                elif line[5:7] == "X ":
                    xref.append(line)
                elif flag_com == " ":
                    record.append(line)
                elif flag_com.lower() in "cdt":
                    if flag_cont != " ":
                        comments[-1].append(line)
                    else:
                        comments.append([line])
                else:
                    # This is a broken record!
                    warnings.warn("Record is malformed, parsing anyway.")
                    record.append(line)
            except (IndexError, ValueError):
                print(record)
                raise

            # if line[7].lower() in "bagel" and line[6].lower() not in "ct":
            #    if line[5] == " " and record:
            #        self._add_record(record, comments)
            #        comments = []
            #        record = []
            #    if line[6].lower() not in "ct":
            #        record.append(line)
            # if line[6].lower() not in "ct":
            #    comments.append(line)
        try:
            if record:
                if record[0][7] == "L":
                    level = self._add_level(record, comments, xref)
                else:
                    self._add_record(record, comments, xref, level)
        except (IndexError, ValueError):
            print(record)
            raise

        for entry in history.split("$")[:-1]:
            try:
                k, v = entry.split("=", maxsplit=1)
                self.history[k.strip()] = v.strip()
            except ValueError:
                # TODO: Maybe wrong linebreak?
                pass

    def add_jpi(self, level):
        for ang_mom in level.ang_mom:
            if (ang_mom.val, ang_mom.parity) in self.jpi_index:
                self.jpi_index[(ang_mom.val, ang_mom.parity)].append(level)
            else:
                self.jpi_index[(ang_mom.val, ang_mom.parity)] = [level]
            return len(self.jpi_index[(ang_mom.val, ang_mom.parity)])


class BaseRecord:
    pass


class Record(BaseRecord):
    def __init__(self, dataset, record, comments, xref):
        self.prop = dict()
        self.dataset = dataset
        self.comments = []
        self.xref = xref
        if comments:
            for comment in comments:
                self.comments.append(GeneralCommentRecord(dataset, comment))

    def load_prop(self, lines):
        for line in lines:
            for entry in line[9:].split("$"):
                entry = entry.strip()
                if not entry:
                    continue
                if "=" in entry:
                    quant, value = entry.split("=", maxsplit=1)
                    self.prop[quant.strip()] = value.strip()
                else:
                    for symb in ["<", ">"]:
                        if symb in entry:
                            quant, value = entry.split(symb, maxsplit=1)
                            self.prop[quant.strip()] = symb + value.strip()
                            return
                    for abbr in ["GT", "LT", "GE", "LE", "AP", "CA", "SY"]:
                        if f" {abbr} " in entry:
                            quant, quant, value = entry.split(" ", maxsplit=2)
                            self.prop[quant.strip()] = f"{value.strip()} {quant}"
                            return
                    if entry[-1] == "?":
                        self.prop[entry[:-1]] = "?"
                        return
                    raise ValueError(f"Cannot process property: '{entry}'.")


class QValueRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.prop = dict()
        self.prop["Q-"] = line[9:19].strip()
        self.prop["DQ-"] = line[19:21].strip()
        self.prop["Q-"] += " " + self.prop["DQ-"].strip()
        self.prop["N"] = line[21:29].strip()
        self.prop["DN"] = line[29:31].strip()
        self.prop["N"] += " " + self.prop["DN"].strip()
        self.prop["P"] = line[31:39].strip()
        self.prop["DP"] = line[39:41].strip()
        self.prop["P"] += " " + self.prop["DP"].strip()
        self.prop["A"] = line[41:49].strip()
        self.prop["DA"] = line[49:55].strip()
        self.prop["A"] += " " + self.prop["DA"].strip()
        self.prop["QREF"] = line[55:80].strip()

        self.q_beta_minus = Quantity(self.prop["Q-"])
        self.neutron_separation = Quantity(self.prop["N"])
        self.proton_separation = Quantity(self.prop["P"])
        self.alpha_decay = Quantity(self.prop["A"])


class CrossReferenceRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.dataset = dataset
        self.dssym = line[8]
        self.dsid = line[9:39].strip()


class GeneralCommentRecord(BaseRecord):
    def __init__(self, dataset, comment):
        self.dataset = dataset
        self.comment = comment
        # self.continuation = line[5] not in ["1", " "]
        # self.comment_type = line[6]
        # self.rtype = line[7]
        # self.psym = line[8]
        # self.comment_text = line[9:80]


class ParentRecord(Record):
    def __init__(self, dataset, record):
        super().__init__(dataset, record, None, None)
        self.prop["E"] = record[9:19].strip()
        self.prop["DE"] = record[19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["J"] = record[21:39].strip()
        self.prop["T"] = record[39:49].strip()
        self.prop["DT"] = record[49:55].strip()
        self.prop["T"] += " " + self.prop["DT"].strip()
        self.prop["QP"] = record[64:74].strip()
        self.prop["DQP"] = record[74:76].strip()
        self.prop["QP"] += " " + self.prop["DQP"].strip()
        self.prop["ION"] = record[76:80].strip()
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.ang_mom = ang_mom_parser(self.prop["J"])
        self.half_life = Quantity(self.prop["T"])
        self.q_value = Quantity(self.prop["QP"], "KEV")


class NormalizationRecord(Record):
    def __init__(self, dataset, record):
        super().__init__(dataset, record, None, None)
        self.prop["NR"] = record[9:19].strip()
        self.prop["DNR"] = record[19:21].strip()
        self.prop["NR"] += " " + self.prop["DNR"].strip()
        self.prop["NT"] = record[21:29].strip()
        self.prop["DNT"] = record[29:31].strip()
        self.prop["NT"] += " " + self.prop["DNT"].strip()
        self.prop["BR"] = record[31:39].strip()
        self.prop["DBR"] = record[39:41].strip()
        self.prop["BR"] += " " + self.prop["DBR"].strip()
        self.prop["NB"] = record[41:49].strip()
        self.prop["DNB"] = record[49:55].strip()
        self.prop["NB"] += " " + self.prop["DNB"].strip()
        self.prop["NP"] = record[55:62].strip()
        self.prop["DNP"] = record[62:64].strip()
        self.prop["NP"] += " " + self.prop["DNP"].strip()
        self.load_prop(record[1:])

        self.branching_ratio = Quantity(self.prop["BR"])
        self.rel_intensity_multiplier = Quantity(self.prop["NR"])
        self.trans_intensity_multiplier = Quantity(self.prop["NT"])


class LevelRecord(Record):
    def __init__(self, dataset, record, comments, xref):
        super().__init__(dataset, record, comments, xref)
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["J"] = record[0][21:39].strip()
        self.prop["T"] = record[0][39:49].strip()
        self.prop["DT"] = record[0][49:55].strip()
        self.prop["T"] += " " + self.prop["DT"].strip()
        self.prop["L"] = record[0][55:64].strip()
        self.prop["S"] = record[0][64:74].strip()
        self.prop["DS"] = record[0][74:76].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["MS"] = record[0][77:79].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])

        self.state_num = None
        self.decays = []
        self.populating = []

        self.attr = dict()
        self.energy = Quantity(self.prop["E"], "KEV")
        self.ang_mom = ang_mom_parser(self.prop["J"])
        self.half_life = Quantity(self.prop["T"])
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"
        self.g_factor = Quantity(self.prop["G"] if "G" in self.prop else "")
        self.metastable = self.prop["MS"] and self.prop["MS"][0] == "M"

        self.decay_ratio = dict()
        for k, v in self.prop.items():
            if len(k) == 2 and k[0] == "B":
                self.attr[k] = Quantity(v)

            if k[0] == "%":
                self.decay_ratio[k[1:]] = Quantity(v, default_unit="%")

        spec_strength_calc = False
        if (
            len(self.prop["S"]) > 2
            and self.prop["S"][0] == "("
            and self.prop["S"][-1] == ")"
        ):
            spec_strength_calc = True
            self.prop["S"] = self.prop["S"][1:-1]
        if not "E+" in self.prop["S"] and "+" in self.prop["S"]:
            spec_strength = self.prop["S"].split("+")
        elif "," in self.prop["S"]:
            spec_strength = self.prop["S"].split(",")
        else:
            spec_strength = [self.prop["S"]]
        self.spec_strength = [
            Quantity(s + " " + self.prop["DS"]) for s in spec_strength
        ]
        if spec_strength_calc:
            for s in self.spec_strength:
                s.calculated = True

        self.index = self.dataset.add_jpi(self)

    def add_decay(self, decay):
        self.decays.append(decay)


class DecayRecord(Record):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref)
        self.dest_level = dest_level


class BetaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["IB"] = record[0][21:29].strip()
        self.prop["DIB"] = record[0][29:31].strip()
        self.prop["IB"] += " " + self.prop["DIB"].strip()
        self.prop["LOGFT"] = record[0][41:49].strip()
        self.prop["DFT"] = record[0][49:55].strip()
        self.prop["LOGFT"] += " " + self.prop["DFT"].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["UN"] = record[0][77:79].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"


class ECRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["IB"] = record[0][21:29].strip()
        self.prop["DIB"] = record[0][29:31].strip()
        self.prop["IB"] += " " + self.prop["DIB"].strip()
        self.prop["IE"] = record[0][31:39].strip()
        self.prop["DIE"] = record[0][39:41].strip()
        self.prop["IE"] += " " + self.prop["DIE"].strip()
        self.prop["LOGFT"] = record[0][41:49].strip()
        self.prop["DFT"] = record[0][49:55].strip()
        self.prop["LOGFT"] += " " + self.prop["DFT"].strip()
        self.prop["TI"] = record[0][64:74].strip()
        self.prop["DTI"] = record[0][74:76].strip()
        self.prop["TI"] += " " + self.prop["DTI"].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["UN"] = record[0][77:79].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])


class AlphaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["IA"] = record[0][21:29].strip()
        self.prop["DIA"] = record[0][29:31].strip()
        self.prop["IA"] += " " + self.prop["DIA"].strip()
        self.prop["HF"] = record[0][31:39].strip()
        self.prop["DHF"] = record[0][39:41].strip()
        self.prop["HF"] += " " + self.prop["DHF"].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])


class ParticleRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop["D"] = record[0][7]
        self.prop["Particle"] = record[0][8]
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["IP"] = record[0][21:29].strip()
        self.prop["DIP"] = record[0][29:31].strip()
        self.prop["IP"] += " " + self.prop["DIP"].strip()
        self.prop["EI"] = record[0][31:39].strip()
        self.prop["T"] = record[0][39:49].strip()
        self.prop["DT"] = record[0][49:55].strip()
        self.prop["T"] += " " + self.prop["DT"].strip()
        self.prop["L"] = record[0][55:64].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["COIN"] = record[0][78].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])

        self.prompt_emission = self.prop["D"] == " "
        self.delayed_emission = self.prop["D"] == "D"


class GammaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, orig_level):
        super().__init__(dataset, record, comments, xref, dest_level=None)
        self.orig_level = orig_level
        if self.orig_level:
            self.orig_level.add_decay(self)
        self.prop["E"] = record[0][9:19].strip()
        self.prop["DE"] = record[0][19:21].strip()
        self.prop["E"] += " " + self.prop["DE"].strip()
        self.prop["RI"] = record[0][21:29].strip()
        self.prop["DRI"] = record[0][29:31].strip()
        self.prop["RI"] += " " + self.prop["DRI"].strip()
        self.prop["M"] = record[0][31:41].strip()
        self.prop["MR"] = record[0][41:49].strip()
        self.prop["DMR"] = record[0][49:55].strip()
        self.prop["MR"] += " " + self.prop["DMR"].strip()
        self.prop["CC"] = record[0][55:62].strip()
        self.prop["DCC"] = record[0][62:64].strip()
        self.prop["CC"] += " " + self.prop["DCC"].strip()
        self.prop["TI"] = record[0][64:74].strip()
        self.prop["DTI"] = record[0][74:76].strip()
        self.prop["TI"] += " " + self.prop["DTI"].strip()
        self.prop["C"] = record[0][76].strip()
        self.prop["COIN"] = record[0][78].strip()
        self.prop["Q"] = record[0][79].strip()
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.rel_intensity = Quantity(self.prop["RI"])
        self.intensity = None
        if self.dataset.normalization_records:
            norm = self.dataset.normalization_records[0]
            self.intensity = self.rel_intensity
            if norm.branching_ratio.val:
                self.intensity *= norm.branching_ratio.val
            if norm.rel_intensity_multiplier.val:
                self.intensity *= norm.rel_intensity_multiplier.val
        self.multipolarity = self.prop["M"]
        self.mixing_ratio = Quantity(self.prop["MR"])
        self.conversion_coeff = Quantity(self.prop["CC"])
        self.rel_tot_trans_intensity = Quantity(self.prop["TI"])
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"

        self.attr = dict()
        for k, v in self.prop.items():
            if k[0:2] == "BE" or k[0:2] == "BM":
                self.attr[k] = Quantity(v)

        self._determine_dest_level()

    def _determine_dest_level(self):
        if "FL" in self.prop:
            if self.prop["FL"] == "?":
                return
            dest_energy = Quantity(self.prop["FL"]).val
        elif self.orig_level:
            energy_gamma = self.energy.val
            mass, _ = az_from_nucid(self.dataset.nucid)
            amu = 931494.10242  # From CODATA 2018
            energy_i = energy_gamma * (1 + 2 * energy_gamma / (mass * amu))
            dest_energy = self.orig_level.energy.val - energy_i
        else:
            return
        try:
            self.dest_level = min(
                [
                    l
                    for l in self.dataset.levels
                    if l.energy.offset == self.energy.offset
                ],
                key=lambda x: abs(x.energy.val - dest_energy),
            )
            self.dest_level.populating.append(self)
        except ValueError:
            pass


class ReferenceRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.prop = dict()
        self.dataset = dataset
        self.prop["MASS"] = line[0:3].strip()
        self.prop["KEYNUM"] = line[9:17].strip()
        self.prop["REFERENCE"] = line[17:80].strip()


def get_record_type(record):
    if record[0][7] == "X":
        return CrossReferenceRecord
    if record[0][7] == "Q":
        return QValueRecord
    if record[0][7] == "N":
        return NormalizationRecord
    if record[0][7] == "L":
        return LevelRecord
    if record[0][7] == "B":
        return BetaRecord
    if record[0][7] == "E":
        return ECRecord
    if record[0][7] == "A":
        return AlphaRecord
    if record[0][7] == "G":
        return GammaRecord
    if record[0][7] in " D" and record[0][8] in "PAN":
        return ParticleRecord
    else:
        raise NotImplementedError(
            f"Unknown record with type '{record[0][7]}': '{record[0]}'"
        )


class Nuclide:
    def __init__(self, mass: int, protons: int):
        self.mass = mass
        self.protons = protons
        self.ensdf = get_active_ensdf()
        self.adopted_levels = self.ensdf.get_adopted_levels((mass, protons))

    def get_isomers(self) -> Iterator["LevelRecord"]:
        """Generator that yields ground state and metastable states.

        Yields:
            LevelRecords for ground state and metastable states.
        """
        if self.adopted_levels.levels[0]:
            yield self.adopted_levels.levels[0]
        if self.adopted_levels.levels[1:]:
            for level in self.adopted_levels.levels[1:]:
                if level.metastable:
                    yield level

    def get_daughters(self) -> List[Tuple[Tuple[int, int], str]]:
        nucid = nucid_from_az((self.mass, self.protons)).strip()
        for nucid_i, name_i in self.ensdf.datasets.keys():
            if name_i.startswith(nucid) and "DECAY" in name_i:
                yield (nucid_i, name_i)


def rec_bracket_parser(s, i=0):
    res = []
    ang_mom = ""
    parity = None
    while i < len(s):
        if s[i] == "(" or s[i] == "[":
            if i + 2 < len(s) and s[i + 2] == ")" and s[i + 1] in "+-":
                parity = s[i + 1]
                res.append((ang_mom, parity))
                ang_mom = ""
                parity = None
                i += 3
                continue
            if ang_mom:
                res.append((ang_mom, parity))
            ang_mom = ""
            parity = None
            i, sub_res = rec_bracket_parser(s, i + 1)
            if i < len(s) and s[i] in "+-":
                for ang_mom_sub, _ in sub_res:
                    res.append((ang_mom_sub, s[i]))
            else:
                res.extend(sub_res)
        elif s[i] == ")" or s[i] == "]":
            if ang_mom:
                res.append((ang_mom, parity))
            ang_mom = ""
            parity = None
            return i + 1, res
        else:
            if s[i] in "+-":
                parity = s[i]
            elif s[i] == ",":
                if ang_mom:
                    res.append((ang_mom, parity))
                ang_mom = ""
                parity = None
            else:
                ang_mom += s[i]
            i += 1
    if ang_mom:
        res.append((ang_mom, parity))
    return i, res


def ang_mom_parser(ang_mom: str) -> List[Tuple[str, Optional[str]]]:
    """
    Parse simple angular momement definitions such as 5/2+ or 4,5,6(-).
    More advanced definitions (silently) result in garbage.
    """
    res = []
    for fragment, parity in rec_bracket_parser(ang_mom)[1]:
        for J in ang_mom_range_to_tuple(fragment):
            res.append(AngularMoment(J, parity))
    return res


def ang_mom_to_tuple(ang_mom):
    if "/" in ang_mom:
        a, b = ang_mom.split("/", 1)
    else:
        a, b = ang_mom, 1
    return int(a), int(b)


def ang_mom_range_to_tuple(ang_mom):
    try:
        if " TO " in ang_mom:
            start, stop = ang_mom.split(" TO ", 1)
        elif ":" in ang_mom:
            start, stop = ang_mom.split(":", 1)
        else:
            yield ang_mom_to_tuple(ang_mom)
            return
        start, div = ang_mom_to_tuple(start)
        stop, _ = ang_mom_to_tuple(stop)
        for i in range(start, stop + div, div):
            yield (i, div)
    except:
        yield ang_mom


class AngularMoment:
    def __init__(self, ang_mom, parity=None):
        self.div = None
        try:
            self.ang_mom, self.div = ang_mom
            self.val = self.ang_mom / self.div
        except:
            self.ang_mom = ang_mom
            self.val = None
        self.parity = parity

    def __repr__(self):
        if self.div != 1:
            J = f"{self.ang_mom}/{self.div}"
        else:
            J = f"{self.ang_mom}"
        if self.parity:
            return f"{J}{self.parity}"
        return J

    def __eq__(self, other):
        if isinstance(other, AngularMoment):
            return self.ang_mom == other.ang_mom and self.parity == other.parity
        elif isinstance(other, tuple):
            if self.parity != other[1]:
                return False
            if self.div:
                ang_mom = self.ang_mom / self.div
                return abs(ang_mom - float(other[0])) < 0.1
            return self.ang_mom == other[0]


def get_active_ensdf():
    if not ENSDF.active_ensdf:
        ENSDF.active_ensdf = ENSDF()
    return ENSDF.active_ensdf
