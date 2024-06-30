"""\
Rias Functional Utilities
=========================

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, June 30 2024

This module contains functional utilities for the Rias framework. These
utilities include classes and functions that support lazy loading, proxy
methods, and other functional programming techniques.
"""

from __future__ import annotations

import copy
import functools
import importlib
import importlib.util
import operator
import sys
import typing as t

T = t.TypeVar("T")

# Sentinel object used to denote an uninitialized state. This unique
# object is used to indicate that the lazy object has not been
# initialized. It acts as a placeholder until the actual object is
# created during the first access.
empty = object()


def get_cached_attribute(path: str, key: str) -> t.Callable[..., T]:
    """Access a specified attribute from a module from cached import.

    This function first checks if the module (path) is already loaded
    and fully initialized. If the module is not loaded or is still
    initializing, it imports the module. Then, it retrieves the specified
    attribute from the module.

    :param path: Fully qualified name of the module from which to load
                 the attribute.
    :param key: The name of the attribute to load from the module.
    :returns: The specified attribute from the module.
    """
    if not (
        (module := sys.modules.get(path))
        and (spec := getattr(module, "__spec__", None))
        and getattr(spec, "_initializing", False) is False
    ):
        module = importlib.import_module(path)
    return getattr(module, key)


def get_attribute(path: str) -> t.Callable[..., T] | None:
    """Access attribute from a module based on the provided path.

    This function takes a fully qualified path (dotted path) string that
    specifies a module and an attribute within that module. It splits
    the path into the module part and the attribute part, then attempts
    to load the attribute using the `get_cached_attribute` function.
    If the attribute cannot be found, it raises an `ImportError`.

    :param path: Fully qualified path to the attribute.
    :returns: Attribute from the module.
    :raises ImportError: If the path is invalid or the attribute cannot
                         be imported.
    """
    try:
        path, key = path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(f"Module path {path!r} is not valid") from err
    try:
        return get_cached_attribute(path, key)
    except AttributeError as err:
        raise ImportError(f"Module {path!r} has no attribute {key!r}") from err


def lazy_proxy_method(method: t.Callable[..., T]) -> t.Callable[..., T]:
    """A decorator to define a lazy proxy method.

    This function returns a decorator that can be used to define methods
    on the LazyLoader class that forward their calls to the underlying
    object once it is loaded.

    :param method: The method to be proxied.
    :return: A decorated method that forwards to the proxied method.
    """

    @functools.wraps(method)
    def _proxy(self: LazyLoader, *args: t.Any, **kwargs: t.Any) -> T:
        if (_wrapped := self._wrapped) is empty:
            self._load()
            _wrapped = self._wrapped
        return method(_wrapped, *args, **kwargs)

    _proxy._mask_wrapped = False  # type: ignore[attr-defined]
    return _proxy


class LazyLoader:
    """A base class for lazy loading (delay instantiation).

    This class provides a mechanism for deferring the initialization
    of an object until it is accessed for the first time. It acts as a
    proxy that forwards all attribute and method accesses to the
    underlying object once it is initialized.

    :var _wrapped: The underlying object (module, function or class)
                   that is going to be wrapped by the child class or
                   lazily loaded, defaults to None.
    """

    _wrapped: object | None = None

    def __init__(self) -> None:
        """Initialize the lazy loader.

        This constructor initializes the _wrapped attribute to the
        sentinel value `empty`, indicating that the underlying object
        has not been loaded yet.
        """
        # NOTE (xames3): If a subclass overrides __init__(), it must
        # also override the __copy__() and __deepcopy__().
        self._wrapped = empty

    def _load(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Load the underlying object.

        This method is a placeholder that must be implemented by
        subclasses to initialize the underlying object. It is called
        automatically when the lazy proxy is accessed for the first time.

        :raises NotImplementedError: If not implemented by the subclass.
        """
        raise NotImplementedError("Subclasses must implement _load() method.")

    def __getattribute__(self, name: str) -> t.Any:
        """Forward attribute access to the underlying object.

        This method is called when an attribute is accessed on the lazy
        proxy. It triggers the loading of the underlying object if it
        has not been loaded yet, and then forwards the attribute access
        to it.

        :param name: The name of the attribute to access.
        :return: The value of the attribute on the underlying object.
        """
        if name == "_wrapped":
            # Directly access the sentinel to avoid recursion.
            return super().__getattribute__(name)
        value = super().__getattribute__(name)
        # If the attribute (name) is a proxy method, raise an error to
        # call __getattr__() and use the _wrapped object method.
        if not getattr(value, "_mask_wrapped", True):
            raise AttributeError
        return value

    __getattr__: t.Callable[..., t.Any] = lazy_proxy_method(getattr)

    def __setattr__(self, name: str, value: t.Any) -> None:
        """Forward attribute assignment to the underlying object.

        This method is called when an attribute is assigned on the lazy
        proxy. It triggers the loading of the underlying object if it
        has not been loaded yet, and then forwards the attribute
        assignment to it.

        :param name: The name of the attribute to assign.
        :param value: The value to assign to the attribute.
        """
        if name == "_wrapped":
            # Directly assign to avoid infinite recursion.
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._load()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name: str) -> None:
        """Delete an attribute from the instance."""
        if name == "_wrapped":
            raise TypeError("Can't delete '_wrapped' attribute")
        if self._wrapped is empty:
            self._load()
        delattr(self._wrapped, name)

    def __copy__(self) -> LazyLoader:
        """Return a shallow copy of the lazy loader.

        This method creates a shallow copy of the lazy proxy. If the
        underlying object has not been loaded yet, the copy remains
        uninitialized. Otherwise, the copy is of the loaded object.

        :return: A shallow copy of the lazy loader.
        """
        # If uninitialized, copy the wrapper else return the copy of the
        # _wrapped object.
        if self._wrapped is empty:
            return type(self)()
        else:
            return copy.copy(self._wrapped)  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, t.Any]) -> t.Any:
        """Return a deep copy of the lazy loader.

        This method creates a deep copy of the lazy proxy. If the
        underlying object has not been loaded yet, the deep copy remains
        uninitialized. Otherwise, the deep copy is of the loaded object.

        :param memo: A dictionary of objects already copied during the
                     current copying pass.
        :return: A deep copy of the lazy loader.
        """
        if self._wrapped is empty:
            output = type(self)()
            memo[id(self)] = output
            return output
        return copy.deepcopy(self._wrapped, memo)

    __class__ = property(  # type: ignore[assignment]
        lazy_proxy_method(operator.attrgetter("__class__"))
    )

    __bool__: t.Callable[..., bool] = lazy_proxy_method(bool)
    __bytes__: t.Callable[..., bytes] = lazy_proxy_method(bytes)
    __str__: t.Callable[..., str] = lazy_proxy_method(str)

    __dir__: t.Callable[..., list[str]] = lazy_proxy_method(dir)
    __hash__: t.Callable[..., int] = lazy_proxy_method(hash)
    __iter__: t.Callable[..., t.Any] = lazy_proxy_method(iter)
    __len__: t.Callable[..., int] = lazy_proxy_method(len)

    __contains__: t.Callable[..., bool] = lazy_proxy_method(operator.contains)
    __delitem__: t.Callable[..., None] = lazy_proxy_method(operator.delitem)
    __getitem__: t.Callable[..., t.Any] = lazy_proxy_method(operator.getitem)
    __setitem__: t.Callable[..., None] = lazy_proxy_method(operator.setitem)

    __eq__: t.Callable[..., bool] = lazy_proxy_method(operator.eq)
    __gt__: t.Callable[..., bool] = lazy_proxy_method(operator.gt)
    __lt__: t.Callable[..., bool] = lazy_proxy_method(operator.lt)
    __ne__: t.Callable[..., bool] = lazy_proxy_method(operator.ne)
