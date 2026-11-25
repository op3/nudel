#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2026 O. Papst.
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

"""Types for parsed ENSDF comments and footnotes"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CommentType = Literal["c", "d", "t"]


@dataclass(frozen=True, slots=True)
class CommentSymbol:
    """A field symbol referenced by a comment, with optional flags."""

    field: str
    flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Comment:
    """A single logical ENSDF comment, including continuation lines.

    ``symbols`` is best-effort; when the LHS cannot be parsed into symbols and
    is not a known general-comment key, the raw LHS is retained in ``lhs``.
    """

    text: str
    kind: CommentType
    rtype: str = ""
    particle: str = ""
    symbols: tuple[CommentSymbol, ...] = ()
    label: str | None = None
    key: str | None = None
    lhs: str = ""
    raw: tuple[str, ...] = ()
