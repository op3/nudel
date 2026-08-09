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
from nudel.core import AngularMoment, ang_mom_parser, ang_mom_range_to_tuple


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


def test_angular_moment_non_tuple_fallback():
    am = AngularMoment(3)
    assert am.ang_mom == 3
    assert am.div is None
    assert am.val is None


def test_angular_moment_wrong_length_tuple_fallback():
    am = AngularMoment((1, 2, 3))
    assert am.ang_mom == (1, 2, 3)
    assert am.div is None
    assert am.val is None


def test_angular_moment_zero_division_fallback():
    am = AngularMoment((3, 0))
    assert am.ang_mom == (3, 0)
    assert am.div == 0
    assert am.val is None


def test_ang_mom_range_non_string_fallback():
    assert list(ang_mom_range_to_tuple(5)) == [5]


def test_ang_mom_range_non_numeric_fallback():
    assert list(ang_mom_range_to_tuple("abc")) == ["abc"]


def test_ang_mom_range_valid():
    assert list(ang_mom_range_to_tuple("3/2 TO 7/2")) == [
        (3, 2),
        (5, 2),
        (7, 2),
    ]


def test_ang_mom_range_lowercase_to():
    assert list(ang_mom_range_to_tuple("2 to 6")) == [
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
    ]


def test_ang_mom_range_lowercase_to_with_parity_via_parser():
    assert [(a.val, a.parity) for a in ang_mom_parser("3 to 6-")] == [
        (3.0, "-"),
        (4.0, "-"),
        (5.0, "-"),
        (6.0, "-"),
    ]


def test_ang_mom_range_lowercase_to_plus_endpoints():
    assert [(a.val, a.parity) for a in ang_mom_parser("2+ to 6+")] == [
        (2.0, "+"),
        (3.0, "+"),
        (4.0, "+"),
        (5.0, "+"),
        (6.0, "+"),
    ]


def test_ang_mom_range_uppercase_TO_still_works():
    assert [(a.val, a.parity) for a in ang_mom_parser("3 TO 6-")] == [
        (3.0, "-"),
        (4.0, "-"),
        (5.0, "-"),
        (6.0, "-"),
    ]


def test_ang_mom_range_colon_still_works():
    assert list(ang_mom_range_to_tuple("3:6")) == [(3, 1), (4, 1), (5, 1), (6, 1)]
