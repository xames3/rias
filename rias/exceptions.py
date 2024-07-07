"""\
Rias Custom Exceptions
======================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, July 07 2024

This module defines custom exception classes for the Rias framework.
These exceptions are used throughout the Rias framework to handle
various error conditions in a consistent and meaningful way.
"""

from __future__ import annotations


class RiasException(Exception):
    """Base class for all exceptions raised by the Rias framework."""

    pass


class RiasEnvironmentError(RiasException):
    """Rias' environment is incorrectly configured."""

    pass
