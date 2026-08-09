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

import pytest
from nudel.core import (
    AlphaRecord,
    BetaRecord,
    CrossReferenceRecord,
    ECRecord,
    GammaRecord,
    LevelRecord,
    NormalizationRecord,
    ParticleRecord,
    QValueRecord,
    get_record_type,
)


def _record(rtype: str, col8: str = " ") -> list[str]:
    line = " " * 80
    return [line[:7] + rtype + col8 + line[9:]]


@pytest.mark.parametrize(
    "rtype, expected",
    [
        ("X", CrossReferenceRecord),
        ("Q", QValueRecord),
        ("N", NormalizationRecord),
        ("L", LevelRecord),
        ("B", BetaRecord),
        ("E", ECRecord),
        ("A", AlphaRecord),
        ("G", GammaRecord),
    ],
)
def test_record_type_lookup(rtype, expected):
    assert get_record_type(_record(rtype)) is expected


@pytest.mark.parametrize("col8", ["P", "A", "N"])
@pytest.mark.parametrize("rtype", [" ", "D"])
def test_record_type_particle(rtype, col8):
    assert get_record_type(_record(rtype, col8)) is ParticleRecord


def test_record_type_unknown():
    with pytest.raises(NotImplementedError, match="Unknown record with type"):
        get_record_type(_record("Z"))


def test_record_type_space_not_particle():
    with pytest.raises(NotImplementedError, match="Unknown record with type"):
        get_record_type(_record(" ", "X"))
