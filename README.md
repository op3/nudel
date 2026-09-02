# 🍝 nudel – Nuclear Data Extraction Library

[![License](https://img.shields.io/badge/License-GPL%20v3+-blue.svg)](COPYING)
[![CI](https://github.com/op3/nudel/actions/workflows/main.yml/badge.svg)](https://github.com/op3/nudel/actions/workflows/main.yml)

Nudel is a parser for the Evaluated Nuclear Structure Data File (ENSDF) format implemented in Python.

## Introduction

[ENSDF](https://www.nndc.bnl.gov/ensdf/) provides recommended nuclear structure and decay information.
The data are organized in a special data format that is described [here](https://www.nndc.bnl.gov/nndcscr/documents/ensdf/ensdf-manual.pdf).
Nudel is an attempt to read those files such that the relevant information can be easily accessed using Python,
without having to worry about the details of the (complicated) data format.
The specification is quite extensive, and thus, the present approach is currently limited to only a few important quantities.
Especially cross-references and comments are not yet properly resolved.

## Obtaining nuclear datasets

### ENSDF

ENSDF data is fetched automatically on first use. The first time you create a
`Nuclide`, nudel downloads the latest ENSDF release from
[NNDC](https://www.nndc.bnl.gov/ensdf/) to `~/.local/share/nudel/ensdf/` and
extracts it. Subsequent uses work offline, reusing the cached data.

```python
from nudel import Nuclide

molybdenum94 = Nuclide(94, 42)  # triggers one-time download on first run
```

The fetched version is *pinned* (sticky-latest): new ENSDF releases do not
affect your scripts until you explicitly upgrade. To list available versions:

```bash
python -m nudel.fetch --list
```

To upgrade to the latest release:

```bash
python -m nudel.fetch --latest
# or in Python:
# Nuclide(94, 42, version="latest")
```

To use a specific ENSDF version (format `YYMMDD`):

```python
Nuclide(94, 42, version="260601")
```

#### Using a manual ENSDF installation

If you already have ENSDF data on disk (e.g. on an HPC cluster or offline
machine), set the `ENSDF_PATH` environment variable to the directory containing
your `ensdf.???` files. nudel will use that directory and never download:

```bash
export ENSDF_PATH=/path/to/ensdf
```

## Requirements

- python>=3.13

Runtime dependencies (`platformdirs`, `pooch`) are installed automatically.
For unit tests: `pytest`, `pytest-cov`.

## Usage

This is a minimal usage example, documentation will be improved in a future version:

```python
from nudel import Nuclide

molybdenum94 = Nuclide(94, 42)
```

## Examples

Notebooks with usage examples can be found in the [examples/notebooks](examples/notebooks) directory.

## License

Copyright © 2026

O. Papst

This code is distributed under the terms of the GNU General Public License v3 or later. See the [COPYING](COPYING) file for more information.
