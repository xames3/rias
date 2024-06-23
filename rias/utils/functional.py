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
import functools
import operator
import typing as t

T = t.TypeVar("T")

# Sentinel object used to denote an uninitialized state. This unique
# object is used to indicate that the lazy object has not been
# initialized. It acts as a placeholder until the actual object is
# created during the first access.
empty = object()


def lazy_proxy_method(func: t.Callable[..., T]) -> t.Callable[..., T]:
    """A proxy method to delay the evaluation of the wrapped object."""

    @functools.wraps(func)
    def inner(self: LazyLoader, *args: t.Any) -> T:
        if (wrapped := self.wrapped) is empty:
            self.load()
            wrapped = self.wrapped
        return func(wrapped, *args)

    inner.mask_wrapped = False  # type: ignore[attr-defined]
    return inner


class LazyLoader:
    """Base class to delay instantiation of the dervied class.

    This class delays the creation of an expensive object until it is
    actually needed. By subclassing this, you can intercept and alter
    the instantiation.
    """

    wrapped: object | None = None

    def __init__(self) -> None:
        """Initialize the lazy instance with a sentinel."""
        # NOTE (xames3): If a subclass overrides __init__(), it must
        # also override the __copy__() and __deepcopy__().
        self.wrapped = empty

    def __getattribute__(self, name: str) -> t.Any:
        """Retrieve an attribute from the instance."""
        if name == "wrapped":
            # Directly access the sentinel to avoid recursion.
            return super().__getattribute__(name)
        value = super().__getattribute__(name)
        # If the attribute (name) is a proxy method, raise an error to
        # call __getattr__() and use the wrapped object method.
        if not getattr(value, "mask_wrapped", True):
            raise AttributeError
        return value

    __getattr__: t.Callable[..., t.Any] = lazy_proxy_method(getattr)

    def __setattr__(self, name: str, value: t.Any) -> None:
        """Set an attribute on the instance."""
        if name == "wrapped":
            # Directly assign to avoid infinite recursion.
            self.__dict__["wrapped"] = value
        else:
            if self.wrapped is empty:
                self.load()
            setattr(self.wrapped, name, value)

    def __delattr__(self, name: str) -> None:
        """Delete an attribute from the instance."""
        if name == "wrapped":
            raise TypeError("Can't delete 'wrapped' attribute")
        if self.wrapped is empty:
            self.load()
        delattr(self.wrapped, name)

    def load(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Must be implemented by the subclasses."""
        raise NotImplementedError("Subclasses must implement load() method.")

    def __copy__(self) -> LazyLoader:
        """Return a shallow copy of the instance."""
        # If uninitialized, copy the wrapper else return the copy of the
        # wrapped object.
        if self.wrapped is empty:
            return type(self)()
        else:
            return copy.copy(self.wrapped)  # type: ignore[return-value]

    def __deepcopy__(self, memo: dict[int, t.Any]) -> t.Any:
        """Return a deep copy of the instance."""
        if self.wrapped is empty:
            output = type(self)()
            memo[id(self)] = output
            return output
        return copy.deepcopy(self.wrapped, memo)

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
