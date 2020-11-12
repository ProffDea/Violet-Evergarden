import random
import datetime

# Status: Work in progress
# Add in a leveling system to reward users
# Add weekly deduction

async def initialize(db, member):
    await db.con.execute('''
        INSERT INTO users (user_id)
        VALUES
            ('%s')
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
            ON users.user_id = '%s'
        WHERE
            guild = '%s'
        ON CONFLICT (guild_reference, user_reference)
        DO NOTHING;
    ''' %
    (member.id,
    member.id,
    member.guild.id)
    )

async def message_gain(db, msg):
    # Duration at which XP shall not be gained
    xp_cooldown = datetime.timedelta(minutes=2)

    xp_gain = random.randint(10, 25)
    last_global_message = await db.con.fetch('''
        SELECT
            now() - last_message
        FROM
            users
        WHERE user_id = '%s';
    ''' %
    (msg.author.id,)
    )
    if last_global_message[0][0] == None or last_global_message[0][0] > xp_cooldown:
        await db.con.execute('''
            UPDATE users
            SET
                experience = experience + %s,
                last_message = NOW()
            WHERE user_id = '%s';
        ''' %
        (xp_gain,
        msg.author.id)
        )

    last_guild_message = await db.con.fetch('''
        SELECT
            now() - guild_users.last_message
        FROM
            guild_users
        INNER JOIN guilds
            ON guilds.id = guild_users.guild_reference
        INNER JOIN users
            ON users.id = guild_users.user_reference
        WHERE guilds.guild = '%s' AND
            users.user_id = '%s';
    ''' %
    (msg.guild.id,
    msg.author.id)
    )
    if last_guild_message[0][0] == None or last_guild_message[0][0] > xp_cooldown:
        await db.con.execute('''
            UPDATE guild_users
            SET
                experience = guild_users.experience + %s,
                last_message = NOW()
            FROM
                guilds
            INNER JOIN users
                ON users.user_id = '%s'
            WHERE
                guilds.guild = '%s' AND
                guild_users.guild_reference = guilds.id AND
                guild_users.user_reference = users.id;
        ''' %
        (xp_gain,
        msg.author.id,
        msg.guild.id)
        )

async def event_claim(db, member, xp_gain):
    await db.con.execute('''
        INSERT INTO users (user_id)
        VALUES
            (%s)
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
            ON users.user_id = '%s'
        WHERE
            guild = '%s'
        ON CONFLICT (guild_reference, user_reference)
        DO NOTHING;

        UPDATE users
        SET
            experience = experience + %s
        WHERE user_id = '%s';

        UPDATE guild_users
        SET
            experience = guild_users.experience + %s
        FROM
            guilds
        INNER JOIN users
            ON users.user_id = '%s'
        WHERE
            guilds.guild = '%s' AND
            guild_users.guild_reference = guilds.id AND
            guild_users.user_reference = users.id;
    ''' %
    (member.id,
    member.id,
    member.guild.id,
    xp_gain,
    member.id,
    xp_gain,
    member.id,
    member.guild.id)
    )