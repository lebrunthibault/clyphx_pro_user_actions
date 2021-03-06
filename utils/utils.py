import inspect
import types
from collections import namedtuple, Sequence as CollectionsSequence
from types import FrameType

from qualname import qualname
from typing import Optional, Any, cast, Callable, TYPE_CHECKING, Iterable

from a_protocol_0.consts import ROOT_DIR, REMOTE_SCRIPTS_DIR
from a_protocol_0.my_types import StringOrNumber, T

if TYPE_CHECKING:
    pass


def scroll_values(items, selected_item, go_next, show_message=False):
    # type: (Iterable[T], Optional[T], bool, bool) -> T
    items_list = list(items)
    selected_item = selected_item or items_list[0]
    increment = 1 if go_next else -1
    index = 0
    try:
        index = (items_list.index(selected_item) + increment) % len(items_list)
        new_item = items_list[index]
        if show_message:
            from a_protocol_0 import Protocol0

            Protocol0.SELF.show_message("Selected %s" % new_item)
        return new_item
    except ValueError:
        return selected_item


def find_if(predicate, seq):
    # type: (Callable[[T], bool], CollectionsSequence[T]) -> Optional[T]
    for x in seq:
        if predicate(x):
            return x
    return None


def is_equal(val1, val2, delta=0.00001):
    # type: (StringOrNumber, StringOrNumber, float) -> bool
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        return abs(val1 - val2) < delta
    else:
        return val1 == val2


def clamp(val, minv, maxv):
    # type: (int, int, int) -> int
    return max(minv, min(val, maxv))


def get_frame_info(frame_count=1):
    # type: (int) -> Optional[Any]
    call_frame = inspect.currentframe()
    for _ in range(frame_count):
        call_frame = call_frame.f_back
    try:
        (filename, line, method_name, _, _) = inspect.getframeinfo(cast(FrameType, call_frame))
    except IndexError:
        return None
    filename = filename.replace(ROOT_DIR + "\\", "").replace(REMOTE_SCRIPTS_DIR + "\\", "")
    class_name = filename.replace(".py", "").split("\\")[-1]

    FrameInfo = namedtuple("FrameInfo", ["filename", "class_name", "line", "method_name"])
    return FrameInfo(filename=filename, class_name=class_name, line=line, method_name=method_name)


def _has_callback_queue(func):
    # type: (Any) -> bool
    """ mixing duck typing and isinstance to ensure we really have a callback handler object """
    from a_protocol_0.utils.callback_descriptor import CallableWithCallbacks
    from _Framework.SubjectSlot import CallableSlotMixin

    return (
        func
        and hasattr(func, "add_callback")
        and (isinstance(func, CallableWithCallbacks) or isinstance(func, CallableSlotMixin))
    )


def is_method(func):
    # type: (Callable) -> bool
    spec = inspect.getargspec(func)
    return bool(spec.args and spec.args[0] == "self")


def is_lambda(func):
    # type: (Callable) -> bool
    return isinstance(func, types.LambdaType) and func.__name__ == "<lambda>"


def get_inner_func(func):
    # type: (Any) -> Callable
    if hasattr(func, "function"):
        return get_inner_func(func.function)
    if hasattr(func, "func"):  # partial
        return get_inner_func(func.func)
    if hasattr(func, "original_func"):
        return get_inner_func(func.original_func)
    if hasattr(func, "listener"):
        return get_inner_func(func.listener)

    return func


def get_class_name_from_method(func):
    # type: (Any) -> str
    if hasattr(func, "__self__"):
        class_name = func.__self__.__class__.__name__

    elif hasattr(func, "__class__"):
        class_name = func.__class__.__name__

    if class_name and all(word not in class_name for word in ["function", "None"]):
        return class_name

    try:
        return ".".join(qualname(func).split(".")[:-1])
    except AttributeError:
        pass

    return ""


def get_callable_name(func, obj=None):
    # type: (Callable, object) -> str
    from a_protocol_0.sequence.Sequence import Sequence

    if isinstance(func, Sequence):
        return func.name

    decorated_func = get_inner_func(func)
    if obj:
        class_name = str(obj) if hasattr(obj, "__repr__") else obj.__class__.__name__
    else:
        class_name = get_class_name_from_method(decorated_func)

    if not hasattr(decorated_func, "__name__"):
        return class_name or "unknown"

    if class_name:
        return "%s.%s" % (class_name, decorated_func.__name__)
    else:
        return decorated_func.__name__


def nop():
    # type: () -> None
    pass
