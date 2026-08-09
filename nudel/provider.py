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

from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import platformdirs

from .util import az_from_nucid


class ENSDFIndexError(RuntimeError):
    """Raised when a cached index entry points to an invalid record."""


class ENSDFProvider(ABC):
    @abstractmethod
    def get_dataset(self, nucleus: tuple[int, int | None], name: str) -> str:
        """
        returns a raw ENSDF dataset
        """
        raise NotImplementedError

    @abstractmethod
    def get_adopted_levels(self, nucleus: tuple[int, int]) -> str:
        """
        returns the raw ADOPTED LEVELS[, GAMMAS] dataset of a nucleus
        """
        raise NotImplementedError


class ENSDFFileProvider(ENSDFProvider):
    def __init__(
        self,
        path: str | Path | None = None,
        version: str = "latest",
    ) -> None:
        """Create an ENSDF provider backed by on-disk ``ensdf.???`` files.

        Resolution order (first match wins):

        1. ``path`` argument — used directly, no fetch, no versioning.
        2. ``ENSDF_PATH`` environment variable — used directly, no fetch.
        3. Otherwise — :func:`nudel.fetch.fetch` is called to download (if
           needed) and locate the requested ENSDF ``version``.

        Args:
            path: Directory holding ``ensdf.???`` files. Bypasses fetch and
                versioning when provided.
            version: ENSDF version (``"latest"`` or ``YYMMDD``). Ignored
                when ``path`` is given or ``ENSDF_PATH`` is set.
        """
        from . import fetch as _fetch

        if path is not None:
            self.folder = Path(path)
            self.version: str | None = None
        elif (env_path := os.getenv("ENSDF_PATH")) is not None:
            self.folder = Path(env_path)
            self.version = None
        else:
            self.folder = Path(_fetch.fetch(version))
            self.version = _fetch.current_version() or "unknown"

        self.cachedir = platformdirs.user_cache_path("nudel")
        self.index: dict[tuple[tuple[int, int | None], str], int] = {}
        self.gen_index()
        self.adopted_levels: dict[tuple[int, int], str] = {}
        for nucleus, name in self.index:
            if "ADOPTED LEVELS" in name:
                mass, Z = nucleus
                if Z is not None:
                    self.adopted_levels[(mass, Z)] = name

    def _index_key(self) -> str:
        """Return the cache filename component identifying this data set."""
        if self.version is not None:
            return self.version
        return "path_" + hashlib.md5(str(self.folder).encode()).hexdigest()[:12]

    def _index_file(self) -> Path:
        return self.cachedir / "index" / f"{self._index_key()}.json"

    @staticmethod
    def _serialize_index(
        index: dict[tuple[tuple[int, int | None], str], int],
        version: str | None,
    ) -> str:
        return json.dumps(
            {
                "version": version,
                "entries": [
                    {"nucleus": list(nucleus), "name": name, "offset": offset}
                    for (nucleus, name), offset in index.items()
                ],
            }
        )

    @staticmethod
    def _deserialize_index(
        text: str,
    ) -> dict[tuple[tuple[int, int | None], str], int]:
        data = json.loads(text)
        index: dict[tuple[tuple[int, int | None], str], int] = {}
        for entry in data.get("entries", []):
            mass, Z = entry["nucleus"]
            index[((mass, Z), entry["name"])] = int(entry["offset"])
        return index

    def gen_index(self) -> None:
        """Build (or load) the index of ENSDF datasets and byte offsets."""
        index_file = self._index_file()
        if index_file.is_file():
            self.index = self._deserialize_index(index_file.read_text())
            return

        ensdf_files = list(self.folder.glob("ensdf.???"))
        if not ensdf_files:
            raise FileNotFoundError(
                f"No ENSDF files (ensdf.???) found in {self.folder}"
            )

        for f_path in ensdf_files:
            with open(f_path, encoding="latin-1") as f:
                linestart = f.tell()
                line = f.readline()
                while line:
                    if line != "\n" and line[2] != " " and line[5:9] == "    ":
                        nucleus = az_from_nucid(line[0:5])
                        self.index[(nucleus, line[9:39].strip())] = linestart
                    linestart = f.tell()
                    line = f.readline()

        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text(self._serialize_index(self.index, self.version))

    def get_dataset(self, nucleus: tuple[int, int | None], name: str) -> str:
        """Return the raw ENSDF dataset for ``(nucleus, name)``.

        Raises:
            KeyError: ``(nucleus, name)`` not in the index.
            ENSDFIndexError: Cached offset does not point at an ID record.
        """
        mass, Z = nucleus
        offset = self.index[nucleus, name]
        res = ""
        with open(self.folder / f"ensdf.{mass:03d}", encoding="latin-1") as f:
            f.seek(offset)
            first = f.readline()
            if len(first) < 9 or first[5:9] != "    ":
                raise ENSDFIndexError(
                    f"Index for ({nucleus}, {name!r}) points to invalid record "
                    f"at byte {offset} in ensdf.{mass:03d}"
                )
            res += first
            for line in f:
                if line.strip() == "":
                    return res
                res += line
        return res

    def get_adopted_levels(self, nucleus: tuple[int, int]) -> str:
        return self.get_dataset(nucleus, self.adopted_levels[nucleus])


class ENSDFInMemoryProvider(ENSDFProvider):
    """Provider backed by an in-memory dict — for tests only.

    Maps ``((mass, Z), name) -> raw_dataset_text`` and is drop-in compatible
    with :class:`nudel.core.ENSDF`, exposing ``.index`` and
    ``.adopted_levels`` like :class:`ENSDFFileProvider`. Lets unit tests run
    without any real ENSDF data on disk.
    """

    def __init__(self, data: dict[tuple[tuple[int, int | None], str], str]) -> None:
        self.data = data
        self.index = dict.fromkeys(data)
        self.adopted_levels: dict[tuple[int, int], str] = {}
        for (mass, Z), name in self.index:
            if Z is not None and "ADOPTED LEVELS" in name:
                self.adopted_levels[(mass, Z)] = name

    def get_dataset(self, nucleus: tuple[int, int | None], name: str) -> str:
        return self.data[nucleus, name]

    def get_adopted_levels(self, nucleus: tuple[int, int]) -> str:
        return self.get_dataset(nucleus, self.adopted_levels[nucleus])
