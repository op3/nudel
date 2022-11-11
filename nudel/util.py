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

"""helper functions for nudel"""

import copy
import enum
import re
import math
from math import isnan
import warnings
from typing import Tuple, Optional, NamedTuple, Union
from functools import lru_cache


ELEMENTS = [
    "Nn",
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
]

ALT_CHARS1 = {
    "!": "",
    '"': "",
    "#": "§",
    "$": "e",
    "%": "√",
    "&": "≡",
    "'": "°",
    "(": "←",
    ")": "→",
    "*": "×",
    "+": "±",
    ",": "½",
    "–": "∓",
    ".": "∝",
    "/": "÷",
    "0": "(",
    "1": ")",
    "2": "[",
    "3": "]",
    "4": "〈",
    "5": "〉",
    "6": "√",
    "7": "∫",
    "8": "∏",
    "9": "∑",
    ":": "†",
    ";": "‡",
    "<": "≤",
    "=": "≠",
    ">": "≥",
    "?": "≈",
    "@": "∞",
    "A": "Α",
    "B": "Β",
    "C": "Η",
    "D": "∆",
    "E": "Ε",
    "F": "Φ",
    "G": "Γ",
    "H": "Χ",
    "I": "Ι",
    "J": "∼",
    "K": "Κ",
    "L": "Λ",
    "M": "Μ",
    "N": "Ν",
    "O": "Ο",
    "P": "Π",
    "Q": "Θ",
    "R": "Ρ",
    "S": "Σ",
    "T": "Τ",
    "U": "Υ",
    "V": "∇",
    "W": "Ω",
    "X": "Ξ",
    "Y": "Ψ",
    "Z": "Ζ",
    "[": "{",
    "]": "}",
    "^": "↑",
    "_": "↓",
    "‘": "′",
    "a": "α",
    "b": "β",
    "c": "η",
    "d": "δ",
    "e": "ε",
    "f": "φ",
    "g": "γ",
    "h": "χ",
    "i": "ι",
    "j": "∈",
    "k": "κ",
    "l": "λ",
    "m": "μ",
    "n": "ν",
    "o": "ο",
    "p": "π",
    "q": "θ",
    "r": "ρ",
    "s": "σ",
    "t": "τ",
    "u": "υ",
    "v": "?",
    "w": "ω",
    "x": "ξ",
    "y": "ψ",
    "z": "ζ",
}

ALT_CHARS2 = {
    "!": "!",
    '"': '"',
    "#": "⊗",
    "$": "$",
    "%": "%",
    "&": "&",
    "'": "Å",
    "(": "(",
    ")": ")",
    "*": "·",
    "+": "+",
    ",": ",",
    "–": "–",
    ".": ".",
    "/": "/",
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    ":": ":",
    ";": ";",
    "<": "<",
    "=": "=",
    ">": ">",
    "?": "?",
    "@": "•",
    "A": "Ä",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "É",
    "F": "F",
    "G": "G",
    "H": "H",
    "I": "I",
    "J": "J",
    "K": "K",
    "L": "L",
    "M": "M",
    "N": "N",
    "O": "Ö",
    "P": "P",
    "Q": "Õ",
    "R": "R",
    "S": "S",
    "T": "T",
    "U": "Ü",
    "V": "V",
    "W": "W",
    "X": "X",
    "Y": "Y",
    "Z": "Z",
    "[": "[",
    "]": "]",
    "^": "^",
    "_": "_",
    "‘": "‘",
    "a": "ä",
    "b": "b",
    "c": "c",
    "d": "d",
    "e": "é",
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "i",
    "j": "j",
    "k": "k",
    "l": "λ",
    "m": "m",
    "n": "n",
    "o": "ö",
    "p": "p",
    "q": "õ",
    "r": "r",
    "s": "s",
    "t": "t",
    "u": "ü",
    "v": "v",
    "w": "w",
    "x": "x",
    "y": "y",
    "z": "z",
}


def az_from_nucid(nucid: str) -> Tuple[int, int]:
    mass, nucleus = re.compile(r"(\d+)([A-Za-z]*)?").search(nucid).groups()
    if len(mass) > 3:
        return int(nucid[:3]), int(nucid[3:]) + 100
    try:
        return int(mass), ELEMENTS.index(nucleus[0] + nucleus[1:].lower())
    except IndexError:
        return int(nucid), None


def nucid_from_az(nucleus):
    mass, Z = nucleus
    try:
        if Z >= len(ELEMENTS) and 100 <= Z < 200:
            name = f"{1:02d}"[-2:]
        else:
            name = ELEMENTS[Z].upper()
        return f"{mass}{name:2}"
    except TypeError:
        return f"{mass:3}  "


class Dimension(enum.Enum):
    TIME = enum.auto()
    ENERGY = enum.auto()
    AREA = enum.auto()
    SCALAR = enum.auto()


class Unit(NamedTuple):
    symb: str
    dimension: Dimension
    basis: float
    ensdf_symb: Optional[str]


Units = [
    Unit("Ya", Dimension.TIME, 31556926e24, "YY"),
    Unit("Za", Dimension.TIME, 31556926e21, "ZY"),
    Unit("Ea", Dimension.TIME, 31556926e18, "EY"),
    Unit("Pa", Dimension.TIME, 31556926e15, "PY"),
    Unit("Ta", Dimension.TIME, 31556926e12, "TY"),
    Unit("Ga", Dimension.TIME, 31556926e9, "GY"),
    Unit("Ma", Dimension.TIME, 31556926e6, "MY"),
    Unit("ka", Dimension.TIME, 31556926e3, "KY"),
    Unit("a", Dimension.TIME, 31556926.0, "Y"),
    Unit("d", Dimension.TIME, 86400.0, "D"),
    Unit("h", Dimension.TIME, 3600.0, "H"),
    Unit("min", Dimension.TIME, 60.0, "M"),
    Unit("s", Dimension.TIME, 1.0, "S"),
    Unit("ms", Dimension.TIME, 1e-3, "MS"),
    Unit("µs", Dimension.TIME, 1e-6, "US"),
    Unit("ns", Dimension.TIME, 1e-9, "NS"),
    Unit("ps", Dimension.TIME, 1e-12, "PS"),
    Unit("fs", Dimension.TIME, 1e-15, "FS"),
    Unit("as", Dimension.TIME, 1e-18, "AS"),
    Unit("eV", Dimension.ENERGY, 1.0, "EV"),
    Unit("keV", Dimension.ENERGY, 1e3, "KEV"),
    Unit("MeV", Dimension.ENERGY, 1e6, "MEV"),
    Unit("GeV", Dimension.ENERGY, 1e9, "GEV"),
    Unit("b", Dimension.AREA, 1.0, "B"),
    Unit("mb", Dimension.AREA, 1e-3, "MB"),
    Unit("μb", Dimension.AREA, 1e-6, "UB"),
    Unit("%", Dimension.SCALAR, 1e-2, "%"),
    Unit("", Dimension.SCALAR, 1.0, ""),
]


class Limit(enum.Enum):
    LOWER_THAN = enum.auto()
    GREATER_THAN = enum.auto()
    LOWER_THAN_EQUAL = enum.auto()
    GREATER_THAN_EQUAL = enum.auto()


LIMIT_STRINGS = {
    "LT": Limit.LOWER_THAN,
    "GT": Limit.GREATER_THAN,
    "LE": Limit.LOWER_THAN_EQUAL,
    "GE": Limit.GREATER_THAN_EQUAL,
}


class Sign(enum.Enum):
    NEGATIVE = "-"
    UNSPECIFIED = 0
    POSITIVE = "+"


class Quantity:
    """Container for an ENSDF quantity

    A quantity is more than just a single number:
    It can have an uncertainty (possibly asymmetric), correspond to
    an upper and/or lower limit or range, contain cross-references,
    comments, units, and include an offset (left or right).

    This class can perform simple calculations with other scalar
    numbers (i.e., *NOT* other Quantity objects). Comparisons are
    possible most of the time, but might not be transitive.
    """

    ref_pattern = re.compile(r"\(((?:\d{4}[a-zA-Z]{2}[a-zA-Z\d]{2}),?)+\)")
    calc_pattern = re.compile(r"[\(\)]")
    assumed_pattern = re.compile(r"[\[\]]")
    pattern = re.compile(
        r"""^
        (?P<comp>(?:[<>]?=?|EQ\s|AP\s|[LG][TE]\s)?)
        (?P<add_l>(?:S[NP]|[xA-Z])?)
        (?P<sign>(?:[-\+])?)
        (?:\s*)
        (?P<leading_digits>(?:\d+)?)
        (?P<decimals>(?:\.\d*)?)
        (?P<exponent>(?:[eE][+-]?\d+)?)
        (?:\s*)
        (?P<add_r>(?:[-\+](?:S[NP]|[xA-Z]))?)
        (?:\s*)
        (?P<chars>(?:[MUNPFA]?S|[KM]?EV|[UM]?B|STABLE|WEAK|[YDHM])?)
        (?:\s*)
        (?P<limit>(?:[LG][TE]|AP|CA|SY)?)
        (?:\s*)
        (?P<unc>(?:\s[\d∞]+)?)
        (?P<unc_pm>(?:\+[\d∞]+\s?-[\d∞]+)?)
        (?P<unc_mp>(?:-[\d∞]+\s?\+[\d∞]+)?)
        (?P<comment>(?:\s[a-z][a-zA-Z0-9,.;\s]+)?)
        $""",
        re.X,
    )

    def __init__(self, val: Optional[str] = None, default_unit: Optional[str] = None):
        """Initialize from an ENSDF quantity.

        If a separate uncertainty is given in a D* field, simply
        append it separated by a space.

        Args:
            val: ENSDF quantity
            default_unit: Set unit if not explicitly stated by val.
        """
        self.input = val
        # Input cleanup (limited character set only)
        if val is not None:
            val = alt_char_float(val)
        self.val, self.pm, self.plus, self.minus = [float("nan")] * 4
        self.upper_bound, self.lower_bound = [float("nan")] * 2
        self.upper_bound_inclusive, self.lower_bound_inclusive = [None] * 2
        self.exponent = 0
        self.decimals = 0
        self.sign = Sign.UNSPECIFIED
        self.approximate = False
        self.calculated = False
        self.from_systematics = False
        self.questionable = False
        self.assumed = False

        self.unit = None
        self.named = None
        self.offset_l, self.offset_r, self.offset = [None] * 3
        self.reference = None
        self.comment = None
        if val is not None:
            self._parse_input()
        if not self.unit and default_unit:
            self.set_unit(default_unit)

    def _parse_input(self, val: Optional[str] = None):
        if val is not None:
            val = val.replace("|?", "?").replace("|@", "∞").strip()
        else:
            val = self.input

        ref = self.ref_pattern.match(val)
        if ref:
            self.reference = ref.group(0).split(",")
            val = self.ref_pattern.sub("", val, 1)

        # This is not very precise: Maybe just a part of the quantity
        # is calculated/assumed (e.g. only the uncertainty).
        val, calculated = self.calc_pattern.subn("", val)
        self.calculated = bool(calculated)
        val, assumed = self.assumed_pattern.subn("", val)
        self.assumed = bool(assumed)

        if "?" in val:
            # A question mark might appear at different positions in
            # the input string and I am not sure the position is of
            # any significance.
            self.questionable = True
            val = val.replace("?", "")

        res = self.pattern.match(val.strip())
        if not res:
            warnings.warn(f"Quantity ranges not yet supported.")
            # FIXME: Ranges (e.g. 'a-b' or 'LT a GT b') not yet implemented
            # or input is malformed (raise ValueError).
            # print(f"Could not parse: {val}")
            return
        frags = res.groupdict()

        if frags["chars"] == "STABLE":
            self.val = float("inf")
            self.sign = Sign.POSITIVE
            self.named = "stable"
            self.unit = get_unit("S")
            return
        elif frags["chars"] == "WEAK":
            self.val = 0.0
            self.sign = Sign.POSITIVE
            self.named = "weak"
            return

        if frags["sign"]:
            if frags["sign"] == "-":
                self.sign = Sign.NEGATIVE
            elif frags["sign"] == "+":
                self.sign = Sign.POSITIVE

        if frags["exponent"]:
            self.exponent = int(frags["exponent"][1:])

        main = None
        if frags["leading_digits"] or frags["decimals"]:
            main = float(frags["sign"] + frags["leading_digits"] + frags["decimals"])
            main *= 10**self.exponent
            if frags["decimals"]:
                self.decimals = len(frags["decimals"].strip(" ."))

        if frags["unc"]:
            self.pm = self._parse_uncertainty(frags["unc"].strip())
        if frags["unc_pm"]:
            plus, minus = frags["unc_pm"].split("-", 1)
            self.plus = self._parse_uncertainty(plus.strip())
            self.minus = self._parse_uncertainty(minus.strip())
        if frags["unc_mp"]:
            minus, plus = frags["unc_mp"].split("+", 1)
            self.plus = self._parse_uncertainty(plus.strip())
            self.minus = self._parse_uncertainty(minus.strip())

        comp = frags["comp"]
        limit = frags["limit"]

        self.approximate |= comp == "AP " or limit == "AP"
        self.from_systematics |= limit == "SY"
        self.calculated |= limit == "CA"

        if main is not None:
            if (len(comp) >= 1 and comp[0] in ["<", "L"]) or (
                len(limit) >= 1 and limit[0] == "L"
            ):
                self.upper_bound = main
                self.upper_bound_inclusive = (
                    len(comp) >= 2 and comp[1] in ["=", "E"]
                ) or (len(limit) >= 2 and limit[1] == "E")
            elif (len(comp) >= 1 and comp[0] in [">", "G"]) or (
                len(limit) >= 1 and limit[0] == "G"
            ):
                self.lower_bound = main
                self.lower_bound_inclusive = (
                    len(comp) >= 2 and comp[1] in ["=", "E"]
                ) or (len(limit) >= 2 and limit[1] == "E")
            else:
                self.val = main

            if frags["chars"]:
                self.set_unit(frags["chars"])
        elif len(frags["chars"]) == 1:
            self.offset_l = frags["chars"].strip("+")
        if frags["add_l"]:
            if self.offset_l:
                self.offset_r = self.offset_l
            self.offset_l = frags["add_l"].strip("+")
        if frags["add_r"]:
            self.offset_r = frags["add_r"].strip("+")

        self.offset = self.offset_l or self.offset_r or None
        if self.offset_l and self.offset_r:
            self.offset = f"{self.offset_l} + {self.offset_r}"

        if self.offset and isnan(self.val):
            self.val = 0.0

        if frags["comment"]:
            self.comment = frags["comment"].strip()

    nubase_quantities = []
    # TODO: This need much more work!
    nubase_pattern = re.compile(
        r"""^
    (?P<comparator>([=<>~])?)
    (?P<desc>(?:stble|non-exist|p-unst)?)
    (?P<sign>(?:[-+])?)
    (?P<leading_digits>(?:(\d+))?)
    (?P<decimals>(?:(\.\d+))?)
    (?P<exponent>(?:([eE]-?\d+))?)
    (?P<hash>(?:(\#))?)
    \s*
    (?P<unit>(?:([a-zA-Z]+))?)
    \s*
    (?P<unc_comp>(?:([<>]))?)
    (?P<unc>(?:(\d+))?)
    (?P<unc_dec>(?:(\.\d+))?)
    (?P<hash_unc>(?:(\#))?)
    \s*
    (?P<comment>(?:([0-9]?[a-zA-Z\-]+))?)
    \s*
    (?P<garbage>(?:[\*\.\&]+)?)
    $""",
        re.X,
    )

    @classmethod
    def from_nubase(cls, val):
        qty = cls()
        if val in ["", "=?"]:
            return
        if val == "stbl":
            qty.val = float("inf")
            qty.sign = Sign.POSITIVE
            qty.named = "stable"
            qty.unit = get_unit("S")
            return
        res = cls.nubase_pattern.match(val.strip())
        if not res:
            qty.nubase_quantities.append(val)
            warnings.warn(f"Error while parsing NUBASE quantity.")
            return qty
        frags = res.groupdict()
        qty.comment = frags["comment"]

        if frags["exponent"]:
            qty.exponent = int(frags["exponent"][1:])

        main = None
        if frags["leading_digits"] or frags["decimals"]:
            main = float(frags["sign"] + frags["leading_digits"] + frags["decimals"])
            main *= 10**qty.exponent
            if frags["decimals"]:
                qty.decimals = len(frags["decimals"].strip(" ."))
        qty.val = main

        if frags["unc"]:
            qty.pm = qty._parse_uncertainty(frags["unc"].strip())

        return qty

    def _parse_uncertainty(self, unc) -> float:
        if "∞" in unc:
            return float("inf")
        return abs(int(unc)) * 10 ** (self.exponent - self.decimals)

    def set_unit(self, unit_symbol: str):
        self.unit = get_unit(unit_symbol)

    def cast_to_unit(self, unit: Union[str, Unit]):
        """Cast quantity in a different unit

        Args:
            unit: Unit to use for the returned Quantity
        """
        if not isinstance(unit, Unit):
            unit = get_unit(unit)
        if self.unit.dimension != unit.dimension:
            raise TypeError("Mismatching Dimensions")
        res = self * (self.unit.basis / unit.basis)
        res.unit = unit
        # TODO: Determine number of decimal places/exponent more intelligently
        #   (already after multiplication)
        res.decimals = int(self.decimals + math.log10(unit.basis / self.unit.basis))
        if res.decimals < 0:
            res.decimals = 0
            res.exponent = int(self.exponent + math.log10(self.unit.basis / unit.basis))
        return res

    def __add__(self, other):
        if isinstance(other, (int, float)):
            s = copy.copy(self)
            s.val += other
            return s

    def __mul__(self, other):
        # TODO: Update number of decimal places/exponent
        if isinstance(other, (int, float)):
            s = copy.copy(self)
            s.val *= other
            s.plus *= other
            s.minus *= other
            s.pm *= other
            s.lower_bound *= other
            s.upper_bound *= other
            return s

    __radd__ = __add__
    __rmul__ = __mul__

    def _format_number(self, number: float, decimal_offset: int = 0):
        num = number * 10 ** (-self.exponent + decimal_offset)
        return f"{num:.{self.decimals - decimal_offset}f}"

    def __str__(self):
        res = ""
        if self.named:
            res = self.named
        else:
            if self.offset_l:
                res = f"{res}{self.offset_l}"
            if self.val and (
                (self.offset_l and self.val >= 0.0) or self.sign == Sign.POSITIVE
            ):
                res = f"{res}+"

            if not isnan(self.lower_bound):
                comp = "≥" if self.lower_bound_inclusive else ">"
                tmp = self._format_number(self.lower_bound)
                res = f"{comp} {res}{tmp}"
            elif not isnan(self.upper_bound):
                comp = "≤" if self.upper_bound_inclusive else "<"
                tmp = self._format_number(self.upper_bound)
                res = f"{comp} {res}{tmp}"
            elif not (isnan(self.upper_bound) or isnan(self.lower_bound)):
                # FIXME: Ranges not yet working!
                pass
            elif not self.offset_l or (self.val and not isnan(self.val)):
                tmp = self._format_number(self.val)
                res = f"{res}{tmp}"

            if not isnan(self.pm):
                tmp = self._format_number(self.pm, self.decimals)
                res = f"{res}({tmp})"
            elif not (isnan(self.plus) or isnan(self.minus)):
                tmp_p = self._format_number(self.plus, self.decimals)
                tmp_m = self._format_number(self.minus, self.decimals)
                res = f"{res}(+{tmp_p}-{tmp_m})"
            if self.exponent != 0:
                res = f"{res}e{self.exponent:d}"
            if self.unit:
                res = f"{res} {self.unit.symb}"
            if self.offset_r:
                res = f"{res} + {self.offset_r}"

        if self.approximate:
            res = f"~ {res}"
        if self.questionable:
            res = f"{res} ?"
        if self.assumed:
            res = f"[{res}]"
        if self.calculated:
            res = f"({res})"
        res = res.replace("inf", "∞")
        return res

    def __repr__(self):
        return f"<{self}>"

    def __lt__(self, other):
        if isinstance(other, (int, float)):
            return self.val < other
        elif isinstance(other, Quantity):
            return self.val < other.val

    def __gt__(self, other):
        if isinstance(other, (int, float)):
            return self.val > other
        elif isinstance(other, Quantity):
            return self.val > other.val

    def __le__(self, other):
        if isinstance(other, (int, float)):
            return self.val <= other
        elif isinstance(other, Quantity):
            return self.val <= other.val

    def __ge__(self, other):
        if isinstance(other, (int, float)):
            return self.val >= other
        elif isinstance(other, Quantity):
            return self.val >= other.val


def alt_char_float(val):
    return val.replace("|?", "?").replace("|@", "∞").replace("INFNT", "∞").strip()


@lru_cache(maxsize=None)
def get_unit(unit_symbol: str):
    """Get Unit object by according symbol (ensdf or standard form)

    Args:
        unit_symbol: Symbol of unit
    """
    for unit in Units:
        if unit.symb == unit_symbol or unit.ensdf_symb == unit_symbol:
            return unit
