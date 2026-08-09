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

"""Tests for nudel.fetch."""

from __future__ import annotations

import json
import zipfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch

import pytest

# Load nudel.fetch as a standalone module to avoid triggering nudel/__init__.py,
# which calls get_active_ensdf() at import time (requires ENSDF data on disk).
_spec = spec_from_file_location(
    "nudel_fetch",
    str(Path(__file__).resolve().parent.parent / "nudel" / "fetch.py"),
)
fetch_mod = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(fetch_mod)

current_version = fetch_mod.current_version
fetch = fetch_mod.fetch
get_url = fetch_mod.get_url
list_versions = fetch_mod.list_versions
resolve_version = fetch_mod.resolve_version
set_current = fetch_mod.set_current

MANIFEST = {
    "distributions": [
        {
            "year": "2021",
            "files": ["ensdf_210101_099.zip", "ensdf_210101_199.zip"],
        },
        {"year": "2022", "files": ["ensdf_220101.zip", "ensdf_220501.zip"]},
        {"year": "2025", "files": ["ensdf_250101.zip", "ensdf_250201.zip"]},
        {"year": "2026", "files": ["ensdf_260805.zip", "ensdf_260707.zip"]},
    ],
    "latest": {"year": "2026", "files": ["ensdf_260805.zip"]},
}


@pytest.fixture
def redirect_paths(tmp_path, monkeypatch):
    """Redirect module-level paths into a temp dir for isolation."""
    data_dir = tmp_path / "data" / "ensdf"
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(fetch_mod, "DATA_DIR", data_dir)
    monkeypatch.setattr(fetch_mod, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(fetch_mod, "CURRENT_FILE", data_dir.parent / "current")
    return tmp_path


@pytest.fixture
def mock_manifest():
    """Patch the manifest fetcher to return the static MANIFEST."""
    with patch.object(fetch_mod, "_get_api_manifest", return_value=MANIFEST) as mocked:
        yield mocked


class TestGetUrl:
    def test_valid(self):
        assert (
            get_url("260805")
            == "https://www.nndc.bnl.gov/ensdfarchivals/distributions/dist26/ensdf_260805.zip"
        )

    def test_invalid(self):
        with pytest.raises(ValueError):
            get_url("invalid")

    @pytest.mark.parametrize("bad", ["26080", "2608050", "26a805", ""])
    def test_invalid_formats(self, bad):
        with pytest.raises(ValueError):
            get_url(bad)


class TestResolveVersion:
    def test_latest(self, mock_manifest):
        assert resolve_version("latest") == "260805"

    def test_explicit(self, mock_manifest):
        assert resolve_version("260707") == "260707"

    def test_unknown(self, mock_manifest):
        with pytest.raises(ValueError, match="Unknown ENSDF version"):
            resolve_version("999999")


class TestListVersions:
    def test_filters_and_sorts(self, mock_manifest):
        versions = list_versions()
        assert versions == [
            "260805",
            "260707",
            "250201",
            "250101",
            "220501",
            "220101",
        ]

    def test_latest_first(self, mock_manifest):
        assert list_versions()[0] == "260805"


class TestStickyLatest:
    def test_current_initially_none(self, redirect_paths):
        assert current_version() is None

    def test_set_and_get(self, redirect_paths):
        set_current("260805")
        assert current_version() == "260805"

    def test_fetch_uses_pin(self, redirect_paths, mock_manifest):
        set_current("260805")
        data_path = fetch_mod.DATA_DIR / "260805"
        data_path.mkdir(parents=True)
        (data_path / "ensdf.001").write_text("dummy")
        result = fetch("latest")
        assert result == data_path
        mock_manifest.assert_not_called()

    def test_fetch_latest_pins(self, redirect_paths, mock_manifest, tmp_path):
        """fetch('latest') pins the resolved version after download."""
        fake_zip = tmp_path / "fake.zip"
        with zipfile.ZipFile(fake_zip, "w") as zf:
            zf.writestr("ensdf.001", b"dummy content\n")
        with patch.object(fetch_mod.pooch, "retrieve", return_value=fake_zip):
            result = fetch("latest")
        assert (result / "ensdf.001").exists()
        assert current_version() == "260805"


class TestFetchExplicit:
    def test_fetch_explicit_no_pin(self, redirect_paths, mock_manifest, tmp_path):
        fake_zip = tmp_path / "fake.zip"
        with zipfile.ZipFile(fake_zip, "w") as zf:
            zf.writestr("ensdf.001", b"dummy content\n")
        with patch.object(fetch_mod.pooch, "retrieve", return_value=fake_zip):
            result = fetch("260805")
        assert (result / "ensdf.001").exists()
        assert (result / "meta.json").exists()
        meta = json.loads((result / "meta.json").read_text())
        assert meta["version"] == "260805"
        assert meta["url"].endswith("ensdf_260805.zip")
        assert "sha256" in meta
        assert "downloaded_at" in meta
        assert current_version() is None


class TestApiCaching:
    def test_cache_hits_once(self, redirect_paths, monkeypatch):
        """Calling _get_api_manifest twice should only hit the network once."""
        response = type(
            "R",
            (),
            {
                "json": staticmethod(lambda: MANIFEST),
                "raise_for_status": lambda self: None,
            },
        )()

        with patch.object(fetch_mod.requests, "get", return_value=response) as get_mock:
            fetch_mod._get_api_manifest()
            fetch_mod._get_api_manifest()
        assert get_mock.call_count == 1
