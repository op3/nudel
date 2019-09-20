# 🍝 nudel – Nuclear Data Extraction Library

[![License](https://img.shields.io/badge/License-GPL%20v3+-blue.svg)](COPYING)

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

To use nudel, a copy of the ENSDF is currently required.
It can be obtained [here](https://www.nndc.bnl.gov/ensarchivals/).
You have to download three files ending in `_099.zip`, `_199.zip` and `_299.zip`.
These files correspond to the evaluated nuclei in the mass ranges 1–99, 100–199 and 200–299.
Extract all files into a single folder.
By default, nudel searches in `$XDG_DATA_HOME/ensdf` for the files (usually, this is `~/.local/share/ensdf`).
Alternatively, you can use `$ENSDF_PATH` to point to the correct directory.

### NUBASE

A future version of this library might support [NUBASE](http://amdc.in2p3.fr/web/nubase_en.html). 

## Requirements

- python>=3.6
- pytest (*optional, only for unit tests*)

No further libraries are required!

## Usage

This is a minimal usage example, documentation will be improved in a future version:

```python
from nudel import Nuclide

molybdenum94 = Nuclide(ensdf, 94, 42)
```

## Examples

Notebooks with usage examples can be found in the [examples/notebooks](examples/notebooks) directory.

## License

Copyright © 2019

O. Papst

This code is distributed under the terms of the GNU General Public License v3 or later. See the [COPYING](COPYING) file for more information.
