"""\
Rias
====

Author: XA <xa@mes3.dev>
Created on: Sunday, June 23 2024
Last updated on: Sunday, June 23 2024

:copyright: (c) 2024 XA. All rights reserved.
:license: MIT, see LICENSE for more details.
"""

from __future__ import annotations

import copy
import operator
import typing as t
from functools import wraps

T = t.TypeVar("T")

# Sentinel object used to denote an uninitialized state. This unique
# object is used to indicate that the lazy object has not been
# initialized. It acts as a placeholder until the actual object is
# created during the first access.
empty = object()


def lazy_proxy_method(func: t.Callable[..., T]) -> t.Callable[..., T]:
    """A proxy method to delay the evaluation of the wrapped object."""

    @wraps(func)
    def inner(self: LazyObject, *args: t.Any) -> T:
        if (_wrapped := self._wrapped) is empty:
            self._load()
            _wrapped = self._wrapped
        return func(_wrapped, *args)

    inner._mask_wrapped = False  # type: ignore[attr-defined]
    return inner


class LazyObject:
    """Base class to delay instantiation of the dervied class.

    This class delays the creation of an expensive object until it is
    actually needed. By subclassing this, you can intercept and alter
    the instantiation.
    """

    _wrapped: object | None = None

    def __init__(self) -> None:
        """Initialize the lazy instance with a sentinel."""
        # NOTE (xames3): If a subclass overrides ``__init__()``, it
        # must also override the ``__copy__()`` and ``__deepcopy__()``.
        self._wrapped = empty

    def __getattribute__(self, name: str) -> t.Any:
        """Retrieve an attribute from the instance."""
        if name == "_wrapped":
            # Directly access the sentinel to avoid recursion.
            return super().__getattribute__(name)
        value = super().__getattribute__(name)
        # If the attribute (name) is a proxy method, raise an error to
        # call ``__getattr__()`` and use the wrapped object method.
        if not getattr(value, "_mask_wrapped", True):
            raise AttributeError
        return value

    __getattr__: t.Callable[..., t.Any] = lazy_proxy_method(getattr)

    def __setattr__(self, name: str, value: t.Any) -> None:
        """Set an attribute on the instance."""
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

    def _load(self) -> None:
        """Must be implemented by the subclasses."""
        raise NotImplementedError("Subclasses must implement _load() method.")

    def __copy__(self) -> LazyObject:
        """Return a shallow copy of the instance."""
        # If uninitialized, copy the wrapper else return the copy of the
        # wrapped object.
        if self._wrapped is empty:
            return type(self)()
        else:
            return copy.copy(self._wrapped)  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, t.Any]) -> t.Any:
        """Return a deep copy of the instance."""
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
