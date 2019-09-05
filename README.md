# pyENSDF

A parser for the Evaluated Nuclear Structure Data File (ENSDF) format implemented in Python.

# Introduction

[ENSDF](https://www.nndc.bnl.gov/ensdf/) provides recommended nuclear structure and decay information.
The data are organized in a special data format that is described [here](https://www.nndc.bnl.gov/nndcscr/documents/ensdf/ensdf-manual.pdf).
pyENSDF is an attempt to read those files such that the relevant information can be easily accessed using Python,
without having to worry about the details of the (complicated) data format.
The specification is quite extensive, and thus, the present approach is currently limited to only a few important quantities.
Especially cross-references and comments are not yet properly resolved.
Furthermore, 


# Obtaining a copy of the ENSDF

To use pyENSDF, a copy of the ENSDF is currently required.
It can be obtained [here](https://www.nndc.bnl.gov/ensarchivals/).
You have to download three files ending in `_099.zip`, `_199.zip` and `_299.zip`.
These files correspond to the evaluated nuclei in the mass ranges 1–99, 100–199 and 200–299.
Extract all files into a single folder.
By default, pyENSDF searches in `$XDG_DATA_HOME/ensdf` for the files (usually, this is `~/.local/share/ensdf`).


# Requirements

- python>=3.7
- [uncertainties](https://pythonhosted.org/uncertainties/)
- [scipy](https://www.scipy.org/)

I expect to be able to drop both the `uncertainy` and `scipy` dependencies in a future version and add support for python3.6


# Usage

This is a minimal usage example, documentation will be improved in a future version:

```python
    from ensdf import ENSDF, Nucleus

    ensdf = ENSDF
    molybdenum94 = Nucleus(ensdf, 94, 42)
```

# License

Copyright 2018

This code is distributed under the terms of the GNU General Public License v3 or later. See the [COPYING](COPYING) file for more information.
