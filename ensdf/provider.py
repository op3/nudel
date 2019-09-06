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

"""Wrapper for ENSDF providers"""


from pathlib import Path
import os
from abc import ABC, abstractmethod
import re
from typing import Union, List, Tuple, Optional

from .util import nucid_from_az, az_from_nucid, Quantity

class ENSDFProvider(ABC):
    @abstractmethod
    def get_dataset(self, nucleus: str, name: str) -> str:
        """
        returns a raw ENSDF dataset

        nucleus: The nucleus of interest (e.g. "22NA")
        name: The name of the dataset (e.g. "ADOPTED LEVELS")
        """
        pass
    
    @abstractmethod
    def get_all_dataset_names(self) -> List[str]:
        pass


class ENSDFFileProvider(ENSDFProvider):
    def __init__(self, folder: Union[str, Path] = None) -> None:
        if folder is None:
            folder = Path(os.getenv("XDG_DATA_HOME",
                Path.home()/".local"/"share"))/"ensdf"
        if isinstance(folder, str):
            folder = Path(folder)
        self.folder = folder

    def get_datasets(self, mass: int) -> List[Tuple[Tuple[int, Optional[int]], str]]:
        headers = []
        with open(self.folder/f"ensdf.{mass:03d}", "r") as ensdf_file:
            next_is_header = True
            for line in ensdf_file:
                if next_is_header:
                    nucid = line[0:5].strip()
                    mass, Z = az_from_nucid(nucid)
                    dataset_id = line[9:39].strip()
                    headers.append(((mass, Z), dataset_id))
                next_is_header = (line.strip() == "")
        return headers



    def get_dataset(self, nucleus: Tuple[int, Optional[int]], name: str) -> str:
        mass, Z = nucleus
        res = ""
        alt_nucid = f"{mass:03d}{Z%100:02d}" if Z else None
        with open(self.folder/f"ensdf.{mass:03d}", "r") as ensdf_file:
            found = False
            for line in ensdf_file:
                if (not found and line[5:9] == '    ' and
                        name == line[9:39].strip() and
                        (nucid_from_az(nucleus) in line[0:5] or
                         (alt_nucid and alt_nucid in line[0:5]))):
                    found = True
                if found:
                    res += line
                    if line.strip() == "":
                        break
            else:
                raise FileNotFoundError(
                    f"ENSDF dataset '{name}' for nucleus '{nucleus}' not found.")
        return res
    
    def get_adopted_levels(self, nucleus: Tuple[int, int]):
        mass, Z = nucleus
        res = ""
        with open(self.folder/f"ensdf.{mass:03d}", "r") as ensdf_file:
            found = False
            for line in ensdf_file:
                if (not found and line[5:9] == '    ' and
                        "ADOPTED LEVELS" == line[9:23] and
                        nucid_from_az(nucleus) in line[0:5]):
                    found = True
                if found:
                    res += line
                    if line.strip() == "":
                        break
            else:
                raise FileNotFoundError(
                    f"ENSDF adopted levels for nucleus '{nucleus}' not found.")
        return res
    
    def get_all_dataset_names(self) -> List[str]:
        for mass in range(1, 300):
            yield from self.get_datasets(mass)