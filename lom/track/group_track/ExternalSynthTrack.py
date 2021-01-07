from typing import TYPE_CHECKING

from a_protocol_0.lom.ClipSlot import ClipSlot
from a_protocol_0.lom.track.group_track.AbstractGroupTrack import AbstractGroupTrack
from a_protocol_0.lom.track.group_track.ExternalSynthTrackActionMixin import ExternalSynthTrackActionMixin
from a_protocol_0.utils.utils import find_last

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from a_protocol_0.lom.track.simple_track.SimpleTrack import SimpleTrack


class ExternalSynthTrack(ExternalSynthTrackActionMixin, AbstractGroupTrack):
    def __init__(self, group_track, *a, **k):
        # type: (SimpleTrack) -> None
        super(ExternalSynthTrack, self).__init__(group_track=group_track, *a, **k)
        self.midi = find_last(lambda t: t.is_midi, self.sub_tracks)  # type: SimpleTrack
        self.audio = find_last(lambda t: t.is_audio, self.sub_tracks)  # type: SimpleTrack
        self.midi.is_scrollable = self.audio.is_scrollable = False

    @property
    def arm(self):
        # type: () -> bool
        return self.midi.arm and self.audio.arm

    @property
    def is_playing(self):
        # type: () -> bool
        return self.midi.is_playing or self.audio.is_playing

    @property
    def is_recording(self):
        # type: () -> bool
        return self.midi.is_recording or self.audio.is_recording

    @property
    def next_empty_clip_slot_index(self):
        # type: () -> ClipSlot
        for i in range(len(self.song.scenes)):
            if not self.midi.clip_slots[i].has_clip and not self.audio.clip_slots[i].has_clip:
                return i
        self.song.create_scene()
        return len(self.song.scenes) - 1