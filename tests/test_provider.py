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

"""Tests for nudel.provider."""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

# Load nudel.provider as a standalone module to avoid triggering nudel/__init__.py,
# which calls get_active_ensdf() at import time (requires ENSDF data on disk).
# provider.py uses a relative import (`from .util import az_from_nucid`), so we
# register a bare `nudel` package and pre-load `nudel.util` first.
_nudel_root = Path(__file__).resolve().parent.parent / "nudel"
_pkg = type(sys)("nudel")
_pkg.__path__ = [str(_nudel_root)]
sys.modules["nudel"] = _pkg

_util_spec = spec_from_file_location("nudel.util", str(_nudel_root / "util.py"))
_util_mod = module_from_spec(_util_spec)
assert _util_spec.loader is not None
_util_spec.loader.exec_module(_util_mod)
sys.modules["nudel.util"] = _util_mod

_spec = spec_from_file_location(
    "nudel.provider",
    str(_nudel_root / "provider.py"),
)
provider_mod = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(provider_mod)
sys.modules["nudel.provider"] = provider_mod

ENSDFFileProvider = provider_mod.ENSDFFileProvider
ENSDFInMemoryProvider = provider_mod.ENSDFInMemoryProvider
ENSDFIndexError = provider_mod.ENSDFIndexError


# A valid ENSDF ID record: 5-char nucid, 4 spaces (cols 6-9), then name.
# "  1H " nucid -> az_from_nucid returns (1, 1).
ID_RECORD = "  1H     ADOPTED LEVELS" + " " * 17 + "\n"
DATASET_BODY = "  1H    0 0+    0.0     0\n"
DATASET_TEXT = ID_RECORD + DATASET_BODY + "\n"


def test_inmemory_get_dataset():
    data = {((1, 1), "ADOPTED LEVELS"): DATASET_TEXT}
    prov = ENSDFInMemoryProvider(data)
    assert prov.get_dataset((1, 1), "ADOPTED LEVELS") == DATASET_TEXT


def test_inmemory_get_adopted_levels():
    data = {((1, 1), "ADOPTED LEVELS"): DATASET_TEXT}
    prov = ENSDFInMemoryProvider(data)
    assert prov.get_adopted_levels((1, 1)) == DATASET_TEXT
    assert prov.adopted_levels == {(1, 1): "ADOPTED LEVELS"}


def test_inmemory_index_and_adopted_levels():
    data = {
        ((1, 1), "ADOPTED LEVELS"): DATASET_TEXT,
        ((1, 1), "DECAY B"): DATASET_TEXT,
        ((1, None), "COULOMB"): DATASET_TEXT,
    }
    prov = ENSDFInMemoryProvider(data)
    assert set(prov.index) == set(data)
    # generic-mass entry (Z is None) must not appear in adopted_levels
    assert prov.adopted_levels == {(1, 1): "ADOPTED LEVELS"}


@pytest.fixture
def patch_cache(tmp_path, monkeypatch):
    """Redirect platformdirs.user_cache_path to a tmp dir."""
    cache_root = tmp_path / "cache"
    monkeypatch.setattr(
        provider_mod.platformdirs,
        "user_cache_path",
        lambda app: cache_root,
    )
    return cache_root


def test_file_provider_path_mode(tmp_path, patch_cache):
    ensdf_file = tmp_path / "ensdf.001"
    ensdf_file.write_text(DATASET_TEXT, encoding="latin-1")

    prov = ENSDFFileProvider(path=tmp_path)
    assert prov.version is None
    assert prov.folder == tmp_path
    assert ((1, 1), "ADOPTED LEVELS") in prov.index
    assert (
        prov.get_dataset((1, 1), "ADOPTED LEVELS") == DATASET_TEXT.rstrip("\n") + "\n"
    )
    assert prov.adopted_levels == {(1, 1): "ADOPTED LEVELS"}

    # JSON index cache was written to the redirected cache dir.
    index_dir = patch_cache / "index"
    json_files = list(index_dir.glob("*.json"))
    assert len(json_files) == 1
    assert json_files[0].read_text().count("ADOPTED LEVELS") == 1


def test_file_provider_empty_dir(tmp_path, patch_cache):
    with pytest.raises(FileNotFoundError, match="No ENSDF files"):
        ENSDFFileProvider(path=tmp_path)


def test_file_provider_corrupted_index(tmp_path, patch_cache):
    ensdf_file = tmp_path / "ensdf.001"
    # First a non-ID line, then the real dataset.
    junk = "garbage line that is not an ID record\n"
    ensdf_file.write_text(junk + DATASET_TEXT, encoding="latin-1")

    prov = ENSDFFileProvider(path=tmp_path)
    # Inject a bad offset pointing at the junk line.
    prov.index[((1, 1), "ADOPTED LEVELS")] = 0
    with pytest.raises(ENSDFIndexError, match="invalid record"):
        prov.get_dataset((1, 1), "ADOPTED LEVELS")


def test_index_roundtrip(tmp_path, patch_cache):
    ensdf_file = tmp_path / "ensdf.001"
    ensdf_file.write_text(DATASET_TEXT, encoding="latin-1")

    prov = ENSDFFileProvider(path=tmp_path)
    original = dict(prov.index)
    serialized = prov._serialize_index(original, prov.version)
    loaded = prov._deserialize_index(serialized)
    assert loaded == original
