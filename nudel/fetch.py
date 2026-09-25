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

"""Fetch and cache ENSDF data from NNDC."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import warnings
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

import platformdirs
import pooch
import requests

ENSDF_API = "https://www.nndc.bnl.gov/ensdfarchivals/distributions/files.json"
ENSDF_BASE = "https://www.nndc.bnl.gov/ensdfarchivals/distributions"
API_CACHE_TTL = 30 * 24 * 3600

DATA_DIR = platformdirs.user_data_path("nudel") / "ensdf"
CACHE_DIR = platformdirs.user_cache_path("nudel")
CURRENT_FILE = DATA_DIR.parent / "current"

_VERSION_RE = re.compile(r"^ensdf_(\d{6})\.zip$")
_USER_AGENT = "nudel/0.0.1 (https://github.com/op3/nudel)"


class ManifestDistribution(TypedDict, total=False):
    year: str
    files: list[str]


class ManifestLatest(TypedDict, total=False):
    files: list[str]


class Manifest(TypedDict, total=False):
    distributions: list[ManifestDistribution]
    latest: ManifestLatest


class _Meta(TypedDict):
    version: str
    url: str
    sha256: str
    downloaded_at: str


def get_url(version: str) -> str:
    """Build the NNDC download URL for a given ``YYMMDD`` version string.

    Args:
        version: 6-digit ENSDF version (e.g. ``"260805"``).

    Returns:
        The full ``https`` download URL for the corresponding zip archive.

    Raises:
        ValueError: If ``version`` is not exactly 6 digits.
    """
    if not (len(version) == 6 and version.isdigit()):
        raise ValueError(f"Invalid ENSDF version: {version!r} (expected 6 digits)")
    return f"{ENSDF_BASE}/dist{version[:2]}/ensdf_{version}.zip"


def _get_api_manifest(*, refresh: bool = False) -> Manifest:
    """Return the parsed NNDC ``files.json`` manifest, with TTL caching.

    The manifest is cached at :data:`CACHE_DIR` ``/ "files.json"`` for
    :data:`API_CACHE_TTL` seconds. On a network failure a stale cache is
    returned with a warning; if no cache exists the error is re-raised.

    Args:
        refresh: Bypass the cache and force a fresh download.

    Returns:
        Parsed manifest dictionary.
    """
    cache_file = CACHE_DIR / "files.json"
    if (
        not refresh
        and cache_file.exists()
        and time.time() - cache_file.stat().st_mtime < API_CACHE_TTL
    ):
        manifest: Manifest = json.loads(cache_file.read_text())
        return manifest

    try:
        response = requests.get(
            ENSDF_API, headers={"User-Agent": _USER_AGENT}, timeout=30
        )
        response.raise_for_status()
        manifest = response.json()
    except Exception:
        if cache_file.exists():
            warnings.warn(
                "Failed to fetch NNDC manifest; using stale cache.",
                stacklevel=2,
            )
            manifest = json.loads(cache_file.read_text())
            return manifest
        raise

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(manifest))
    return manifest


def list_versions(*, refresh: bool = False) -> list[str]:
    """Return all available single-zip ENSDF versions, newest first.

    Only years >= 2022 (single-zip format) are considered; pre-2022 split
    archives are ignored.

    Args:
        refresh: Bypass the API cache when fetching the manifest.
    """
    manifest = _get_api_manifest(refresh=refresh)
    versions: list[str] = []
    for dist in manifest.get("distributions", []):
        try:
            year = int(dist["year"])
        except (KeyError, ValueError, TypeError):
            continue
        if year < 2022:
            continue
        for fname in dist.get("files", []):
            match = _VERSION_RE.match(fname)
            if match:
                versions.append(match.group(1))
    return sorted(versions, reverse=True)


def resolve_version(version: str = "latest", *, refresh: bool = False) -> str:
    """Resolve a version request to a concrete ``YYMMDD`` string.

    Args:
        version: ``"latest"`` or an explicit 6-digit version.
        refresh: Bypass the API cache when resolving ``"latest"``.

    Returns:
        A concrete 6-digit version string.

    Raises:
        ValueError: If ``version`` is unknown or malformed.
    """
    if version == "latest":
        manifest = _get_api_manifest(refresh=refresh)
        latest = manifest.get("latest")
        for fname in latest.get("files", []) if latest is not None else []:
            match = _VERSION_RE.match(fname)
            if match:
                return match.group(1)
        raise ValueError("No latest version found in NNDC manifest")
    available = list_versions(refresh=refresh)
    if version not in available:
        raise ValueError(
            f"Unknown ENSDF version: {version!r}. See `python -m nudel.fetch --list`."
        )
    return version


def current_version() -> str | None:
    """Return the pinned "current" version, or ``None`` if unset."""
    if not CURRENT_FILE.exists():
        return None
    value = CURRENT_FILE.read_text().strip()
    return value or None


def set_current(version: str) -> None:
    """Pin ``version`` as the current sticky-latest version."""
    CURRENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_FILE.write_text(version)


def fetch(version: str = "latest", *, refresh: bool = False) -> Path:
    """Download (if needed) and extract an ENSDF version, returning its path.

    With ``version="latest"`` and an existing pin, the pinned version is used
    without any network call (sticky-latest). On a successful fetch of a
    ``"latest"`` request the pin is updated.

    Args:
        version: ``"latest"`` or an explicit 6-digit version.
        refresh: Bypass caches (API + sticky-latest pin).

    Returns:
        Path to the directory holding the extracted ``ensdf.???`` files.
    """
    pinned = current_version()
    if version == "latest" and not refresh and pinned is not None:
        resolved = pinned
    else:
        resolved = resolve_version(version, refresh=refresh)

    data_path = DATA_DIR / resolved
    if data_path.exists() and any(data_path.glob("ensdf.???")):
        return data_path

    url = get_url(resolved)
    zip_path = pooch.retrieve(
        url,
        known_hash=None,
        path=CACHE_DIR / "downloads",
        fname=f"ensdf_{resolved}.zip",
    )
    zip_path = Path(zip_path)
    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    data_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(data_path)
    meta: _Meta = {
        "version": resolved,
        "url": url,
        "sha256": sha,
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    (data_path / "meta.json").write_text(json.dumps(meta, indent=2))
    zip_path.unlink()
    if version == "latest":
        set_current(resolved)
    return data_path


def _cli(argv: list[str] | None = None) -> int:
    """Command-line entry point for ``python -m nudel.fetch``."""
    parser = argparse.ArgumentParser(
        prog="python -m nudel.fetch",
        description="Fetch and cache ENSDF data from NNDC.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print all available versions, one per line (newest first).",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="print the resolved latest version.",
    )
    parser.add_argument(
        "--fetch",
        nargs="?",
        const="latest",
        default=None,
        metavar="VERSION",
        help="fetch VERSION (defaults to 'latest') and print its data path.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="bypass API and sticky-latest caches.",
    )
    args = parser.parse_args(argv)

    if args.list:
        for v in list_versions(refresh=args.refresh):
            print(v)
        return 0
    if args.latest:
        print(resolve_version("latest", refresh=args.refresh))
        return 0
    if args.fetch is not None:
        print(fetch(args.fetch, refresh=args.refresh))
        return 0
    current = current_version()
    if current is not None:
        print(current)
    else:
        print(resolve_version("latest", refresh=args.refresh))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
