import traceback

from a_protocol_0.lom.Song import Song
from a_protocol_0.utils.log import log


def print_except(func):
    def decorate(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            err = "ScriptError: " + str(e)
            args[0].log_message(traceback.format_exc())

    return decorate


def init_song(func):
    """ first decorator called (outer) """
    def decorate(self, *args, **kwargs):
        try:
            if func.__name__ != "create_actions":
                self._my_song = Song(self._song, self)
                self._my_song.current_action_name = self._my_song.current_action_name or func.__name__
            func(self, *args, **kwargs)
        except Exception as e:
            err = "ScriptError: " + str(e)
            self.canonical_parent.log_message(traceback.format_exc())
            self.canonical_parent.clyphx_pro_component.trigger_action_list('push msg "%s"' % err)

        # unarm previous tracks if necessary
        if func.__name__ != "create_actions":
            if self.unarm_other_tracks:
                if self.mySong().other_armed_group_track(self.current_track):
                    self.mySong().other_armed_group_track(self.current_track).action_unarm()
                for simple_track in self.mySong().simple_armed_tracks(self.current_track):
                    simple_track.action_unarm()
                self.unarm_other_tracks = False
            log(self.mySong().current_action_name)

    return decorate


def unarm_other_tracks(func):
    """ second decorator called (inner) """
    def decorate(self, *args, **kwargs):
        try:
            if func.__name__ != "create_actions":
                self.unarm_other_tracks = True
                self._my_song.current_action_name = func.__name__
            func(self, *args, **kwargs)
        except Exception as e:
            err = "ScriptError: " + str(e)
            self.canonical_parent.log_message(traceback.format_exc())
            self.canonical_parent.clyphx_pro_component.trigger_action_list('push msg "%s"' % err)

    return decorate


def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:  # there's probably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls

    return decorate