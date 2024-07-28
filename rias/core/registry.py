"""\
Rias Components & Management
============================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 30 2024
Last updated on: Sunday, July 28 2024
"""

from __future__ import annotations

import inspect
import sys
import types
import typing as t
from collections import defaultdict
from importlib import import_module

from rias.exceptions import RiasEnvironmentError
from rias.utils.functional import get_attribute
from rias.utils.functional import module_has_submodule
from rias.workflows.core import Workflow

WM = dict[str, type[Workflow]]


class Components:
    """A registry that stores the configuration of installed components
    within the Rias framework.
    """

    def __init__(
        self, managers: t.Iterable[ComponentManager | str] | None = ()
    ) -> None:
        """Initialize the components with registered components."""
        if managers is None and hasattr(sys.modules[__name__], "components"):
            raise RuntimeError("You must supply 'managers' argument.")
        self.workflows: t.DefaultDict[str, WM] = defaultdict(dict)
        self.manangers: dict[str, ComponentManager] = {}

    def are_workflows_loaded(self) -> None:
        ...

    def are_components_loaded(self) -> None:
        ...


class ComponentManager:
    """A class that represents a base component manager.

    This class is responsible for managing the configuration and proper
    initialization of a component within the framework.

    :param name: Fully qualified name of the component.
    :param module: Root module for the component.
    """

    alias: str

    def __init__(self, name: str, module: types.ModuleType) -> None:
        """Initialize the manager with a name and it's module."""
        self.name = name.rpartition(".")[2]
        self.module = module
        if not self.name.isidentifier():
            raise RiasEnvironmentError(
                f"ComponentManager, {type(self).__qualname__!r} has an"
                " attribute name which is not a valid Python identifier"
            )
        # NOTE (xames3): Mapping of workflow to their respective workflow
        # classes. This mapping enables the dynamic retrieval and
        # instantiation of workflow classes by their names. The
        # deliberate initialization serves two critical purposes:
        #   - Prevent accidental access
        #   - Indicate initialization state
        self.workflow_mapping: WM = {}
        self.workflow_module: types.ModuleType | None = None
        # A reference to the components registry that manages this
        # `ComponentManager` instance. This reference is assigned by the
        # registry itself when the `ComponentManager` instance is
        # registered. The Components registry acts as a central system
        # that keeps track of all the registered components and their
        # configurations within the Rias framework. By setting this
        # reference, the registry allows the `ComponentManager` to
        # access the registry's functionalities, enabling efficient
        # communication and coordination among different components.
        self.components: Components | None = None

    def __repr__(self) -> str:
        """Return a string representation of the component manager."""
        return f"{type(self).__name__}({self.name!r})"

    @classmethod
    def create(cls, hook: str) -> ComponentManager:
        """Create a `ComponentManager` instance from the hook.

        This method is a component factory that creates a component
        manager instance from the provided hook point.

        :param hook: Relative hook path to the component manager.
        :return: Component manager instance based off the hook.
        """
        # NOTE (xames3): Type definition is explicitly marked as `t.Any`
        # to bypass `mypy` errors due to eager evaluation.
        component_manager: t.Any = None
        component_module: t.Any = None
        component_name: t.Any = None
        # Attempt to import the module specified by the hook. This block
        # tries to dynamically load the module using the hook string. If
        # an exception occurs, it means the module couldn't be imported.
        try:
            component_module = import_module(hook)
        except Exception:
            component_module = None
        else:
            # Check if the imported module has a submodule `components`.
            # The submodule is expected to contain the actual component
            # manager classes.
            # NOTE (xames3): This is not a guaranteed mechanism and
            # might change in future.
            if module_has_submodule(component_module, "components"):
                module = import_module(f"{hook}.components")
                # Inspect the module to find all classes that are
                # subclasses of `ComponentManager`. Filter these classes
                # to include only those that have the `primary`
                # attribute set to true. This allows developers to
                # define more than one manager in the same file.
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
                    component_manager = managers[0][1]
                else:
                    # If there are multiple primary managers, refine the
                    # search to those with `primary` set to false.
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
                            "Multiple primary instances of ComponentManager "
                            "found. Ensure only one primary ComponentManager "
                            "is specified"
                        )
                    elif len(managers) == 1:
                        component_manager = managers[0][1]
            if component_manager is None:
                component_manager = cls
                component_name = hook
        if component_manager is None:
            try:
                component_manager = get_attribute(hook)
            except Exception:
                pass
        if component_module is None and component_manager is None:
            # HACK (xames3): Check if the path exists and if the
            # component name starts with an uppercase letter (implying
            # it's a class). This is something which is not guaranteed.
            path, _, component = hook.rpartition(".")
            if path and component[0].isupper():
                module = import_module(path)
                available = [
                    repr(name)
                    for name, instance in inspect.getmembers(
                        module, inspect.isclass
                    )
                    if issubclass(instance, cls) and instance is not cls
                ]
                err = f"Couldn't find class {component!r} in module {path!r}. "
                if available:
                    err += f"Available managers are: {', '.join(available)}"
                raise ImportError(err)
            else:
                import_module(hook)
        if not issubclass(component_manager, ComponentManager):
            raise RiasEnvironmentError(
                f"The provided hook {hook!r} does not correspond to a valid"
                " subclass of ComponentManager. Ensure the hook points to a"
                " proper ComponentManager subclass"
            )
        if component_name is None:
            try:
                component_name = component_manager.alias
            except AttributeError:
                raise RiasEnvironmentError(
                    f"The specified component manager {hook!r} does not have"
                    " an 'alias' attribute"
                )
        try:
            component_module = import_module(component_name)
        except ImportError:
            raise RiasEnvironmentError(
                f"Unable to import the component module {component_name!r}."
                " Ensure the module path is correct and the module is"
                " accessible."
            )
        return component_manager(component_name, component_module)

    def get_workflow(
        self, workflow: str, loaded: bool = True
    ) -> type[Workflow]:
        """Retrieve a workflow by its name, with an optional check for
        whether it has been loaded.

        This method allows retrieval of a workflow from the internal
        mapping by its name. It includes an optional parameter to
        specify whether to check if the workflow or component has been
        loaded before attempting retrieval. This ensures that workflows
        are accessed only if they meet the specified loading criteria,
        thereby maintaining the integrity and state of the workflows
        within the system.

        :param workflow: The name of the workflow to be retrieved.
        :param loaded: A flag indicating whether to check if the workflow
            (if True) or component (if False) has been loaded before
            retrieval, defaults to True.
        :return: Workflow (component) associated with the specified name.
        :raises LookupError: If the workflow name is not found in the
            internal mapping.

        .. note::

            [1] The workflow names are stored in a case-insensitive
                manner, and thus the lookup is performed using the
                lowercase version of the provided name.
            [2] Ensure that the appropriate workflows or components are
                loaded into the registry before attempting to retrieve
                them using this method.
        """
        assert self.components is not None
        if loaded:
            self.components.are_workflows_loaded()
        else:
            self.components.are_components_loaded()
        try:
            return self.workflow_mapping[workflow.lower()]
        except KeyError:
            raise LookupError(
                f"Workflow (component) {workflow!r} not found in the registry."
                " Ensure it is correctly loaded and the name is spelled"
                " correctly"
            )

    def load_workflows(self) -> None:
        """Load and map workflows the current `ComponentManager`.

        This method initializes the workflow mapping for the component
        manager by assigning workflows from the registry specific to the
        component's name. It also checks if the component module
        contains a submodule named `workflows`, and it found, imports
        this submodule. This enables the dynamic loading and management
        of workflows associated with the component, ensuring that all
        relevant workflows are available for use within the system.

        .. note::

            [1] This method assumes that the registry's workflows are
                correctly structured and mapped to the component's name.
                Ensure that the registry is properly initialized and
                populated before invoking this method.
            [2] The `workflows` submodule should exist within the
                component's module if additional workflow definitions are
                required. Otherwise, the method relies solely on the
                registry's workflows mapping.
        """
        assert self.components is not None
        assert self.workflow_module is not None
        self.workflow_mapping = self.components.workflows[self.name]
        if module_has_submodule(self.module, "workflows"):
            self.workflow_module = import_module(f"{self.name}.workflows")
