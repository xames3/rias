"""\
Rias Core Agent & Management
============================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 30 2024
Last updated on: Saturday, July 06 2024
"""

from __future__ import annotations

import types

from rias.exceptions import ConfigurationError


class AgentManager:
    """A class that represents a base agent manager.

    This class is responsible for managing the configuration and proper
    initialization of an agent within the framework.

    :param name: Fully qualified name of the agent.
    :param module: Root module for the agent.
    """

    name: str

    def __init__(self, name: str, module: types.ModuleType) -> None:
        """Initialize the manager with an agent name and it's module."""
        if not name.rpartition(".")[2].isidentifier():
            raise ConfigurationError(
                f"Agent name {name!r} is not a valid Python identifier"
            )
        # NOTE (xames3): Mapping of workflow to their respective workflow
        # classes. This mapping enables the dynamic retrieval and
        # instantiation of workflow classes by their names. Initially,
        # it is set to None. The deliberate initialization serves two
        # critical purposes:
        #   - Prevent accidental access
        #   - Indicate initialization state
        self._workflow_mapping = None
        self._workflow_module = None
        self._agent_name = name
        self._agent_module = module

    def __repr__(self) -> str:
        """Return a string representation of the agent manager."""
        return f"{type(self).__name__}({self._agent_name!r})"
