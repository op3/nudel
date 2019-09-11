#!/usr/bin/env python

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

KEYWORDS = '''\
ensdf
nuclear-data
nuclear-physics
nuclear-structure
parser
physics
python
'''
CLASSIFIERS = '''\
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
Operating System :: MacOS :: MacOS X
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: POSIX :: BSD
Operating System :: POSIX :: Linux
Operating System :: UNIX
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Topic :: Scientific/Engineering
Topic :: Scientific/Engineering :: Physics
'''

setup(
    name='nudel',
    version='0.0.1',
    description='Nuclear Data Extraction Library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/op3/nudel',
    author='O. Papst',
    author_email='opapst@ikp.tu-darmstadt.de',
    license='GPL',
    classifiers=CLASSIFIERS.strip().split('\n'),
    keywords=KEYWORDS.strip().replace('\n', ' '),
    extras_require={
        'test': [
            'pytest',
            'pytest-cov'
        ],
    },
    packages=[
        'nudel',
    ],
)

