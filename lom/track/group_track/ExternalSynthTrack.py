import itertools

from typing import TYPE_CHECKING, Optional

from _Framework.Util import forward_property
from a_protocol_0.lom.ObjectSynchronizer import ObjectSynchronizer
from a_protocol_0.lom.clip_slot.ClipSlotSynchronizer import ClipSlotSynchronizer
from a_protocol_0.lom.track.group_track.AbstractGroupTrack import AbstractGroupTrack
from a_protocol_0.lom.track.group_track.ExternalSynthTrackActionMixin import ExternalSynthTrackActionMixin
from a_protocol_0.lom.track.simple_track.TrackSynchronizer import TrackSynchronizer
from a_protocol_0.utils.utils import find_last

if TYPE_CHECKING:
    from a_protocol_0.lom.track.simple_track.SimpleTrack import SimpleTrack


class ExternalSynthTrack(ExternalSynthTrackActionMixin, AbstractGroupTrack):
    def __init__(self, *a, **k):
        super(ExternalSynthTrack, self).__init__(*a, **k)
        self.midi_track = find_last(lambda t: t.is_midi, self.sub_tracks)  # type: SimpleTrack
        self.audio_track = find_last(lambda t: t.is_audio, self.sub_tracks)  # type: SimpleTrack
        self.instrument_track = self.midi_track
        self.midi_track.abstract_group_track = self.audio_track.abstract_group_track = self

        self.midi_track.is_scrollable = self.audio_track.is_scrollable = False

        self._instrument_listener.subject = self.instrument_track
        self._instrument_listener()

        with self.parent.component_guard():
            self._midi_audio_synchronizer = TrackSynchronizer(self.audio_track, self.midi_track)
            self._midi_track_synchronizer = ObjectSynchronizer(self.base_track, self.midi_track, "_track", ["solo"])

            self._clip_slot_synchronizers = [
                ClipSlotSynchronizer(midi_clip_slot, audio_clip_slot)
                for midi_clip_slot, audio_clip_slot in itertools.izip(
                    self.midi_track.clip_slots, self.audio_track.clip_slots
                )
            ]

        self.audio_track.set_output_routing_to(self.base_track)
        self.selection_tracks = [self.base_track, self.midi_track, self.audio_track]

    @property
    def solo(self):
        return any(track.solo for track in self.all_tracks)

    @solo.setter
    def solo(self, solo):
        if not solo:
            for track in self.all_tracks:
                track.solo = False
        else:
            self.midi_track.solo = self.audio._track.toggle_solo = True

    @property
    def can_be_armed(self):
        return True

    @property
    def is_armed(self):
        # type: () -> bool
        return self.midi_track.is_armed or self.audio_track.is_armed

    @property
    def is_playing(self):
        # type: () -> bool
        return self.midi_track.is_playing or self.audio_track.is_playing

    @property
    def is_recording(self):
        # type: () -> bool
        return self.midi_track.is_recording or self.audio_track.is_recording

    @property
    def next_empty_clip_slot_index(self):
        # type: () -> Optional[int]
        for i in range(self.song.selected_scene.index, len(self.song.scenes)):
            if not self.midi_track.clip_slots[i].has_clip and not self.audio_track.clip_slots[i].has_clip:
                return i
        return None

    @forward_property("audio_track")
    def set_output_routing_to(self):
        pass

    def disconnect(self):
        super(ExternalSynthTrack, self).disconnect()
        self._midi_track_synchronizer.disconnect()
        self._midi_audio_synchronizer.disconnect()
        for clip_slot_synchronizer in self._clip_slot_synchronizers:
            clip_slot_synchronizer.disconnect()
