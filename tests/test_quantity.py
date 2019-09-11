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

"""Tests for nudel.util.Quantity"""

from math import isnan, isclose
import pytest

from nudel.util import Quantity, Limit, Dimension, Sign, get_unit


QUANTITY_DEFAULT = {
    'val': float('nan'),
    'pm': float('nan'),
    'plus': float('nan'),
    'minus': float('nan'),
    'upper_bound': float('nan'),
    'lower_bound': float('nan'),
    'upper_bound_inclusive': None,
    'lower_bound_inclusive': None,
    'exponent': 0,
    'decimals': 0,
    'sign': Sign.UNSPECIFIED,
    'approximate': False,
    'calculated': False,
    'from_systematics': False,
    'questionable': False,
    'assumed': False,
    'unit': None,
    'named': None,
    'offset_l': None,
    'offset_r': None,
    'reference': None,
    'comment': None
}

def cmp_nan_safe(a, b):
    try:
        if isnan(a):
            return isnan(b)
    except:
        pass
    return a == b

@pytest.mark.parametrize("quantity, mod_dict, printed", [
    ["", {
    }, "nan"],
    ["-0.16 5", {
        "val": -0.16,
        "pm": 0.05,
        "decimals": 2,
        "sign": Sign.NEGATIVE,
    }, "-0.16(5)"],
    ["(0.062 +19-37)", {
        "val": 0.062,
        "plus": 0.019,
        "minus": 0.037,
        "decimals": 3,
        "calculated": True,
    }, "(0.062(+19-37))"],
    ["1189.7", {
        "val": 1189.7,
        "decimals": 1,
    }, "1189.7"],
    ["(6 +4-5)", {
        "val": 6.0,
        "plus": 4,
        "minus": 5,
        "calculated": True,
    }, "(6(+4-5))"],
    ["70 4", {
        "val": 70.0,
        "pm": 4,
    }, "70(4)"],
    ["914.1+X 3", {
        "val": 914.1,
        "pm": 0.30000000000000004,
        "decimals": 1,
        "offset_r": "X",
    }, "914.1(3) + X"],
    ["1693.9 6", {
        "val": 1693.9,
        "pm": 0.6000000000000001,
        "decimals": 1,
    }, "1693.9(6)"],
    ["100", {
        "val": 100.0,
    }, "100"],
    ["10.4 PS +28-14", {
        "val": 10.4,
        "plus": 2.8000000000000003,
        "minus": 1.4000000000000001,
        "decimals": 1,
        "unit": get_unit("ps"),
    }, "10.4(+28-14) ps"],
    ["6.1 PS 3", {
        "val": 6.1,
        "pm": 0.30000000000000004,
        "decimals": 1,
        "unit": get_unit("ps"),
    }, "6.1(3) ps"],
    ["0.3 LT", {
        "upper_bound": 0.3,
        "upper_bound_inclusive": False,
        "decimals": 1,
    }, "< 0.3"],
    ["16 LT", {
        "upper_bound": 16.0,
        "upper_bound_inclusive": False,
    }, "< 16"],
    ["2.21E3", {
        "val": 2210.0,
        "exponent": 3,
        "decimals": 2,
    }, "2.21e3"],
    ["1.25E+3 13", {
        "val": 1250.0,
        "pm": 130,
        "exponent": 3,
        "decimals": 2,
    }, "1.25(13)e3"],
    ["2.9E+2 +22-28", {
        "val": 290.0,
        "plus": 220,
        "minus": 280,
        "exponent": 2,
        "decimals": 1,
    }, "2.9(+22-28)e2"],
    ["-1.586E4 10", {
        "val": -15860.0,
        "pm": 100,
        "exponent": 4,
        "decimals": 3,
        "sign": Sign.NEGATIVE,
    }, "-1.586(10)e4"],
    ["550 PS 20", {
        "val": 550.0,
        "pm": 20,
        "unit": get_unit("ps"),
    }, "550(20) ps"],
    ["0.3 NS LE", {
        "upper_bound": 0.3,
        "upper_bound_inclusive": True,
        "decimals": 1,
        "unit": get_unit("ns"),
    }, "≤ 0.3 ns"],
    ["8E+2", {
        "val": 800.0,
        "exponent": 2,
    }, "8e2"],
    ["7 PS LE", {
        "upper_bound": 7.0,
        "upper_bound_inclusive": True,
        "unit": get_unit("ps"),
    }, "≤ 7 ps"],
    ["-8150 60", {
        "val": -8150.0,
        "pm": 60,
        "sign": Sign.NEGATIVE,
    }, "-8150(60)"],
    ["<88", {
        "upper_bound": 88.0,
        "upper_bound_inclusive": False,
    }, "< 88"],
    ["+11.8 +44-20", {
        "val": 11.8,
        "plus": 4.4,
        "minus": 2.0,
        "decimals": 1,
        "sign": Sign.POSITIVE,
    }, "+11.8(+44-20)"],
    ["STABLE", {
        "val": float('inf'),
        "sign": Sign.POSITIVE,
        "named": 'stable',
        "unit": get_unit("s"),
    }, "stable"],
    ["WEAK", {
        "val": 0.0,
        "sign": Sign.POSITIVE,
        "named": 'weak',
    }, "weak"],
    ["-13 +3-7", {
        "val": -13.0,
        "plus": 3,
        "minus": 7,
        "sign": Sign.NEGATIVE,
    }, "-13(+3-7)"],
    ["+7.1", {
        "val": 7.1,
        "decimals": 1,
        "sign": Sign.POSITIVE,
    }, "+7.1"],
    ["0.0+X", {
        "val": 0.0,
        "decimals": 1,
        "offset_r": "X",
    }, "0.0 + X"],
    ["X", {
        "val": 0.0,
        "offset_l": "X",
    }, "X"],
    ["6.0 NS", {
        "val": 6.0,
        "decimals": 1,
        "unit": get_unit("ns"),
    }, "6.0 ns"],
    ["2.20E4 SY", {
        "val": 22000.0,
        "exponent": 4,
        "decimals": 2,
        "from_systematics": True,
    }, "2.20e4"],
    ["-9.E2 SY", {
        "val": -900.0,
        "exponent": 2,
        "sign": Sign.NEGATIVE,
        "from_systematics": True,
    }, "-9e2"],
    ["-650 SY", {
        "val": -650.0,
        "sign": Sign.NEGATIVE,
        "from_systematics": True,
    }, "-650"],
    [">0.00020", {
        "lower_bound": 0.0002,
        "lower_bound_inclusive": False,
        "decimals": 5,
    }, "> 0.00020"],
    [">4.6E-6", {
        "lower_bound": 4.599999999999999e-06,
        "lower_bound_inclusive": False,
        "exponent": -6,
        "decimals": 1,
    }, "> 4.6e-6"],
    ["6.7E+20 Y GE", {
        "lower_bound": 6.7e+20,
        "lower_bound_inclusive": True,
        "exponent": 20,
        "decimals": 1,
        "unit": get_unit("a"),
    }, "≥ 6.7e20 a"],
    ["43 MS +21-15", {
        "val": 43.0,
        "plus": 21,
        "minus": 15,
        "unit": get_unit("ms"),
    }, "43(+21-15) ms"],
    ["0+X", {
        "val": 0.0,
        "offset_r": "X",
    }, "0 + X"],
    ["9E1 8", {
        "val": 90.0,
        "pm": 80,
        "exponent": 1,
    }, "9(8)e1"],
    [".008", {
        "val": 0.008,
        "decimals": 3,
    }, "0.008"],
    ["13620+X 3", {
        "val": 13620.0,
        "pm": 3,
        "offset_r": "X",
    }, "13620(3) + X"],
    ["-1.0 AP", {
        "val": -1.0,
        "decimals": 1,
        "sign": Sign.NEGATIVE,
        "approximate": True,
    }, "~ -1.0"],
    ["1.20E3 Y 18", {
        "val": 1200.0,
        "pm": 180,
        "exponent": 3,
        "decimals": 2,
        "unit": get_unit("a"),
    }, "1.20(18)e3 a"],
    ["200 KEV", {
        "val": 200.0,
        "unit": get_unit("keV"),
    }, "200 keV"],
    ["10E-3 EV 2", {
        "val": 0.01,
        "pm": 0.002,
        "exponent": -3,
        "unit": get_unit("eV"),
    }, "10(2)e-3 eV"],
    ["SN+0.02343 2", {
        "val": 0.02343,
        "pm": 2e-05,
        "decimals": 5,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
    }, "SN+0.02343(2)"],
    ["9E+1 +4-5", {
        "val": 90.0,
        "plus": 40,
        "minus": 50,
        "exponent": 1,
    }, "9(+4-5)e1"],
    ["X+12772.6", {
        "val": 12772.6,
        "decimals": 1,
        "sign": Sign.POSITIVE,
        "offset_l": "X",
    }, "X+12772.6"],
    ["X+18439 17", {
        "val": 18439.0,
        "pm": 17,
        "sign": Sign.POSITIVE,
        "offset_l": "X",
    }, "X+18439(17)"],
    ["+0.48 -8+6", {
        "val": 0.48,
        "plus": 0.06,
        "minus": 0.08,
        "decimals": 2,
        "sign": Sign.POSITIVE,
    }, "+0.48(+6-8)"],
    ["SN+58", {
        "val": 58.0,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
    }, "SN+58"],
    ["2000+Y AP", {
        "val": 2000.0,
        "approximate": True,
        "offset_r": "Y",
    }, "~ 2000 + Y"],
    ["2E-4 LE", {
        "upper_bound": 0.0002,
        "upper_bound_inclusive": True,
        "exponent": -4,
    }, "≤ 2e-4"],
    ["-1232E+1 17", {
        "val": -12320.0,
        "pm": 170,
        "exponent": 1,
        "sign": Sign.NEGATIVE,
    }, "-1232(17)e1"],
    ["1.14E-4 EV", {
        "val": 0.00011399999999999999,
        "exponent": -4,
        "decimals": 2,
        "unit": get_unit("eV"),
    }, "1.14e-4 eV"],
    ["6E-2 EV GT", {
        "lower_bound": 0.06,
        "lower_bound_inclusive": False,
        "exponent": -2,
        "unit": get_unit("eV"),
    }, "> 6e-2 eV"],
    [".0003 EV 4", {
        "val": 0.0003,
        "pm": 0.0004,
        "decimals": 4,
        "unit": get_unit("eV"),
    }, "0.0003(4) eV"],
    ["-4014", {
        "val": -4014.0,
        "sign": Sign.NEGATIVE,
    }, "-4014"],
    ["SN+X", {
        "val": 0.0,
        "offset_l": "SN",
        "offset_r": "X",
    }, "SN + X"],
    ["1.5E+2 FS +15-6", {
        "val": 150.0,
        "plus": 150,
        "minus": 60,
        "exponent": 2,
        "decimals": 1,
        "unit": get_unit("fs"),
    }, "1.5(+15-6)e2 fs"],
    [".00005 2", {
        "val": 5e-05,
        "pm": 2e-05,
        "decimals": 5,
    }, "0.00005(2)"],
    ["+8 -4+7", {
        "val": 8.0,
        "plus": 7,
        "minus": 4,
        "sign": Sign.POSITIVE,
    }, "+8(+7-4)"],
    ["-7E1 +4-57", {
        "val": -70.0,
        "plus": 40,
        "minus": 570,
        "exponent": 1,
        "sign": Sign.NEGATIVE,
    }, "-7(+4-57)e1"],
    ["2.6 -5+8", {
        "val": 2.6,
        "plus": 0.8,
        "minus": 0.5,
        "decimals": 1,
    }, "2.6(+8-5)"],
    ["-1.047E4", {
        "val": -10470.0,
        "exponent": 4,
        "decimals": 3,
        "sign": Sign.NEGATIVE,
    }, "-1.047e4"],
    ["0.52 NS -5+9", {
        "val": 0.52,
        "plus": 0.09,
        "minus": 0.05,
        "decimals": 2,
        "unit": get_unit("ns"),
    }, "0.52(+9-5) ns"],
    ["SN+Y", {
        "val": 0.0,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
        "offset_r": "Y",
    }, "SN + Y"],
    ["<1.0 +19-10", {
        "plus": 1.9000000000000001,
        "minus": 1.0,
        "upper_bound": 1.0,
        "upper_bound_inclusive": False,
        "decimals": 1,
    }, "< 1.0(+19-10)"],
    ["SN+380-426", {
        "val": 0.0,
        "plus": 380,
        "minus": 426,
        "offset_l": "SN",
    }, "SN(+380-426)"],
    ["SN+.000802 5", {
        "val": 0.000802,
        "pm": 4.9999999999999996e-06,
        "decimals": 6,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
    }, "SN+0.000802(5)"],
    ["Y+5.0E2 43", {
        "val": 500.0,
        "pm": 430,
        "exponent": 2,
        "decimals": 1,
        "sign": Sign.POSITIVE,
        "offset_l": "Y",
    }, "Y+5.0(43)e2"],
    ["+0.16 PS +8-4", {
        "val": 0.16,
        "plus": 0.08,
        "minus": 0.04,
        "decimals": 2,
        "sign": Sign.POSITIVE,
        "unit": get_unit("ps"),
    }, "+0.16(+8-4) ps"],
    ["-.036 13", {
        "val": -0.036,
        "pm": 0.013000000000000001,
        "decimals": 3,
        "sign": Sign.NEGATIVE,
    }, "-0.036(13)"],
    ["-.08 +16-12", {
        "val": -0.08,
        "plus": 0.16,
        "minus": 0.12,
        "decimals": 2,
        "sign": Sign.NEGATIVE,
    }, "-0.08(+16-12)"],
    ["-1.8E2 +11-46", {
        "val": -180.0,
        "plus": 110,
        "minus": 460,
        "exponent": 2,
        "decimals": 1,
        "sign": Sign.NEGATIVE,
    }, "-1.8(+11-46)e2"],
    ["-9E3 SY", {
        "val": -9000.0,
        "exponent": 3,
        "sign": Sign.NEGATIVE,
        "from_systematics": True,
    }, "-9e3"],
    ["SN+0.0691 LT", {
        "val": 0.0,
        "upper_bound": 0.0691,
        "upper_bound_inclusive": False,
        "decimals": 4,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
    }, "< SN0.0691"],
    ["<5E-5", {
        "upper_bound": 5e-05,
        "upper_bound_inclusive": False,
        "exponent": -5,
    }, "< 5e-5"],
    ["<0.00213 5", {
        "pm": 5e-05,
        "upper_bound": 0.00213,
        "upper_bound_inclusive": False,
        "decimals": 5,
    }, "< 0.00213(5)"],
    ["SP+8.70E+3", {
        "val": 8700.0,
        "exponent": 3,
        "decimals": 2,
        "sign": Sign.POSITIVE,
        "offset_l": "SP",
    }, "SP+8.70e3"],
    ["<1.4E-5 5", {
        "pm": 4.9999999999999996e-06,
        "upper_bound": 1.4e-05,
        "upper_bound_inclusive": False,
        "exponent": -5,
        "decimals": 1,
    }, "< 1.4(5)e-5"],
    ["52E2 FS +52-17", {
        "val": 5200.0,
        "plus": 5200,
        "minus": 1700,
        "exponent": 2,
        "unit": get_unit("fs"),
    }, "52(+52-17)e2 fs"],
    [".004 CA", {
        "val": 0.004,
        "decimals": 3,
        "calculated": True,
    }, "(0.004)"],
    ["0.00594 15 if E2 TRANSITION.", {
        "val": 0.00594,
        "pm": 0.00015000000000000001,
        "decimals": 5,
        "comment": "if E2 TRANSITION.",
    }, "0.00594(15)"],
    ["SP+4962 AP", {
        "val": 4962.0,
        "sign": Sign.POSITIVE,
        "approximate": True,
        "offset_l": "SP",
    }, "~ SP+4962"],
    ["SN+1713E-6 4", {
        "val": 0.001713,
        "pm": 4e-06,
        "exponent": -6,
        "sign": Sign.POSITIVE,
        "offset_l": "SN",
    }, "SN+1713(4)e-6"],
    [">100 +40-90", {
        "plus": 40,
        "minus": 90,
        "lower_bound": 100.0,
        "lower_bound_inclusive": False,
    }, "> 100(+40-90)"],
    [">46 15", {
        "pm": 15,
        "lower_bound": 46.0,
        "lower_bound_inclusive": False,
    }, "> 46(15)"],
    [">1.2E+2 +36-6", {
        "plus": 360,
        "minus": 60,
        "lower_bound": 120.0,
        "lower_bound_inclusive": False,
        "exponent": 2,
        "decimals": 1,
    }, "> 1.2(+36-6)e2"],
    ["<8E-7 4", {
        "pm": 4e-07,
        "upper_bound": 8e-07,
        "upper_bound_inclusive": False,
        "exponent": -7,
    }, "< 8(4)e-7"],
    [".20E+3 3", {
        "val": 200.0,
        "pm": 30,
        "exponent": 3,
        "decimals": 2,
    }, "0.20(3)e3"],
    ["4939.8+X AP", {
        "val": 4939.8,
        "decimals": 1,
        "approximate": True,
        "offset_r": "X",
    }, "~ 4939.8 + X"],
])
def test_quantity(quantity, mod_dict, printed):
    q = Quantity(quantity)
    for k, v in QUANTITY_DEFAULT.items():
        if k in mod_dict:
            assert cmp_nan_safe(mod_dict[k], q.__dict__[k])
        else:
            assert cmp_nan_safe(v, q.__dict__[k])
    assert printed == str(q)

def test_default_unit():
    q = Quantity("45 2", default_unit="KEV")
    assert q.unit == get_unit("keV")

def test_default_unit_no_overwrite():
    q = Quantity("45 MEV 2", default_unit="KEV")
    assert q.unit == get_unit("MeV")

# TODO: The following quantities currently fail:
#   '6.3 PS 9-60', '0.61,0.40', '0.03-0.04', '.05,.1'

def test_quantity_cast_unit():
    qfs = Quantity("10 FS")
    assert isclose(qfs.val, 1e1)
    assert qfs.unit == get_unit("fs")

    qas = qfs.cast_to_unit("as")
    assert isclose(qas.val, 1e4)
    assert qas.unit == get_unit("as")

    qns = qfs.cast_to_unit("ns")
    assert isclose(qns.val, 1e-5)
    assert qns.unit == get_unit("ns")

    
