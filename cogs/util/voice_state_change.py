from enum import IntEnum

from discord import VoiceState


class EventType(IntEnum):
    NOTHING = 0
    JOINED = 1
    LEFT = 2
    SWITCHED = 3

    @classmethod
    def status(cls, before: VoiceState, after: VoiceState):
        if before.channel is None and after.channel is not None:
            return cls.JOINED
        elif before.channel is not None and after.channel is None:
            return cls.LEFT
        elif after.channel == before.channel:
            return cls.NOTHING
        else:
            return cls.SWITCHED
