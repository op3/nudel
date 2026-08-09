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

"""Unit tests for the :func:`nudel.core.slice_fields` helper and the
module-level field-layout tables."""

from __future__ import annotations

import pytest
from nudel.core import (
    BETA_FIELDS,
    EC_FIELDS,
    GAMMA_FIELDS,
    LEVEL_FIELDS,
    PARTICLE_FIELDS,
    QVALUE_FIELDS,
    REFERENCE_FIELDS,
    XREF_FIELDS,
    slice_fields,
)


def _blank_line(length: int = 80) -> str:
    return " " * length


def _splice(line: str, start: int, text: str) -> str:
    return line[:start] + text + line[start + len(text) :]


def test_slice_fields_empty_line():
    line = _blank_line()
    fields = slice_fields(line, LEVEL_FIELDS)
    assert fields["E"] == ""
    assert fields["DE"] == ""
    assert fields["J"] == ""
    assert "Q" not in fields


def test_slice_fields_level_energy():
    line = _blank_line()
    line = _splice(line, 9, "    100.0")
    fields = slice_fields(line, LEVEL_FIELDS)
    assert fields["E"] == "100.0"
    assert fields["DE"] == ""
    assert "Q" not in fields


def test_slice_fields_qvalue():
    line = _blank_line()
    line = _splice(line, 9, "    -15000")
    line = _splice(line, 19, "50")
    fields = slice_fields(line, QVALUE_FIELDS)
    assert fields["Q-"] == "-15000"
    assert fields["DQ-"] == "50"


def test_slice_fields_gamma_multipolarity():
    line = _blank_line()
    line = _splice(line, 31, "[M1+E2]   ")
    fields = slice_fields(line, GAMMA_FIELDS)
    assert fields["M"] == "[M1+E2]"


def test_slice_fields_single_char_fields_stripped():
    line = _blank_line()
    line = _splice(line, 76, "?")
    fields = slice_fields(line, LEVEL_FIELDS)
    assert fields["C"] == "?"
    assert "Q" not in fields


def test_slice_fields_single_char_space_becomes_empty():
    line = _blank_line()
    fields = slice_fields(line, LEVEL_FIELDS)
    assert fields["C"] == ""
    assert fields["MS"] == ""
    assert "Q" not in fields


def test_slice_fields_xref():
    line = _blank_line()
    line = _splice(line, 8, "A")
    line = _splice(line, 9, " 24SI ADOPTED LEVELS        ")
    fields = slice_fields(line, XREF_FIELDS)
    assert fields["dssym"] == "A"
    assert fields["dsid"] == "24SI ADOPTED LEVELS"


def test_slice_fields_reference():
    line = _blank_line()
    line = _splice(line, 0, " 24")
    line = _splice(line, 9, "12345678")
    line = _splice(line, 17, "Nucl. Phys. A123, 1 (2000)            ")
    fields = slice_fields(line, REFERENCE_FIELDS)
    assert fields["MASS"] == "24"
    assert fields["KEYNUM"] == "12345678"
    assert fields["REFERENCE"] == "Nucl. Phys. A123, 1 (2000)"


@pytest.mark.parametrize(
    ("fields", "start", "text", "key", "expected"),
    [
        (LEVEL_FIELDS, 9, "    100.0", "E", "100.0"),
        (LEVEL_FIELDS, 19, "50", "DE", "50"),
        (LEVEL_FIELDS, 39, " 1.2 PS  ", "T", "1.2 PS"),
        (BETA_FIELDS, 41, "   6.123 ", "LOGFT", "6.123"),
        (EC_FIELDS, 31, "   50.0  ", "IE", "50.0"),
        (GAMMA_FIELDS, 21, "  100.0  ", "RI", "100.0"),
        (PARTICLE_FIELDS, 21, "  100.0  ", "IP", "100.0"),
    ],
)
def test_slice_fields_parametrized(fields, start, text, key, expected):
    line = _blank_line()
    line = _splice(line, start, text)
    result = slice_fields(line, fields)
    assert result[key] == expected


def test_slice_fields_returns_all_keys():
    line = _blank_line()
    for fields in [
        LEVEL_FIELDS,
        GAMMA_FIELDS,
        QVALUE_FIELDS,
        BETA_FIELDS,
        EC_FIELDS,
        PARTICLE_FIELDS,
        REFERENCE_FIELDS,
        XREF_FIELDS,
    ]:
        result = slice_fields(line, fields)
        assert set(result.keys()) == {name for name, _, _ in fields}


def test_slice_fields_uncertainty_pair():
    line = _blank_line()
    line = _splice(line, 9, "   100.0 ")
    line = _splice(line, 19, "50")
    fields = slice_fields(line, LEVEL_FIELDS)
    assert fields["E"] == "100.0"
    assert fields["DE"] == "50"
    combined = fields["E"] + " " + fields["DE"]
    assert combined == "100.0 50"
