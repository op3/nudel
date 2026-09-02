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

"""Python interface for ENSDF nuclear data"""

__version__ = "0.0.1"

from .core import Nuclide as Nuclide
from .core import get_active_ensdf as get_active_ensdf

__all__ = ["Nuclide", "get_active_ensdf", "__version__"]
