"""\
Rias Components & Management
============================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 30 2024
Last updated on: Saturday, July 27 2024
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
_COMPONENTS_MODULE: t.Literal["components"] = "components"
_WORKFLOWS_MODULE: t.Literal["workflows"] = "workflows"


class Components:
    pass


class ComponentManager:
    """A class that represents a base component manager.

    This class is responsible for managing the configuration and proper
    initialization of a component within the framework.

    :param name: Fully qualified name of the component.
    :param module: Root module for the component.
    """

    name: str

    def __init__(self, name: str, module: types.ModuleType) -> None:
        """Initialize the manager with a name and it's module."""
        self._component_name = name.rpartition(".")[2]
        self._component_module = module
        if not self._component_name.isidentifier():
            raise RiasEnvironmentError(
                f"ComponentManager, {type(self).__qualname__!r} has an"
                " attribute name which is not a valid Python identifier"
            )
        # NOTE (xames3): Mapping of workflow to their respective workflow
        # classes. This mapping enables the dynamic retrieval and
        # instantiation of workflow classes by their names. Initially,
        # it is set to `None`. The deliberate initialization serves two
        # critical purposes:
        #   - Prevent accidental access
        #   - Indicate initialization state
        # TODO (xames3): Add proper type hint for `_workflow_mapping`
        # when worflows are defined. Ideally it should be a mapping of
        # `dict[str, Workflow]` and not `Components`.
        self._workflow_mapping = None
        self._workflow_module = None
        # A reference to the components registry that manages this
        # `ComponentManager` instance. This reference is assigned by the
        # registry itself when the `ComponentManager` instance is
        # registered. The Components registry acts as a central system
        # that keeps track of all the registered components and their
        # configurations within the Rias framework. By setting this
        # reference, the registry allows the `ComponentManager` to
        # access the registry's functionalities, enabling efficient
        # communication and coordination among different components.
        self._registry: Components | None = None

    def __repr__(self) -> str:
        """Return a string representation of the component manager."""
        return f"{type(self).__name__}({self._component_name!r})"

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
            if module_has_submodule(component_module, _COMPONENTS_MODULE):
                module = import_module(f"{hook}.{_COMPONENTS_MODULE}")
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
                managers = [
                    repr(name)  # type: ignore[misc]
                    for name, instance in inspect.getmembers(
                        module, inspect.isclass
                    )
                    if issubclass(instance, cls) and instance is not cls
                ]
                err = f"Couldn't find class {component!r} in module {path!r}. "
                if managers:
                    err += f"Available managers are: {', '.join(managers)}"  # type: ignore[arg-type]
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
                component_name = component_manager.name
            except AttributeError:
                raise RiasEnvironmentError(
                    f"The specified component manager {hook!r} does not have a"
                    " name attribute. Ensure the component manager class"
                    " defines a 'name' attribute"
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

    def get_workflow(self, workflow: str, loaded: bool = True) -> Components:
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
        if loaded:
            self._registry.are_workflows_loaded()
        else:
            self._registry.are_components_loaded()
        try:
            return self._workflow_mapping[workflow.lower()]
        except KeyError:
            raise LookupError(
                f"Workflow (component) {workflow!r} not found in the registry."
                " Ensure it is correctly loaded and the name is spelled"
                " correctly."
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
        self._workflow_mapping = self._registry.workflows[self._component_name]
        if module_has_submodule(self._component_module, _WORKFLOWS_MODULE):
            self._workflow_module = import_module(
                f"{self._component_name}.{_WORKFLOWS_MODULE}"
            )
