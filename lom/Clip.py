class Clip:
    def __init__(self, clip, index):
        self.clip = clip
        self.index = index

    def __nonzero__(self):
        return self.index != 0

    def __eq__(self, other):
        if isinstance(other, Clip):
            return self.clip == other.clip
        return False

    @property
    def length(self):
        # type: () -> float
        """ For looped clips: loop length in beats """
        return self.clip.length

    @property
    def name(self):
        # type: () -> str
        return self.clip.name

    @property
    def color(self):
        # type: () -> int
        return self.clip.color

    @color.setter
    def color(self, color):
        # type: (int) -> None
        self.clip.color = color

    @property
    def is_playing(self):
        # type: () -> bool
        return self.clip.is_playing if self.index != 0 else False

    @is_playing.setter
    def is_playing(self, is_playing):
        # type: (bool) -> None
        if self.index != 0:
            self.clip.is_playing = is_playing

    @property
    def is_recording(self):
        # type: () -> bool
        return self.clip.is_recording

    @property
    def playing_position(self):
        # type: () -> float
        """
        For MIDI and warped audio clips the value is given in beats of absolute clip time. Zero beat time of the clip is where 1 is shown in the bar/beat/16th time scale at the top of the clip view.
        """
        return self.clip.playing_position
