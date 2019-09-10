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

"""Wrapper for ENSDF providers"""


from pathlib import Path
import os
from os.path import getmtime
from abc import ABC, abstractmethod
import re
import pickle
import lzma
from typing import Union, List, Tuple, Optional

from .util import nucid_from_az, az_from_nucid, Quantity

class ENSDFProvider(ABC):
    @abstractmethod
    def get_dataset(self, nucleus: Tuple[int, Optional[int]], name: str) -> str:
        """
        returns a raw ENSDF dataset
        """
        pass

    @abstractmethod
    def get_adopted_levels(self, nucleus: Tuple[int, int]) -> str:
        """
        returns the raw ADOPTED LEVELS[, GAMMAS] dataset of a nucleus
        """
        pass

class ENSDFFileProvider(ENSDFProvider):
    def __init__(self, folder: Union[str, Path] = None) -> None:
        if not folder:
            folder = os.getenv(
                "ENSDF_PATH",
                Path(os.getenv("XDG_DATA_HOME",
                     Path.home()/".local"/"share"))/"ensdf")
        if isinstance(folder, str):
            folder = Path(folder)
        self.folder = folder
        self.cachedir = Path(os.getenv("XDG_CACHE_HOME",
            Path.home()/".cache"))/"nudel"
        self.cachedir.mkdir(exist_ok=True)
        self.index = dict()
        self.gen_index()
        self.adopted_levels = dict()
        for nucleus, name in self.index.keys():
            if "ADOPTED LEVELS" in name:
                self.adopted_levels[nucleus] = name

    def gen_index(self):
        """
        Generate index of ENSDF datasets and file position
        """
        ensdf_files = list(self.folder.glob('ensdf.???'))
        index_file = self.cachedir/"ensdf_index.pickle.xz"
        last_modified = max([getmtime(f_path) for f_path in ensdf_files])
        if index_file.is_file() and getmtime(index_file) > last_modified:
            with lzma.open(index_file, 'r') as index:
                self.index = pickle.load(index)
                return

        for f_path in ensdf_files:
            with open(f_path, 'r') as f:
                linestart = f.tell()
                line = f.readline()
                while line:
                    if line[2] != ' ' and line[5:9] == '    ':
                        nucleus = az_from_nucid(line[0:5])
                        self.index[(nucleus, line[9:39].strip())] = linestart
                    linestart = f.tell()
                    line = f.readline()
        if self.index:
            with lzma.open(index_file, 'wb') as index:
                pickle.dump(self.index, index, protocol=pickle.HIGHEST_PROTOCOL)

    def get_dataset(self, nucleus: Tuple[int, Optional[int]], name: str) -> str:
        mass, Z = nucleus
        res = ""
        with open(self.folder/f"ensdf.{mass:03d}", "r") as f:
            f.seek(self.index[nucleus, name])
            for line in f:
                if line.strip() == "":
                    return res
                res += line
    
    def get_adopted_levels(self, nucleus: Tuple[int, int]) -> str:
        return self.get_dataset(nucleus, self.adopted_levels[nucleus])