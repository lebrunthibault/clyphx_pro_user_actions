from a_protocol_0.instruments.AbstractInstrument import AbstractInstrument


class InstrumentNull(AbstractInstrument):
    def __init__(self, *a, **k):
        super(InstrumentNull, self).__init__(*a, **k)
        self.is_null = True
