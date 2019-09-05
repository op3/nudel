#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2019 O. Papst.
#
# This file is part of pyENSDF.
#
# pyENSDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyENSDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyENSDF.  If not, see <http://www.gnu.org/licenses/>.

"""helper functions for pyENSDF"""

import copy
import enum
from typing import Tuple
import re

import uncertainties


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

class Quantity:
    def __init__(self, val: str, dval: str = "", has_unit=True):
        self.orig_val = val
        self.orig_dval = dval
        self.val, self.pm, self.plus, self.minus = [float('nan')]*4
        self.sign = 0  # -1, 0, 1 = negative, unknown, positive
        self.limit = None
        self.approximate = False
        self.calculated = False
        self.from_systematics = False
        self.asym_uncertainty = False
        self.unit = ""
        self.offset = None
        self.reference = None
        self.questionable = False
        self.assumed = False
        self.comment = None

        # TODO: Maybe it is possible to find a regex for parsing?
        if "?" in val or "|?" in val:
            self.questionable = True
            val = val.replace('|?', '').replace('?', '')
        if not val:
            return
        if val[0] == "<":
            self.limit = Limit.LOWER_THAN
            val = val[1:]
        elif val[0] == ">":
            self.limit = Limit.GREATER_THAN
            val = val[1:]
        elif val == "STABLE":
            self.val = float('inf')
            self.sign = 1
            return
        elif val == "WEAK":
            self.val = float('0')
            self.sign = 1
            return
        elif val == "-":
            self.sign = -1
            return
        elif val == "+":
            self.sign = +1
            return
        if val[0] == "(" and val[-1] == ")":
            self.questionable = True
            val = val[1:-1].strip()
        if val[0] == "[" and val[-1] == "]":
            self.assumed = True
            val = val[1:-1].strip()
        if "(" in val and val[-1] == ")":
            val, ref = val.split('(', 1)
            val = val.strip()
            self.reference = ref[:-1]
        if ' ' in val:
            if has_unit:
                val, self.unit = val.split(' ', 1)
            else:
                val, dval, *rest = val.split(' ', 2)
                if rest:
                    self.comment = rest[0]

        exponent = 0
        if "E" in val[1:]:
            val, exponent = val.split('E', 1)
            exponent = int(exponent)
        elif "e" in val[1:]:
            val, exponent = val.split('e', 1)
            exponent = int(exponent)
        if "+" in val[1:]:
            a, b = val.split('+', 1)
            if a.strip().isalpha() and b.strip().isalpha():
                self.offset = f"{a}+{b}"
                val = ""
            elif a.strip().isalpha():
                self.offset, val = a.strip(), b.strip()
            elif b.strip().isalpha():
                self.offset, val = b.strip(), a.strip()
            else:
                # WARN: Not yet implemented
                return
        elif "-" in val[1:]:
            a, b = val.split('-', 1)
            if a.strip().isalpha() and b.strip().isalpha():
                self.offset = f"{a}-{b}"
                val = ""
            elif a.strip().isalpha():
                self.offset, val = a.strip(), f"-{b.strip()}"
            else:
                # WARN: Not yet implemented
                return
        elif any(c.isalpha() for c in val):
            self.offset = val
        elif "," in val[1:]:
            # WARN: Lists not yet implemented
            return
        elif val:
            val = alt_char_float(val)
            # The next line solves problems with some typos in ENSDF
            val = val.replace('(', '')
            self.val = float(f"{val}") * 10**exponent
            if val[0] == "+":
                self.sign = 1
                val = val[1:]
            elif val[0] == -1:
                self.sign = -1
                val = val[1:]

        if dval:
            dval = dval.strip()
            if dval in LIMIT_STRINGS:
                self.limit = LIMIT_STRINGS[dval]
            elif dval in ["AP", "CA", "SY"]:
                self.approximate = (dval == "AP")
                self.calculated = (dval == "CA")
                self.from_systematics = (dval == "SY")
            else:
                # use uncertainties library for easier conversion
                if "+" in dval and "-" in dval:
                    self.asym_uncertainty = True
                    if dval[0] == "+":
                        plus, minus = dval.split('-')
                        plus = plus[1:].strip()
                    else:
                        minus, plus = dval.split('+')
                        minus = minus[1:].strip()
                    plus = alt_char_float(plus)
                    minus = alt_char_float(minus)
                    res_plus = uncertainties.ufloat_fromstr(f"{val}({plus})")
                    res_minus = uncertainties.ufloat_fromstr(f"{val}({minus})")
                    self.plus = res_plus.std_dev * 10**exponent
                    self.minus = res_minus.std_dev * 10**exponent
                elif "+" in dval[1:] or "-" in dval[1:]:
                    # TODO: No idea what this is supposed to mean
                    pass
                else:
                    dval = alt_char_float(dval)
                    res = uncertainties.ufloat_fromstr(f"{val}({dval})")
                    self.pm = res.std_dev * 10**exponent

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
        if self.offset:
            res += f"{self.offset} + "
        if self.pm:
            uf = uncertainties.ufloat(self.val, self.pm)
            res += f"{uf}"
        else:
            res += f"{self.val}"
        if self.unit:
            res += f" {self.unit}"
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