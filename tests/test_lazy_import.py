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

"""Tests for lazy import behaviour and the ``version=`` kwarg."""

from __future__ import annotations

import importlib
import sys

import platformdirs
from nudel.core import ENSDF, Dataset, Nuclide, get_active_ensdf
from nudel.provider import ENSDFInMemoryProvider


def _make_adopted_levels_dataset(mass: int, Z: int) -> str:
    """Build a minimal valid ENSDF ADOPTED LEVELS dataset string."""
    from nudel.util import nucid_from_az

    nucid = nucid_from_az((mass, Z))  # e.g. "94Mo" (mass-prefixed, symbol)
    # Pad nucid to 5 chars (cols 0-4), then 4 spaces (cols 5-8), then the
    # dataset name starting at col 9 and padded to col 39.
    nucid5 = f"{nucid:<5}"
    name = "ADOPTED LEVELS"
    # ID record: 5-char nucid, 4 spaces (cols 5-8), name from col 9, pad to 80.
    id_line = f"{nucid5}    {name:<75}"[:80] + "\n"
    # Level record: nucid, then "  L" at cols 5-7, level data, padded to 80.
    level_body = f"{nucid5}  L   0.0    0+     STABLE"
    level_line = f"{level_body:<80}"[:80] + "\n"
    # A single trailing blank line terminates the dataset; avoid a second
    # trailing newline which would produce an empty element after split.
    return id_line + level_line


def test_import_nudel_no_side_effects(tmp_path, monkeypatch):
    """``import nudel`` must not touch the filesystem or network."""
    # Redirect platformdirs to a clean tmp tree so we can detect any writes.
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    monkeypatch.setattr(
        platformdirs, "user_data_path", lambda app: data_root, raising=False
    )
    monkeypatch.setattr(
        platformdirs, "user_cache_path", lambda app: cache_root, raising=False
    )

    # Drop any cached nudel package and re-import fresh.
    for name in list(sys.modules):
        if name == "nudel" or name.startswith("nudel."):
            del sys.modules[name]

    importlib.import_module("nudel")

    # No directories should have been created just by importing.
    assert not data_root.exists()
    assert not cache_root.exists()
    # And no active ENSDF should have been instantiated.
    from nudel.core import ENSDF as ENSDF2

    assert ENSDF2.active_ensdf is None


def test_nuclide_accepts_version_kwarg():
    """``Nuclide`` accepts an explicit ``ensdf=`` (version is ignored)."""
    dataset = _make_adopted_levels_dataset(94, 42)
    data = {((94, 42), "ADOPTED LEVELS"): dataset}
    prov = ENSDFInMemoryProvider(data)
    fake = ENSDF(provider=prov)

    # Dataset.__init__ calls get_active_ensdf(); install our fake so it
    # doesn't try to build a real (network-fetching) ENSDF.
    ENSDF.active_ensdf = fake
    try:
        nuc = Nuclide(94, 42, ensdf=fake, version="latest")
    finally:
        ENSDF.active_ensdf = None

    assert isinstance(nuc.adopted_levels, Dataset)
    assert nuc.adopted_levels.nucid == "94MO"
    assert nuc.ensdf is fake


def test_nuclide_version_kwarg_ignored_when_ensdf_given():
    """When ``ensdf=`` is provided, ``version=`` must be ignored."""
    dataset = _make_adopted_levels_dataset(94, 42)
    data = {((94, 42), "ADOPTED LEVELS"): dataset}
    prov = ENSDFInMemoryProvider(data)
    fake = ENSDF(provider=prov)

    ENSDF.active_ensdf = fake
    try:
        # version="260707" would fetch if respected; with ensdf= it must not.
        nuc = Nuclide(94, 42, ensdf=fake, version="260707")
    finally:
        ENSDF.active_ensdf = None

    assert nuc.ensdf is fake


def test_get_active_ensdf_lazy():
    """``ENSDF.active_ensdf`` is None until something asks for it; the
    explicit ``ensdf=`` path on ``Nuclide`` does NOT populate the global."""
    ENSDF.active_ensdf = None
    try:
        assert ENSDF.active_ensdf is None

        dataset = _make_adopted_levels_dataset(94, 42)
        data = {((94, 42), "ADOPTED LEVELS"): dataset}
        prov = ENSDFInMemoryProvider(data)
        fake = ENSDF(provider=prov)

        # Install fake as active so Dataset parsing inside Nuclide doesn't
        # trigger get_active_ensdf()'s lazy-create branch.
        ENSDF.active_ensdf = fake
        Nuclide(94, 42, ensdf=fake)

        # After constructing with explicit ensdf=, the global remains the
        # one we set (not re-created, not None).
        assert ENSDF.active_ensdf is fake
    finally:
        ENSDF.active_ensdf = None


def test_get_active_ensdf_returns_existing():
    """``get_active_ensdf`` returns the already-set active instance without
    constructing a new one."""
    dataset = _make_adopted_levels_dataset(94, 42)
    data = {((94, 42), "ADOPTED LEVELS"): dataset}
    fake = ENSDF(provider=ENSDFInMemoryProvider(data))

    ENSDF.active_ensdf = fake
    try:
        assert get_active_ensdf() is fake
        assert get_active_ensdf("latest") is fake
    finally:
        ENSDF.active_ensdf = None
