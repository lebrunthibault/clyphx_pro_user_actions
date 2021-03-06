from typing import List, Optional, Any, Callable

from a_protocol_0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from a_protocol_0.interface.EncoderAction import EncoderAction
from a_protocol_0.interface.EncoderModifier import EncoderModifier
from a_protocol_0.interface.EncoderModifierEnum import EncoderModifierEnum
from a_protocol_0.interface.MultiEncoder import MultiEncoder
from a_protocol_0.interface.MultiEncoderModifier import MultiEncoderModifier


class AbstractActionGroup(AbstractControlSurfaceComponent):
    """
    An action group represents a group of 16 encoder available on my faderfox ec4
    It responds on a midi channel to cc messages
    See MultiEncoder to configure an encoder
    """

    def __init__(self, channel, filter_active_tracks=False, *a, **k):
        # type: (int, bool, Any, Any) -> None
        super(AbstractActionGroup, self).__init__(*a, **k)
        self.available_modifiers = [  # noqa
            EncoderModifier(type) for type in list(EncoderModifierEnum)
        ]  # type: List[EncoderModifier]
        self.channel = channel
        self.filter_active_tracks = filter_active_tracks
        self.multi_encoders = []  # type: List[MultiEncoder]

    def _add_multi_encoder(self, multi_encoder):
        # type: (MultiEncoder) -> MultiEncoder
        assert (
            len([encoder for encoder in self.multi_encoders if encoder.identifier == multi_encoder.identifier]) == 0
        ), ("duplicate multi encoder with id %s" % multi_encoder.identifier)
        self.multi_encoders.append(multi_encoder)
        return multi_encoder

    def add_encoder(self, id, name, filter_active_tracks=True, on_press=None, on_long_press=None, on_scroll=None):
        # type: (int, str, bool, Optional[Callable], Optional[Callable], Optional[Callable]) -> MultiEncoder
        encoder = MultiEncoder(group=self, identifier=id, name=name, filter_active_tracks=filter_active_tracks)
        for action in EncoderAction.make_actions(on_press=on_press, on_long_press=on_long_press, on_scroll=on_scroll):
            encoder.add_action(action)
        return self._add_multi_encoder(encoder)

    def add_modifier(self, id, modifier_type, on_scroll=None):
        # type: (int, EncoderModifierEnum, Optional[Callable]) -> MultiEncoder
        encoder = MultiEncoderModifier(group=self, identifier=id, modifier_type=modifier_type)
        if on_scroll:
            encoder.add_action(EncoderAction.make_actions(on_scroll=on_scroll)[0])
        return self._add_multi_encoder(encoder)
