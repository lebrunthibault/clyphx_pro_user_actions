import collections
from functools import partial

import Live
from typing import Any, List

from a_protocol_0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from a_protocol_0.lom.Scene import Scene
from a_protocol_0.lom.track.simple_track.SimpleTrack import SimpleTrack
from a_protocol_0.utils.decorators import handle_error, p0_subject_slot


class SongManager(AbstractControlSurfaceComponent):
    __subject_events__ = ("selected_track", "added_track")

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(SongManager, self).__init__(*a, **k)
        self.tracks_listener.subject = self.song._song
        # keeping a list of instantiated tracks because we cannot access
        # song.live_track_to_simple_track when tracks are deleted
        self._simple_tracks = []  # type: List[SimpleTrack]

    def init_song(self):
        # type: () -> None
        self.on_scene_list_changed()
        self._highlighted_clip_slot = self.song.highlighted_clip_slot
        self._highlighted_clip_slot_poller()
        self.song.reset()

    @handle_error
    def on_scene_list_changed(self):
        # type: () -> None
        self.parent.sceneBeatScheduler.clear()
        self.tracks_listener()
        self.parent.setFixerManager.refresh_scenes_appearance()
        if self.song.playing_scene:
            self.song.playing_scene.schedule_next_scene_launch()

    @handle_error
    def on_selected_track_changed(self):
        # type: () -> None
        """ not for master and return tracks """
        if len(self.song.live_track_to_simple_track):
            # noinspection PyUnresolvedReferences
            self.notify_selected_track()

    @p0_subject_slot("tracks")
    @handle_error
    def tracks_listener(self):
        # type: () -> None
        self.parent.log_debug("SongManager : start mapping tracks")

        # Check if tracks were added
        previous_simple_track_count = len(list(self._simple_tracks))
        has_added_tracks = previous_simple_track_count and len(self.song._song.tracks) > previous_simple_track_count

        self._generate_simple_tracks()
        self._generate_abstract_group_tracks()
        self._generate_scenes()

        # Notify if added track(s)
        if has_added_tracks and self.song.selected_track:
            # noinspection PyUnresolvedReferences
            self.notify_added_track()

        self._simple_tracks = list(self.song.simple_tracks)
        self.parent.defer(partial(self.parent.setFixerManager.refresh_set_appearance, log=False))
        self.parent.log_debug("SongManager : mapped tracks")
        self.parent.log_debug()
        # noinspection PyUnresolvedReferences
        self.notify_selected_track()  # trigger other components

    def _generate_simple_tracks(self):
        # type: () -> None
        """ instantiate SimpleTracks (including return / master, that are marked as inactive) """
        self._simple_tracks[:] = []

        # instantiate set tracks
        for track in list(self.song._song.tracks) + list(self.song._song.return_tracks):
            self._generate_simple_track(track=track)

        self.song.master_track = self._generate_simple_track(track=self.song._song.master_track)

        # Refresh track mapping
        self.song.live_track_to_simple_track = collections.OrderedDict()
        for track in self._simple_tracks:
            self.song.live_track_to_simple_track[track._track] = track

        # Store clip_slots mapping. track and scene changes trigger a song remapping so it's fine
        self.song.clip_slots_by_live_live_clip_slot = {
            clip_slot._clip_slot: clip_slot for track in self.song.simple_tracks for clip_slot in track.clip_slots
        }

    def _generate_simple_track(self, track):
        # type: (Live.Track.Track) -> SimpleTrack
        simple_track = self.parent.trackManager.instantiate_simple_track(track=track)
        self.song.live_track_to_simple_track[track] = simple_track
        self._simple_tracks.append(simple_track)
        return simple_track

    def _generate_abstract_group_tracks(self):
        # type: () -> None
        # 2nd pass : instantiate AbstractGroupTracks
        for track in self.song.simple_tracks:
            if track.is_foldable:
                self.parent.trackManager.instantiate_abstract_group_track(track)

    def _generate_scenes(self):
        # type: () -> None
        live_scenes = self.song._song.scenes

        # disconnect removed scenes
        for scene in self.song.scenes:
            if scene._scene not in live_scenes:
                scene.disconnect()

        # create a dict access from live scenes
        scene_mapping = collections.OrderedDict()
        for scene in self.song.scenes:
            scene_mapping[scene._scene] = scene

        self.song.scenes[:] = []

        # get the right scene or instantiate new scenes
        for live_scene in live_scenes:
            if live_scene in scene_mapping:
                self.song.scenes.append(scene_mapping[live_scene])
            else:
                self.song.scenes.append(Scene(live_scene))

        if Scene.LOOPING_SCENE:
            Scene.LOOPING_SCENE.schedule_next_scene_launch()

    def _highlighted_clip_slot_poller(self):
        # type: () -> None
        if self.song.highlighted_clip_slot and self.song.highlighted_clip_slot != self._highlighted_clip_slot:
            self._highlighted_clip_slot = self.song.highlighted_clip_slot
            if self.song.highlighted_clip_slot.clip:
                self.parent.push2Manager.update_clip_grid_quantization()
                self._highlighted_clip_slot.clip._on_selected()
        self.parent.schedule_message(1, self._highlighted_clip_slot_poller)
