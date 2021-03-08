import sqlite3


# noinspection SqlNoDataSourceInspection
class DB:
    conn = sqlite3.connect(':memory:')

    with conn:
        # Create table
        conn.execute('''CREATE TABLE if NOT EXISTS TempChannels
                     (discordUser INTEGER NOT NULL,
                     textChannel INTEGER NOT NULL,
                     voiceChannel INTEGER NOT NULL,
                     token INTEGER NOT NULL,
                     CONSTRAINT singeUse UNIQUE (discordUser),
                     PRIMARY KEY (discordUser, token)
                     )''')

    with conn:
        # Create table
        conn.execute('''CREATE TABLE if NOT EXISTS Invites
                     (message_id INTEGER primary key,
                     token INTEGER NOT NULL,
                     member_id INTEGER,
                     channel_id INTEGER NOT NULL,
                     FOREIGN KEY (token) references TempChannels(token))''')


if __name__ == '__main__':
    DB()
