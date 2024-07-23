"""\
Rias Core Agent & Management
============================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 30 2024
Last updated on: Sunday, July 14 2024
"""

from __future__ import annotations

import inspect
import types
import typing as t
from importlib import import_module

from rias.exceptions import RiasEnvironmentError
from rias.utils.functional import get_attribute
from rias.utils.functional import module_has_submodule

# NOTE (xames3): This is bound to change as the API gets more
# complicated to better suit the developers narratives. But for now,
# it's fine to move forward with this patchy implementation.
_AGENTS_MODULE: t.Literal["agents"] = "agents"


class Agent:
    pass


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
        self._agent_name = name
        self._agent_module = module
        if not name.rpartition(".")[2].isidentifier():
            raise RiasEnvironmentError(
                f"Agent manager, {type(self).__qualname__!r} has an attribute"
                " name which is not a valid Python identifier"
            )
        # NOTE (xames3): Mapping of workflow to their respective workflow
        # classes. This mapping enables the dynamic retrieval and
        # instantiation of workflow classes by their names. Initially,
        # it is set to None. The deliberate initialization serves two
        # critical purposes:
        #   - Prevent accidental access
        #   - Indicate initialization state
        # TODO (xames3): Add proper type hint for `_workflow_mapping`
        # when worflows are defined. Ideally it should be a mapping of
        # `dict[str, Workflow]` and not `Agent`.
        self._workflow_mapping = None
        self._workflow_module = None
        # A reference to the agents registry that manages this
        # AgentManager instance. This reference is assigned by the
        # registry itself when the AgentManager instance is registered.
        # The Agents registry acts as a central system that keeps track
        # of all the registered agents and their configurations within
        # the Rias framework. By setting this reference, the registry
        # allows the AgentManager to access the registry's
        # functionalities, enabling efficient communication and
        # coordination among different agents.
        self._registry: Agent | None = None

    def __repr__(self) -> str:
        """Return a string representation of the agent manager."""
        return f"{type(self).__name__}({self._agent_name!r})"

    @classmethod
    def create(cls, hook: str) -> AgentManager:
        """Create an AgentManager instance from the hook.

        This method is an Agent factory that creates an agent manager
        instance from the provided hook point.

        :param hook: Relative hook path to the agent manager.
        :return: Agent manager instance based off the hook.
        """
        # NOTE (xames3): Type definition is explicitly marked as `t.Any`
        # to bypass `mypy` errors due to eager evaluation.
        agent_manager: t.Any = None
        agent_module: t.Any = None
        agent_name: t.Any = None
        # Attempt to import the module specified by the hook. This block
        # tries to dynamically load the module using the hook string. If
        # an exception occurs, it means the module couldn't be imported.
        try:
            agent_module = import_module(hook)
        except Exception:
            agent_module = None
        else:
            # Check if the imported module has a submodule `agents`. The
            # submodule is expected to contain the actual agent manager
            # classes.
            # NOTE (xames3): This is not a guaranteed mechanism and
            # might change in future.
            if module_has_submodule(agent_module, _AGENTS_MODULE):
                module = import_module(f"{hook}.{_AGENTS_MODULE}")
                # Inspect the module to find all classes that are
                # subclasses of `AgentManager`. Filter these classes to
                # include only those that have the `primary` attribute
                # set to True. This allows developers to define more than
                # one manager in the same file.
                managers = [
                    (name, instance)
                    for name, instance in inspect.getmembers(
                        module, inspect.isclass
                    )
                    if (
                        issubclass(instance, cls)
                        and instance is not cls
                        and getattr(instance, "primary", True)
                    )
                ]
                # If there is exactly one primary manager, select it.
                if len(managers) == 1:
                    agent_manager = managers[0][1]
                else:
                    # If there are multiple primary managers, refine the
                    # search to those with `primary` set to False.
                    managers = [
                        (name, instance)
                        for name, instance in managers
                        if (getattr(instance, "primary", False))
                    ]
                    if len(managers) > 1:
                        # If more than one manager still remains, raise
                        # an error indicating the ambiguity. This one
                        # might be a little tricky to catch, hence the
                        # check.
                        raise RuntimeError(
                            "Multiple primary instances of AgentManager "
                            "found. Ensure only one primary AgentManager "
                            "is specified"
                        )
                    elif len(managers) == 1:
                        agent_manager = managers[0][1]
            if agent_manager is None:
                agent_manager = cls
                agent_name = hook
        if agent_manager is None:
            try:
                agent_manager = get_attribute(hook)
            except Exception:
                pass
        if agent_module is None and agent_manager is None:
            # HACK (xames3): Check if the path exists and if the agent
            # name starts with an uppercase letter (implying it's a
            # class). This is something which is not guaranteed.
            path, _, agent = hook.rpartition(".")
            if path and agent[0].isupper():
                module = import_module(path)
                managers = [
                    repr(name)  # type: ignore[misc]
                    for name, instance in inspect.getmembers(
                        module, inspect.isclass
                    )
                    if issubclass(instance, cls) and instance is not cls
                ]
                err = f"Couldn't find class {agent!r} in module {path!r}. "
                if managers:
                    err += f"Available managers are: {', '.join(managers)}"  # type: ignore[arg-type]
                raise ImportError(err)
            else:
                import_module(hook)
        if not issubclass(agent_manager, AgentManager):
            raise RiasEnvironmentError(
                f"The provided hook {hook!r} does not correspond to a valid"
                " subclass of AgentManager. Ensure the hook points to a proper"
                " AgentManager subclass"
            )
        if agent_name is None:
            try:
                agent_name = agent_manager.name
            except AttributeError:
                raise RiasEnvironmentError(
                    f"The specified agent manager {hook!r} does not have a"
                    " name attribute. Ensure the agent manager class defines a"
                    " 'name' attribute"
                )
        try:
            agent_module = import_module(agent_name)
        except ImportError:
            raise RiasEnvironmentError(
                f"Unable to import the agent module {agent_name!r}."
                " Ensure the module path is correct and the module is"
                " accessible."
            )
        return agent_manager(agent_name, agent_module)

    def get_workflow(self, workflow: str, loaded: bool = True) -> Agent:
        """Retrieve a workflow by its name, with an optional check for
        whether it has been loaded.

        This method allows retrieval of a workflow from the internal
        mapping by its name. It includes an optional parameter to
        specify whether to check if the workflow or agent has been loaded
        before attempting retrieval. This ensures that workflows are
        accessed only if they meet the specified loading criteria,
        thereby maintaining the integrity and state of the workflows
        within the system.

        :param workflow: The name of the workflow to be retrieved.
        :param loaded: A flag indicating whether to check if the workflow
            (if True) or agent (if False) has been loaded before
            retrieval, defaults to True.
        :return: Workflow (agent) associated with the specified name.
        :raises LookupError: If the workflow name is not found in the
            internal mapping.

        .. note::

            [1] The workflow names are stored in a case-insensitive
                manner, and thus the lookup is performed using the
                lowercase version of the provided name.
            [2] Ensure that the appropriate workflows or agents are
                loaded into the registry before attempting to retrieve
                them using this method.
        """
        if loaded:
            self._registry.are_workflows_loaded()
        else:
            self._registry.are_agents_loaded()
        try:
            return self._workflow_mapping[workflow.lower()]
        except KeyError:
            raise LookupError(
                f"Workflow (agent) {workflow!r} not found in the registry."
                " Ensure it is correctly loaded and the name is spelled"
                " correctly."
            )
