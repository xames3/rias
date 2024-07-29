"""\
Rias Default Settings
=====================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, July 28 2024

This module defines the default settings and values for the Rias
framework. These defaults are used throughout the framework unless
overridden by user-defined configurations.
"""

import typing as t

# TODO (xames3): Enforce value validation and type checking
debug: bool = True
components_registry: t.Iterable[str] = []
