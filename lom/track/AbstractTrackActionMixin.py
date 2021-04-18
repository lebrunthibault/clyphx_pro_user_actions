from functools import partial

import Live
from typing import TYPE_CHECKING, Callable, Any, Optional

from _Framework.Util import find_if
from a_protocol_0.errors.Protocol0Error import Protocol0Error
from a_protocol_0.lom.device.RackDevice import RackDevice
from a_protocol_0.sequence.Sequence import Sequence
from a_protocol_0.utils.decorators import retry

if TYPE_CHECKING:
    from a_protocol_0.lom.track.AbstractTrack import AbstractTrack


# noinspection PyTypeHints
class AbstractTrackActionMixin(object):
    def select(self):
        # type: (AbstractTrack) -> None
        return self.song.select_track(self)

    def toggle_arm(self):
        # type: (AbstractTrack) -> None
        return self.unarm() if self.is_armed else self.arm()

    def toggle_solo(self):
        self.solo = not self.solo

    def arm(self):
        # type: (AbstractTrack) -> Optional[Sequence]
        if self.is_armed:
            return
        self.base_track.collapse_devices()
        self.song.unfocus_all_tracks()
        return self.arm_track()

    def arm_track(self):
        # type: (AbstractTrack) -> None
        raise NotImplementedError()

    def unarm(self):
        # type: (AbstractTrack) -> None
        self.color = self.base_color
        [setattr(track, "is_armed", False) for track in self.all_tracks]
        [setattr(clip, "color", self.base_color) for clip in self.all_clips]
        self.unarm_track()

    def unarm_track(self):
        # type: (AbstractTrack) -> None
        pass

    def show_hide_instrument(self):
        # type: (AbstractTrack) -> None
        if not self.instrument:
            self.instrument_track.instrument = self.parent.deviceManager.make_instrument_from_simple_track(
                track=self.instrument_track
            )

        if not self.instrument or not self.instrument.can_be_shown:
            return
        self.parent.clyphxNavigationManager.show_track_view()
        self.is_folded = False
        self.instrument.show_hide()

    def scroll_presets_or_samples(self, go_next):
        # type: (AbstractTrack, bool) -> None
        if self.instrument:
            self.instrument.scroll_presets_or_samples(go_next)

    def scroll_preset_categories(self, go_next):
        # type: (AbstractTrack, bool) -> None
        if self.instrument:
            self.instrument.scroll_preset_categories(go_next=go_next)

    def switch_monitoring(self):
        # type: (AbstractTrack) -> None
        raise NotImplementedError()

    def record(self, record_func):
        # type: (AbstractTrack, Callable) -> Optional[Sequence]
        """ restart audio to get a count in and recfix"""
        if not self.can_be_armed:
            return
        if self.is_recording:
            return self.undo()
        if self.song._song.session_record_status != Live.Song.SessionRecordStatus.off:
            return
        self.song._song.session_automation_record = True

        self.song.stop_playing()

        if len(filter(None, [t.is_hearable for t in self.song.simple_tracks])) <= 1:
            self.song.metronome = True

        seq = Sequence()
        if not self.is_armed:
            seq.add(self.arm, silent=True)
        if self.next_empty_clip_slot_index is None:
            seq.add(self.song.create_scene)
            # here the tracks are mapped again ! we cannot simply call this method again on a stale object
            seq.add(self.parent.current_action.execute)
        else:
            seq.add(record_func)

        return seq.done()

    def _post_record(self, *a, **k):
        # type: (AbstractTrack, Any, Any) -> None
        " overridden "
        self.song.metronome = False
        self.has_monitor_in = False
        self.base_track.playable_clip.select()

    def record_all(self):
        # type: () -> Sequence
        """ this records normally on a simple track and both midi and audio on a group track """
        raise NotImplementedError

    def record_audio_only(self, *a, **k):
        # type: (AbstractTrack) -> Sequence
        """
        overridden
        this records normally on a simple track and only audio on a group track
        is is available on other tracks just for ease of use
        """
        return self.record_all()

    def play_stop(self):
        # type: (AbstractTrack) -> None
        return self.stop() if self.is_playing else self.play()

    def play(self):
        # type: (AbstractTrack) -> None
        from a_protocol_0.lom.track.simple_track.SimpleTrack import SimpleTrack

        if self.is_foldable:
            [sub_track.play() for sub_track in self.sub_tracks]
        elif isinstance(self, SimpleTrack) and self.playable_clip:
            self.playable_clip.is_playing = True
            self.playable_clip.start_marker = self.song.selected_scene.playing_position

    def stop(self, immediate=False):
        # type: (AbstractTrack, bool) -> None
        qz = self.song.clip_trigger_quantization
        if immediate:
            self.song.clip_trigger_quantization = 0
        self.base_track._track.stop_all_clips()
        if immediate:
            self.parent.defer(partial(setattr, self.song, "clip_trigger_quantization", qz))

    def undo(self):
        # type: (AbstractTrack) -> None
        self.parent.clear_tasks()
        self.undo_track()

    def undo_track(self):
        # type: (AbstractTrack) -> None
        raise NotImplementedError()

    def reset_track(self):
        # type: (AbstractTrack) -> None
        self.solo = False
        self.unarm()
        self.collapse_devices()

    def load_any_device(self, device_type, device_name):
        # type: (AbstractTrack, str, str) -> Sequence
        seq = Sequence()
        seq.add(self.select)
        seq.add(partial(self.parent.browserManager.load_any_device, device_type, device_name))
        return seq.done()

    def collapse_devices(self):
        # type: (AbstractTrack) -> None
        for device in self.all_devices:
            device.is_collapsed = not (
                isinstance(device, RackDevice) or self.parent.deviceManager.is_track_instrument(self, device)
            )

    @retry(3, 8)
    def set_output_routing_to(self, track):
        # type: (AbstractTrack, AbstractTrack) -> None
        if track is None:
            raise Protocol0Error("You passed None to %s" % self.set_output_routing_to.__name__)

        from a_protocol_0.lom.track.AbstractTrack import AbstractTrack

        track = track._track if isinstance(track, AbstractTrack) else track
        output_routing_type = find_if(lambda r: r.attached_object == track, self.available_output_routing_types)

        if not output_routing_type:
            output_routing_type = find_if(
                lambda r: r.display_name.lower() == track.name.lower(), self.available_output_routing_types
            )

        if not output_routing_type:
            raise Protocol0Error("Couldn't find the output routing type of the given track")

        if self.output_routing_type != output_routing_type:
            self.output_routing_type = output_routing_type

    def set_input_routing_type(self, track):
        # type: (AbstractTrack, Any) -> None
        from a_protocol_0.lom.track.AbstractTrack import AbstractTrack

        track = track._track if isinstance(track, AbstractTrack) else track

        if track is None:
            self.input_routing_type = self.available_input_routing_types[-1]  # No input
            return

        input_routing_type = find_if(lambda r: r.attached_object == track, self.available_input_routing_types)
        if not input_routing_type:
            input_routing_type = find_if(
                lambda r: r.display_name.lower() == track.name.lower(), self.available_input_routing_types
            )

        if not input_routing_type:
            raise Protocol0Error("Couldn't find the input routing type of the given track")

        if self.input_routing_type != input_routing_type:
            self.input_routing_type = input_routing_type
