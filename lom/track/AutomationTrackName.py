import re
from typing import TYPE_CHECKING

import Live

from _Framework.SubjectSlot import subject_slot_group
from a_protocol_0.errors.Protocol0Error import Protocol0Error
from a_protocol_0.lom.track.TrackName import TrackName

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from a_protocol_0.lom.track.simple_track.AbstractAutomationTrack import AbstractAutomationTrack


class AutomationTrackName(TrackName):
    def __init__(self, track, *a, **k):
        # type: (AbstractAutomationTrack) -> None
        super(AutomationTrackName, self).__init__(track, *a, **k)
        self.automated_parameter_name = None
        self._name_listener(self.track)

    @subject_slot_group("name")
    def _name_listener(self, changed_track):
        # type: (Live.Track.Track) -> None
        match = re.match("^_(?P<automated_parameter_name>.*)$", self.track.name)

        if not match or not match.group("automated_parameter_name"):
            self.parent.log_dev(self.track.name)
            raise Protocol0Error("AbstractAutomationTrack is missing it's track name automated parameter")

        self.automated_parameter_name = match.group("automated_parameter_name").strip()

    def set_track_name(self, *a, **k):
        """ Not necessary for AbstractAutomationTrack """
        pass