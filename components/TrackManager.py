import itertools
from functools import partial

import Live
from typing import Optional, Callable, Any

from a_protocol_0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from a_protocol_0.devices.InstrumentMinitaur import InstrumentMinitaur
from a_protocol_0.errors.Protocol0Error import Protocol0Error
from a_protocol_0.lom.device.Device import Device
from a_protocol_0.lom.track.AbstractTrack import AbstractTrack
from a_protocol_0.lom.track.group_track.AbstractGroupTrack import AbstractGroupTrack
from a_protocol_0.lom.track.group_track.AutomatedTrack import AutomatedTrack
from a_protocol_0.lom.track.group_track.AutomationTracksCouple import AutomationTracksCouple
from a_protocol_0.lom.track.group_track.ExternalSynthTrack import ExternalSynthTrack
from a_protocol_0.lom.track.group_track.SimpleGroupTrack import SimpleGroupTrack
from a_protocol_0.lom.track.simple_track.AudioBusTrack import AudioBusTrack
from a_protocol_0.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
from a_protocol_0.lom.track.simple_track.SimpleMidiTrack import SimpleMidiTrack
from a_protocol_0.lom.track.simple_track.SimpleTrack import SimpleTrack
from a_protocol_0.sequence.Sequence import Sequence
from a_protocol_0.utils.decorators import p0_subject_slot, defer


class TrackManager(AbstractControlSurfaceComponent):
    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(TrackManager, self).__init__(*a, **k)
        self.tracks_added = False
        self.automation_track_color = None
        self._added_track_listener.subject = self.parent.songManager
        self._selected_track_listener.subject = self.parent.songManager

    @p0_subject_slot("added_track")
    @defer
    def _added_track_listener(self):
        # type: () -> Sequence
        self.song.begin_undo_step()  # Live crashes on undo without this
        seq = Sequence()
        seq.add(self.song.current_track._added_track_init)
        seq.add(self.song.end_undo_step)
        return seq.done()

    @p0_subject_slot("selected_track")
    def _selected_track_listener(self):
        # type: () -> None
        if not self.song.selected_track.is_recording:
            self.parent.defer(self._update_nav_view)

    def _update_nav_view(self):
        # type: () -> None
        if self.song.selected_track.nav_view == "clip":
            self.parent.clyphxNavigationManager.show_clip_view()
        elif self.song.selected_track.nav_view == "track":
            self.parent.clyphxNavigationManager.show_track_view()

    def group_track(self):
        # type: () -> Sequence
        seq = Sequence()
        seq.add(self.parent.clyphxNavigationManager.focus_main)
        seq.add(
            self.parent.keyboardShortcutManager.group_track,
            complete_on=self._added_track_listener,
            check_timeout=4,
        )
        return seq.done()

    def create_midi_track(self, index, name, device=None):
        # type: (int, str, Device) -> Sequence
        return self._create_track(
            track_creator=partial(self.song._song.create_midi_track, index), name=name, device=device
        )

    def create_audio_track(self, index, name, device=None):
        # type: (int, str, Device) -> Sequence
        return self._create_track(
            track_creator=partial(self.song._song.create_audio_track, index), name=name, device=device
        )

    def _create_track(self, track_creator, name, device):
        # type: (Callable, str, Optional[Device]) -> Sequence
        seq = Sequence().add(wait=1, silent=True)  # defer change
        seq.add(track_creator, complete_on=self.parent.songManager._tracks_listener)
        seq.add(
            lambda: self.song.selected_track.track_name.update(base_name=name),
            name="set track name to %s" % name,
        )
        if device:
            seq.add(lambda: self.song.selected_track.clear_devices(), name="clear devices")
            seq.add(
                partial(
                    self.parent.browserManager.load_any_device,
                    device_type=device.device_type,
                    device_name=device.name,
                ),
                silent=True,
            )

        return seq.done()

    def instantiate_simple_track(self, track, index):
        # type: (Live.Track.Track, int) -> SimpleTrack
        # checking first on existing tracks
        if track in self.parent.songManager.live_track_to_simple_track:
            simple_track = self.parent.songManager.live_track_to_simple_track[track]
            simple_track.map_clip_slots()
            return simple_track
        if index == self.song.AUDIO_BUS_TRACK_INDEX:
            return AudioBusTrack(track=track, index=index)
        elif track.has_midi_input:
            return SimpleMidiTrack(track=track, index=index)
        elif track.has_audio_input:
            return SimpleAudioTrack(track=track, index=index)

        assert False, "unknown track type %s" % track

    def instantiate_abstract_group_track(self, group_track):
        # type: (SimpleTrack) -> AbstractGroupTrack
        if not group_track.is_foldable:
            raise Protocol0Error("You passed a non group_track to instantiate_abstract_group_track : %s" % group_track)

        # calling factories by most specific first
        abstract_group_track = self.make_external_synth_track(group_track=group_track)
        if abstract_group_track:
            abstract_group_track = (
                self.make_automated_track(group_track=group_track, wrapped_track=abstract_group_track)
                or abstract_group_track
            )
        if not abstract_group_track:
            abstract_group_track = self.make_automated_track(group_track=group_track)
        if not abstract_group_track:
            abstract_group_track = SimpleGroupTrack(group_track=group_track)

        # this should be here because as abstract_group_track creation is conditional on sub_track state
        # we first check if the track could be created, then if it's the same type and return it if we have a match
        if group_track in self.parent.songManager.live_track_to_simple_track:
            previous_group_track = self.parent.songManager.live_track_to_simple_track[group_track]
            if type(abstract_group_track) is type(previous_group_track):
                abstract_group_track.disconnect()
                return previous_group_track

        return abstract_group_track

    def make_external_synth_track(self, group_track):
        # type: (SimpleTrack) -> Optional[ExternalSynthTrack]
        """ discarding automated tracks in creation / suppression """
        if len([sub_track for sub_track in group_track.sub_tracks if not self._is_automated_sub_track(sub_track)]) != 2:
            return None

        is_external_synth_track = False
        if any(sub_track.instrument and sub_track.instrument.IS_EXTERNAL_SYNTH for sub_track in group_track.sub_tracks):
            is_external_synth_track = True
        # minitaur is a special case as it doesn't have a vst
        elif group_track.track_name.base_name.lower() == InstrumentMinitaur.NAME:
            is_external_synth_track = True

        return ExternalSynthTrack(group_track=group_track) if is_external_synth_track else None

    def make_automated_track(self, group_track, wrapped_track=None):
        # type: (SimpleTrack, AbstractTrack) -> Optional[AutomatedTrack]
        automation_audio_tracks = [
            track for track in group_track.sub_tracks if self._is_automated_sub_track(track) and track.is_audio
        ]
        automation_midi_tracks = [
            track for track in group_track.sub_tracks if self._is_automated_sub_track(track) and track.is_midi
        ]

        if len(automation_audio_tracks) == 0 and len(automation_midi_tracks) == 0:
            return None
        main_tracks = [t for t in group_track.sub_tracks if t not in automation_audio_tracks + automation_midi_tracks]

        if wrapped_track is None:
            if len(main_tracks) != 1:
                return None
            wrapped_track = main_tracks[0]
            if wrapped_track != group_track.sub_tracks[-1]:
                raise Protocol0Error("The main track of a AutomatedTrack track should always be the last of the group")

        if len(automation_audio_tracks) != len(automation_midi_tracks):
            return None  # inconsistent state, happens on creation or when tracks are deleted

        # at this point we should have a consistent state with audio - midi * n and main track at this end
        # any other state is a bug and raises in AutomationTracksCouple __init__
        automation_tracks_couples = [
            AutomationTracksCouple(group_track, audio_track, midi_track)
            for audio_track, midi_track in itertools.izip(automation_audio_tracks, automation_midi_tracks)  # type: ignore[attr-defined]
        ]

        return AutomatedTrack(
            group_track=group_track,
            automation_tracks_couples=automation_tracks_couples,
            wrapped_track=wrapped_track,
        )

    def _is_automated_sub_track(self, track):
        # type: (SimpleTrack) -> bool
        if track.index in self.parent.automationTrackManager.created_tracks_indexes:
            return True
        return track.name.startswith("_")
