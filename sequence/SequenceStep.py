from functools import partial

from typing import TYPE_CHECKING, Iterable, Any, Union, Callable, Optional, cast, List

from _Framework.SubjectSlot import subject_slot
from a_protocol_0.errors.SequenceError import SequenceError
from a_protocol_0.lom.AbstractObject import AbstractObject
from a_protocol_0.sequence.SequenceStateMachineMixin import SequenceStateMachineMixin
from a_protocol_0.utils.callback_descriptor import CallableWithCallbacks
from a_protocol_0.utils.decorators import p0_subject_slot
from a_protocol_0.utils.timeout import TimeoutLimit
from a_protocol_0.utils.utils import _has_callback_queue, is_lambda, get_callable_name, nop

if TYPE_CHECKING:
    from a_protocol_0.sequence.Sequence import Sequence


class SequenceStep(AbstractObject, SequenceStateMachineMixin):
    __subject_events__ = ("terminated", "errored")

    def __init__(
        self,
        func,  # type: Callable
        sequence,  # type: Sequence
        wait,  # type: int
        name,  # type: str
        complete_on,  # type: Optional[Union[Callable, CallableWithCallbacks]]
        do_if,  # type: Optional[Callable]
        return_if,  # type: Optional[Callable]
        check_timeout,  # type: int
        silent,  # type: bool
        *a,  # type: Any
        **k  # type: Any
    ):
        """ the tick is 100 ms """
        super(SequenceStep, self).__init__(*a, **k)
        self.debug = False if silent else sequence.debug
        self._original_name = name
        if not name and func == nop:
            name = "wait %s" % wait if wait else "pass"
        self.name = "step %s" % (name or get_callable_name(func))
        self._sequence_name = sequence.name
        self._callable = func
        self._wait = wait or 0
        self._complete_on = complete_on
        self._check_timeout = check_timeout
        self._check_count = 0
        self._callback_timeout = None  # type: Optional[Callable]
        self.res = None  # type: Optional[Any]
        self._do_if = do_if
        self._return_if = return_if
        self.early_returned = False

        conditions = [do_if, return_if]
        self._condition = next((c for c in conditions if c), None)  # type: Optional[Callable]

        assert callable(self._callable), "You passed a non callable (%s) to %s" % (self._callable, self)
        assert len(list(filter(None, conditions))) <= 1, "You cannot specify multiple conditions in a step"
        from a_protocol_0.sequence.Sequence import Sequence

        assert all(
            [not isinstance(condition, Sequence) for condition in conditions]
        ), "You passed a Sequence object instead of a Sequence factory for a condition"

    def __repr__(self):
        # type: () -> str
        output = self.name
        if self._complete_on:
            if _has_callback_queue(self._complete_on):
                output += " (and wait for listener call : %s)" % get_callable_name(self._complete_on)
            elif is_lambda(self._complete_on) and not self._original_name and self.debug:
                output += " (and poll for lambda condition)"
            else:
                output += " (and poll for %s)" % get_callable_name(self._complete_on)
        if self._do_if:
            output += " (has_if)"
        elif self._return_if:
            output += " (has_return_if)"

        return "[%s]" % output

    @staticmethod
    def make(sequence, callback, *a, **k):
        # type: (Sequence, Union[Callable, Iterable], Any, Any) -> SequenceStep
        if isinstance(callback, Iterable):

            def parallel_sequence_creator(callbacks):
                # type: (List[Callable]) -> Sequence
                from a_protocol_0.sequence.ParallelSequence import ParallelSequence

                seq = ParallelSequence(silent=not sequence.debug)
                [seq.add(func) for func in callbacks]
                return seq.done()

            callback = partial(parallel_sequence_creator, callback)

        return SequenceStep(callback, sequence=sequence, *a, **k)

    def _on_start(self):
        # type: () -> None
        if self._condition:
            self._execute_condition()
        else:
            self._execute()

    def _execute_condition(self):
        # type: () -> None
        terminate_callback = cast(
            CallableWithCallbacks,
            (self._terminate_if_condition if self._condition == self._do_if else self._terminate_return_condition),
        )
        try:
            condition_res = self._execute_callable(cast(Callable, self._condition))
        except SequenceError:
            return

        self._handle_return_value(condition_res, terminate_callback, terminate_callback)

    @p0_subject_slot("terminated")
    def _terminate_if_condition(self, res=None):
        # type: (Optional[Any]) -> None
        if_res = res
        if if_res is not None and self._terminate_if_condition.subject:
            if_res = self._terminate_if_condition.subject.res
        if self.debug:
            self.parent.log_info("%s condition returned %s" % (self, if_res))

        if if_res and self._do_if:
            self._execute()
        else:
            self.res = True  # Sequence is not an error
            self.terminate()

    @subject_slot("terminated")
    def _terminate_return_condition(self, res=None):
        # type: (Optional[Any]) -> None
        return_res = res
        if return_res is not None and self._terminate_return_condition.subject:
            return_res = self._terminate_return_condition.subject.res
        if self.debug:
            self.parent.log_info("%s condition returned %s" % (self, return_res))

        if return_res and self._return_if:
            self.early_returned = True
            self.terminate()
        else:
            self._execute()

    def _check_for_step_completion(self, res=None):
        # type: (Optional[Any]) -> None
        if not self._complete_on and not self._wait:
            return self.terminate()

        if not self._complete_on and self._wait:
            return self.parent._wait(self._wait, self.terminate)

        if _has_callback_queue(self._complete_on):
            self._add_callback_on_listener(cast(CallableWithCallbacks, self._complete_on))
            return

        try:
            check_res = self._execute_callable(cast(Callable, self._complete_on))
        except SequenceError:
            return  # handled

        if _has_callback_queue(check_res):  # allows async linking to a listener
            return self._add_callback_on_listener(cast(CallableWithCallbacks, check_res))

        if check_res:
            self.terminate()
        else:
            if self._check_count == self._check_timeout:
                return self._step_timed_out()
            self.parent._wait(pow(2, self._check_count), self._check_for_step_completion)
            self._check_count += 1

    def _add_callback_on_listener(self, listener):
        # type: (CallableWithCallbacks) -> None
        if not self._check_timeout:
            listener.add_callback(self.terminate)
        else:
            self._callback_timeout = TimeoutLimit(
                func=self.terminate,
                awaited_listener=listener,
                timeout_limit=self._check_timeout,
                on_timeout=self._step_timed_out,
            )
            listener.add_callback(self._callback_timeout)

    def _execute_callable(self, func):
        # type: (Callable) -> Any
        try:
            return func()
        except SequenceError:
            self.parent.log_notice("caught sequence error !!!!!")
            raise
        except Exception as e:
            self.error()
            self.parent.errorManager.handle_error(e, "%s : %s" % (self._sequence_name, self))
            raise SequenceError()  # will stop sequence processing

    def _handle_return_value(self, res, listener, success_callback):
        # type: (Any, CallableWithCallbacks, Callable[Any]) -> None
        from a_protocol_0.sequence.Sequence import Sequence

        if isinstance(res, Sequence):
            if res.errored:
                self.error()
            elif res.terminated:
                success_callback(res.res)
            else:
                listener.subject = res  # type: ignore[attr-defined]
                if not res.started:
                    res.start()
        else:
            success_callback(res)

    def _execute(self):
        # type: () -> None
        try:
            res = self._execute_callable(self._callable)
        except SequenceError:
            return

        self._handle_return_value(res, self._step_sequence_terminated_listener, self._check_for_step_completion)  # type: ignore[arg-type]

    def _step_timed_out(self):
        # type: () -> None
        if isinstance(self._complete_on, CallableWithCallbacks) and self._callback_timeout:
            self._complete_on.clear_callbacks()

        if self.debug:
            self.parent.log_error("timeout completion error on %s" % self, debug=False)

        self.error()

    @p0_subject_slot("terminated")
    def _step_sequence_terminated_listener(self):
        # type: () -> None
        self.res = self._step_sequence_terminated_listener.subject.res
        self._check_for_step_completion()
