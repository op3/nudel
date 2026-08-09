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

"""Tests for ``nudel.core.AngularMoment`` ``__repr__`` and ``__eq__``."""

import pytest
from nudel.core import AngularMoment


@pytest.mark.parametrize(
    "obj, expected",
    [
        (AngularMoment(3), "3"),
        (AngularMoment(3, "+"), "3+"),
        (AngularMoment((3, 2)), "3/2"),
        (AngularMoment((3, 2), "-"), "3/2-"),
        (AngularMoment((4, 1)), "4"),
        (AngularMoment((4, 1), "+"), "4+"),
    ],
)
def test_repr(obj, expected):
    assert repr(obj) == expected


def test_eq_div_tuple():
    assert AngularMoment((3, 2)) == (1.5, None)


def test_eq_plain_value_with_parity():
    assert AngularMoment(3, "+") == (3, "+")
