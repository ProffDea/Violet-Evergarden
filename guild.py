import discord
import os
import psycopg2
import asyncio
import time
import datetime
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
                menus = ['auto', 'personal', 'create', 'manage', 'settings', 'randomizer', 'randomizer_add', 'randomizer_view', 'server']
                alter = ['properties', 'transfer', 'permanent', 'name', 'bitrate', 'limit', 'position', 'category', 'overwrites', 'view', 'connect', 'speak', 'stream', 'move', 'reset']
                if Menu != None:
                    vc = None
                    cur.execute(f"SELECT voicechl, owner FROM vclist WHERE owner = '{ctx.author.id}';")
                    rows = cur.fetchall()
                    chunk = []
                    for r in rows:
                        chunk += [r[0]]
                        if self.bot.get_channel(r[0]).guild.id == ctx.guild.id and Channel == str(r[0]):
                            vc = self.bot.get_channel(r[0])
                    perms = ctx.channel.permissions_for(ctx.author)
                    manage = perms.manage_channels
                    if Menu.lower() in ['auto', 'server'] and manage == False:
                        await menu.user(self, ctx,  cur)
                        return
                    elif Menu.lower() in menus:
                        await getattr(menu, Menu)(self, ctx, cur)
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
                        await getattr(menu, Menu)(self, ctx, cur, voice)
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
            await ctx.send(f"💌 | **{ctx.author.name}**'s menu has been exited due to error.")
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        else:
            raise error

class menu(object):
    def __init_(self, bot):
        self.bot = bot

    def exit(self, ctx):
        return f"💌 | **{ctx.author.name}**'s menu has been exited."

    def timeout(self, ctx):
        return f"💌 | **{ctx.author.name}**'s menu has been exited due to timeout."

    def miss_permission(self):
        return "💌 | Missing permissions. Please make sure I have all the necessary permissions to properly work!\nPermissions such as: `Manage Channels`, `Read Text Channels & See Voice Channels`, `Send Messages`, `Manage Messages`, `Use External Emojis`, `Add Reactions`, `Connect`, `Move Members`"

    def invalid(self):
        return 'Please choose a valid option.'

    async def user(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        options, spread = {"Personal Voice Channel" : "personal",
                        "User Settings" : "settings",
                        "Server Settings" : "server"}, ''
        perms = ctx.channel.permissions_for(ctx.author)
        manage = perms.manage_channels
        if manage == False:
            options.pop("Server Settings")
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        info = False
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "User Menu",
                    description = f"```py\n{spread}\n```\n🇽 Exit menu\nℹ️ More Information (Menu will stay intact)\n\nEnter one of the corresponding options",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("🇽")
                await msg.add_reaction("ℹ️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif 'ℹ️' in str(result) and info == False:
                    info = True
                    await msg.clear_reaction("ℹ️")
                    await ctx.send(""">>> **Personal Voice Channel**: Access everything to do with your own personal voice channels through this option
**User Settings**: Change settings correlating to your account that'll effect your personal voice channels
**Server Settings**: This option will only be visible to users with manage channel permissions. Change settings that'll help manage this server""")
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def auto(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute(f"SELECT autovc FROM servers WHERE guild = '{ctx.guild.id}';")
        auto = cur.fetchall()
        if auto[0][0] != None:
            autovc = self.bot.get_channel(auto[0][0])
            autoname, autoid, remove = autovc.name, str(autovc.id), "❌ Remove Auto Voice Channel\n"
        else:
            autoname, autoid, remove = 'None', 'None', ''
        cur.execute("SELECT voicechl FROM vclist")
        vclist = cur.fetchall()
        
        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Auto Voice Channel Menu",
                    description = f"```py\nEnter a voice channel 'name' or 'ID'\n```\n⬅️ Go back\n🇽 Exit menu\n{remove}\nAuto Voice Channel will be the main voice channel used to create personal voice channels upon joining",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Auto", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {autoname}\nID: {autoid}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")
                if auto[0][0] != None:
                    await msg.add_reaction("❌")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()
                if str(type(result)) != "<class 'tuple'>":
                    vc = [voice for voice in ctx.guild.voice_channels if result.content.lower() in voice.name.lower() or result.content in str(voice.id)]

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.server(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif '❌' in str(result) and auto[0][0] != None:
                    await msg.delete()
                    cur.execute(f"UPDATE servers SET autovc = NULL WHERE guild = '{ctx.guild.id}';")
                    await menu.auto(self, ctx, cur)
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif vc and vc[0].id not in [item[0] for item in vclist]:
                    await msg.delete()
                    cur.execute(f"UPDATE servers SET autovc = '{vc[0].id}' WHERE guild = '{ctx.guild.id}'")
                    e = discord.Embed(
                        title = "AUTO VOICE CHANNEL SET",
                        description = "Thank you for using automated voice channels",
                        color = discord.Color.purple()
                    )
                    e.set_author(name=f"Vc Auto", icon_url=ctx.author.avatar_url)
                    e.set_footer(text=f"New AutoVC: {vc[0].name}\nID: {vc[0].id}\nOld AutoVC: {autoname}\nID: {autoid}")
                    msg = await ctx.send(embed=e)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def personal(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        options, spread = {"Create Voice Channel" : "create",
                        "Manage Voice Channels" : "manage"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Personal Voice Channel Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\n\nPersonal voice channels are channels made for server members to customize",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Personal", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.user(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
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

    async def manage(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute("SELECT voicechl, owner FROM vclist;")
        vclist = cur.fetchall()
        options, spread = [], ''
        for v in vclist:
            if v[1] == ctx.author.id or v[1] == None:
                vc = self.bot.get_channel(v[0])
                if vc.guild.id == ctx.guild.id:
                    if v[1] == None:
                        own = " - **NO OWNER**"
                    else:
                        own = ""
                    options += [vc.id]
                    spread += f"{options.index(vc.id) + 1}.) {vc.name} : {vc.id}{own}\n"
        if spread == '':
            spread = "No voice channels found.\n"

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Manage Voice Channel Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\n\nChange properties of voice channels that are owned by {ctx.author.name}",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Manage", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.personal(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await menu.properties(self, ctx, cur, options[int(result.content) - 1])
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def properties(self, ctx, cur, chl):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        vc = self.bot.get_channel(chl)
        cur.execute(f"SELECT static FROM vclist WHERE voicechl = '{vc.id}';")
        static = cur.fetchall()
        for s in static:
            static = s[0]
        if ctx.author.id in self.bot.name_cool:
            sec = int(round(time.time() - self.bot.name_cool[ctx.author.id]['log']))
        else:
            sec = 301
        if sec <= 300:
            name_cd = f" | {5-(sec//60)%60} minute(s)"
        else:
            name_cd = ''

        options, spread = {f"Transfer Owner - '{ctx.author}'" : "transfer",
                        f"Permanent - {static}" : "permanent",
                        f"Name - '{vc.name}'{name_cd}" : "name",
                        f"Bitrate - {vc.bitrate} kbps" : "bitrate",
                        f"User Limit - {vc.user_limit}" : "user_limit",
                        f"Position - {vc.position}" : "position",
                        f"Category - '{vc.category}'" : "category",
                        f"Overwrites" : "overwrites"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Properties Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\n\nProperties of the voice channel that can be changed",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Properties [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")
                
            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.manage(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur, chl)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
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
                                        await menu.overwrites(self, context, cursor, channel)
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

    async def permanent(self, ctx, cur, chl):
        vc = self.bot.get_channel(chl)
        cur.execute(f"SELECT static FROM vclist WHERE voicechl = '{vc.id}';")
        rows = cur.fetchall()
        for r in rows:
            static = r[0]
        if static == True:
            change = "CHANNEL NO LONGER PERMANENT"
            tip = "Channel will be deleted when no members are present"
            cur.execute(f"UPDATE vclist SET static = 'FALSE' WHERE voicechl = '{vc.id}';")
        elif static == False:
            change = "CHANNEL NOW PERMANENT"
            tip = "Channel will NOT be deleted when no members are present"
            cur.execute(f"UPDATE vclist SET static = 'TRUE' WHERE voicechl = '{vc.id}';")
        e = discord.Embed(
            title = f"{change}",
            description = f"Thank you for using automated voice channels",
            color = discord.Color.purple()
        )
        e.set_author(name=f"Vc Permanent [CHANNEL ID]", icon_url=ctx.author.avatar_url)
        e.set_footer(text=f"{tip}\nName: {vc.name}\nID: {vc.id}")
        await ctx.send(embed=e)
        return

    async def name(self, ctx, cur, chl):
        if ctx.author.id in self.bot.name_cool:
            sec = int(round(time.time() - self.bot.name_cool[ctx.author.id]['log']))
        else:
            sec = 301

        if sec <= 300:
            if 5-(sec//60)%60 == 1:
                minute = 'minute'
            else:
                minute = 'minutes'
            await ctx.send(f"Please wait **{5-(sec//60)%60}** {minute} before changing the name again")
            return

        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter, vc = 0, self.bot.get_channel(chl)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Name Menu",
                    description = "```py\nEnter a name as a 'message' to change channel name\n```\n\n⬅️ Go back\n🇽 Exit menu\n\n5 minute cooldown after changing name",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Name [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.properties(self, ctx, cur, chl)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                else:
                    await msg.delete()
                    name = result.content
                    await menu.name_confirm(self, ctx, cur, chl, name)
                    return

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def name_confirm(self, ctx, cur, chl, name):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter, vc = 0, self.bot.get_channel(chl)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Name Menu",
                    description = f"Are you sure you wish to change `{vc.name}`'s channel name?\n\n⬅️ Go back\n🇽 Exit menu\n☑️ Change Name to `{name}`\n\n5 minute cooldown after changing name",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Name [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction('⬅️')
                await msg.add_reaction('🇽')
                await msg.add_reaction('☑️')

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.name(self, ctx, cur, chl)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif '☑️' in str(result):
                    await msg.delete()
                    old = vc.name
                    await vc.edit(name=name, reason="Name Changed")
                    self.bot.name_cool.update({ctx.author.id : {'log' : time.time()}})
                    e = discord.Embed(
                        title = "NAME CHANGED",
                        description = "Thank you for using automated voice channels",
                        color = discord.Color.purple()
                    )
                    e.set_author(name=f"Vc Name [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                    e.set_footer(text=f"New Name: {vc.name}\nOld Name: {old}\nID: {vc.id}")
                    await ctx.send(embed=e)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def bitrate(self, ctx, cur, chl):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter = 0
        vc = self.bot.get_channel(chl)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Bitrate Menu",
                    description = f"```py\nSelect a number between 8000-96000\n```\n⬅️ Go back\n🇽 Exit menu\n\nDefault for voice channels is 64000kbps\nHigher number is better audio quality yet requires better internet connection vice versa",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Bitrate [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                
                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.properties(self, ctx, cur, chl)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) >= 8000 and int(result.content) <= 96000:
                    await msg.delete()
                    old = vc.bitrate
                    await vc.edit(bitrate=int(result.content), reason="Bitrate Changed")
                    e = discord.Embed(
                        title = "BITRATE CHANGED",
                        description = f"Thank you for using automated voice channels",
                        color = discord.Color.purple()
                    )
                    e.set_author(name=f"Vc Bitrate [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                    e.set_footer(text=f"New Bitrate: {vc.bitrate}\nOld Bitrate: {old}\nName: {vc.name}\nID: {vc.id}")
                    await ctx.send(embed=e)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def limit(self, ctx, cur, chl):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter = 0
        vc = self.bot.get_channel(chl)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "User Limit Menu",
                    description = f"```py\nSelect a number between 0-99\n```\n⬅️ Go back\n🇽 Exit menu\n\n0 is limitless users",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Limit [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.properties(self, ctx, cur, chl)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif  int(result.content) >= 0 and int(result.content) <= 99:
                    await msg.delete()
                    old = vc.user_limit
                    await vc.edit(user_limit=int(result.content), reason="User Limit Changed")
                    e = discord.Embed(
                        title = "USER LIMIT CHANGED",
                        description = f"Thank you for using automated voice channels",
                        color = discord.Color.purple()
                    )
                    e.set_author(name=f"Vc Limit [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                    e.set_footer(text=f"New Limit: {vc.user_limit}\nOld Limit: {old}\nName: {vc.name}\nID: {vc.id}")
                    await ctx.send(embed=e)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
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

    async def overwrites(self, ctx, cur, chl):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        options, spread = {"View Channel" : "view",
                        "Connect" : "connect",
                        "Speak" : "speak",
                        "Stream" : "stream",
                        "Move Members" : "move"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"
        
        counter = 0
        vc = self.bot.get_channel(chl)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Overwrites Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\n\nOverwrite permissions are what allows you to join, talk, and even see the voice channel, etc.",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Overwrites [CHANNEL ID]", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {vc.name}\nID: {vc.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()
                    
                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.properties(self, ctx, cur, chl)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur, chl)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
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
                    await menu.overwrites(self, context, cursor, channel)
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
                            await menu.overwrites(self, context, cursor, channel)
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
                                        await menu.overwrites(self, context, cursor, channel)
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
                    await menu.overwrites(self, context, cursor, channel)
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
                            await menu.overwrites(self, context, cursor, channel)
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
                                        await menu.overwrites(self, context, cursor, channel)
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
                    await menu.overwrites(self, context, cursor, channel)
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
                            await menu.overwrites(self, context, cursor, channel)
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
                                        await menu.overwrites(self, context, cursor, channel)
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
                    await menu.overwrites(self, context, cursor, channel)
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
                            await menu.overwrites(self, context, cursor, channel)
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
                                        await menu.overwrites(self, context, cursor, channel)
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
                    await menu.overwrites(self, context, cursor, channel)
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
                            await menu.overwrites(self, context, cursor, channel)
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
                                        await menu.overwrites(self, context, cursor, channel)
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

    async def settings(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        options, spread = {"Channel Name Randomizer" : "randomizer"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "User Settings Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\n\nThis is where all settings for {ctx.author.name} is located at",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Settings", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.user(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def randomizer(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        options, spread = {"Add Names" : "randomizer_add",
                        "View/Edit Name List" : "randomizer_view"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        info = False
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Channel Name Randomizer Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\nℹ️ More information (Menu will stay intact)\n\nNames for personal voice channels will be picked at random",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Randomizer", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")
                await msg.add_reaction("ℹ️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.settings(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif 'ℹ️' in str(result) and info == False:
                    info = True
                    await msg.clear_reaction("ℹ️")
                    await ctx.send(f">>> The user (**{ctx.author.name}**) will be able to make and store a maximum of 30 custom made names.\nUpon the creation of the user's personal voice channel, 1 of these 30 names (or less) will be picked at random to represent the personal voice channel's name. \n\nNote: These names are global to all servers and the name will not be displayed but still stored if blacklisted in the server.")
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def randomizer_add(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute(f"INSERT INTO members (user_id) VALUES ('{ctx.author.id}') ON CONFLICT (user_id) DO NOTHING;")
        cur.execute(f"SELECT unnest(name_generator) FROM members WHERE user_id = '{ctx.author.id}';")
        name_list = cur.fetchall()

        counter = 0
        left = 30 - len(name_list)
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Add Names to Randomizer Menu",
                    description = f"```py\nEnter a name as a 'message' one by one\n```\n\n⬅️ Go back\n🇽 Exit menu\n\nStore up to a maximum of 30 names\nMenu will stay open until timeout or reaction by emoji",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Randomizer_Add", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Total Names: {len(name_list)}\nName: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.randomizer(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                else:
                    if left > 0:
                        left = left - 1
                        cur.execute("""UPDATE members SET name_generator = name_generator || '{%s}' WHERE user_id = '%s';""" % (result.content, ctx.author.id))
                        await result.add_reaction("✅")
                    else:
                        await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def randomizer_view(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute(f"SELECT unnest(name_generator) FROM members WHERE user_id = '{ctx.author.id}';")
        name_list, spread = cur.fetchall(), ''
        if name_list == []:
            spread += "```py\nNo names found\n```"
            empty = True
        else:
            empty = False
        for name in name_list:
            if len(name_list) == 1:
                spread += f"```py\n{name_list.index(name) + 1}.) {name[0]}\n```"
            elif name == name_list[0]:
                spread += f"```py\n{name_list.index(name) + 1}.) {name[0]}\n"
            elif name == name_list[-1]:
                spread += f"{name_list.index(name) + 1}.) {name[0]}\n```"
            else:
                spread += f"{name_list.index(name) + 1}.) {name[0]}\n"
        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                if empty == False:
                    delete = '⚠️ Delete all names\n'
                else:
                    delete = ''
                e = discord.Embed(
                    title = "List of Randomizer Names Menu",
                    description = f"{spread}\n⬅️ Go back\n🇽 Exit menu\n{delete}\nIf you wish to delete a name, select the name by it's number\nMenu will stay open until timeout or reaction by emoji",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Randomizer_View", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")
                if empty == False:
                    await msg.add_reaction("⚠️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.randomizer(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif '⚠️' in str(result) and empty == False:
                    def verify_c(reaction, user):
                        return user == ctx.author and reaction.message.id == confirm.id

                    confirm_count = 0
                    while True:
                        confirm_count = confirm_count + 1
                        if confirm_count == 1:
                            confirm = await ctx.send(f"{ctx.author.mention} Are you sure you want to delete all names?")
                            await confirm.add_reaction("✅")
                            await confirm.add_reaction("❌")
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=5, check=verify_c)

                        if '✅' == str(reaction):
                            await msg.delete()
                            await confirm.delete()
                            cur.execute(f"UPDATE members SET name_generator = NULL WHERE user_id = '{user.id}';")
                            await menu.randomizer_view(self, ctx, cur)
                            return
                        elif '❌' == str(reaction):
                            await confirm.delete()
                            try:
                                await msg.remove_reaction("⚠️", user)
                                break
                            except discord.NotFound:
                                break
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(name_list) and int(result.content) != 0:
                    await msg.delete()
                    cur.execute(f"UPDATE members SET name_generator = array_remove(name_generator, '{name_list[int(result.content) - 1][0]}') WHERE user_id = '{ctx.author.id}';")
                    await result.add_reaction("✅")
                    await menu.randomizer_view(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def server(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute(f"SELECT autovc FROM servers WHERE guild = '{ctx.guild.id}';")
        auto = cur.fetchall()
        for a in auto:
            if a[0] == None:
                auto_name = 'None'
                break
            else:
                get_chl = self.bot.get_channel(a[0])
                auto_name = get_chl.name
                break
        options, spread = {f"Auto Voice Channel : '{auto_name}'" : "auto"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        counter = 0
        info = False
        while True:
            counter = counter + 1
            if counter == 1:
                e = discord.Embed(
                    title = "Server Settings Menu",
                    description = f"```py\n{spread}\n```\n⬅️ Go back\n🇽 Exit menu\nℹ️ More information (Menu will stay intact)\n\nThis is where all settings for this server is located at",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"Vc Server", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f"Name: {ctx.guild.name}\nID: {ctx.guild.id}")
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")
                await msg.add_reaction("ℹ️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await menu.user(self, ctx, cur)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif 'ℹ️' in str(result) and info == False:
                    info = True
                    await msg.clear_reaction("ℹ️")
                    await ctx.send(f""">>> **Auto Voice Channel**: Select a voice channel to be used as the main channel in the server to create personal voice channels upon joining it
""")
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.isdigit() == False:
                    await result.add_reaction("❌")
                elif int(result.content) <= len(options) and int(result.content) != 0:
                    await msg.delete()
                    await getattr(menu, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                    return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

def setup(bot):
    bot.add_cog(Settings(bot))
