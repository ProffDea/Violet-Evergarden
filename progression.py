import random
import datetime
from postgresql import database

# Status: Work in progress
# Add in a leveling system to reward users
# Add weekly deduction

class experience(object):
    def __init__(self, db):
        self.db = db

    def initialize(self, msg):
        self.db.cur.execute(f'''
            INSERT INTO users (user_id)
            VALUES
                ({msg.author.id})
            ON CONFLICT (user_id)
            DO NOTHING;

            INSERT INTO guild_users (
                guild_reference,
                user_reference
                )
            SELECT
                guilds.id,
                users.id
            FROM
                guilds
            INNER JOIN users
                ON users.user_id = '{msg.author.id}'
            WHERE
                guild = '{msg.guild.id}'
            ON CONFLICT (guild_reference, user_reference)
            DO NOTHING;
        ''')

    def message(self, msg):
        xp_gain = random.randint(10, 20)
        self.db.cur.execute(f'''
            SELECT
                now() - last_message
            FROM
                users
            WHERE user_id = '{msg.author.id}';
        ''')
        last_global_message = self.db.cur.fetchall()
        if last_global_message[0][0] == None or last_global_message[0][0] > datetime.timedelta(minutes=2):
            self.db.cur.execute(f'''
                UPDATE users
                SET
                    experience = experience + {xp_gain},
                    last_message = NOW()
                WHERE user_id = '{msg.author.id}';
            ''')
        self.db.cur.execute(f'''
            SELECT
                now() - guild_users.last_message
            FROM
                guild_users
            INNER JOIN guilds
                ON guilds.id = guild_users.guild_reference
            INNER JOIN users
                ON users.id = guild_users.user_reference
            WHERE guilds.guild = '{msg.guild.id}' AND
                users.user_id = '{msg.author.id}';
        ''')
        last_guild_message = self.db.cur.fetchall()
        if last_guild_message[0][0] == None or last_guild_message[0][0] > datetime.timedelta(minutes=2):
            self.db.cur.execute(f'''
                UPDATE guild_users
                SET
                    experience = guild_users.experience + {xp_gain},
                    last_message = NOW()
                FROM
                    guilds
                INNER JOIN users
                    ON users.user_id = '{msg.author.id}'
                WHERE guilds.guild = '{msg.guild.id}' AND
                    users.user_id = '{msg.author.id}';
            ''')

    def voice(self):
        pass