"""\
Rias Randomization Utilities
============================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 30 2024
Last updated on: Sunday, July 07 2024

This module provides utility functions for generating random strings and
unique identifiers within the Rias framework. Under the hood, it
leverages Python's `secrets` module for cryptographically secure random
number generation, making it suitable for tasks requiring high security,
such as generating secret keys.
"""

from __future__ import annotations

import secrets
import string
from uuid import uuid4

_ASCII: str = string.ascii_letters


def generate_string(length: int, characters: str = _ASCII) -> str:
    """Generate a random string of specified length.

    This function creates a random string of specified length from the
    provided set of characters. By default, it uses ASCII letters (both
    uppercase and lowercase) if no character set is provided.

    :param length: The length of the random string to generate.
    :param characters: The string of characters to use for generating
        the random string, defaults to ASCII letters.
    :return: A random string of the specified length.
    """
    return "".join(secrets.choice(characters) for _ in range(length))


def generate_secret_key() -> str:
    """Generate a random secret key suitable for cryptographic use.

    This function creates a random secret key of length 50 using a
    predefined set of characters. The character set includes lowercase
    letters, digits, and special characters.

    :return: A random secret key of length 50.
    """
    characters = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return generate_string(50, characters)


# Generate a unique identifier using the UUID version 4 standard. This is
# useful for creating unique IDs for agents within the Rias framework.
generate_id = lambda: uuid4()
