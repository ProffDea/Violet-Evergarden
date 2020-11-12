import discord
import time
import datetime
import asyncio
import textwrap
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from predicate import higher_power
from progression import initialize
from async_postgresql import async_database

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_time.start()
        self.vote_in_progress = False
        self.vote_user_cooldown = {}

    @commands.command(name='Prefix')
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def prefix(self, ctx, *, new_prefix=None):
        if not ctx.guild:
            await ctx.send("💌 | My prefix is `v.` or you can just @ me")
        else:
            db = async_database()
            await db.connect()
            try:
                if new_prefix == None:
                    server_prefix = await db.con.fetch('''
                        SELECT
                            prefix
                        FROM
                            guild_settings
                        INNER JOIN guilds
                            ON guilds.id = guild_settings.guild_reference
                        WHERE
                            guilds.guild = '%s';
                        ''' %
                        (ctx.guild.id,)
                        )
                    await ctx.send("💌 | **%s**'s Prefix: `%s`" % (ctx.guild.name, server_prefix[0][0]))
                elif ctx.channel.permissions_for(ctx.author).manage_guild == True and new_prefix != None and len(new_prefix) < 10:
                    await db.con.execute('''
                        UPDATE
                            guild_settings
                        SET
                            prefix = '%s'
                        FROM
                            guilds
                        WHERE
                            guilds.guild = '%s' AND
                            guild_settings.guild_reference = guilds.id;
                        ''' %
                        (new_prefix,
                        ctx.guild.id)
                        )
                    await ctx.message.add_reaction('✅')
                else:
                    await ctx.message.add_reaction('❌')
            finally:
                await db.close()

    @commands.command(name='Avatar', aliases=['PFP', 'Picture'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def avatar(self, ctx, *, member: discord.Member=None):
        if member == None:
            member = ctx.author
        eb = discord.Embed(
            title = '%s' % (member,),
            description = '[Link](%s)' % (member.avatar_url,),
            color = discord.Color.purple()
        )
        eb.set_image(url=member.avatar_url)
        eb.set_footer(text='💌')
        await ctx.send(embed=eb)

    @commands.command(name='Ping', aliases=['Latency'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def ping(self, ctx):
        await ctx.send('💌 | Latency: **%s**ms' % (round(self.bot.latency * 1000),))

    @commands.command(name='Uptime')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def uptime(self, ctx):
        uptime = datetime.now() - self.bot.startup_time
        await ctx.send("💌 | **%s**'s Uptime: `%s`" % (self.bot.user.name, timedelta(seconds=uptime.seconds)))
    
    @commands.command(name='Level', aliases=['Experience', 'XP'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def level(self, ctx, *, member: discord.Member = None):
        if member == None:
            member = ctx.author
        if member.bot == True:
            return await ctx.send("💌 | Bots don't have XP")
        db = async_database()
        await db.connect()
        try:
            global_xp = await db.con.fetch('''
                SELECT
                    experience
                FROM
                    users
                WHERE user_id = '%s';
            ''' %
            (member.id,)
            )
            guild_xp = await db.con.fetch('''
                SELECT
                    guild_users.experience
                FROM
                    guild_users
                INNER JOIN guilds
                    ON guilds.id = guild_users.guild_reference
                INNER JOIN users
                    ON users.id = guild_users.user_reference
                WHERE guilds.guild = '%s' AND
                    users.user_id = '%s';
            ''' %
            (ctx.guild.id,
            member.id)
            )
            if global_xp == []:
                global_xp = [(0,)]
            if guild_xp == []:
                guild_xp = [(0,)]
        finally:
            try:
                embed = discord.Embed(
                    title="%s's Experience Card" % (member.name,),
                    description="```json\nGlobal Experience: %s\nServer Experience: %s\n```" % (global_xp[0][0], guild_xp[0][0]),
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.avatar_url)
                await ctx.send(embed=embed)
            except:
                pass
            await db.close()

    @commands.command(name='Voice_Role', aliases=['VR'])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def vr(self, ctx, role: discord.Role = None, *, channel: discord.VoiceChannel = None):
        if role == None:
            db = async_database()
            await db.connect()
            try:
                voice_roles = await db.con.fetch('''
                    SELECT
                        channel,
                        role
                    FROM
                        voice_roles
                    INNER JOIN guilds
                        ON guilds.id = voice_roles.guild_reference
                    WHERE
                        guilds.guild = '%s';
                ''' %
                (ctx.guild.id,)
                )
                pair = "Run the command with a valid role while in a voice channel to assign a voice role\nThis is all the voice roles assigned in this server from channel to role names\n\n"
                if voice_roles != []:
                    for group in voice_roles:
                        channel = self.bot.get_channel(group[0])
                        role = ctx.guild.get_role(group[1])
                        pair += "**%s** : `%s`\n" % (role.name, channel.name)
                else:
                    pair += "**None**"
                await ctx.send(pair)
            finally:
                await db.close()
            return

        if channel is None and ctx.author.voice is None:
            await ctx.send("A valid voice channel is required")
            return
        if channel is None:
            channel = ctx.author.voice.channel

        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                INSERT INTO voice_roles (
                    guild_reference,
                    channel,
                    role
                )
                SELECT
                    guilds.id,
                    '%s',
                    '%s'
                FROM
                    guilds
                WHERE
                    guilds.guild = '%s'
                ON CONFLICT (channel)
                DO
                    UPDATE
                    SET
                        role = '%s';
            ''' %
            (channel.id,
            role.id,
            ctx.guild.id,
            role.id)
            )
            await ctx.message.add_reaction('✅')
        finally:
            await db.close()

    @commands.command(name='Remove_Voice_Role', aliases=['RVR'])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def rvr(self, ctx, *, channel: discord.VoiceChannel = None):
        if channel == None:
            await ctx.send("Please select a valid channel")
            return

        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                DELETE FROM
                    voice_roles
                USING guilds
                WHERE
                    guilds.guild = '%s' AND
                    channel = '%s';
            ''' %
            (ctx.guild.id,
            channel.id)
            )
            await ctx.message.add_reaction('✅')
        finally:
            await db.close()

    # Can not mute bots due to user_reference being null as bots are not stored in users
    @commands.command(name='Mute')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def mute(self, ctx, *, member: discord.Member):
        if ctx.channel.overwrites_for(member).send_messages == False:
            return await ctx.send("**%s** is already muted in %s!" % (member.name, ctx.channel.mention))

        if ctx.author != ctx.guild.owner and higher_power(ctx.author, member) == False and member != ctx.author:
            return await ctx.send("💌 | Can not mute member that has a higher role than you")

        if member == ctx.author or ctx.author != ctx.guild.owner:
            return await ctx.send("💌 | Can not mute yourself")
        
        if member.bot:
            return await ctx.send("💌 | Can not mute bots")
            
        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                INSERT INTO muted_users (
                    user_reference,
                    guild_reference,
                    channel,
                    mute_duration
                )
                VALUES (
                    (SELECT
                        id
                    FROM
                        users
                    WHERE
                        user_id = '%s'),
                    (SELECT
                        id
                    FROM
                        guilds
                    WHERE
                        guild = '%s'),
                    '%s',
                    NOW()
                )
                ON CONFLICT (user_reference, guild_reference, channel)
                DO NOTHING;
            ''' %
            (member.id,
            member.guild.id,
            ctx.channel.id)
            )

            await ctx.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages=False))
            await ctx.send("**%s** has been muted in %s" % (member.name, ctx.channel.mention))
        finally:
            await db.close()

    @commands.command(name='Unmute')
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def unmute(self, ctx, *, member: discord.Member):
        if ctx.channel.overwrites_for(member).send_messages != False:
            return await ctx.send("**%s** is not muted in %s!" % (member.name, ctx.channel.mention))

        if ctx.author != ctx.guild.owner and higher_power(ctx.author, member) == False and member != ctx.author:
            return await ctx.send("💌 | Can not unmute member that has a higher role than you")

        if member == ctx.author or ctx.author != ctx.guild.owner:
            return await ctx.send("💌 | Can not unmute yourself")

        db = async_database()
        await db.connect()
        try:
            await db.con.execute('''
                DELETE FROM
                    muted_users
                WHERE
                    user_reference IN (
                        SELECT
                            id
                        FROM
                            users
                        WHERE
                            user_id = '%s'
                    ) AND
                    guild_reference IN (
                        SELECT
                            id
                        FROM
                            guilds
                        WHERE
                            guild = '%s'
                    ) AND
                    channel = '%s';
            ''' %
            (member.id,
            member.guild.id,
            ctx.channel.id)
            )

            await ctx.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages=None))
            await ctx.send("**%s** has been unmuted in %s" % (member.name, ctx.channel.mention))
        finally:
            await db.close()

    @commands.command(name='DisconnectAFK', aliases=['DCAFK'])
    @commands.has_permissions(manage_guild=True)
    async def disconnect_afk(self, ctx):
        db = async_database()
        await db.connect()
        try:
            dc_afk = await db.con.fetch('''
                SELECT
                    dc_afk
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
                    );
            ''' %
            (ctx.guild.id,)
            )

            if dc_afk[0][0] == True:
                await ctx.send(f"💌 | Members will stay in the AFK channel and no longer disconnect")
                toggle = False

            elif dc_afk[0][0] == False:
                await ctx.send(f"💌 | Members will no longer stay in the AFK channel and will be disconnected")
                toggle = True

            await db.con.execute('''
                UPDATE guild_settings
                SET
                    dc_afk = '%s'
                WHERE
                    guild_reference IN (
                        SELECT
                            id
                        FROM
                            guilds
                        WHERE
                            guild = '%s'
                    );
            ''' %
            (toggle,
            ctx.guild.id)
            )
        finally:
            await db.close()

    @commands.command(name='Voice_Stats', aliases=['VS'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def voice_stats(self, ctx, *, member: discord.Member = None):
        if member == None:
            member = ctx.author
        
        db = async_database()
        await db.connect()
        try:
            await initialize(db, member)

            global_user = await db.con.fetch('''
                SELECT
                    voice_duration,
                    deafen_duration,
                    deafen_amount
                FROM
                    users
                WHERE
                    user_id = '%s'
            ''' %
            (member.id,)
            )

            guild_user = await db.con.fetch('''
                SELECT
                    last_voice,
                    last_deafen,
                    voice_duration,
                    deafen_duration,
                    deafen_amount
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
            (ctx.guild.id,
            member.id)
            )

            if member.voice is not None and guild_user[0][0] is not None:
                guild_last_voice = datetime.now() - guild_user[0][0]
                guild_last_deafen = datetime.now() - guild_user[0][1] if member.voice.self_deaf == True else timedelta(seconds=0)
            else:
                guild_last_voice = timedelta(seconds=0)
                guild_last_deafen = timedelta(seconds=0)

            # All global stats
            global_voice_duration = timedelta(seconds=global_user[0][0] + guild_last_voice.seconds)
            global_deafen_duration = timedelta(seconds=global_user[0][1] + guild_last_deafen.seconds)
            global_percentage = 'N/A' if global_user[0][0] + guild_last_voice.seconds == 0 else "{:.0%}".format((global_user[0][1] + guild_last_deafen.seconds)/(global_user[0][0] + guild_last_voice.seconds))
            global_deafen_amount = global_user[0][2]

            fit = 16 - len(str(global_voice_duration))
            global_voice_dash = ''
            counter = 0
            while counter < fit:
                global_voice_dash += '.'
                counter = counter + 1

            fit = 15 - len(str(global_deafen_duration))
            global_deafen_dash = ''
            counter = 0
            while counter < fit:
                global_deafen_dash += '.'
                counter = counter + 1

            # All guild stats
            guild_voice_duration = timedelta(seconds=guild_user[0][2] + guild_last_voice.seconds)
            guild_deafen_duration = timedelta(seconds=guild_user[0][3] + guild_last_deafen.seconds)
            guild_percentage = 'N/A' if guild_user[0][2] + guild_last_voice.seconds == 0 else "{:.0%}".format((guild_user[0][3] + guild_last_deafen.seconds)/(guild_user[0][2] + guild_last_voice.seconds))
            guild_deafen_amount = guild_user[0][4]
            
            fit = 16 - len(str(guild_voice_duration))
            guild_voice_dash = ''
            counter = 0
            while counter < fit:
                guild_voice_dash += '.'
                counter = counter + 1

            fit = 15 - len(str(guild_deafen_duration))
            guild_deafen_dash = ''
            counter = 0
            while counter < fit:
                guild_deafen_dash += '.'
                counter = counter + 1

            embed = discord.Embed(
                title = "%s's Voice Statistics" % (member.name,),
                description = '',
                color = discord.Color.blue()
            )
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name="Global",
                            value=textwrap.dedent('''
                            ```json
                            Voice %s %s
                            Deafen %s %s
                            Percentage .... %s
                            Deafen Sessions %s
                            ```
                            ''') % (global_voice_dash,
                                    global_voice_duration,
                                    global_deafen_dash,
                                    global_deafen_duration,
                                    global_percentage,
                                    global_deafen_amount),
                            inline=False)
            embed.add_field(name=ctx.guild.name,
                            value=textwrap.dedent('''
                            ```json
                            Voice %s %s
                            Deafen %s %s
                            Percentage .... %s
                            Deafen Sessions %s
                            ```
                            ''') % (guild_voice_dash,
                                    guild_voice_duration,
                                    guild_deafen_dash,
                                    guild_deafen_duration,
                                    guild_percentage,
                                    guild_deafen_amount),
                            inline=False)

            await ctx.send(embed=embed)
        finally:
            await db.close()

    @commands.command(name='Voice_Leaderboard', aliases=['VL'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def voice_leaderboard(self, ctx):
        db = async_database()
        await db.connect()
        try:
            voice_durations = await db.con.fetch('''
                SELECT
                    user_id,
                    guild_users.last_voice,
                    guild_users.voice_duration
                FROM
                    guild_users
                INNER JOIN users
                    ON users.id = guild_users.user_reference
                WHERE
                    guild_reference IN (
                        SELECT
                            id
                        FROM
                            guilds
                        WHERE
                            guild = '%s'
                    )
                ORDER BY
                    guild_users.voice_duration DESC;
            ''' %
            (ctx.guild.id,)
            )

            deafen_durations = await db.con.fetch('''
                SELECT
                    user_id,
                    guild_users.last_deafen,
                    guild_users.deafen_duration
                FROM
                    guild_users
                INNER JOIN users
                    ON users.id = guild_users.user_reference
                WHERE
                    guild_reference IN (
                        SELECT
                            id
                        FROM
                            guilds
                        WHERE
                            guild = '%s'
                    )
                ORDER BY
                    guild_users.deafen_duration DESC;
            ''' %
            (ctx.guild.id,)
            )
            voice_scoreboard = ''
            deafen_scoreboard = ''
            counter = 0
            for user in voice_durations:
                if counter >= 10:
                    break

                member = ctx.guild.get_member(user[0])
                if member == None:
                    continue
                name = "%s-" % (member.name[slice(10)]) if len(member.name) > 10 else member.name
                guild_last_voice = datetime.now() - user[1] if member.voice is not None and user[1] is not None else timedelta(seconds=0)
                duration = timedelta(seconds=user[2] + guild_last_voice.seconds)
                if duration != timedelta(seconds=0):
                    fit = 26 - len(name) - len(str(duration))
                    dash = ''
                    dash_counter = 0
                    while dash_counter < fit:
                        dash += '.'
                        dash_counter = dash_counter + 1
                    voice_scoreboard += "%s %s %s\n" % (name, dash, duration)
                    counter = counter + 1

            counter = 0
            for user in deafen_durations:
                if counter >= 10:
                    break

                member = ctx.guild.get_member(user[0])
                if member == None:
                    continue
                name = "%s-" % (member.name[slice(10)]) if len(member.name) > 10 else member.name
                guild_last_deafen = datetime.now() - user[1] if member.voice is not None and user[1] is not None else timedelta(seconds=0)
                duration = timedelta(seconds=user[2] + guild_last_deafen.seconds)
                if duration != timedelta(seconds=0):
                    fit = 26 - len(name) - len(str(duration))
                    dash = ''
                    dash_counter = 0
                    while dash_counter < fit:
                        dash += '.'
                        dash_counter = dash_counter + 1
                    deafen_scoreboard += "%s %s %s\n" % (name, dash, duration)
                    counter = counter + 1


            embed = discord.Embed(
                title="%s's Voice Leaderboard" % (ctx.guild.name,),
                description='',
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name='Top 10 Users in Voice Channels the Longest',
                            value="```json\n%s\n```" % (voice_scoreboard),
                            inline=False)
            embed.add_field(name='Top 10 Users Deafened the Longest',
                            value="```json\n%s\n```" % (deafen_scoreboard),
                            inline=False)
            await ctx.send(embed=embed)
        finally:
            await db.close()

    # A personal command with the potential to become a feature
    @commands.command(name='Vote_Kick', aliases=['VK'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def vote_kick(self, ctx, member: discord.Member = None, *, frame='1h'):
        if member == None:
            return await ctx.send("💌 | Please give a valid member")
        await ctx.message.delete()
        if self.vote_in_progress == True:
            return await ctx.send("💌 | A vote is currently in progress!", delete_after=15)
        if ctx.author.voice.channel.permissions_for(member).speak == False:
            return await ctx.send("💌 | That member is already muted in the channel!", delete_after=15)
        if ctx.author.voice == None:
            return await ctx.send("💌 | Command can only be ran while in a voice channel", delete_after=15)
        for user, date in self.vote_user_cooldown.items():
            if ctx.author.id == user:
                cooldown = datetime.now() - date
                if cooldown <= timedelta(minutes=5):
                    round_date = timedelta(minutes=5) - cooldown
                    return await ctx.send("💌 | You can vote again in **`%s`** minutes" % (round_date.seconds//60,))
                else:
                    del self.vote_user_cooldown[ctx.author.id]
        if member == None or member.bot == True or member == ctx.author:
            return await ctx.send("""💌 | Please enter a valid member\nExample:\n`t.vk "ProfDea" 3h`""", delete_after=15)
        valid_users = []
        for user in ctx.author.voice.channel.members:
            if user.bot == False:
                valid_users += [user]
        if len(valid_users) <= 2:
            return await ctx.send("💌 | Voting requires more than 2 members in the voice channel.", delete_after=15)

        try:
            number, hour = frame
        except:
            number = False
            hour = False
        if len(frame) > 2 or number.isdigit() == False or int(number) <= 0 or int(number) >= 6 or hour.lower() != 'h':
            return await ctx.send("""💌 | Invalid time frame. Valid time frames are 1-5 hours and/or 1-60 minutes\nExample:\n`t.vk "Violet Evergarden" 3h 24m`""", delete_after=15)

        self.vote_in_progress = True
        self.vote_user_cooldown.update({ctx.author.id : datetime.now()})
        await ctx.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=False))

        async def register(self, ctx, member):
            deadline = 60

            embed = discord.Embed(
                title='Register to Vote',
                description='You have 1 minute to react to the emoji below to register for the upcoming vote, then the vote will begin.',
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.avatar_url)

            notification = ''
            for user in ctx.author.voice.channel.members:
                if user != member and user.bot == False:
                    notification += "%s " % (user.mention)
            event = await ctx.send("%s\n" % (notification,), embed=embed)
            await event.add_reaction('📩')
            await asyncio.sleep(deadline)
            update = await ctx.channel.fetch_message(event.id)
            reaction = update.reactions
            voters = await reaction[0].users().flatten()
            await event.delete()
            return voters

        registered = await register(self, ctx, member)
        registered = [user for user in registered if user in ctx.author.voice.channel.members and user.bot == False and user.id != member.id]
        if len(registered) < 2:
            self.vote_in_progress = False
            return await ctx.send("💌 | Not enough members registered to make a fair vote")

        yes = 0
        no = 0
        log = []

        status = "Vote in Progress!"
        embed = discord.Embed(
            title=status,
            description='If vote succeeds, **%s** will be disconnected and muted for **`%s`** hours.\nAll votes will be anonymous.' % (member.name, number),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="%s votes in!" % (yes + no), value='```json\n%s for ✅\n%s for ❌\n```' % (yes, no), inline=False)

        notification = ''
        for user in registered:
            if user != member and user.bot == False:
                notification += "%s " % (user.mention)
        event = await ctx.send("%s\n" % (notification,), embed=embed)
        await event.add_reaction('✅')
        await event.add_reaction('❌')

        def verify(reaction, user):
            return user.bot == False and user in registered and reaction.emoji in ['✅', '❌'] and reaction.message.id == event.id

        event_start = time.time()
        loop = True
        while loop:
            time_passed = round(time.time() - event_start)
            try:
                time_left = 300 - time_passed
                reaction, user = await self.bot.wait_for('reaction_add', timeout=time_left, check=verify)
                if user in log:
                    await event.remove_reaction(reaction.emoji, user)
                else:
                    log += [user]
                    if reaction.emoji == '✅':
                        yes = yes + 1
                    if reaction.emoji == '❌':
                        no = no + 1
                    await event.remove_reaction(reaction.emoji, user)
                    if yes/len(registered) >= 2/3:
                        loop = False
                        kick = True
                        status = "Vote has passed!"
                        effect = "%s can no longer speak in the voice channel for %s hour(s)!" % (member.name, number)
                    elif no/len(registered) >= 1/3:
                        loop = False
                        kick = False
                        status = "Vote has failed!"
                        effect = "%s will not be muted." % (member.name,)
                    else:
                        update = discord.Embed(
                            title=status,
                            description='If vote succeeds, **%s** will be disconnected and muted for **`%s`** hours.\nAll votes will be anonymous.' % (member.name, number),
                            color=discord.Color.blue()
                        )
                        update.set_thumbnail(url=member.avatar_url)
                        update.add_field(name="%s votes in!" % (yes + no), value='```json\n%s for ✅\n%s for ❌\n```' % (yes, no), inline=False)
                        await event.edit(content="%s\n" % (notification,), embed=update)
            except asyncio.TimeoutError:
                loop = False
                kick = False
                status = "Vote has failed!"
                effect = "%s will not be muted." % (member.name,)
        
        await event.delete()
        conclusion = await ctx.send(
            textwrap.dedent('''
                ```json
                %s

                %s
                Total Votes:  %s
                Votes for ✅: %s
                Votes for ❌: %s
                ```
            ''' %
            (status,
            effect,
            yes + no,
            yes,
            no)))

        if kick == True:
            if member in ctx.author.voice.channel.members:
                try:
                    await member.move_to(None)
                except:
                    pass
            await ctx.author.voice.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(speak=False))
            db = async_database()
            await db.connect()
            try:
                await db.con.execute('''
                    INSERT INTO muted_users (
                        user_reference,
                        guild_reference,
                        channel,
                        mute_duration
                    )
                    SELECT
                        users.id,
                        guilds.id,
                        '748421073959256096',
                        '%s'
                    FROM
                        users
                    INNER JOIN guilds
                        ON guilds.guild = '%s'
                    WHERE
                        user_id = '%s'
                    ON CONFLICT (user_reference, guild_reference, channel)
                    DO NOTHING;
                ''' %
                (datetime.now() + timedelta(hours=int(number)),
                ctx.guild.id,
                member.id)
                )
            finally:
                await db.close()
        self.vote_in_progress = False
        await asyncio.sleep(10)
        try:
            await conclusion.delete()
        except:
            pass
        await ctx.channel.set_permissions(member, overwrite=discord.PermissionOverwrite(read_messages=None))

    # Personal command that can be deleted
    @commands.command(name="18+")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def nsfw_role(self, ctx, *, member: discord.Member = None):
        # This command is for personal use
        
        if member == None:
            return await ctx.send("💌 | Sorry, please type in a valid member", delete_after=10)

        _role = [role.id for role in ctx.author.roles if role.id == 760738626345893914]
        if _role == []:
            return await ctx.send("💌 | Sorry, you must be part of the role group in order to use this command", delete_after=10)

        _role = [role.id for role in member.roles if role.id == 760738626345893914]
        if _role != []:
            return await ctx.send("💌 | The member you named already has the required role", delete_after=10)
        
        await member.add_roles(ctx.guild.get_role(760738626345893914), reason="%s gave role to %s" % (ctx.author, member))
        await ctx.message.add_reaction('✅')

        _reportChannel = ctx.guild.get_channel(760996881001480213)
        _currentTime = datetime.now()
        if _currentTime.hour > 12:
            _timeConversion = _currentTime.hour - 12
            _AmPm = "PM"
        else:
            _timeConversion = _currentTime.hour
            _AmPm = "AM"

        embed = discord.Embed(
            title="%s/%s/%s %s:%s %s" % (
                                        _currentTime.month,
                                        _currentTime.day,
                                        _currentTime.year,
                                        _timeConversion,
                                        _currentTime.minute,
                                        _AmPm
                                        ),
            description="`%s` gave `%s` the 18+ voice channel role" % (ctx.author, member),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text="Giver ID: %s\nRecipient ID: %s" % (ctx.author.id, member.id))
        await _reportChannel.send(embed=embed)

    # This is a personal command that plays a specified mp3 file in the voice channel
    @commands.command(name="Sound", aliases=["S"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    async def sound(self, ctx):
        await ctx.message.delete()
        if ctx.author.voice == None:
            return
        if ctx.guild.me.voice == None:
            await ctx.author.voice.channel.connect()
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("2020-11-08 15-39-08.mp3"))
        ctx.voice_client.play(source)
        await asyncio.sleep(2)
        await ctx.voice_client.disconnect()

    @tasks.loop(seconds=60)
    async def check_time(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)
        db = async_database()
        await db.connect()
        try:
            mute_duration = await db.con.fetch('''
                SELECT
                    users.user_id,
                    guilds.guild,
                    muted_users.channel,
                    muted_users.mute_duration
                FROM
                    muted_users
                INNER JOIN users
                    ON users.id = muted_users.user_reference
                INNER JOIN guilds
                    ON guilds.id = muted_users.guild_reference;
            '''
            )
            for user in mute_duration:
                if datetime.now() >= user[3]:
                    channel = self.bot.get_channel(int(user[2]))
                    guild = self.bot.get_guild(int(user[1]))
                    member = guild.get_member(int(user[0]))
                    if member == None:
                        continue
                    if isinstance(channel, discord.channel.VoiceChannel):
                        await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(speak=None))
                    elif isinstance(channel, discord.channel.TextChannel):
                        await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(send_messages=None))
                    await db.con.execute('''
                        DELETE FROM
                            muted_users
                        WHERE
                            user_reference IN (
                                SELECT
                                    id
                                FROM
                                    users
                                WHERE
                                    user_id = '%s'
                            ) AND
                            guild_reference IN (
                                SELECT
                                    id
                                FROM
                                    guilds
                                WHERE
                                    guild = '%s'
                            ) AND
                            channel = '%s';
                    ''' %
                    (user[0],
                    user[1],
                    user[2])
                    )

            guild_user = await db.con.fetch('''
                SELECT
                    users.user_id,
                    guilds.guild,
                    guild_users.last_voice,
                    guild_users.last_deafen,
                    guild_users.voice_duration,
                    guild_users.deafen_duration
                FROM
                    guild_users
                INNER JOIN users
                    ON users.id = guild_users.user_reference
                INNER JOIN guilds
                    ON guilds.id = guild_users.guild_reference;
            ''')
            for user in guild_user:
                server = self.bot.get_guild(int(user[1]))
                member = server.get_member(int(user[0]))
                if member == None:
                    continue
                if member.voice is None and user[2] is not None:
                    record = datetime.now() - user[2]
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

                        UPDATE
                            users
                        SET
                            voice_duration = voice_duration + %s
                        WHERE
                            user_id = '%s';
                    ''' %
                    (record.seconds,
                    user[1],
                    user[0],
                    record.seconds,
                    user[0])
                    )
                # Potential to be scrapped
                if member.voice is not None and member.voice.self_deaf == False and user[3] is not None or member.voice is None and user[3] is not None:
                    record = datetime.now() - user[3]
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

                        UPDATE
                            users
                        SET
                            deafen_duration = deafen_duration + %s
                        WHERE
                            user_id = '%s';
                    ''' %
                    (record.seconds,
                    user[1],
                    user[0],
                    record.seconds,
                    user[0])
                    )
        finally:
            await db.close()

def setup(bot):
    bot.add_cog(Utility(bot))