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

"""Tests verifying parse errors are logged instead of printed to stdout."""

import logging

import pytest
from nudel.core import ENSDF
from nudel.provider import ENSDFInMemoryProvider

# Valid 40-char ID record for nucid "  1H" (A=1, Z=1), followed by a body
# line that is recognized as a level record (flag_rectype == "L" at col 7)
# but is far too short for LevelRecord's column slicing, which raises
# IndexError on `record[0][79]` — caught by the final except block.
# Single trailing newline: `dataset_plain.split("\n")` yields
# `[id_record, body_line, ""]`, and `self.raw[:-1]` drops the empty string.
MALFORMED = "  1H     ADOPTED LEVELS" + " " * 17 + "\n  1H   L \n"


def test_parse_error_logs_at_error_level(caplog):
    prov = ENSDFInMemoryProvider({((1, 1), "ADOPTED LEVELS"): MALFORMED})
    ensdf = ENSDF(provider=prov)
    ENSDF.active_ensdf = ensdf
    try:
        with (
            caplog.at_level(logging.ERROR, logger="nudel.core"),
            pytest.raises((IndexError, ValueError)),
        ):
            ensdf.get_dataset((1, 1), "ADOPTED LEVELS")
        assert any("Failed to parse record" in rec.message for rec in caplog.records)
    finally:
        ENSDF.active_ensdf = None
