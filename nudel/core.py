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

import logging
import re
import warnings
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from .provider import ENSDFFileProvider, ENSDFProvider
from .util import ELEMENTS, Quantity, az_from_nucid, nucid_from_az

logger = logging.getLogger(__name__)


def slice_fields(line: str, fields: tuple[tuple[str, int, int], ...]) -> dict[str, str]:
    """Slice ``line`` into a ``{name: stripped_value}`` dict per the layout table."""
    return {name: line[start:end].strip() for name, start, end in fields}


QVALUE_FIELDS = (
    ("Q-", 9, 19),
    ("DQ-", 19, 21),
    ("N", 21, 29),
    ("DN", 29, 31),
    ("P", 31, 39),
    ("DP", 39, 41),
    ("A", 41, 49),
    ("DA", 49, 55),
    ("QREF", 55, 80),
)

XREF_FIELDS = (
    ("dssym", 8, 9),
    ("dsid", 9, 39),
)

PARENT_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("J", 21, 39),
    ("T", 39, 49),
    ("DT", 49, 55),
    ("QP", 64, 74),
    ("DQP", 74, 76),
    ("ION", 76, 80),
)

NORMALIZATION_FIELDS = (
    ("NR", 9, 19),
    ("DNR", 19, 21),
    ("NT", 21, 29),
    ("DNT", 29, 31),
    ("BR", 31, 39),
    ("DBR", 39, 41),
    ("NB", 41, 49),
    ("DNB", 49, 55),
    ("NP", 55, 62),
    ("DNP", 62, 64),
)

LEVEL_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("J", 21, 39),
    ("T", 39, 49),
    ("DT", 49, 55),
    ("L", 55, 64),
    ("S", 64, 74),
    ("DS", 74, 76),
    ("C", 76, 77),
    ("MS", 77, 79),
)

BETA_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("IB", 21, 29),
    ("DIB", 29, 31),
    ("LOGFT", 41, 49),
    ("DFT", 49, 55),
    ("C", 76, 77),
    ("UN", 77, 79),
)

EC_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("IB", 21, 29),
    ("DIB", 29, 31),
    ("IE", 31, 39),
    ("DIE", 39, 41),
    ("LOGFT", 41, 49),
    ("DFT", 49, 55),
    ("TI", 64, 74),
    ("DTI", 74, 76),
    ("C", 76, 77),
    ("UN", 77, 79),
)

ALPHA_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("IA", 21, 29),
    ("DIA", 29, 31),
    ("HF", 31, 39),
    ("DHF", 39, 41),
    ("C", 76, 77),
)

PARTICLE_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("IP", 21, 29),
    ("DIP", 29, 31),
    ("EI", 31, 39),
    ("T", 39, 49),
    ("DT", 49, 55),
    ("L", 55, 64),
    ("C", 76, 77),
    ("COIN", 78, 79),
)

GAMMA_FIELDS = (
    ("E", 9, 19),
    ("DE", 19, 21),
    ("RI", 21, 29),
    ("DRI", 29, 31),
    ("M", 31, 41),
    ("MR", 41, 49),
    ("DMR", 49, 55),
    ("CC", 55, 62),
    ("DCC", 62, 64),
    ("TI", 64, 74),
    ("DTI", 74, 76),
    ("C", 76, 77),
    ("COIN", 78, 79),
)

REFERENCE_FIELDS = (
    ("MASS", 0, 3),
    ("KEYNUM", 9, 17),
    ("REFERENCE", 17, 80),
)


class ENSDF:
    active_ensdf = None

    def __init__(
        self,
        provider: "ENSDFProvider | None" = None,
        *,
        version: str = "latest",
    ):
        """Create ENSDF instance

        Args:
            provider: provider for ENSDF database
            version: ENSDF version (``"latest"`` or ``YYMMDD``). Ignored
                when ``provider`` is given.
        """
        self.provider = provider or ENSDFFileProvider(version=version)
        self.datasets = dict.fromkeys(self.provider.index)
        self._old_active = None

    def get_dataset(self, nuclide: tuple[int, int | None], name: str) -> "Dataset":
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
        if self.datasets[(nuclide, name)] is None:
            res = self.provider.get_dataset(nuclide, name)
            self.datasets[(nuclide, name)] = Dataset(res)
        return self.datasets[(nuclide, name)]

    def get_adopted_levels(self, nuclide: tuple[int, int]) -> "Dataset":
        """Get adopted levels dataset of a nuclide

        Args:
            nuclide: Nuclide given in (nucleons, protons) format

        Returns:
            Dataset "ADOPTED LEVELS[…]" of given nuclide
        """
        name = self.provider.adopted_levels[nuclide]
        if self.datasets[(nuclide, name)] is None:
            res = Dataset(self.provider.get_adopted_levels(nuclide))
            self.datasets[(nuclide, name)] = res
        return self.datasets[(nuclide, name)]

    def get_datasets_by_nuclide(self, nuclide: tuple[int, int | None]) -> list[str]:
        """Get names of all datasets of a nuclide

        Args:
            nuclide: Nuclide given in (nucleons, protons) format.
                Use protons=None for generic mass-specific dataset.

        Returns:
            List of dataset identifier names for given nuclide
        """
        res = []
        for dnuclide, name in self.datasets:
            if dnuclide == nuclide:
                res.append(name)
        return res

    def get_indexed_nuclides(self) -> list[tuple[int, int]]:
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
        self.mass, self.protons = az_from_nucid(self.nucid)
        self.nucleus = (self.mass, self.protons)
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
        self.cross_references = {}
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
                        try:
                            self.comments[-1].append(line)
                        except IndexError:
                            self.comments.append([line])
                    else:
                        self.comments.append([line])
                else:
                    if flag_rectype in "BAGEL" or (
                        flag_rectype in " D" and flag_particle in "PAN"
                    ):
                        header = False
                    elif flag_rectype == "X":
                        crr = CrossReferenceRecord(self, line)
                        self.cross_references[crr.dssym] = crr
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
                        try:
                            comments[-1].append(line)
                        except IndexError:
                            comments.append([line])
                    else:
                        comments.append([line])
                else:
                    # This is a broken record!
                    warnings.warn("Record is malformed, parsing anyway.", stacklevel=2)
                    record.append(line)
            except (IndexError, ValueError):
                logger.error("Failed to parse record: %r", record)
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
            logger.error("Failed to parse record: %r", record)
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
        if level.ang_mom:
            return len(self.jpi_index[(ang_mom.val, ang_mom.parity)])

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.nucid} ({self.dataset_id})>"


class BaseRecord:
    pass


class Record(BaseRecord):
    def __init__(self, dataset, record, comments: list | None, xref: list | None):
        self.prop = dict()
        self.record = record
        self.dataset = dataset
        self.comments = []
        self._xref = xref
        self.parse_xref()
        if comments:
            for comment in comments:
                self.comments.append(GeneralCommentRecord(dataset, comment))

    def parse_xref(self):
        self.xref = {}
        if not self._xref:
            return
        for xref in self._xref:
            refs = re.search(r".*XREF=([^\$]*)(\$(.*))?", xref.strip())
            if refs is None:
                continue
            comments_all = refs.group(2)
            refs = re.findall(r"([A-Z])(?:\(([^\)]*)\))?", refs.group(1))
            for char, comment in refs:
                self.xref[char] = XReference(
                    char,
                    (comment or "") + (comments_all or ""),
                    self.dataset.cross_references[char],
                )

    def parse_entry(self, entry):
        entry = entry.strip()
        if not entry:
            return
        if "=" in entry:
            quant, value = entry.split("=", maxsplit=1)
            self.prop[quant.strip()] = value.strip()
            return
        if entry.startswith("%"):
            m = re.match(r"([A-Z]+)(.*)", entry[1:])
            if m:
                self.prop["%" + m.group(1)] = f"{m.group(2).strip()} AP"
                return
        for symb in ["|?", "?"]:
            if symb in entry:
                quant, value = entry.split(symb, maxsplit=1)
                self.prop[quant.strip()] = f"{value.strip()} AP"
                return
        for symb in ["<", ">"]:
            if symb in entry:
                quant, value = entry.split(symb, maxsplit=1)
                self.prop[quant.strip()] = symb + value.strip()
                return
        for abbr in ["GT", "LT", "GE", "LE", "AP", "CA", "SY"]:
            if f" {abbr} " in entry:
                quant, abbr, value = entry.split(" ", maxsplit=2)
                self.prop[quant.strip()] = f"{value.strip()} {abbr}"
                return
        if entry[-1] == "?":
            self.prop[entry[:-1]] = "?"
            return
        raise ValueError(f"Cannot process property: '{entry}'.")

    def load_prop(self, lines):
        for line in lines:
            for entry in line[9:].split("$"):
                self.parse_entry(entry)


class QValueRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.prop = slice_fields(line, QVALUE_FIELDS)
        self.prop["Q-"] += " " + self.prop["DQ-"]
        self.prop["N"] += " " + self.prop["DN"]
        self.prop["P"] += " " + self.prop["DP"]
        self.prop["A"] += " " + self.prop["DA"]

        self.q_beta_minus = Quantity(self.prop["Q-"])
        self.neutron_separation = Quantity(self.prop["N"])
        self.proton_separation = Quantity(self.prop["P"])
        self.alpha_decay = Quantity(self.prop["A"])

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: Q-={self.q_beta_minus},"
            f" N={self.neutron_separation}, P={self.proton_separation},"
            f" A={self.alpha_decay}>"
        )


class CrossReferenceRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.parent_dataset = dataset
        fields = slice_fields(line, XREF_FIELDS)
        self.dssym = fields["dssym"]
        self.dsid = fields["dsid"]

    def get_dataset(self):
        return ENSDF.active_ensdf.get_dataset(self.parent_dataset.nucleus, self.dsid)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.dsid}>"


class GeneralCommentRecord(BaseRecord):
    def __init__(self, dataset, comment):
        self.dataset = dataset
        self.comment = comment
        # self.continuation = line[5] not in ["1", " "]
        # self.comment_type = line[6]
        # self.rtype = line[7]
        # self.psym = line[8]
        # self.comment_text = line[9:80]

    def __repr__(self):
        if len(self.comment) > 40:
            return f"<{self.__class__.__name__}: '{self.comment[:40]}…'>"
        else:
            return f"<{self.__class__.__name__}: '{self.comment}'>"


class ParentRecord(Record):
    def __init__(self, dataset, record):
        super().__init__(dataset, record, None, None)
        self.prop.update(slice_fields(record, PARENT_FIELDS))
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["T"] += " " + self.prop["DT"]
        self.prop["QP"] += " " + self.prop["DQP"]
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.ang_mom = ang_mom_parser(self.prop["J"])
        self.half_life = Quantity(self.prop["T"])
        self.q_value = Quantity(self.prop["QP"], "KEV")


class NormalizationRecord(Record):
    def __init__(self, dataset, record):
        super().__init__(dataset, record, None, None)
        self.prop.update(slice_fields(record, NORMALIZATION_FIELDS))
        self.prop["NR"] += " " + self.prop["DNR"]
        self.prop["NT"] += " " + self.prop["DNT"]
        self.prop["BR"] += " " + self.prop["DBR"]
        self.prop["NB"] += " " + self.prop["DNB"]
        self.prop["NP"] += " " + self.prop["DNP"]
        self.load_prop(record[1:])

        self.branching_ratio = Quantity(self.prop["BR"])
        self.rel_intensity_multiplier = Quantity(self.prop["NR"])
        self.trans_intensity_multiplier = Quantity(self.prop["NT"])


class LevelRecord(Record):
    def __init__(self, dataset, record, comments, xref):
        super().__init__(dataset, record, comments, xref)
        self.prop.update(slice_fields(record[0], LEVEL_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["T"] += " " + self.prop["DT"]
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
        self.g_factor = Quantity(self.prop.get("G", ""))
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
        if "E+" not in self.prop["S"] and "+" in self.prop["S"]:
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

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.energy} {self.ang_mom}>"


class DecayRecord(Record):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref)
        self.dest_level = dest_level


class BetaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop.update(slice_fields(record[0], BETA_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["IB"] += " " + self.prop["DIB"]
        self.prop["LOGFT"] += " " + self.prop["DFT"]
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.energy}>"


class ECRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop.update(slice_fields(record[0], EC_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["IB"] += " " + self.prop["DIB"]
        self.prop["IE"] += " " + self.prop["DIE"]
        self.prop["LOGFT"] += " " + self.prop["DFT"]
        self.prop["TI"] += " " + self.prop["DTI"]
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.energy}>"


class AlphaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop.update(slice_fields(record[0], ALPHA_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["IA"] += " " + self.prop["DIA"]
        self.prop["HF"] += " " + self.prop["DHF"]
        self.load_prop(record[1:])

        self.energy = Quantity(self.prop["E"], "KEV")
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.energy}>"


class ParticleRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, dest_level):
        super().__init__(dataset, record, comments, xref, dest_level)
        self.prop["D"] = record[0][7]
        self.prop["Particle"] = record[0][8]
        self.prop.update(slice_fields(record[0], PARTICLE_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["IP"] += " " + self.prop["DIP"]
        self.prop["T"] += " " + self.prop["DT"]
        self.load_prop(record[1:])

        self.prompt_emission = self.prop["D"] == " "
        self.delayed_emission = self.prop["D"] == "D"

        self.energy = Quantity(self.prop["E"], "KEV")
        self.questionable = self.prop["Q"] == "?"
        self.expected = self.prop["Q"] == "S"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.energy}>"


class GammaRecord(DecayRecord):
    def __init__(self, dataset, record, comments, xref, orig_level):
        super().__init__(dataset, record, comments, xref, dest_level=None)
        self.orig_level = orig_level
        if self.orig_level:
            self.orig_level.add_decay(self)
        self.prop.update(slice_fields(record[0], GAMMA_FIELDS))
        self.prop["Q"] = record[0][79].strip()
        self.prop["E"] += " " + self.prop["DE"]
        self.prop["RI"] += " " + self.prop["DRI"]
        self.prop["MR"] += " " + self.prop["DMR"]
        self.prop["CC"] += " " + self.prop["DCC"]
        self.prop["TI"] += " " + self.prop["DTI"]
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
                    lvl
                    for lvl in self.dataset.levels
                    if lvl.energy.offset == self.energy.offset
                ],
                key=lambda x: abs(x.energy.val - dest_energy),
            )
            self.dest_level.populating.append(self)
        except ValueError:
            pass

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: {self.energy}"
            f"({self.orig_level.energy} {self.orig_level.ang_mom} → "
            f"{self.dest_level.energy} {self.dest_level.ang_mom})>"
        )


class ReferenceRecord(BaseRecord):
    def __init__(self, dataset, line):
        self.prop = slice_fields(line, REFERENCE_FIELDS)
        self.dataset = dataset


@dataclass
class XReference:
    char: str
    comments: str
    reference: CrossReferenceRecord


RECORD_TYPES: dict[str, type] = {
    "X": CrossReferenceRecord,
    "Q": QValueRecord,
    "N": NormalizationRecord,
    "L": LevelRecord,
    "B": BetaRecord,
    "E": ECRecord,
    "A": AlphaRecord,
    "G": GammaRecord,
}


def get_record_type(record):
    rtype = record[0][7]
    if rtype in " D" and record[0][8] in "PAN":
        return ParticleRecord
    try:
        return RECORD_TYPES[rtype]
    except KeyError:
        raise NotImplementedError(
            f"Unknown record with type '{rtype}': '{record[0]}'"
        ) from None


class Nuclide:
    def __init__(
        self,
        mass: int,
        protons: int,
        *,
        ensdf: "ENSDF | None" = None,
        version: str = "latest",
    ):
        self.mass = mass
        self.protons = protons
        self.ensdf = ensdf if ensdf is not None else get_active_ensdf(version=version)
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

    def get_daughters(self) -> Iterator[tuple[tuple[int, int], str]]:
        nucid = nucid_from_az((self.mass, self.protons)).strip()
        for nucid_i, name_i in self.ensdf.datasets:
            if name_i.startswith(nucid) and "DECAY" in name_i:
                yield (nucid_i, name_i)

    def __str__(self):
        element = ELEMENTS[self.protons]
        return f"{self.mass}{element}"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self}>"


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


def ang_mom_parser(ang_mom: str) -> "list[AngularMoment]":
    """
    Parse simple angular momement definitions such as 5/2+ or 4,5,6(-).
    More advanced definitions (silently) result in garbage.
    """
    if _is_simple_range(ang_mom):
        return _parse_simple_range(ang_mom)
    res = []
    for fragment, parity in rec_bracket_parser(ang_mom)[1]:
        for J in ang_mom_range_to_tuple(fragment):
            res.append(AngularMoment(J, parity))
    return res


def _is_simple_range(s: str) -> bool:
    if not any(sep in s for sep in (" to ", " TO ", ":")):
        return False
    return not any(c in s for c in "(),[]&")


def _parse_simple_range(s: str) -> "list[AngularMoment]":
    if " to " in s:
        start_str, stop_str = s.split(" to ", 1)
    elif " TO " in s:
        start_str, stop_str = s.split(" TO ", 1)
    elif ":" in s:
        start_str, stop_str = s.split(":", 1)
    else:
        return []
    start_parity = None
    if start_str and start_str[-1] in "+-":
        start_parity = start_str[-1]
        start_str = start_str[:-1]
    stop_parity = None
    if stop_str and stop_str[-1] in "+-":
        stop_parity = stop_str[-1]
        stop_str = stop_str[:-1]
    try:
        pairs = list(ang_mom_range_to_tuple(f"{start_str} to {stop_str}"))
    except (TypeError, ValueError):
        pairs = []
    if not pairs or not isinstance(pairs[0], tuple):
        return [AngularMoment(s, None)]
    res = []
    last = len(pairs) - 1
    for idx, J in enumerate(pairs):
        if idx == 0:
            parity = start_parity
        elif idx == last:
            parity = stop_parity
        else:
            parity = None
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
        if " to " in ang_mom or " TO " in ang_mom:
            start, stop = (
                ang_mom.split(" to ", 1)
                if " to " in ang_mom
                else ang_mom.split(" TO ", 1)
            )
        elif ":" in ang_mom:
            start, stop = ang_mom.split(":", 1)
        else:
            yield ang_mom_to_tuple(ang_mom)
            return
        start, div = ang_mom_to_tuple(start)
        stop, _ = ang_mom_to_tuple(stop)
        for i in range(start, stop + div, div):
            yield (i, div)
    except (TypeError, ValueError):
        yield ang_mom


class AngularMoment:
    def __init__(self, ang_mom, parity=None):
        self.div = None
        try:
            self.ang_mom, self.div = ang_mom
            self.val = self.ang_mom / self.div
        except (TypeError, ValueError, ZeroDivisionError):
            self.ang_mom = ang_mom
            self.val = None
        self.parity = parity

    def __repr__(self):
        if self.div is not None and self.div != 1:
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


def get_active_ensdf(version: str = "latest") -> "ENSDF":
    if ENSDF.active_ensdf is None:
        ENSDF.active_ensdf = ENSDF(version=version)
    return ENSDF.active_ensdf
