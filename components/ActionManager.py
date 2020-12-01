from __future__ import with_statement

from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import *
from a_protocol_0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from a_protocol_0.consts import RECORDING_TIME_ONLY_AUDIO
from a_protocol_0.controls.MultiEncoder import MultiEncoder
from a_protocol_0.utils.decorators import button_action


class ActionManager(AbstractControlSurfaceComponent):
    def __init__(self, *a, **k):
        super(ActionManager, self).__init__(*a, **k)
        record_encoder = MultiEncoder(channel=15, identifier=9)
        record_encoder.on_scroll = self.scroll_recording_times
        record_encoder.on_press = self.record_ext

        track_encoder = MultiEncoder(channel=15, identifier=13)
        track_encoder.on_scroll = self.scroll_tracks
        track_encoder.on_press = self.arm_ext
        track_encoder.on_long_press = self.solo_ext

        device_encoder = MultiEncoder(channel=15, identifier=14)
        device_encoder.on_press = self.sel_ext
        device_encoder.on_scroll = self.scroll_presets

        self.switch_monitoring_ext.subject = ButtonElement(True, MIDI_NOTE_TYPE, channel=15, identifier=3)

        restart_encoder = MultiEncoder(channel=15, identifier=12)
        restart_encoder.on_press = self.restart_track
        restart_encoder.on_long_press = self.restart_set

        stop_encoder = MultiEncoder(channel=15, identifier=11)
        stop_encoder.on_press = self.stop_track
        stop_encoder.on_long_press = self.stop_set
        self.undo_ext.subject = ButtonElement(True, MIDI_NOTE_TYPE, channel=15, identifier=16)

    @button_action()
    def arm_ext(self):
        """ arm or unarm both midi and audio track """
        if self.current_track.is_simple_group:
            self.current_track.is_folded = not self.current_track.is_folded
            return

        if self.current_track.arm:
            self.current_track.action_unarm()
        else:
            self.song.unarm_other_tracks()
            self.current_track.action_arm()

    @button_action()
    def sel_ext(self):
        """ Sel instrument track to open ext editor """
        self.current_track.action_sel()

    @button_action(auto_arm=True)
    def solo_ext(self):
        self.current_track.action_solo()

    @button_action()
    def switch_monitoring_ext(self):
        self.current_track.action_switch_monitoring()

    @button_action(is_scrollable=True)
    def scroll_recording_times(self, go_next):
        """ record both midi and audio on group track """
        increment = 1 if go_next else - 1
        if self.current_track.recording_time is not None:
            index = self.current_track.recording_times.index(self.current_track.recording_time) + increment
        else:
            index = 0

        value = self.current_track.recording_times[index % (len(self.current_track.recording_times) - 1)]
        self.current_track.recording_time = value
        self.parent.show_message("Recording %s" % str(value))

    @button_action(auto_arm=True)
    def record_ext(self):
        """ record both midi and audio on group track """
        if self.current_track.recording_time == RECORDING_TIME_ONLY_AUDIO:
            return self.current_track.action_restart_and_record(self.current_track.action_record_audio_only, only_audio=True)
        else:
            self.current_track.bar_count = int(self.current_track.recording_time.split()[0])
            self.current_track.action_restart_and_record(self.current_track.action_record_all)

    @button_action()
    def restart_track(self):
        """" restart a live set from group tracks track names """
        self.current_track.restart()

    @button_action()
    def restart_set(self):
        """" restart a live set from group tracks track names """
        [track.restart() for track in self.song.tracks]

    @button_action()
    def stop_track(self):
        """" stop a live set from group tracks track names """
        self.current_track.stop()

    @button_action()
    def stop_set(self):
        """" stop a live set from group tracks track names """
        self.song.stop_all_clips()

    @button_action()
    def undo_ext(self):
        """" undo last recording """
        self.current_track.action_undo()

    @button_action(is_scrollable=True, log_action=False)
    def scroll_tracks(self, go_next):
        """ scroll top tracks """
        self.song.scroll_tracks(go_next)

    @button_action(is_scrollable=True, auto_arm=True)
    def scroll_presets(self, go_next):
        """ scroll track device presets or samples """
        self.current_track.instrument.action_scroll_presets_or_samples(go_next)