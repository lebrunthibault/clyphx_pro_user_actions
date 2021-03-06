import Live
from typing import List, Any, Callable

from a_protocol_0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from a_protocol_0.lom.AbstractObject import AbstractObject
from a_protocol_0.utils.utils import get_callable_name


class SchedulerEvent(AbstractObject):
    def __init__(self, callback, tick_count, *a, **k):
        # type: (Callable, int, Any, Any) -> None
        super(SchedulerEvent, self).__init__(*a, **k)
        self._executed = False
        self._callback = callback
        self._tick_count = tick_count
        self._ticks_left = tick_count
        self.name = get_callable_name(self._callback)

    def __repr__(self):
        # type: () -> str
        return "%s (%d / %d)" % (self.name, self._ticks_left, self._tick_count)

    @property
    def is_timeout_elapsed(self):
        # type: () -> bool
        return self._ticks_left == 0

    def decrement_timeout(self):
        # type: () -> None
        assert self._ticks_left > 0
        self._ticks_left -= 1

    def execute(self):
        # type: () -> None
        assert not self._executed
        if self.song.errored:
            return
        self._executed = True
        try:
            self._callback()
        except Exception as e:
            self.parent.errorManager.handle_error(e)


class FastScheduler(AbstractControlSurfaceComponent):
    TICK_MS_DURATION = 17  # average 17 ms

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(FastScheduler, self).__init__(*a, **k)
        self._scheduler = Live.Base.Timer(callback=self._on_tick, interval=1, repeat=True)
        self._scheduler.start()
        self._scheduled_events = []  # type: List[SchedulerEvent]

    def stop(self):
        # type: () -> None
        self._scheduled_events = []
        self._scheduler.stop()

    def restart(self):
        # type: () -> None
        self.stop()
        self._scheduler.start()

    def _on_tick(self):
        # type: () -> None
        for scheduled_event in self._scheduled_events[:]:
            if scheduled_event.is_timeout_elapsed:
                self._execute_event(scheduled_event)
            else:
                scheduled_event.decrement_timeout()

    def _execute_event(self, scheduled_event):
        # type: (SchedulerEvent) -> None
        assert scheduled_event.is_timeout_elapsed
        scheduled_event.execute()
        try:
            self._scheduled_events.remove(scheduled_event)
        except ValueError:
            pass

    def schedule(self, tick_count, callback):
        # type: (int, Callable) -> None
        """ timeout_duration in ms """
        scheduled_event = SchedulerEvent(callback=callback, tick_count=tick_count)
        self._scheduled_events.append(scheduled_event)
        if scheduled_event.is_timeout_elapsed:
            self._execute_event(scheduled_event)

    def schedule_next(self, callback):
        # type: (Callable) -> None
        self.schedule(self.TICK_MS_DURATION, callback)
