#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from io import open as io_open

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

__author__ = "Casper da Costa-Luis <casper.dcl@physics.org>"
__licence__ = "Apache-2.0"
src_dir = os.path.abspath(os.path.dirname(__file__))

README_rst = ""
fndoc = os.path.join(src_dir, "README.rst")
with io_open(fndoc, mode="r", encoding="utf-8") as fd:
    README_rst = fd.read()
requirements_dev = os.path.join(src_dir, "requirements-dev.txt")
with io_open(requirements_dev, mode="r", encoding="utf-8") as fd:
    requirements_dev = fd.readlines()
setup(
    name="shtab",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Automatically generate shell tab completion scripts"
    " for python CLI apps",
    long_description=README_rst,
    long_description_content_type="text/x-rst",
    license=__licence__,
    author=__author__.split("<")[0].strip(),
    author_email=__author__.split("<")[1][:-1],
    url="https://github.com/iterative/shtab",
    platforms=["any"],
    packages=["shtab"],
    provides=["shtab"],
    install_requires=[
        "argparse; python_version < '2.7'"
        " or ('3.0' <= python_version and python_version < '3.2')"
    ],
    extras_require={"dev": requirements_dev},
    entry_points={"console_scripts": ["shtab=shtab:main.main"]},
    package_data={"shtab": ["LICENCE"]},
    python_requires=">=2.7, !=3.0.*, !=3.1.*",
    classifiers=[
        # Trove classifiers
        # (https://pypi.org/pypi?%3Aaction=list_classifiers)
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Other Audience",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: SunOS/Solaris",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation",
        "Programming Language :: Python :: Implementation :: IronPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Unix Shell",
        "Topic :: Desktop Environment",
        "Topic :: Education :: Computer Aided Instruction (CAI)",
        "Topic :: Education :: Testing",
        "Topic :: Office/Business",
        "Topic :: Other/Nonlisted Topic",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Pre-processors",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Shells",
        "Topic :: System :: System Shells",
        "Topic :: Terminals",
        "Topic :: Utilities",
    ],
    keywords="tab complete completion shell bash zsh argparse",
)
