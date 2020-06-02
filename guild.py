import discord
import os
import psycopg2
import asyncio
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name='Prefix', help='Allows to change the default prefix to a custom one.')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def prefix(self, ctx, *, changeprefix=None):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try:
                if changeprefix == None:
                    pass
                elif ctx.channel.permissions_for(ctx.author).manage_guild == True and len(changeprefix) <= 9:
                    cur.execute(f"UPDATE servers SET prefix = '{changeprefix}' WHERE guild = '{ctx.guild.id}';")
                    await ctx.send(f"Prefix for `{ctx.guild.name}` has been changed to **{changeprefix}**")
                elif len(changeprefix) >= 9:
                    await ctx.send("Please make the prefix less than 10 characters long.")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == False:
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
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.command(name="Vc", help="In Beta")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vc(self, ctx, Menu=None, Channel=None):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try:
                menus = ['auto', 'personal', 'create', 'manage', 'settings']
                alter = ['properties', 'transfer', 'permanent', 'name', 'bitrate', 'limit', 'position', 'category', 'overwrite', 'view', 'connect', 'speak', 'stream', 'move', 'reset']
                if Menu != None:
                    vc = None
                    cur.execute(f"SELECT voicechl, owner FROM vclist WHERE owner = '{ctx.author.id}';")
                    rows = cur.fetchall()
                    chunk = []
                    for r in rows:
                        chunk += [r[0]]
                        if self.bot.get_channel(r[0]).guild.id == ctx.guild.id and Channel == str(r[0]):
                            vc = self.bot.get_channel(r[0])
                    if Menu.lower() in menus:
                        await getattr(menu, Menu)(self, ctx, cur) # return?
                        return
                    elif Menu.lower() in alter:
                        if ctx.author.voice == None:
                            pass
                        elif ctx.author.voice.channel.id in chunk and Channel == None:
                            vc = True
                            voice = ctx.author.voice.channel.id
                        if vc != None and Channel != None:
                            voice = int(Channel)
                        if vc == None:
                            await menu.user(self, ctx, cur)
                            return
                        await getattr(menu, Menu)(self, ctx, cur, voice) # return?
                        return
                await menu.user(self, ctx, cur)
                return
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

class menu(object):
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
                content = f"```py\n'Menu for User' - {context.author.name}\n```\n**`1.)`** `Auto Voice Channel :` {auto_name}{access}\n`2.)` `Personal Voice Channel`\n`3.)` `User Settings`\n\n```py\n# Enter one of the corresponding options\n💌 Enter 'exit' to leave menu\n```"
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
                elif wfc == '2' or 'personal' in wfc:
                    await msg.delete()
                    await menu.personal(self, context, cursor)
                    return
                elif wfc == '3' or 'user' in wfc or 'setting' in wfc:
                    await msg.delete()
                    await menu.settings(self, context, cursor)
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
                content = f"```py\n'Menu for Auto Voice Channel' - {auto_name}{auto_id} | {prefix}vc Auto\n```\nPlease enter a voice channel\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining{option}\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                for c in context.guild.channels:
                    instance = isinstance(c, discord.VoiceChannel)
                    if wfc == c.name.lower() and instance or wfc == str(c.id) and instance or wfc == c.mention.lower() and instance or wfc == 'none' and auto_name != 'None':
                        cursor.execute(f"SELECT voicechl FROM vclist;")
                        vclist = cursor.fetchall()
                        if [item for item in vclist if c.id in item]:
                            break
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
                content = f"```py\n'Menu for Personal Voice Channel' - {context.author.name} | {prefix}vc Personal\n```\n`1.)` `Create voice channel`\n`2.)` `Manage voice channels`\n\n```py\n# Personal voice channels are channels made for server members to edit to their heart's content\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
        cursor.execute(f"INSERT INTO vclist (voicechl, owner, static) VALUES ('{vc.id}', '{context.author.id}', 'f');")
        content = f"```py\n# {context.author.name} | Personal Voice Channel\n```\n💌 **CHANNEL CREATED** 💌\n\n```py\n# name / id: {vc.name} / {vc.id}\n```"
        await context.send(content)
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
            cursor.execute("SELECT * FROM vclist;")
            rows = cursor.fetchall()
            mlist = ""
            num, vname, vid = [], [], []
            for n, r in enumerate(rows):
                if r[1] == context.author.id or r[1] == None:
                    vc = self.bot.get_channel(r[0])
                    if vc.guild.id == context.guild.id:
                        if r[1] == None:
                            own = " - **NO OWNER**"
                        else:
                            own = ""
                        mlist += f"`{n + 1}.)` **`{vc.name}`** `:` `{vc.id}`{own}\n"
                        num += [str(n+1)]
                        vname += [vc.name]
                        vid += [str(vc.id)]
            if mlist == "":
                mlist = "No voice channels found.\n"
            if counter == 1:
                content = f"```py\n'Menu for Manage Voice Channels' - {context.author.name} | {prefix}vc Manage\n```\n{mlist}\n```py\n# Change properties of voice channels that are owned by {context.author.name}\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                cursor.execute(f"SELECT static FROM vclist WHERE voicechl = '{vc.id}';")
                rows = cursor.fetchall()
                for r in rows:
                    static = r[0]
                content = f"{notif}```py\n'Menu for Properties' - {vc.name} | {prefix}vc Properties [CHANNEL ID]\n```\n`1.)` `Owner Transfership` - current owner: **{context.author.name}**\n`2.)` `Add Co-Owner` - **Work in Progress**\n`3.)` `Permanent Channel` - **{static}**\n`4.)` `Channel Name` - **{vc.name}**\n`5.)` `Channel Bitrate` - **{vc.bitrate}kbps**\n`6.)` `User Limit` - **{vc.user_limit}**\n`7.)` `Channel Position` - **{vc.position}**\n`8.)` `Channel Category` - **{vc.category}**\n`9.)` `Overwrite Permissions`\n\n```py\n# Properties of the voice channel that can be changed\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                elif wfc == '1' or 'transfer' in wfc:
                    await msg.delete()
                    await menu.transfer(self, context, cursor, channel)
                    return
                #elif wfc == '2' or 'add' in wfc:
                #    await msg.delete()
                #    await menu.co_owner(self, context, cursor, channel)
                #    return
                elif wfc == '3' or 'permanent' in wfc:
                    await msg.delete()
                    await menu.permanent(self, context, cursor, channel)
                    return
                elif wfc == '4' or 'name' in wfc:
                    await msg.delete()
                    await menu.name(self, context, cursor, channel)
                    return
                elif wfc == '5' or 'bitrate' in wfc:
                    await msg.delete()
                    await menu.bitrate(self, context, cursor, channel)
                    return
                elif wfc == '6' or 'user limit' in wfc:
                    await msg.delete()
                    await menu.user_limit(self, context, cursor, channel)
                    return
                elif wfc == '7' or 'position' in wfc:
                    await msg.delete()
                    await menu.position(self, context, cursor, channel)
                    return
                elif wfc == '8' or 'category' in wfc:
                    await msg.delete()
                    await menu.category(self, context, cursor, channel)
                    return
                elif wfc == '9' or 'overwrite' in wfc or 'permission' in wfc:
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def transfer(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Ownership Transfer' - {vc.name} | {prefix}vc Transfer [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n```py\n# Transfering ownership will no longer allow you to edit this voice channel and will remove your permissions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m.bot == True:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Ownership Transfer' - {vc.name} | {prefix}vc Transfer [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n**Bots can not be owners of voice channels**\n\n```py\n# Transfering ownership will no longer allow you to edit this voice channel and will remove your permissions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Ownership Transfer' - {vc.name} | {prefix}vc Transfer [CHANNEL ID]\n```\nAre you sure you wish to transfer ownership to **{m.name}**?\n`Yes`/`No`\n\n```py\n# Transfering ownership will no longer allow you to edit this voice channel and will remove your permissions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'yes':
                                        await msg.delete()
                                        cursor.execute(f"UPDATE vclist SET owner = '{m.id}' WHERE voicechl = '{vc.id}';")
                                        author_perm = vc.overwrites_for(context.author)
                                        await vc.set_permissions(m, overwrite=author_perm)
                                        await vc.set_permissions(context.author, overwrite=None)
                                        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **OWNERSHIP TRANSFERED TO {m.name.upper()}** 💌\n\n```py\n# {context.author.name} can no longer edit this voice channel\n```")
                                        return
                                    elif wfc == 'no':
                                        await wf.delete()
                                        await msg.edit(content=f"```py\n'Menu for Ownership Transfer' - {vc.name} | {prefix}vc Transfer [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n```py\n# Transfering ownership will no longer allow you to edit this voice channel and will remove your permissions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def co_owner(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Adding Co-Owners' - {vc.name} | {prefix}vc Co-Owner [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n```py\n# Adding Co-Owners will allow them to edit the voice channel with exceptions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            cursor.execute(f"SELECT admin FROM vclist WHERE voicechl = '{vc.id}';")
                            rows = cursor.fetchall()
                            array = []
                            for r in rows:
                                if r[0] != None:
                                    array += [r[0]]
                            if m.bot == True:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Adding Co-Owners' - {vc.name} | {prefix}vc Co-Owners [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n**Bots can not be Co-Owners of voice channels**\n\n```py\n# Adding Co-Owners will allow them to edit the voice channel with exceptions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            elif m.id in array:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Adding Co-Owners' - {vc.name} | {prefix}vc Co-Owners [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n**Member already a Co-Owner**\n\n```py\n# Adding Co-Owners will allow them to edit the voice channel with exceptions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Adding Co-Owners' - {vc.name} | {prefix}vc Co-Owners [CHANNEL ID]\n```\nAre you sure you wish to add **{m.name}** as a Co-Owner?\n`Yes`/`No`\n\n```py\n# Adding Co-Owners will allow them to edit the voice channel with exceptions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'yes':
                                        await msg.delete()
                                        cursor.execute("""INSERT INTO vclist (admin) VALUES ('{"%s"}');""", (m.id))
                                        author_perm = vc.overwrites_for(context.author)
                                        await vc.set_permissions(m, overwrite=author_perm)
                                        await vc.set_permissions(context.author, overwrite=None)
                                        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **{m.name.upper()} ADDED AS CO-OWNER** 💌\n\n```py\n# {m.name} can now edit this voice channel.\n```")
                                        return
                                    elif wfc == 'no':
                                        await wf.delete()
                                        await msg.edit(content=f"```py\n'Menu for Co-Owner' - {vc.name} | {prefix}vc Co-Owner [CHANNEL ID]\n```\nPlease enter a valid `member`\n\n```py\n# Adding Co-Owners will allow them to edit the voice channel with exceptions.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def permanent(self, context, cursor, channel):
        vc = self.bot.get_channel(channel)
        cursor.execute(f"SELECT static FROM vclist WHERE voicechl = '{vc.id}';")
        rows = cursor.fetchall()
        for r in rows:
            static = r[0]
        if static == True:
            change = "CHANNEL NO LONGER PERMANENT"
            tip = "Channel will be deleted when no members are present"
            cursor.execute(f"UPDATE vclist SET static = 'FALSE' WHERE voicechl = '{vc.id}';")
        elif static == False:
            change = "CHANNEL NOW PERMANENT"
            tip = "Channel will NOT be deleted when no members are present"
            cursor.execute(f"UPDATE vclist SET static = 'TRUE' WHERE voicechl = '{vc.id}';")
        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **{change}** 💌\n\n```py\n# {tip}\n```")
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
                content = f"```py\n'Menu for Name' - {vc.name} | {prefix}vc Name [CHANNEL ID]\n```\nEnter a `message` to be the name for the selected voice channel\n\n```py\n# Displays the user's input as the voice channel's name\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                    await vc.edit(name=wf.content, reason="Name Changed")
                    await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **NAME CHANGED** 💌\n\n```py\n# new name: {vc.name}\n```")
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
                content = f"```py\n'Menu for Bitrate' - {vc.name} | {prefix}vc Bitrate [CHANNEL ID]\n```\nSelect a number between `8000-96000`\n\n```py\n# Default for voice channels is 64000kbps | Higher number is better audio quality yet requires better internet connection vice versa\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                content = f"```py\n'Menu for User Limit' - {vc.name} | {prefix}vc Limit [CHANNEL ID]\n```\nSelect a number between `0-99`\n\n```py\n# 0 is limitless users\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                pnumb = f"`{str(int(num[-1]) + 1)}.)` Select this position to go below **{vname[-1]}** (Does not want to work)\n"
                content = f"```py\n'Menu for Position' - {vc.name} | {prefix}vc Position [CHANNEL ID]\n```\nChoose a **channel's** position to be on top of them\n\n{posvc}{pnumb}\n```py\n# Position number is the channel's current position in the category\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                content = f"```py\n'Menu for Category' - {vc.name} | {prefix}vc Category [CHANNEL ID]\n```\n{extra}{cat}\n```py\n# A category is a group of channels that is usually related to said category\n{option}💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                        return
                    elif wfc == 'none':
                        catchl = None
                        await vc.edit(category=catchl, reason="Moving out of Category")
                        await context.send(f"```py\n# {context.author.name} | Properties - {vc.name} | {vc.id}\n```\n💌 **CHANNEL MOVED** 💌\n\n```py\n# new category: None\n```")
                        return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def overwrite(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Overwrite' - {vc.name} | {prefix}vc Overwrite [CHANNEL ID]\n```\n`1.)` `View Channel`\n`2.)` `Connect`\n`3.)` `Speak`\n`4.)` `Stream`\n`5.)` `Move Members`\n\n```py\n# Overwrite permissions are what allows you to join, talk, and even see the voice channel, etc.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
                elif wfc == '1' or 'view' in wfc:
                    await msg.delete()
                    await menu.view(self, context, cursor, channel)
                    return
                elif wfc == '2' or 'connect' in wfc:
                    await msg.delete()
                    await menu.connect(self, context, cursor, channel)
                    return
                elif wfc == '3' or 'speak' in wfc:
                    await msg.delete()
                    await menu.speak(self, context, cursor, channel)
                    return
                elif wfc == '4' or 'video' in wfc:
                    await msg.delete()
                    await menu.stream(self, context, cursor, channel)
                    return
                elif wfc == '5' or 'move' in wfc or 'member' in wfc:
                    await msg.delete()
                    await menu.move(self, context, cursor, channel)
                    return
                else:
                    await context.send(menu.invalid(self))
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def view(self, context, cursor, channel):
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
                content = f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == 'everyone':
                    await wf.delete()
                    await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\n**Everyone** selected: `Grant`/`Default`/`Deny`\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                    while True:
                        wf = await self.bot.wait_for('message', timeout=60, check=verify)
                        wfc = wf.content.lower()
                        if wfc == 'cancel':
                            await wf.delete()
                            await msg.edit(content=content)
                            break
                        elif wfc == 'back':
                            await msg.delete()
                            await menu.overwrite(self, context, cursor, channel)
                            return
                        elif wfc == 'exit':
                            await msg.delete()
                            await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                            return
                        elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                            await msg.delete()
                            return
                        if wfc == 'grant':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.view_channel = None
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.view_channel = None
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.view_channel = True
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Granted**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'default':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.view_channel = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.view_channel = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.view_channel = None
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Not Set**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'deny':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.view_channel = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.view_channel = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.view_channel = False
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Denied**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        else:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                else:
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m == context.guild.me:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n**Please don't touch my permissions**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\n**{m.name}** selected: `Grant`/`Default`/`Deny`\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'cancel':
                                        await wf.delete()
                                        await msg.edit(content=content)
                                        break
                                    elif wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'grant':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.view_channel = True
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Granted**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'default':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.view_channel = None
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Not Set**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'deny':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.view_channel = False
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for View Channel' - {vc.name} | {prefix}vc View [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Denied**\n\n```py\n# View channel allows users to be able to see the voice channel which allows them to access it.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        #elif wf.mentions:
                        #    await context.send(f"{wf.mentions[0].name} selected.")
                        #    return
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def connect(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == 'everyone':
                    await wf.delete()
                    await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\n**Everyone** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                    while True:
                        wf = await self.bot.wait_for('message', timeout=60, check=verify)
                        wfc = wf.content.lower()
                        if wfc == 'cancel':
                            await wf.delete()
                            await msg.edit(content=content)
                            break
                        elif wfc == 'back':
                            await msg.delete()
                            await menu.overwrite(self, context, cursor, channel)
                            return
                        elif wfc == 'exit':
                            await msg.delete()
                            await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                            return
                        elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                            await msg.delete()
                            return
                        if wfc == 'grant':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.connect = None
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.connect = None
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.connect = True
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Granted**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'default':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.connect = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.connect = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.connect = None
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Not Set**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'deny':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.connect = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.connect = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.connect = False
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Denied**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        else:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                else:
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m == context.guild.me:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n**Please don't touch my permissions**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\n**{m.name}** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'cancel':
                                        await wf.delete()
                                        await msg.edit(content=content)
                                        break
                                    elif wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'grant':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.connect = True
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Granted**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'default':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.connect = None
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Not Set**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'deny':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.connect = False
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Connect' - {vc.name} | {prefix}vc Connect [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Denied**\n\n```py\n# Connect allows users to join the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def speak(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == 'everyone':
                    await wf.delete()
                    await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\n**Everyone** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                    while True:
                        wf = await self.bot.wait_for('message', timeout=60, check=verify)
                        wfc = wf.content.lower()
                        if wfc == 'cancel':
                            await wf.delete()
                            await msg.edit(content=content)
                            break
                        elif wfc == 'back':
                            await msg.delete()
                            await menu.overwrite(self, context, cursor, channel)
                            return
                        elif wfc == 'exit':
                            await msg.delete()
                            await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                            return
                        elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                            await msg.delete()
                            return
                        if wfc == 'grant':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.speak = None
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.speak = None
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.speak = True
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Granted**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'default':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.speak = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.speak = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.speak = None
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Not Set**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'deny':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.speak = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.speak = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.speak = False
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Denied**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        else:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                else:
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m == context.guild.me:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n**Please don't touch my permissions**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\n**{m.name}** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'cancel':
                                        await wf.delete()
                                        await msg.edit(content=content)
                                        break
                                    elif wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'grant':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.speak = True
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Granted**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'default':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.speak = None
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Not Set**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'deny':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.speak = False
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Speak' - {vc.name} | {prefix}vc Speak [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Denied**\n\n```py\n# Speak allows users to talk in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def stream(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == 'everyone':
                    await wf.delete()
                    await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\n**Everyone** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                    while True:
                        wf = await self.bot.wait_for('message', timeout=60, check=verify)
                        wfc = wf.content.lower()
                        if wfc == 'cancel':
                            await wf.delete()
                            await msg.edit(content=content)
                            break
                        elif wfc == 'back':
                            await msg.delete()
                            await menu.overwrite(self, context, cursor, channel)
                            return
                        elif wfc == 'exit':
                            await msg.delete()
                            await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                            return
                        elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                            await msg.delete()
                            return
                        if wfc == 'grant':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.stream = None
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.stream = None
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.stream = True
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Granted**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'default':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.stream = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.stream = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.stream = None
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Not Set**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'deny':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.stream = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.stream = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.stream = False
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Denied**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        else:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                else:
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m == context.guild.me:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n**Please don't touch my permissions**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\n**{m.name}** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'cancel':
                                        await wf.delete()
                                        await msg.edit(content=content)
                                        break
                                    elif wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'grant':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.stream = True
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Granted**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'default':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.stream = None
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Not Set**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'deny':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.stream = False
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Stream' - {vc.name} | {prefix}vc Stream [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Denied**\n\n```py\n# Stream allows users to share their screen or application in the voice channel.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def move(self, context, cursor, channel):
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
                content = f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                msg = await context.send(content)
            try:
                wf = await self.bot.wait_for('message', timeout=60, check=verify)
                wfc = wf.content.lower()
                if wfc == 'back':
                    await msg.delete()
                    await menu.overwrite(self, context, cursor, channel)
                    return
                elif wfc == 'exit':
                    await msg.delete()
                    await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                    return
                elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                    await msg.delete()
                    return
                elif wfc == 'everyone':
                    await wf.delete()
                    await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\n**Everyone** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                    while True:
                        wf = await self.bot.wait_for('message', timeout=60, check=verify)
                        wfc = wf.content.lower()
                        if wfc == 'cancel':
                            await wf.delete()
                            await msg.edit(content=content)
                            break
                        elif wfc == 'back':
                            await msg.delete()
                            await menu.overwrite(self, context, cursor, channel)
                            return
                        elif wfc == 'exit':
                            await msg.delete()
                            await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                            return
                        elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                            await msg.delete()
                            return
                        if wfc == 'grant':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.move_members = None
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.move_members = None
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.move_members = True
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Granted**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'default':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.move_members = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.move_members = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.move_members = None
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Not Set**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        elif wfc == 'deny':
                            await wf.delete()
                            bot_perm = vc.overwrites_for(context.guild.me)
                            bot_perm.move_members = True
                            author_perm = vc.overwrites_for(context.author)
                            author_perm.move_members = True
                            default_perm = vc.overwrites_for(context.guild.default_role)
                            default_perm.move_members = False
                            await vc.set_permissions(context.guild.me, overwrite=bot_perm)
                            await vc.set_permissions(context.author, overwrite=author_perm)
                            await vc.set_permissions(context.guild.default_role, overwrite=default_perm)
                            await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\nEveryone: **Denied**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                            break
                        else:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                else:
                    for m in context.guild.members:
                        if wfc == m.name.lower() or wf.content == str(m.id) or wfc == m.display_name: # doesn't trigger on mention
                            if m == context.guild.me:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n**Please don't touch my permissions**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                break
                            else:
                                await wf.delete()
                                await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\n**{m.name}** selected: `Grant`/`Default`/`Deny`\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'cancel' to select a different member\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                while True:
                                    wf = await self.bot.wait_for('message', timeout=60, check=verify)
                                    wfc = wf.content.lower()
                                    if wfc == 'cancel':
                                        await wf.delete()
                                        await msg.edit(content=content)
                                        break
                                    elif wfc == 'back':
                                        await msg.delete()
                                        await menu.overwrite(self, context, cursor, channel)
                                        return
                                    elif wfc == 'exit':
                                        await msg.delete()
                                        await context.send(f"💌 | {context.author.mention}'s menu has been exited.")
                                        return
                                    elif wf.content == f'{prefix}vc' or wf.content == f'{prefix}VC' or wf.content == f'{prefix}Vc' or wf.content == f'{prefix}vC':
                                        await msg.delete()
                                        return
                                    elif wfc == 'grant':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.move_members = True
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Granted**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'default':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.move_members = None
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Not Set**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    elif wfc == 'deny':
                                        await wf.delete()
                                        member_perm = vc.overwrites_for(m)
                                        member_perm.move_members = False
                                        await vc.set_permissions(m, overwrite=member_perm)
                                        await msg.edit(content=f"```py\n'Menu for Move' - {vc.name} | {prefix}vc Move [CHANNEL ID]\n```\nPlease enter valid `members` or type `everyone` to edit their permission\n\n{m.name}: **Denied**\n\n```py\n# Move members allows users to move other users into voice channels they have access to or disconnect them.\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```")
                                        break
                                    else:
                                        await wf.delete()
                                        invalid = await context.send(menu.invalid(self))
                                        await invalid.delete(delay=1)
                                break
                        elif m == context.guild.members[-1]:
                            await wf.delete()
                            invalid = await context.send(menu.invalid(self))
                            await invalid.delete(delay=1)
                            break
                        else:
                            pass
            except asyncio.TimeoutError:
                await msg.delete()
                await context.send(f"💌 | {context.author.mention} menu has been exited due to timeout.")
                return

    async def settings(self, context, cursor):
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
                content = f"```py\n'User Settings' - {context.author.name} | {prefix}vc Settings\n```\nWork in progress\n\n```py\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
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
