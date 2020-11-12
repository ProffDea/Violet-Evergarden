import discord
import random
import asyncio
import time
import datetime
from datetime import datetime
from discord.ext import commands
from progression import initialize, message_gain, event_claim
from async_postgresql import async_database

class events(commands.Cog):

    # Status: Work in progress

    # So far manages server IDs when joining and leaving guilds
    # More needs to be added in here later
    # Events is where it can be easily abused and ratelimiting is required

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                INSERT INTO guilds (guild)
                VALUES
                        ('%s')
                ON CONFLICT (guild)
                DO NOTHING;

                INSERT INTO guild_settings (guild_reference)
                SELECT
                    id
                FROM
                    guilds
                ON CONFLICT (guild_reference)
                DO NOTHING;
                ''' %
                (guild.id,)
                )
        finally:
            await db.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                DELETE FROM
                    guilds
                WHERE
                    guild = '%s';
                ''' %
                (guild.id,)
                )
        finally:
            await db.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        db = async_database()
        await db.connect()
        try:
            welcome_channel = await db.con.fetch('''
                SELECT
                    welcome_channel
                FROM
                    guild_settings
                WHERE
                    guild_reference IN (
                        SELECT
                            id
                        FROM
                            guilds
                        WHERE
                            guild = '%s'
                    )
            ''' %
            (member.guild.id,)
            )
            if welcome_channel != []:
                welcome_channel = member.guild.get_channel(welcome_channel[0][0])
        finally:
            await db.close()

        # Epic seven guild invite for personal use
        if member.guild.id == 647205092029759488:
            for invite in self.bot.owner_invites:
                if invite.code == "vk68knV5wU":
                    for real_invite in await member.guild.invites():
                        if real_invite.code == "vk68knV5wU":
                            if real_invite.uses > invite.uses:
                                guild_member_verify = True
                                self.bot.owner_invites = await member.guild.invites()
                            else:
                                guild_member_verify = False
                    if guild_member_verify == True:
                        await member.add_roles(member.guild.get_role(771628610552725524), reason="Guild member")
                    else:
                        await member.add_roles(member.guild.get_role(647271471760015368), reason="Not a guild member")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                DELETE FROM
                    voice
                WHERE
                    channel = '%s';
                
                DELETE FROM
                    voice_roles
                WHERE
                    channel = '%s';

                DELETE FROM
                    muted_users
                WHERE
                    channel = '%s';
            ''' %
            (channel.id,
            channel.id,
            channel.id)
            )
        finally:
            await db.close()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                DELETE FROM
                    voice_roles
                WHERE
                    role = '%s';
            ''' %
            (role.id,)
            )
        finally:
            await db.close()

    # Update database for muted users | {before} and {after} are guild.channel
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        # Have event trigger on something else other than pure chance to prevent spam
        # Percent chance of event occuring
        chance = 5
        event_occurred = False
        roll = random.randint(1, 100)
        ctx = await self.bot.get_context(message)
        if roll <= chance and ctx.valid == False:
            event_occurred = True
            # Emoji to react to
            event_emoji = '💌'
            # Amount of participants allowed to participate in the event
            max_participants = 5
            # How long this event will last for in seconds
            event_length = 180

            try:
                await message.add_reaction(event_emoji)
            except:
                pass
            participants = {}
            event_start = time.time()
            loop = True
            def verify(reaction, member):
                return str(reaction.emoji) == event_emoji and reaction.message == message and member.bot == False and member not in participants

            while loop and len(participants) <= max_participants:
                time_passed = round(time.time() - event_start)
                try:
                    time_left = event_length - time_passed
                    await self.bot.wait_until_ready()
                    reaction, member = await self.bot.wait_for('reaction_add',
                                                    timeout=time_left,
                                                    check=verify)
                    # Amount of XP member will gain from event
                    xp_gain = random.randint(10, 25)

                    participants.update({member : xp_gain})
                    await message.remove_reaction(event_emoji, member)
                    await message.channel.send("%s | **%s** +%s xp" % (reaction.emoji, member.name, xp_gain), delete_after=10)
                except asyncio.TimeoutError:
                    loop = False
            try:
                await message.remove_reaction(event_emoji, self.bot.user)
            except:
                pass
        
        # Do anything that doesn't require the database above this line
        db = async_database()
        await db.connect()
        try:

            await initialize(db, message.author)
            await message_gain(db, message)

            if event_occurred == True and participants != {}:
                for member, xp in participants.items():
                    await event_claim(db, member, xp)
        finally:
            await db.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        # Do anything that doesn't require the database above this line
        db = async_database()
        await db.connect()
        try:

            await initialize(db, member)
            
            # Records how long user has been deafened for
            # Triggers on deafen
            if before.self_deaf != after.self_deaf and after.self_deaf == True:
                await db.con.execute('''
                    UPDATE
                        users
                    SET
                        last_deafen = NOW(),
                        deafen_amount = deafen_amount + 1
                    WHERE
                        user_id = '%s';

                    UPDATE
                        guild_users
                    SET
                        last_deafen = NOW(),
                        deafen_amount = deafen_amount + 1
                    WHERE
                        guild_reference IN (
                            SELECT
                                id
                            FROM
                                guilds
                            WHERE
                                guild = '%s'
                        ) AND
                        user_reference IN (
                            SELECT
                                id
                            FROM
                                users
                            WHERE
                                user_id = '%s'
                        );
                ''' %
                (member.id,
                member.guild.id,
                member.id)
                )

            # Triggers on undeafen
            elif before.self_deaf != after.self_deaf and after.self_deaf == False:
                global_last_deafen = await db.con.fetch('''
                    SELECT
                        last_voice,
                        last_deafen
                    FROM
                        users
                    WHERE
                        user_id = '%s';
                ''' %
                (member.id,)
                )
                if global_last_deafen != [] and global_last_deafen[0][1] is not None:
                    record = datetime.now() - global_last_deafen[0][1]
                    await db.con.execute('''
                        UPDATE
                            users
                        SET
                            last_deafen = null,
                            deafen_duration = deafen_duration + %s
                        WHERE
                            user_id = '%s'
                    ''' %
                    (record.seconds,
                    member.id)
                    )

                    if global_last_deafen[0][0] is None:
                        await db.con.execute('''
                            UPDATE
                                users
                            SET
                                last_voice = NOW(),
                                voice_duration = voice_duration + %s
                            WHERE
                                user_id = '%s'
                        ''' %
                        (record.seconds,
                        member.id)
                        )
                
                last_deafen = await db.con.fetch('''
                    SELECT
                        last_voice,
                        last_deafen
                    FROM
                        guild_users
                    WHERE
                        guild_reference IN (
                            SELECT
                                id
                            FROM
                                guilds
                            WHERE
                                guild = '%s'
                        ) AND
                        user_reference IN (
                            SELECT
                                id
                            FROM
                                users
                            WHERE
                                user_id = '%s'
                        );
                ''' %
                (member.guild.id,
                member.id)
                )
                if last_deafen != [] and last_deafen[0][1] is not None:
                    record = datetime.now() - last_deafen[0][1]
                    await db.con.execute('''
                        UPDATE
                            guild_users
                        SET
                            last_deafen = null,
                            deafen_duration = deafen_duration + %s
                        WHERE
                            guild_reference IN (
                                SELECT
                                    id
                                FROM
                                    guilds
                                WHERE
                                    guild = '%s'
                            ) AND
                            user_reference IN (
                                SELECT
                                    id
                                FROM
                                    users
                                WHERE
                                    user_id = '%s'
                            );
                    ''' %
                    (record.seconds,
                    member.guild.id,
                    member.id)
                    )

                    if last_deafen[0][0] is None:
                        await db.con.execute('''
                            UPDATE
                                guild_users
                            SET
                                last_voice = NOW(),
                                voice_duration = voice_duration + %s
                            WHERE
                                guild_reference IN (
                                    SELECT
                                        id
                                    FROM
                                        guilds
                                    WHERE
                                        guild = '%s'
                                ) AND
                                user_reference IN (
                                    SELECT
                                        id
                                    FROM
                                        users
                                    WHERE
                                        user_id = '%s'
                                );
                        ''' %
                        (record.seconds,
                        member.guild.id,
                        member.id)
                        )

            # Record last_deafen when joining a vc deafened | Record deafen_duration when disconnecting while deafened
            if before.self_deaf == True and after.self_deaf == True:

                # Hard join
                if before.channel is None:
                    await db.con.execute('''
                        UPDATE
                            users
                        SET
                            last_deafen = NOW()
                        WHERE
                            user_id = '%s';

                        UPDATE
                            guild_users
                        SET
                            last_deafen = NOW()
                        WHERE
                            guild_reference IN (
                                SELECT
                                    id
                                FROM
                                    guilds
                                WHERE
                                    guild = '%s'
                            ) AND
                            user_reference IN (
                                SELECT
                                    id
                                FROM
                                    users
                                WHERE
                                    user_id = '%s'
                            );
                    ''' %
                    (member.id,
                    member.guild.id,
                    member.id)
                    )

                # Hard disconnect
                elif after.channel is None:
                    global_last_deafen = await db.con.fetch('''
                        SELECT
                            last_deafen
                        FROM
                            users
                        WHERE
                            user_id = '%s'
                    ''' %
                    (member.id,)
                    )
                    if global_last_deafen != [] and global_last_deafen[0][0] is not None:
                        record = datetime.now() - global_last_deafen[0][0]
                        await db.con.execute('''
                            UPDATE
                                users
                            SET
                                last_deafen = null,
                                deafen_duration = deafen_duration + %s
                            WHERE
                                user_id = '%s';
                        ''' %
                        (record.seconds,
                        member.id)
                        )

                    last_deafen = await db.con.fetch('''
                        SELECT
                            last_deafen
                        FROM
                            guild_users
                        WHERE
                            guild_reference IN (
                                SELECT
                                    id
                                FROM
                                    guilds
                                WHERE
                                    guild = '%s'
                            ) AND
                            user_reference IN (
                                SELECT
                                    id
                                FROM
                                    users
                                WHERE
                                    user_id = '%s'
                            );
                    ''' %
                    (member.guild.id,
                    member.id)
                    )
                    if last_deafen != [] and last_deafen[0][0] is not None:
                        record = datetime.now() - last_deafen[0][0]
                        await db.con.execute('''
                            UPDATE
                                guild_users
                            SET
                                last_deafen = null,
                                deafen_duration = deafen_duration + %s
                            WHERE
                                guild_reference IN (
                                    SELECT
                                        id
                                    FROM
                                        guilds
                                    WHERE
                                        guild = '%s'
                                ) AND
                                user_reference IN (
                                    SELECT
                                        id
                                    FROM
                                        users
                                    WHERE
                                        user_id = '%s'
                                );
                        ''' %
                        (record.seconds,
                        member.guild.id,
                        member.id)
                        )

            # Do anything relating with voice updates above this line
            if before.deaf != after.deaf or before.mute != after.mute or before.self_mute != after.self_mute or before.self_deaf != after.self_deaf or before.self_stream != after.self_stream or before.self_video != after.self_video:
                return

            # Triggers when member moved between voice channels
            # Checks if user moved to keep voice role or not
            # Updates last_voice column for member
            if before.channel is not None and after.channel is not None:
                before_role = await db.con.fetch('''
                    SELECT
                        role
                    FROM
                        voice_roles
                    INNER JOIN guilds
                        ON guilds.id = voice_roles.guild_reference
                    WHERE
                        channel = '%s'
                ''' %
                (before.channel.id,)
                )
                after_role = await db.con.fetch('''
                    SELECT
                        role
                    FROM
                        voice_roles
                    INNER JOIN guilds
                        ON guilds.id = voice_roles.guild_reference
                    WHERE
                        channel = '%s'
                ''' %
                (after.channel.id,)
                )

                if before_role != [] and after_role == []:
                    role = before.channel.guild.get_role(before_role[0][0])
                    try:
                        await member.remove_roles(role, reason="Voice role for %s" % (before.channel.name,))
                    except:
                        pass

                elif before_role == [] and after_role != []:
                    role = after.channel.guild.get_role(after_role[0][0])
                    try:
                        await member.add_roles(role, reason="Voice role for %s" % (after.channel.name,))
                    except:
                        pass

                elif before_role == [] and after_role == []:
                    pass

                elif before_role[0][0] != after_role[0][0]:
                    old_role = before.channel.guild.get_role(before_role[0][0])
                    new_role = after.channel.guild.get_role(after_role[0][0])
                    try:
                        await member.remove_roles(old_role, reason="Voice role for %s" % (before.channel.name,))
                    except:
                        pass
                    try:
                        await member.add_roles(new_role, reason="Voice role for %s" % (after.channel.name,))
                    except:
                        pass

                await db.con.execute('''
                    UPDATE
                        users
                    SET
                        last_voice = NOW()
                    WHERE
                        user_id = '%s';

                    UPDATE
                        guild_users
                    SET
                        last_voice = NOW()
                    WHERE
                        guild_reference IN (
                            SELECT
                                id
                            FROM
                                guilds
                            WHERE
                                guild = '%s'
                        ) AND
                        user_reference IN (
                            SELECT
                                id
                            FROM
                                users
                            WHERE
                                user_id = '%s'
                        );
                ''' %
                (member.id,
                member.guild.id,
                member.id)
                )

            # Triggers when member joined a voice channel
            # Adds corresponding voice role
            # Updates last_voice column for member
            elif after.channel is not None:
                voice_role = await db.con.fetch('''
                    SELECT
                        role
                    FROM
                        voice_roles
                    INNER JOIN guilds
                        ON guilds.guild = '%s'
                    WHERE
                        guild_reference = guilds.id AND
                        channel = '%s';
                ''' %
                (after.channel.guild.id,
                after.channel.id)
                )
                if voice_role != [] and voice_role[0][0] is not None:
                    role = after.channel.guild.get_role(voice_role[0][0])
                    try:
                        await member.add_roles(role, reason="Voice role for %s" % (after.channel.name,))
                    except:
                        pass

                await db.con.execute('''
                    UPDATE
                        users
                    SET
                        last_voice = NOW()
                    WHERE
                        user_id = '%s';

                    UPDATE
                        guild_users
                    SET
                        last_voice = NOW()
                    WHERE
                        guild_reference IN (
                            SELECT
                                id
                            FROM
                                guilds
                            WHERE
                                guild = '%s'
                        ) AND
                        user_reference IN (
                            SELECT
                                id
                            FROM
                                users
                            WHERE
                                user_id = '%s'
                        );
                ''' %
                (member.id,
                member.guild.id,
                member.id)
                )

            # Triggers when member disconnected from a voice channel
            # Removes corresponding voice role
            # Updates last_voice and voice_duration column for member
            elif before.channel is not None:
                voice_role = await db.con.fetch('''
                    SELECT
                        role
                    FROM
                        voice_roles
                    INNER JOIN guilds
                        ON guilds.guild = '%s'
                    WHERE
                        guild_reference = guilds.id AND
                        channel = '%s';
                ''' %
                (before.channel.guild.id,
                before.channel.id)
                )
                if voice_role != [] and voice_role[0][0] is not None:
                    role = before.channel.guild.get_role(voice_role[0][0])
                    try:
                        await member.remove_roles(role, reason="Voice role for %s" % (before.channel.name,))
                    except:
                        pass

                global_last_voice = await db.con.fetch('''
                    SELECT
                        last_voice
                    FROM
                        users
                    WHERE
                        user_id = '%s';
                ''' %
                (member.id,)
                )
                if global_last_voice != [] and global_last_voice[0][0] is not None:
                    record = datetime.now() - global_last_voice[0][0]
                    await db.con.execute('''
                        UPDATE
                            users
                        SET
                            last_voice = null,
                            voice_duration = voice_duration + %s
                        WHERE
                            user_id = '%s';
                    ''' %
                    (record.seconds,
                    member.id)
                    )

                last_voice = await db.con.fetch('''
                    SELECT
                        last_voice
                    FROM
                        guild_users
                    WHERE
                        guild_reference IN (
                            SELECT
                                id
                            FROM
                                guilds
                            WHERE
                                guild = '%s'
                        ) AND
                        user_reference IN (
                            SELECT
                                id
                            FROM
                                users
                            WHERE
                                user_id = '%s'
                        );
                ''' %
                (member.guild.id,
                member.id)
                )
                if last_voice != [] and last_voice[0][0] is not None:
                    record = datetime.now() - last_voice[0][0]
                    await db.con.execute('''
                        UPDATE
                            guild_users
                        SET
                            last_voice = null,
                            voice_duration = voice_duration + %s
                        WHERE
                            guild_reference IN (
                                SELECT
                                    id
                                FROM
                                    guilds
                                WHERE
                                    guild = '%s'
                            ) AND
                            user_reference IN (
                                SELECT
                                    id
                                FROM
                                    users
                                WHERE
                                    user_id = '%s'
                            );
                    ''' %
                    (record.seconds,
                    member.guild.id,
                    member.id)
                    )

            dc_afk = await db.con.fetch('''
                SELECT
                    dc_afk
                FROM
                    guild_settings
                INNER JOIN guilds
                    ON guilds.guild = '%s'
                WHERE
                    guild_reference = guilds.id;
            ''' %
            (member.guild.id,)
            )
        finally:
            await db.close()
        # Do anything that requires the database but needs to sleep below this line

        # Disconnects AFK users
        if after.afk and after.channel is not None and dc_afk[0][0] == True and after.channel == member.guild.afk_channel:
            try:
                await asyncio.sleep(1)
                await member.move_to(None)
                return
            except:
                return

def setup(bot):
    bot.add_cog(events(bot))