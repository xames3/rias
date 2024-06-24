"""\
Rias Framework
==============

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, June 23 2024

This module initializes the Rias framework, setting up the necessary
imports and configurations required for the framework to function
properly.

The Rias project provides a comprehensive framework for machine learning
workflow management, enabling users to easily fetch datasets, write
custom models, train them, and deploy to various cloud services. It
relies on a community of contributors who write plugins or agents to
extend its functionality.
"""

from rias.utils.config import configuration as configuration
from rias.version import __version__ as __version__

version: str = __version__
