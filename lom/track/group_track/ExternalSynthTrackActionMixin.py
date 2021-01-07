from typing import TYPE_CHECKING

from a_protocol_0.lom.Colors import Colors

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from a_protocol_0.lom.track.group_track.ExternalSynthTrack import ExternalSynthTrack


# noinspection PyTypeHints
class ExternalSynthTrackActionMixin(object):
    def action_arm_track(self):
        # type: (ExternalSynthTrack) -> None
        self.color = Colors.ARM
        self.base_track.is_folded = False
        self.midi.action_arm_track()
        self.audio.action_arm_track()
        self.midi.has_monitor_in = False
        self.audio.has_monitor_in = True

    def action_unarm_track(self):
        # type: (ExternalSynthTrack) -> None
        self.midi.has_monitor_in = self.audio.has_monitor_in = False

    def action_switch_monitoring(self):
        # type: (ExternalSynthTrack) -> None
        if self.midi.has_monitor_in and self.audio.has_monitor_in:
            self.midi.has_monitor_in = self.audio.has_monitor_in = False
        elif self.audio.has_monitor_in:
            self.midi.has_monitor_in = True
        else:
            self.audio.has_monitor_in = True

    def action_record_all(self):
        # type: (ExternalSynthTrack) -> None
        self.midi.bar_count = self.audio.bar_count = self.bar_count
        self.midi.action_record_all(clip_slot_index=self.next_empty_clip_slot_index)
        self.audio.action_record_all(clip_slot_index=self.next_empty_clip_slot_index)

    def action_record_audio_only(self):
        # type: (ExternalSynthTrack) -> None
        if self.midi.is_playing:
            self.audio.bar_count = int(round((self.midi.playable_clip.length + 1) / 4))
        clip_slot_index = self.midi.playable_clip.index if not self.audio.clip_slots[self.midi.playable_clip.index].has_clip else None
        self.audio.action_record_all(clip_slot_index=clip_slot_index)

    def action_undo_track(self):
        # type: (ExternalSynthTrack) -> None
        [sub_track.action_undo_track() for sub_track in self.sub_tracks]