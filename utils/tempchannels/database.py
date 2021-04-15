import aiosqlite

# noinspection SqlNoDataSourceInspection
from aiosqlite import Connection


class TempChannelDB:

    def __init__(self):
        self._db = None

    @property
    def db(self) -> Connection:
        return self._db

    def __setattr__(self, key, value):
        if key not in self.__dict__ \
                or (key in self.__dict__ and not self.__dict__[key]):
            self.__dict__[key] = value
        else:
            AttributeError("You may not mutate this instance")

    def __delattr__(self, item):
        AttributeError("You may not mutate this instance")

    async def make(self):
        if not self._db:
            self._db = await aiosqlite.connect('./data/temp_channels.py', timeout=10)

            await self._db.execute('''CREATE TABLE if NOT EXISTS TempChannels
                             (discordUser INTEGER NOT NULL,
                             textChannel INTEGER NOT NULL,
                             voiceChannel INTEGER NOT NULL,
                             token INTEGER NOT NULL,
                             CONSTRAINT singeUse UNIQUE (discordUser),
                             PRIMARY KEY (discordUser, token)
                             )''')

            await self._db.execute('''CREATE TABLE if NOT EXISTS Invites
                             (message_id INTEGER primary key,
                             token INTEGER NOT NULL,
                             member_id INTEGER,
                             channel_id INTEGER NOT NULL,
                             FOREIGN KEY (token) references TempChannels(token))''')
        return self
