import os
from os.path import isfile, isdir

from typing import TYPE_CHECKING, List

from a_protocol_0.devices.presets.InstrumentPreset import InstrumentPreset
from a_protocol_0.lom.AbstractObject import AbstractObject

if TYPE_CHECKING:
    from a_protocol_0.devices.AbstractInstrument import AbstractInstrument


class InstrumentPresetList(AbstractObject):
    def __init__(self, instrument, *a, **k):
        # type: (AbstractInstrument, List[InstrumentPreset]) -> None
        super(InstrumentPresetList, self).__init__(*a, **k)
        self.instrument = instrument
        self.has_preset_names = False
        self.presets = []  # type: List[InstrumentPreset]
        self.selected_preset = None  # type: InstrumentPreset
        self.import_presets()

    def __repr__(self):
        repr = "preset count: %d\n" % len(self.presets)
        repr += "selected preset: %s" % self.selected_preset

        return repr

    def import_presets(self):
        self._import_presets()
        self.selected_preset = self._get_selected_preset()

    def _import_presets(self):
        self.presets = []
        presets_path = self.instrument.presets_path
        if not presets_path:
            self.presets = [InstrumentPreset(instrument=self.instrument, index=i) for i in range(0, self.instrument.NUMBER_OF_PRESETS)]
            self.has_preset_names = False
            return

        self.has_preset_names = True
        if isfile(presets_path):
            self.presets = [InstrumentPreset(instrument=self.instrument, index=i, name=name) for i, name in enumerate(open(presets_path).readlines())]
        elif isdir(presets_path):
            for root, sub_dirs, files in os.walk(presets_path):
                for file in [file for file in files if file.endswith(self.instrument.PRESET_EXTENSION)]:
                    self.presets.append(InstrumentPreset(instrument=self.instrument, index=len(self.presets), name=file))

    def _get_selected_preset(self):
        # type: () -> InstrumentPreset
        """ Checking first the device name (e.g. simpler) and then the track name """
        return self._find_by_name(self.instrument.name) or self.presets[self.instrument.track.selected_preset_index]

    def _find_by_name(self, name):
        # type: (str) -> None
        for preset in self.presets:
            if preset.name == name:
                return preset

        return None

    def scroll(self, go_next):
        # type: (bool) -> None
        new_preset_index = self.selected_preset.index + (1 if go_next else - 1)
        self.selected_preset = self.presets[new_preset_index % len(self.presets)]
