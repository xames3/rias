"""\
Rias
====

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, June 23 2024

:copyright: (c) 2024 XA. All rights reserved.
:license: MIT, see LICENSE for more details.
"""

import platform
import site
import sys

from pkg_resources import parse_version

try:
    import setuptools
except ImportError:
    raise RuntimeError(
        "Could not install Rias in the environment as setuptools is "
        "missing. Please create a new virtual environment before proceeding."
    )

mini_py_version: str = "3.10"
rias_py_version: str = platform.python_version()

if parse_version(rias_py_version) < parse_version(mini_py_version):
    raise SystemExit(
        "Could not install Rias! It requires python version 3.10+, "
        f"you are using {rias_py_version}..."
    )

# BUG: Cannot install into user directory with editable source.
# Using this solution: https://stackoverflow.com/a/68487739/14316408
# to solve the problem with installation. As of October, 2022 the issue
# is still open on GitHub: https://github.com/pypa/pip/issues/7953.
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

if __name__ == "__main__":
    setuptools.setup()
