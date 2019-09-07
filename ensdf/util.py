#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2019 O. Papst.
#
# This file is part of nuclstruc.
#
# nuclstruc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# nuclstruc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with nuclstruc.  If not, see <http://www.gnu.org/licenses/>.

"""helper functions for nuclstruc"""

import copy
import enum
import re
from typing import Tuple, Optional


ELEMENTS = [
    "Nn", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na",
    "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V",
    "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se",
    "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh",
    "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba",
    "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho",
    "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt",
    "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac",
    "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg",
    "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og", 
]

ALT_CHARS1 = {
    '!': '',
    '"': '',
    '#': '§',
    '$': 'e',
    '%': '√',
    '&': '≡',
    '\'': '°',
    '(': '←',
    ')': '→',
    '*': '×',
    '+': '±',
    ',': '½',
    '–': '∓',
    '.': '∝',
    '/': '÷',
    '0': '(',
    '1': ')',
    '2': '[',
    '3': ']',
    '4': '〈',
    '5': '〉',
    '6': '√',
    '7': '∫',
    '8': '∏',
    '9': '∑',
    ':': '†',
    ';': '‡',
    '<': '≤',
    '=': '≠',
    '>': '≥',
    '?': '≈',
    '@': '∞',
    'A': 'Α',
    'B': 'Β',
    'C': 'Η',
    'D': '∆',
    'E': 'Ε',
    'F': 'Φ',
    'G': 'Γ',
    'H': 'Χ',
    'I': 'Ι',
    'J': '∼',
    'K': 'Κ',
    'L': 'Λ',
    'M': 'Μ',
    'N': 'Ν',
    'O': 'Ο',
    'P': 'Π',
    'Q': 'Θ',
    'R': 'Ρ',
    'S': 'Σ',
    'T': 'Τ',
    'U': 'Υ',
    'V': '∇',
    'W': 'Ω',
    'X': 'Ξ',
    'Y': 'Ψ',
    'Z': 'Ζ',
    '[': '{',
    ']': '}',
    '^': '↑',
    '_': '↓',
    '‘': '′',
    'a': 'α',
    'b': 'β',
    'c': 'η',
    'd': 'δ',
    'e': 'ε',
    'f': 'φ',
    'g': 'γ',
    'h': 'χ',
    'i': 'ι',
    'j': '∈',
    'k': 'κ',
    'l': 'λ',
    'm': 'μ',
    'n': 'ν',
    'o': 'ο',
    'p': 'π',
    'q': 'θ',
    'r': 'ρ',
    's': 'σ',
    't': 'τ',
    'u': 'υ',
    'v': '?',
    'w': 'ω',
    'x': 'ξ',
    'y': 'ψ',
    'z': 'ζ'}

ALT_CHARS2 = {
    '!': '!',
    '"': '"',
    '#': '⊗',
    '$': '$',
    '%': '%',
    '&': '&',
    '\'': 'Å',
    '(': '(',
    ')': ')',
    '*': '·',
    '+': '+',
    ',': ',',
    '–': '–',
    '.': '.',
    '/': '/',
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    ':': ':',
    ';': ';',
    '<': '<',
    '=': '=',
    '>': '>',
    '?': '?',
    '@': '•',
    'A': 'Ä',
    'B': 'B',
    'C': 'C',
    'D': 'D',
    'E': 'É',
    'F': 'F',
    'G': 'G',
    'H': 'H',
    'I': 'I',
    'J': 'J',
    'K': 'K',
    'L': 'L',
    'M': 'M',
    'N': 'N',
    'O': 'Ö',
    'P': 'P',
    'Q': 'Õ',
    'R': 'R',
    'S': 'S',
    'T': 'T',
    'U': 'Ü',
    'V': 'V',
    'W': 'W',
    'X': 'X',
    'Y': 'Y',
    'Z': 'Z',
    '[': '[',
    ']': ']',
    '^': '^',
    '_': '_',
    '‘': '‘',
    'a': 'ä',
    'b': 'b',
    'c': 'c',
    'd': 'd',
    'e': 'é',
    'f': 'f',
    'g': 'g',
    'h': 'h',
    'i': 'i',
    'j': 'j',
    'k': 'k',
    'l': 'λ',
    'm': 'm',
    'n': 'n',
    'o': 'ö',
    'p': 'p',
    'q': 'õ',
    'r': 'r',
    's': 's',
    't': 't',
    'u': 'ü',
    'v': 'v',
    'w': 'w',
    'x': 'x',
    'y': 'y',
    'z': 'z'}

def az_from_nucid(nucid: str) -> Tuple[int, int]:
    mass, nucleus = re.compile(r'(\d+)([A-Za-z]*)?').search(nucid).groups()
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

TIME_UNITS = {
    "Y": 365. * 86400., # Definition of year is unclear
    "D": 86400.,
    "H": 3600.,
    "M": 60.,
    "S": 1.,
    "MS": 1e-3,
    "US": 1e-6,
    "NS": 1e-9,
    "PS": 1e-12,
    "FS": 1e-15,
    "AS": 1e-18,
}

ENERGY_UNITS = {
    "EV": 1.,
    "KEV": 1e3,
    "MEV": 1e6,
    "GEV": 1e9,
}

AREA_UNITS = {
    "B": 1.,
    "MB": 1e-3,
    "UB": 1e-6,
}

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


class Dimension(enum.Enum):
    TIME = enum.auto()
    ENERGY = enum.auto()
    AREA = enum.auto()
    FRACTION = enum.auto()

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
    all_orig = set()
    xref_pattern = re.compile(r'\(((?:\d{4}[a-zA-Z]{2}[a-zA-Z\d]{2}),?)+\)')
    calc_pattern = re.compile(r'[\(\)]')
    assumed_pattern = re.compile(r'[\[\]]')
    pattern = re.compile(r"""^
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
        (?P<unc_pm>(?:\+?[\d∞]+\s?-[\d∞]+)?)
        (?P<unc_mp>(?:-[\d∞]+\s?\+[\d∞]+)?)
        (?P<comment>(?:\s[a-z][a-zA-Z0-9,.;\s]+)?)
        $""", re.X)

    def __init__(self, val: str):
        """Initialize from an ENSDF quantity.

        If a separate uncertainty is given in a D* field, simply
        append it separated by a space.

        Args:
            val: ENSDF quantity
        """
        # Input cleanup (limited character set only)
        val = val.replace('|?', '?').replace('|@', '∞').strip()
        self.input = val
        self.all_orig.add(self)
        self.val, self.pm, self.plus, self.minus = [float('nan')]*4
        self.upper_bound, self.lower_bound = [float('nan')]*2
        self.upper_bound_inclusive, self.lower_bound_inclusive = [None]*2
        self.exponent = 0
        self.decimals = 0
        self.sign = Sign.UNSPECIFIED
        self.approximate = False
        self.calculated = False
        self.from_systematics = False
        self.asym_uncertainty = False
        self.questionable = False
        self.assumed = False

        self.unit = ""
        self.named = None
        self.offset_l, self.offset_r, self.offset = [None]*3
        self.dimension = None
        self.xref = None
        self.comment = None
        self._parse_input()

    def _parse_input(self, val: Optional[str] = None):
        if val is not None:
            val = val.replace('|?', '?').replace('|@', '∞').strip()
        else:
            val = self.input

        xref = self.xref_pattern.match(val)
        if xref:
            self.xref = xref.group(0).split(',')
            val = self.xref_pattern.sub("", val, 1)
        
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
            val.replace('?', '')
        
        res = self.pattern.match(val.strip())
        if not res:
            # WARN: Ranges (e.g. 'a-b' or 'LT a GT b') not yet implemented
            # or input is malformed (ValueError).
            return
        frags = res.groupdict()

        if frags["chars"] == "STABLE":
            self.val = float('inf')
            self.sign = Sign.POSITIVE
            self.named = "stable"
            return
        elif frags["chars"] == "WEAK":
            self.val = 0.
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
            main = float(frags["sign"] +
                         frags["leading_digits"] +
                         frags["decimals"])
            main *= 10**self.exponent
            if frags["decimals"]:
                self.decimals = len(frags["decimals"].strip(' .'))
        
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

        self.approximate |= (comp == "AP " or limit == "AP")
        self.from_systematics |= (limit == "SY")
        self.calculated |= (limit == "CA")

        if main:
            if ((len(comp) >= 1 and comp[0] in ["<", "L"]) or
                (len(limit) >= 1 and limit[0] == "L")):
                self.lower_bound = main
                self.lower_bound_inclusive = (
                    (len(comp) >= 2 and comp[1] in ["=", "E"]) or
                    (len(limit) >= 2 and limit[1] == "E"))
            elif ((len(comp) >= 1 and comp[0] in [">", "G"]) or
                (len(limit) >= 1 and limit[0] == "G")):
                self.upper_bound = main
                self.upper_bound_inclusive = (
                    (len(comp) >= 2 and comp[1] in ["=", "E"]) or
                    (len(limit) >= 2 and limit[1] == "E"))
            else:
                self.val = main
            
            if frags["chars"]:
                self.set_unit(frags["chars"])
        elif len(frags["chars"]) == 1:
            self.offset_l = frags["chars"].strip('+')
        if frags["add_l"]:
            self.offset_l = frags["add_l"].strip('+')
        elif frags["add_r"]:
            self.offset_r = frags["add_r"].strip('+')
        self.offset = self.offset_l or self.offset_r

    def _parse_uncertainty(self, unc) -> float:
        if "∞" in unc:
            return float('inf')
        return abs(int(unc)) * 10**(self.exponent - self.decimals)
    
    def set_unit(self, unit: str):
        if unit in ENERGY_UNITS:
            self.dimension = Dimension.ENERGY
        elif unit in TIME_UNITS:
            self.dimension = Dimension.TIME
        elif unit in AREA_UNITS:
            self.dimension = Dimension.AREA
        else:
            raise ValueError(f"Unknown unit: {unit}")
        self.unit = unit

    def __add__(self, other):
        if isinstance(other, (int, float)):
            s = copy.copy(self)
            s.val += other
            return s

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            s = copy.copy(self)
            s.val *= other
            return s

    __radd__ = __add__
    __rmul__ = __mul__

    def __str__(self):
        res = ""
        return res
    
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
    return val.replace('|@', 'inf').replace('INFNT', 'inf')