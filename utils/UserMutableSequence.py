import abc
from collections import MutableSequence as CollectionsMutableSequence

from typing import Any, Iterator, Union, TypeVar, MutableSequence

from _Framework.SubjectSlot import SubjectMeta
from a_protocol_0.lom.AbstractObject import AbstractObject

T = TypeVar("T")


class CombinedMeta(SubjectMeta, abc.ABCMeta):
    """
    makes it possible to inherit both from AbstractObject and class defining
    abc.ABCMeta as its meta class
    """

    pass


class UserMutableSequence(CollectionsMutableSequence, AbstractObject):
    __metaclass__ = CombinedMeta

    """
    base class for defining custom list classes
    """

    def __init__(self, list, *a, **k):
        # type: (MutableSequence[T], Any, Any) -> None
        super(UserMutableSequence, self).__init__(*a, **k)
        self._list = list

    def __getitem__(self, value):
        # type: (int) -> T
        assert isinstance(value, int), "slice access not allowed"
        return self._list[value]

    def __delitem__(self, value):
        # type: (T) -> None
        self._list.remove(value)

    def __setitem__(self, index, value):
        # type: (Union[int, slice], T) -> None
        if value in self or not isinstance(index, int):
            return None
        self._list[index] = value

    def insert(self, index, value):
        # type: (int, T) -> None
        self._list.insert(index, value)

    def __iter__(self):
        # type: () -> Iterator[T]
        return iter(self._list)

    def __len__(self):
        # type: () -> int
        return len(self._list)
