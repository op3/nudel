#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2026 nudel contributors.
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

"""End-to-end smoke test: parse *every* dataset in the latest ENSDF release.

This test loads the pinned/latest ENSDF distribution (downloading it on
first run, reusing the cache thereafter — same mechanism as the rest of
the test suite and CI) and feeds every indexed dataset through the real
``nudel.core.Dataset`` parser. It does not assert on the *contents* of any
individual dataset; it only verifies that the parser does not blow up on
real-world data at scale. A small failure budget is tolerated so that
known minor parser bugs (tracked in TODO.md) do not mask regressions.
"""

from __future__ import annotations

import warnings

import pytest
from nudel import fetch
from nudel.core import ENSDF

# Fraction of datasets that must parse cleanly. Kept generous to tolerate
# the handful of known parser bugs (e.g. ``AngularMoment.__repr__`` with
# ``div is None``, the ``add_jpi`` indentation bug) without masking new
# regressions. Bump it down as those bugs get fixed.
MIN_SUCCESS_RATE = 0.95


@pytest.fixture(scope="module")
def ensdf_latest():
    """Return an active :class:`ENSDF` backed by the latest ENSDF release.

    Skips the whole module if the data cannot be obtained (e.g. no network
    and no cached copy), so local runs without data do not hard-fail.
    """
    try:
        fetch.fetch("latest")
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"could not obtain ENSDF data: {exc}")

    ensdf = ENSDF(provider=None)  # default provider resolves the pin/path
    # ``Dataset.__init__`` consults the module-global ``active_ensdf``, so
    # install this instance for the lifetime of the module.
    ENSDF.active_ensdf = ensdf
    assert ensdf.datasets, "ENSDF index is empty"
    yield ensdf
    ENSDF.active_ensdf = None


def test_parse_all_datasets_smoke(ensdf_latest):
    """Every indexed dataset in the latest ENSDF release must parse.

    Collects per-dataset failures and asserts the overall success rate is
    at least :data:`MIN_SUCCESS_RATE`. Failure details are surfaced via the
    assertion message so regressions are immediately diagnosable.
    """
    total = 0
    failures: list[str] = []

    # The parser emits ``warnings.warn`` for malformed records; suppress the
    # flood so the test report stays readable.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for nucleus, name in list(ensdf_latest.datasets):
            total += 1
            try:
                ensdf_latest.get_dataset(nucleus, name)
            except Exception as exc:  # noqa: BLE001 - smoke test: any failure
                failures.append(f"{nucleus} {name!r}: {type(exc).__name__}: {exc}")

    success = total - len(failures)
    rate = success / total if total else 0.0
    summary = (
        f"parsed {success}/{total} datasets ({rate:.2%}); {len(failures)} failures"
    )
    assert rate >= MIN_SUCCESS_RATE, (
        summary
        + "\n"
        + "\n".join(failures[:50])
        + ("\n..." if len(failures) > 50 else "")
    )
    assert total > 0
    # Surface the summary even on success (truncated) for visibility in CI logs.
    if failures:
        print(f"\n[smoke] {summary}\n" + "\n".join(failures[:20]))
