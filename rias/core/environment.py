"""\
Rias Environment Management
===========================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, July 07 2024

This module manages a default-state environment (configurations) for the
Rias framework. It provides access to configurations or settings defined
in Rias' `defaults` module and allows for dynamic access and updating
of these settings during runtime.
"""

from __future__ import annotations

import importlib
import os
import typing as t

from rias.utils import defaults
from rias.utils.functional import LazyLoader
from rias.utils.functional import empty

_V = t.TypeVar("_V")

_USER_ENVIRONMENT_MODULE: t.Final[str] = "USER_ENVIRONMENT_MODULE"


class EnvironmentManager:
    """A class that manages Rias' working environment.

    This class provides access to Rias' fundamental or default
    environment settings defined in Rias' `defaults` module. It allows
    for dynamic access to these settings, default values, and provides
    methods for managing and updating configurations during runtime.

    :var _overridden: Set to track overridden configuration attributes.
    :param module: Path to the user-defined environment module.

    .. note::

        The EnvironmentManager class is designed to be used as a
        singleton, although not completely. The instance of environment
        manager is accessed via the LazyEnvironmentManager class which
        wraps this one.
    """

    def __init__(self, module: str | None) -> None:
        """Initialize the environment manager with specified environment
        module.

        This constructor imports settings from the `defaults` module but
        still allowing it to be overridden by the values from a
        user-specified configuration or environment module if provided.
        """
        for default in dir(defaults):
            setattr(self, default, getattr(defaults, default))
        self.__dict__["_overridden"] = set()
        self._user_module = module
        if self._user_module:
            settings = importlib.import_module(self._user_module)
            for setting in dir(settings):
                setattr(self, setting, getattr(settings, setting))

    def __repr__(self) -> str:
        """Return a string representation of the environment manager."""
        if self._user_module:
            return f"{type(self).__name__}({self._user_module!r})"
        return f"{type(self).__name__}({defaults.__name__!r})"


class LazyEnvironmentManager(LazyLoader):
    """A lazy proxy class for managing Rias' environment.

    This class extends the ``LazyLoader`` to provide lazy loading
    capabilities specifically for environment management. The purpose of
    this class is to defer the initialization and loading of the
    configuration settings until they are actually accessed. This can
    optimize performance and resource usage by avoiding unnecessary
    loading of environment data.

    The workable environment is not loaded at the time of the object's
    creation. Instead, it is loaded only when a configuration value or a
    setting is accessed for the first time. Once the setting is accessed
    and loaded, it is cached within the instance to allow for quick
    subsequent access without the need to reload the data.

    The class also provides overridden attribute access methods to
    seamlessly manage the lazy loading and caching of settings.

    .. note::

        The LazyEnvironmentManager class is designed to provide the
        same interface as the EnvironmentManager class, forwarding all
        attribute and method accesses to the underlying instance once it
        is initialized.
    """

    def _load(self) -> None:
        """Load the underlying EnvironmentManager instance.

        This method initializes the EnvironmentManager instance and
        stores it in the `_wrapped` attribute. It is called
        automatically when the lazy proxy is accessed for the first time.

        .. note::

            This method must be implemented by the subclasses of
            `LazyLoader`.
        """
        get = os.environ.get
        self._wrapped = EnvironmentManager(get(_USER_ENVIRONMENT_MODULE))

    def __repr__(self) -> str:
        """Return a string representation of the lazy env manager."""
        if self._wrapped is empty:
            return f"LazyEnvironmentManager('default')"
        return repr(self._wrapped)

    def __getattr__(self, name: str) -> t.Any:
        """Retrieve the value of a setting and cache it."""
        if (_wrapped := self._wrapped) is empty:
            self._load()
            _wrapped = self._wrapped
        value = getattr(_wrapped, name)
        self.__dict__[name] = value
        return value

    def __setattr__(self, name: str, value: t.Any) -> None:
        """Set the value of a setting to override."""
        if name == "_wrapped":
            self.__dict__.clear()
        else:
            if name not in self.__dict__:
                raise AttributeError(
                    "EnvironmentManager is already configured. You must set "
                    f"the attribute using environment.update({name}={value})"
                )
            self.__dict__.pop(name, None)
        return super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """Delete a configuration value and clear it from cache."""
        super().__delattr__(name)
        self.__dict__.pop(name, None)

    def update(self, **kwargs: _V) -> None:
        """Update and reconfigure manager with additional options."""
        for key, value in kwargs.items():
            if key in self.__dict__:
                self._overridden.add(key)
            else:
                self.__dict__[key] = object()
            setattr(self, key, value)

    @property
    def configured(self) -> bool:
        """Return True if the values have already been configured."""
        return self._wrapped is not empty


environment = LazyEnvironmentManager()
