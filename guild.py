import asyncio, discord, os, psycopg2
from discord.ext import commands

invalid = 'Please choose a valid option.'

class Settings(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name='Prefix', help='Allows to change the default prefix to a custom one.')
    @commands.guild_only()
    async def prefix(self, ctx, *, changeprefix=None):
        try: # Catches keyerror
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try: # Catches forbidden
                if ctx.channel.permissions_for(ctx.author).manage_guild == True and changeprefix != None:
                    if len(changeprefix) <= 9:
                        cur.execute(f"UPDATE servers SET prefix = '{changeprefix}' WHERE guild = '{ctx.guild.id}';")
                        await ctx.send(f"Prefix for `{ctx.guild.name}` has been changed to **{changeprefix}**")
                    else:
                        await ctx.send("Please make the prefix less than 10 characters long.")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == False and changeprefix != None:
                    await ctx.send("This command requires the user to have `Manage Server` permissions to use.")
                cur.execute(f"SELECT prefix FROM servers WHERE guild = '{ctx.guild.id}';")
                rows = cur.fetchall()
                for r in rows:
                    prefixmsg = r[0]
                    break
                if ctx.channel.permissions_for(ctx.author).manage_guild == True and changeprefix == None:
                    await ctx.send(f"The current prefix for this server is **{prefixmsg}**\n\nIn order to change the prefix of the server, type `{prefixmsg}prefix [TEXT]`")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == False and changeprefix == None:
                    await ctx.send(f"The current prefix for the server is **{prefixmsg}**")
            except discord.Forbidden:
                try:
                    await ctx.send(menu.miss_permission(self))
                except:
                    return
            conn.commit()
            cur.close()
            conn.close()

    @commands.command(name="Vc", help="In Beta")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def vc(self, ctx, Menu=None, Channel=None):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try:
                await menu.user(self, ctx, cur)
            finally:
                conn.commit()
                cur.close()
                conn.close()
    @vc.error
    async def vc_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(f"💌 | {ctx.author.mention}'s menu has been exited due to error (menu most likely got deleted).")
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        else:
            raise error

class menu:
    def __init_(self, bot):
        self.bot = bot

    def miss_permission(self):
        return "💌 | Missing permissions. Please make sure I have all the necessary permissions to properly work!\nPermissions such as: `Manage Channels`, `Read Text Channels & See Voice Channels`, `Send Messages`, `Manage Messages`, `Use External Emojis`, `Add Reactions`, `Connect`, `Move Members`"

    def invalid(self):
        return 'Please choose a valid option.'

    async def user(self, context, cursor):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        while True:
            counter = counter + 1
            perms = context.channel.permissions_for(context.author)
            manage = perms.manage_channels
            if manage == True:
                access = ""
            elif manage == False:
                access = " - **Access Denied**"
            if counter == 1:
                cursor.execute(f"SELECT autovc FROM servers WHERE guild = '{context.guild.id}';")
                rows = cursor.fetchall()
                for r in rows:
                    if r[0] == None:
                        auto_name = 'None'
                        break
                    else:
                        get_chl = self.bot.get_channel(r[0])
                        auto_name = get_chl.name
                        break
                content = f"```py\n'Menu for User' - {context.author.name}\n```\n**`1.)`** `Auto Voice Channel :` {auto_name}{access}\n`2.)` `Personal Voice Channel`\n\n```py\n# Enter one of the corresponding options\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}tvc' or wf.content == f'{prefix}tVC' or wf.content == f'{prefix}tVc' or wf.content == f'{prefix}tvC':
                    await msg.delete()
                    return
                elif wfc == '1' and manage == True or 'auto' in wfc and manage == True:
                    await msg.delete()
                    await menu.auto(self, context, cursor)
                    return
                elif wfc == '2' or 'manage' in wfc:
                    await msg.delete()
                    await menu.personal(self, context, cursor)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def auto(self, context, cursor):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        while True:
            counter = counter + 1
            if counter == 1:
                cursor.execute(f"SELECT autovc FROM servers WHERE guild = '{context.guild.id}';")
                rows = cursor.fetchall()
                for r in rows:
                    if r[0] == None:
                        auto_name = 'None'
                        auto_id = " | 'ID' - None"
                        break
                    else:
                        get_chl = self.bot.get_channel(r[0])
                        auto_name = get_chl.name
                        auto_id = f" | 'ID' - {get_chl.id}"
                        break
                if auto_name == 'None':
                    option = ''
                else:
                    option = f"\n💌 Enter 'none' to remove {auto_name}"
                content = f"```py\n'Menu for Auto Voice Channel' - {auto_name}{auto_id}\n```\nPlease enter a voice channel\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining{option}\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                for c in context.guild.channels:
                    instance = isinstance(c, discord.VoiceChannel)
                    if wfc == c.name.lower() and instance or wfc == str(c.id) and instance or wfc == c.mention.lower() and instance or wfc == 'none' and auto_name != 'None':
                        if wfc == 'none':
                            place = 'None'
                            clean = 'NULL'
                        else:
                            place = c.name
                            clean = f"'{c.id}'"
                        await msg.delete()
                        cursor.execute(f"UPDATE servers SET autovc = {clean} WHERE guild = '{context.guild.id}';")
                        await context.send(f"```py\n# {context.author.name} | Auto Voice Channel\n```\n💌 **AUTO VOICE CHANNEL SET** 💌\n\n```py\n# from '{auto_name}' to '{place}'\n```")
                        return
                if wfc == 'back':
                    await msg.delete()
                    await menu.user(self, context, cursor)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}tvc' or wf.content == f'{prefix}tVC' or wf.content == f'{prefix}tVc' or wf.content == f'{prefix}tvC':
                    await msg.delete()
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def personal(self, context, cursor):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"```py\n'Menu for Personal Voice Channel' - {context.author.name}\n```\n`1.)` `Create voice channel`\n`2.)` `Manage voice channels`\n\n```py\n# Personal voice channels are channels made for server members to edit to their heart's content\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.user(self, context, cursor)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}tvc' or wf.content == f'{prefix}tVC' or wf.content == f'{prefix}tVc' or wf.content == f'{prefix}tvC':
                    await msg.delete()
                    return
                elif wfc == '1' or 'create' in wfc:
                    await msg.delete()
                    await menu.create(self, context, cursor)
                    return
                elif wfc == '2' or 'manage' in wfc:
                    await msg.delete()
                    await menu.manage(self, context, cursor)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def create(self, context, cursor):
        cursor.execute("SELECT owner FROM vclist;")
        rows = cursor.fetchall()
        for r in rows:
            if r == None:
                break
            elif r[0] == context.author.id:
                await context.send(f"```py\n# Personal Voice Channel\n```\n**❗CHANNEL DENIED❗**\n\n```py\n# {context.author.name} already has a voice channel created\n```")
                return
        vc = await context.guild.create_voice_channel(name=f"💌{context.author.name}")
        cursor.execute(f"INSERT INTO vclist (voicechl, owner, members, static) VALUES ('{vc.id}', '{context.author.id}', '1', 'f')")
        content = f"```py\n# {context.author.name} | Personal Voice Channel\n```\n💌 **CHANNEL CREATED** 💌\n\n```py\n# name / id: {vc.name} / {vc.id}\n```"
        await context.send(content)
        await menu.confirm(self, context, cursor, vc.id)
        return

    async def manage(self, context, cursor):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        while True:
            counter = counter + 1
            cursor.execute("SELECT * FROM vclist;") # Change this so it selects only voice channels in the guild
            rows = cursor.fetchall()
            mlist = ""
            num, vname, vid = [], [], []
            for n, r in enumerate(rows):
                if r[1] == context.author.id or r[1] == None:
                    if r[1] == None:
                        own = " - **NO OWNER**"
                    else:
                        own = ""
                    vc = self.bot.get_channel(r[0])
                    mlist += f"`{n + 1}.)` **`{vc.name}`** `:` `{vc.id}`{own}\n"
                    num += [str(n+1)]
                    vname += [vc.name]
                    vid += [str(vc.id)]
            if mlist == "":
                mlist = "No voice channels found.\n"
            if counter == 1:
                content = f"```py\n'Menu for Personal Voice Channel' - Manage Voice Channels\n```\n{mlist}\n```py\n# Change properties of voice channels that are owned by {context.author.name}\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.personal(self, context, cursor)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc in num or wfc in vname or wfc in vid:
                    if wfc in num:
                        pos = num.index(wfc)
                    elif wfc in vname:
                        pos = vname.index(wfc)
                    elif wfc in vid:
                        pos = vid.index(wfc)
                    await msg.delete()
                    await menu.properties(self, context, cursor, int(vid[pos]))
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def properties(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        cursor.execute("SELECT voicechl, owner FROM vclist;")
        rows = cursor.fetchall()
        for r in rows:
            if r[1] == None and r[0] == vc.id:
                cursor.execute(f"UPDATE vclist SET owner = '{context.author.id}' WHERE voicechl = '{vc.id}';")
                notif = f"**{vc.name.upper()}** has been claimed by **{context.author.name.upper()}**\n"
            else:
                notif = ""
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"{notif}```py\n'Menu for Properties' - {vc.name}\n```\n`1.)` `Channel Name` - **{vc.name}**\n`2.)` `Channel Bitrate` - **{vc.bitrate}kbps**\n`3.)` `User Limit` - **{vc.user_limit}**\n`4.)` `Channel Position` - **{vc.position}**\n`5.)` `Channel Category` - **{vc.category}**\n`6.)` `Overwrite Permissions`\n\n```py\n# Properties of the voice channel that can be changed\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.manage(self, context, cursor)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == '1' or 'name' in wfc:
                    await msg.delete()
                    await menu.name(self, context, cursor, channel)
                    return
                elif wfc == '2' or 'bitrate' in wfc:
                    await msg.delete()
                    await menu.bitrate(self, context, cursor, channel)
                    return
                elif wfc == '3' or 'user limit' in wfc:
                    await msg.delete()
                    await menu.user_limit(self, context, cursor, channel)
                    return
                elif wfc == '4' or 'position' in wfc:
                    await msg.delete()
                    await menu.position(self, context, cursor, channel)
                    return
                elif wfc == '5' or 'category' in wfc:
                    await msg.delete()
                    await menu.category(self, context, cursor, channel)
                    return
                elif wfc == '6' or 'overwrite' in wfc or 'permission' in wfc:
                    await msg.delete()
                    await context.send("Work in progresss")
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def name(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"```py\n'Menu for Name' - {vc.name}\n```\nEnter a `message` to be the name for the selected voice channel\n\n```py\n# Displays the user's input as the voice channel's name | Name will always be in lower case due to discord limitations\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                else:
                    await msg.delete()
                    await vc.edit(name=wfc, reason="Name Changed")
                    await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 ** NAME CHANGED** 💌\n\n```py\n# new name: {vc.name}\n```")
                    await menu.confirm(self, context, cursor, channel)
                    return
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def bitrate(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"```py\n'Menu for Bitrate' - {vc.name}\n```\nSelect a number between `8000-96000`\n\n```py\n# Default for voice channels is 64000kbps | Higher number is better audio quality yet requires better internet connection vice versa\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wf.content.isdigit() == True and int(wfc) >= 8000 and int(wfc) <= 96000:
                    await msg.delete()
                    await vc.edit(bitrate=int(wfc), reason="Bitrate Changed")
                    await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **BITRATE CHANGED** 💌\n\n```py\n# new bitrate: {vc.bitrate}\n```")
                    await menu.confirm(self, context, cursor, channel)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def user_limit(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"```py\n'Menu for User Limit' - {vc.name}\n```\nSelect a number between `0-99`\n\n```py\n# 0 is limitless users\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wf.content.isdigit() == True and int(wfc) >= 0 and int(wfc) <= 99:
                    await msg.delete()
                    await vc.edit(user_limit=int(wfc), reason="User Limit Changed")
                    await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **USER LIMIT CHANGED** 💌\n\n```py\n# new user limit : {vc.user_limit}\n```")
                    await menu.confirm(self, context, cursor, channel)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return
        
    async def position(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        while True:
            counter = counter + 1
            posvc = ""
            num, vname, vid = [], [], []
            if vc.category == None:
                for n, p in enumerate(context.guild.voice_channels):
                    if p.category == None:
                        posvc += f"`{n + 1}.)` Position **{p.position}** - `{p.name}` `:` `{p.id}`\n"
                        num += [str(n + 1)]
                        vname += [p.name]
                        vid += [str(p.id)]
            else:
                for n, p in enumerate(vc.category.voice_channels):
                    posvc += f"`{n + 1}.)` Position **{p.position}** - `{p.name}` `:` `{p.id}`\n"
                    num += [str(n + 1)]
                    vname += [p.name]
                    vid += [str(p.id)]
            if counter == 1:
                pnumb = f"`{str(int(num[-1]) + 1)}.)` Select this position to go below **{vname[-1]}** (Does not want to work)"
                content = f"```py\n'Menu for Position' - {vc.name}\n```\nChoose a **channel's** position to be on top of them\n\n{posvc}{pnumb}\n```py\n# Position number is the channel's current position in the category\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc in num or wfc in vname or wfc in vid or wfc == str(len(num) + 1):
                    await msg.delete()
                    if wfc in num or wfc in vname or wfc in vid:
                        if wfc in num:
                            pos = num.index(wfc)
                        elif wfc in vname:
                            pos = vname.index(wfc)
                        elif wfc in vid:
                            pos = vid.index(wfc)
                        newpos = 0
                        pvc = self.bot.get_channel(int(vid[pos]))
                    elif wfc == str(len(num) + 1):
                        newpos = 1
                        pvc = self.bot.get_channel(int(vid[-1]))
                    await vc.edit(position=pvc.position + newpos, reason="Moving Channel")
                    await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **CHANNEL MOVED** 💌\n\n```py\n# new position: {vc.position}\n```")
                    await menu.confirm(self, context, cursor, channel)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return
            
    async def category(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        vc = self.bot.get_channel(channel)
        while True:
            counter = counter + 1
            extra = ""
            cat = ""
            option = ""
            empty = False
            num, cname, cid = [], [], []
            for n, g in enumerate(context.guild.categories):
                cat += f"`{n + 1}.)` **`{g.name}`** `:` `{g.id}`\n"
                num += [str(n + 1)]
                cname += [g.name]
                cid += [str(g.id)]
            if cat == "":
                cat += "There are currently no **categories** in this server\n"
                empty = True
            else:
                extra += "Please select a **category** for the voice channel to be in\n\n"
                if vc.category != None:
                    option += "💌 Enter 'none' to make the voice channel have no category\n"
            if counter == 1:
                content = f"```py\n'Menu for Category' - {vc.name}\n```\n{extra}{cat}\n```py\n# A category is a group of channels that is usually related to said category\n{option}💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc in num or wfc in cname or wfc in cid or wfc == 'none' and empty == False:
                    await msg.delete()
                    if wfc in num or wfc in cname or wfc in cid:
                        if wfc in num:
                            pos = num.index(wfc)
                        elif wfc in cname:
                            pos = cname.index(wfc)
                        elif wfc in cid:
                            pos = cid.index(wfc)
                        catchl = self.bot.get_channel(int(cid[pos]))
                        await vc.edit(category=catchl, reason="Moving to Category")
                        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **CHANNEL MOVED** 💌\n\n```py\n# new category: {vc.category.name}\n```")
                        await menu.confirm(self, context, cursor, channel)
                        return
                    elif wfc == 'none':
                        catchl = None
                        await vc.edit(category=catchl, reason="Moving out of Category")
                        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **CHANNEL MOVED** 💌\n\n```py\n# new category: None\n```")
                        await menu.confirm(self, context, cursor, channel)
                        return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def confirm(self, context, cursor, channel):
        def verify(v):
            return v.content and v.author == context.author and v.channel == context.channel
        counter = 0
        cursor.execute(f"SELECT prefix FROM servers WHERE guild = '{context.guild.id}'")
        rows = cursor.fetchall()
        for r in rows:
            prefix = r[0]
        while True:
            counter = counter + 1
            if counter == 1:
                content = f"```py\n'Confirmation' - {context.author.name}\n```\n{context.author.mention}, Enter `done` to finish or enter `back` to change more settings"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'done':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wfc == 'back':
                    await msg.delete()
                    await menu.properties(self, context, cursor, channel)
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return


def setup(bot):
    bot.add_cog(Settings(bot))