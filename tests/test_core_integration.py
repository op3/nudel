#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2026 nudel contributors.
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

"""Integration tests for ``nudel.core`` against synthetic ENSDF fixtures.

The fixtures in ``tests/data/synthetic.py`` describe a fictitious
superheavy nucleus ``50019`` (Z=119, A=500, N=381) — no such nuclide
exists in nature and no real ENSDF data is copied. The fixtures are
wired through ``ENSDFInMemoryProvider`` so the real
``Dataset``/``LevelRecord``/``GammaRecord`` parsers are exercised end
to end without touching the filesystem or network.
"""

from __future__ import annotations

import pytest
from nudel.core import ENSDF, BetaRecord, Dataset, GammaRecord, Nuclide
from nudel.provider import ENSDFInMemoryProvider

from tests.data.synthetic import DATASETS

NUCLEUS = (500, 119)


@pytest.fixture
def ensdf():
    """An ENSDF backed by the synthetic 50019 datasets, installed as the
    active global for the duration of the test (then cleared)."""
    prov = ENSDFInMemoryProvider(DATASETS)
    fake = ENSDF(provider=prov)
    ENSDF.active_ensdf = fake
    try:
        yield fake
    finally:
        ENSDF.active_ensdf = None


@pytest.fixture
def adopted(ensdf):
    return ensdf.get_dataset(NUCLEUS, "ADOPTED LEVELS, GAMMAS")


@pytest.fixture
def decay(ensdf):
    return ensdf.get_dataset(NUCLEUS, "500OG B- DECAY")


def test_dataset_header(adopted):
    assert adopted.nucid == "50019"
    assert adopted.mass == 500 and adopted.protons == 119
    assert adopted.nucleus == NUCLEUS
    assert adopted.dataset_id == "ADOPTED LEVELS, GAMMAS"
    assert adopted.dataset_ref == ""
    assert adopted.publication == "2026SM01"
    assert adopted.date is not None
    assert adopted.date.year == 2026 and adopted.date.month == 1


def test_history_parsed(adopted):
    assert adopted.history == {"TYP": "FUL", "AUT": "J. Smith", "DAT": "2026"}


def test_qvalue_record(adopted):
    assert len(adopted.qrecords) == 1
    q = adopted.qrecords[0]
    assert q.q_beta_minus.val == -15000.0
    assert q.q_beta_minus.pm == 50.0
    assert q.neutron_separation.val == 4200.0
    assert q.proton_separation.val == 5800.0
    assert q.alpha_decay.val == 3200.0


def test_cross_references(adopted):
    assert set(adopted.cross_references) == {"A", "B"}
    assert adopted.cross_references["A"].dssym == "A"
    assert adopted.cross_references["A"].dsid == "500OG B- DECAY"
    assert adopted.cross_references["B"].dsid == "50019 EC DECAY"


def test_normalization_record(adopted):
    assert len(adopted.normalization_records) == 1
    norm = adopted.normalization_records[0]
    assert norm.branching_ratio.val == 100.0
    assert norm.rel_intensity_multiplier.val == 1.0
    assert norm.trans_intensity_multiplier.val == 1.0


def test_header_comments(adopted):
    assert len(adopted.comments) == 1
    group = adopted.comments[0]
    assert len(group) == 2
    assert "fictitious superheavy nucleus" in group[0][9:]
    assert "no real ENSDF data" in group[1][9:]


def test_levels_count_and_ground_state(adopted):
    assert len(adopted.levels) == 9
    gs = adopted.levels[0]
    assert gs.energy.val == 0.0
    assert gs.half_life.val == 1.2
    assert gs.ang_mom == [(1.5, "-")]
    assert gs.state_num == 0


def test_level_fractional_jpi_and_halflife(adopted):
    lvl = adopted.levels[1]
    assert lvl.energy.val == 156.4
    assert lvl.energy.pm == pytest.approx(0.4)
    assert len(lvl.ang_mom) == 1
    am = lvl.ang_mom[0]
    assert am.val == 2.5
    assert am.parity == "+"
    assert lvl.half_life.val == 0.82
    assert lvl.half_life.pm == pytest.approx(0.07)


def test_level_metastable_flag(adopted):
    lvl = adopted.levels[2]
    assert lvl.metastable is True
    assert lvl.energy.val == 412.3


def test_level_expected_flag(adopted):
    lvl = adopted.levels[3]
    assert lvl.expected is True
    assert lvl.questionable is False


def test_level_questionable_flag(adopted):
    lvl = adopted.levels[4]
    assert lvl.questionable is True
    assert lvl.expected is False


def test_level_offset_energy(adopted):
    lvl = adopted.levels[5]
    assert lvl.energy.offset == "X"
    assert lvl.energy.val == 1850.0


def test_level_spectroscopic_strength(adopted):
    lvl = adopted.levels[6]
    assert len(lvl.spec_strength) == 1
    assert lvl.spec_strength[0].val == 0.31
    assert lvl.spec_strength[0].pm == pytest.approx(0.03)


def test_level_decay_ratio_continuation(adopted):
    lvl = adopted.levels[7]
    assert "P" in lvl.decay_ratio
    assert lvl.decay_ratio["P"].val == 100.0


def test_ang_mom_range(adopted):
    lvl = adopted.levels[8]
    assert len(lvl.ang_mom) == 3
    assert {am.val for am in lvl.ang_mom} == {4.0, 5.0, 6.0}
    assert lvl.ang_mom[-1].parity == "-"


def test_jpi_index_groups_same_parity(adopted):
    assert (1.5, "-") in adopted.jpi_index
    assert (2.5, "+") in adopted.jpi_index
    assert (4.0, "+") in adopted.jpi_index
    assert len(adopted.jpi_index[(1.5, "-")]) == 1


def test_jpi_index_includes_all_ang_mom_for_multi_jpi_level(adopted):
    lvl = adopted.levels[8]
    assert (4.0, None) in adopted.jpi_index
    assert (5.0, None) in adopted.jpi_index
    assert (6.0, "-") in adopted.jpi_index
    assert lvl in adopted.jpi_index[(4.0, None)]
    assert lvl in adopted.jpi_index[(5.0, None)]


def test_gamma_basic_fields(adopted):
    gs = adopted.levels[0]
    assert len(gs.decays) == 1
    g = gs.decays[0]
    assert isinstance(g, GammaRecord)
    assert g.energy.val == 156.4
    assert g.energy.pm == pytest.approx(0.4)
    assert g.rel_intensity.val == 100.0
    assert g.multipolarity == "[E1]"
    assert g.conversion_coeff.val == pytest.approx(1.28e-3)
    assert g.conversion_coeff.pm == pytest.approx(2e-5)


def test_gamma_m1_e2_mixing_and_ti(adopted):
    lvl = adopted.levels[1]
    g = lvl.decays[0]
    assert g.multipolarity == "[M1+E2]"
    assert g.mixing_ratio.val == 0.42
    assert g.mixing_ratio.pm == pytest.approx(0.002)
    assert g.rel_tot_trans_intensity.val == 0.42
    assert g.rel_tot_trans_intensity.pm == pytest.approx(0.01)


def test_gamma_be_bm_continuation_attrs(adopted):
    lvl = adopted.levels[1]
    g = lvl.decays[0]
    assert "BE1W" in g.attr
    assert "BM1W" in g.attr
    assert g.attr["BE1W"].val == pytest.approx(0.042)
    assert g.attr["BM1W"].val == pytest.approx(0.420)


def test_gamma_fl_dest_level_override(adopted):
    lvl = adopted.levels[1]
    g = lvl.decays[0]
    assert g.dest_level is adopted.levels[0]
    assert g.dest_level.energy.val == 0.0


def test_gamma_questionable_flag(adopted):
    lvl = adopted.levels[8]
    g = lvl.decays[0]
    assert g.questionable is True


def test_gamma_xref_continuation(adopted):
    lvl = adopted.levels[8]
    g = lvl.decays[1]
    assert "A" in g.xref
    assert g.xref["A"].char == "A"


def test_gamma_dest_level_determined_by_energy(adopted):
    lvl = adopted.levels[8]
    g = lvl.decays[0]
    assert g.energy.val == 412.3
    assert g.dest_level is adopted.levels[7]
    assert g.dest_level.energy.val == 2680.0


def test_decay_parent_record(decay):
    assert len(decay.parents) == 1
    p = decay.parents[0]
    assert p.energy.val == 0.0
    assert p.ang_mom == [(0, "+")]
    assert p.half_life.val == 1.5
    assert p.q_value.val == 1520.0


def test_decay_beta_records(decay):
    betas = [r for r in decay.records if isinstance(r, BetaRecord)]
    assert len(betas) == 2
    assert betas[0].energy.val == 15200.0
    assert betas[0].prop["IB"].startswith("100")
    assert betas[0].prop["LOGFT"].startswith("6.42")
    assert betas[1].energy.val == 15044.0


def test_decay_beta_eav_continuation(decay):
    betas = [r for r in decay.records if isinstance(r, BetaRecord)]
    assert "EAV" in betas[0].prop
    assert betas[0].prop["EAV"] == "6433.44 49"


def test_decay_gamma_record(decay):
    gammas = [r for r in decay.records if isinstance(r, GammaRecord)]
    assert len(gammas) == 1
    assert gammas[0].energy.val == 156.4
    assert gammas[0].multipolarity == "[M1]"
    assert gammas[0].dest_level is decay.levels[0]


def test_nuclide_adopted_levels(ensdf):
    nuc = Nuclide(500, 119, ensdf=ensdf)
    assert isinstance(nuc.adopted_levels, Dataset)
    assert nuc.adopted_levels.nucid == "50019"
    assert nuc.mass == 500 and nuc.protons == 119


def test_nuclide_get_isomers(ensdf):
    nuc = Nuclide(500, 119, ensdf=ensdf)
    isomers = list(nuc.get_isomers())
    assert isomers[0] is nuc.adopted_levels.levels[0]
    assert isomers[0].energy.val == 0.0
    metastable = [lvl for lvl in isomers[1:]]
    assert len(metastable) == 1
    assert metastable[0].metastable is True
    assert metastable[0].energy.val == 412.3


def test_get_datasets_by_nuclide(ensdf):
    names = ensdf.get_datasets_by_nuclide(NUCLEUS)
    assert set(names) == {"ADOPTED LEVELS, GAMMAS", "500OG B- DECAY"}
