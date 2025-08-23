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
Extract the archive to `$XDG_DATA_HOME/ensdf`.
Usually, this path corresponds to `~/.local/share/ensdf`.
You should end up with files such as `~/.local/share/ensdf/ensdf.208`, etc.
Alternatively, you can set `$ENSDF_PATH` to point to a different directory for the data.

## Requirements

- python>=3.7
- pytest (*optional, only for unit tests*)
- pytest-cov (*optional, only for unit tests*)

No further libraries are required!

## Usage

This is a minimal usage example, documentation will be improved in a future version:

```python
from nudel import Nuclide

molybdenum94 = Nuclide(94, 42)
```

## Examples

Notebooks with usage examples can be found in the [examples/notebooks](examples/notebooks) directory.

## License

Copyright © 2019

O. Papst

This code is distributed under the terms of the GNU General Public License v3 or later. See the [COPYING](COPYING) file for more information.
