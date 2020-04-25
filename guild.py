import asyncio, discord, os, psycopg2
from discord.ext import commands

MissingPerm = "💌 | Missing permissions. Please make sure I have all the necessary permissions to properly work!\nPermissions such as: `Manage Channels`, `Read Text Channels & See Voice Channels`, `Send Messages`, `Manage Messages`, `Use External Emojis`, `Add Reactions`, `Connect`, `Move Members`"
menuexit = 'menu has been exited.'
menutimeout = 'menu has been exited due to timeout.'
menuerror = 'menu has been exited due to error (menu most likely got deleted).'
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
                    await ctx.send(MissingPerm)
                except:
                    return
            conn.commit()
            cur.close()
            conn.close()

    @commands.command(name='Vc', help='In Beta')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def vc(self, ctx):
        def menu(m):
            return m.content and m.author == ctx.author and m.channel == ctx.channel
        counter = 0
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try: # Catches timeout error
                cur.execute(f"SELECT prefix FROM servers WHERE guild = '{ctx.guild.id}'")
                rows = cur.fetchall()
                for r in rows:
                    fix = r[0]
                while True: # Menu for the user
                    counter = counter + 1
                    p = ctx.channel.permissions_for(ctx.author)
                    mc = p.manage_channels
                    if mc == True:
                        grant = ""
                    elif mc == False:
                        grant = " - **Access Denied**"
                    if counter == 1:
                        cur.execute(f"SELECT autovc FROM servers WHERE guild = '{ctx.guild.id}';")
                        rows = cur.fetchall()
                        for r in rows:
                            if r[0] == None:
                                value = 'None'
                                valueid = " | 'ID' - None"
                                break
                            else:
                                get = self.bot.get_channel(r[0])
                                value = get.name
                                valueid = f" | 'ID' - {get.id}"
                                break
                        cont = f"```py\n'Menu for User' - {ctx.author.name}\n```\n**`1.)`** `Auto Voice Channel :` {value}{grant}\n`2.)` `Personal Voice Channel`\n\n```py\n# Enter one of the corresponding options\n💌 Enter 'exit' to leave menu\n```"
                        msg = await ctx.send(cont)
                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                    mmc = mm.content.lower()

                    if mmc == '1' and mc == True or 'auto' in mmc and mc == True:
                        await msg.delete()
                        counter = 0
                        while True: # Menu for Auto Voice Channel
                            counter = counter + 1
                            if counter == 1:
                                if value == 'None':
                                    option = ''
                                else:
                                    option = f" |`💌`| Type **none** to __remove `{value}`__"
                                cont = f"```py\n'Menu for Auto Voice Channel' - {value}{valueid}\n```\nPlease enter a voice channel{option}\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                msg = await ctx.send(cont)
                            mm = await self.bot.wait_for('message', timeout=60, check=menu)
                            mmc = mm.content.lower()
                            back = 0
                            for chan in ctx.guild.channels:
                                isi = isinstance(chan, discord.VoiceChannel)

                                if mmc == chan.name.lower() and isi or mmc == str(chan.id) and isi or mmc == chan.mention.lower() and isi or mmc == 'none' and value != 'None':
                                    if mmc == 'none':
                                        place = 'None'
                                        clean = 'NULL'
                                    if mmc != 'none':
                                        place = chan.name
                                        clean = f"'{chan.id}'"
                                    await msg.delete()
                                    counter = 0
                                    while True: # Confirm Settings for Auto Voice Channel
                                        counter = counter + 1
                                        if counter == 1:
                                            cont = f"```py\n'Menu for Auto Voice Channel (Continued)' - {value}{valueid}\n```\n`{place}` Selected |`💌`| Type **confirm** to __save settings__\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                            msg = await ctx.send(cont)
                                        mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                        mmc = mm.content.lower()

                                        if mmc == 'confirm':
                                            await msg.delete()
                                            cur.execute(f"UPDATE servers SET autovc = {clean} WHERE guild = '{ctx.guild.id}';")
                                            cont = f"```py\n# Auto Voice Channel\n```\n💌 **SETTINGS SAVED** 💌\n\n```py\n# from '{value}' to '{place}'\n```"
                                            await ctx.send(cont)
                                            return

                                        elif mmc == 'back':
                                            back = back + 1
                                            counter = 0
                                            await msg.delete()
                                            break

                                        elif mmc == 'exit':
                                            await msg.delete()
                                            await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                            return

                                        elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                            await msg.delete()
                                            return

                                        else:
                                            await ctx.send(invalid)

                                    # End of Settings for Auto Voice Channel

                                else:
                                    pass

                            if mmc == 'back' and back == 0:
                                counter = 0
                                await msg.delete()
                                break

                            elif mmc == 'exit':
                                await msg.delete()
                                await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                return

                            elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                await msg.delete()
                                return

                            else:
                                await ctx.send(invalid)

                    # End of Menu for Auto Voice Channel

                    elif mmc == '1' and mc == False or 'auto' in mmc and mc == False:
                        await ctx.send(f"**{ctx.author.name}** requires the `Manage Channels` permissions to access that menu!")
                    
                    elif mmc == '2' or 'personal' in mmc:
                        await msg.delete()
                        counter = 0
                        while True: # Menu for Personal Voice Channel
                            counter = counter + 1
                            if counter == 1:
                                cont = "```py\n'Menu for Personal Voice Channel'\n```\n`1.)` `Create voice channel`\n`2.)` `Manage voice channels`\n\n```py\n# Personal voice channels are channels made for server members to edit to their heart's content\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                msg = await ctx.send(cont)
                            mm = await self.bot.wait_for('message', timeout=60, check=menu)
                            mmc = mm.content.lower()

                            if mmc == '1' or 'create' in mmc:
                                await msg.delete()
                                cur.execute("SELECT owner FROM vclist;")
                                rows = cur.fetchall()
                                for r in rows:
                                    if r == None:
                                        break
                                    elif r[0] == ctx.author.id:
                                        await ctx.send(f"```py\n# Personal Voice Channel\n```\n**❗CHANNEL DENIED❗**\n\n```py\n# {ctx.author.name} already has a voice channel created\n```")
                                        return
                                vc = await ctx.guild.create_voice_channel(name=f"💌{ctx.author.name}")
                                cur.execute(f"INSERT INTO vclist (voicechl, owner, members, static) VALUES ('{vc.id}', '{ctx.author.id}', '1', 'f')")
                                cont = f"```py\n# Personal Voice Channel\n```\n💌 **CHANNEL CREATED** 💌\n\n```py\n# name / id: {vc.name} / {vc.id}\n```"
                                msg = await ctx.send(cont)
                                return

                            elif mmc == '2' or 'manage' in mmc:
                                await msg.delete()
                                counter = 0
                                while True: # Menu for Managing
                                    counter = counter + 1
                                    cur.execute("SELECT * FROM vclist;") # Change this so it selects only voice channels in the guild
                                    rows = cur.fetchall()
                                    mlist = ""
                                    num, choice, vca = [], [], []
                                    for n, r in enumerate(rows):
                                        if r[1] == ctx.author.id or r[1] == None:
                                            if r[1] == None:
                                                own = " - **NO OWNER**"
                                            else:
                                                own = ""
                                            vc = self.bot.get_channel(r[0])
                                            mlist += f"`{n + 1}.)` **`{vc.name}`** `:` `{vc.id}`{own}\n"
                                            num += [str(n+1)]
                                            choice += [vc.name]
                                            vca += [str(vc.id)]
                                    if mlist == "":
                                        mlist = "No voice channels found.\n"
                                    if counter == 1:
                                        cont = f"```py\n'Menu for Personal Voice Channel - Manage Voice Channels'\n```\n{mlist}\n```py\n# Change properties of voice channels that are owned by {ctx.author.name}\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                        msg = await ctx.send(cont)
                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                    mmc = mm.content.lower()

                                    if mmc in num or mmc in choice or mmc in vca:
                                        if mmc in num:
                                            pos = num.index(mmc)
                                        elif mmc in choice:
                                            pos = choice.index(mmc)
                                        elif mmc in vca:
                                            pos = vca.index(mmc)
                                        vc = self.bot.get_channel(int(vca[pos]))
                                        cur.execute("SELECT voicechl, owner FROM vclist;")
                                        rows = cur.fetchall()
                                        for r in rows:
                                            if r[1] == None and r[0] == vc.id:
                                                cur.execute(f"UPDATE vclist SET owner = '{ctx.author.id}' WHERE voicechl = '{vc.id}';")
                                                notif = f"**{vc.name.upper()}** has been claimed by **{ctx.author.name.upper()}**\n"
                                            else:
                                                notif = ""
                                        await msg.delete()
                                        counter = 0
                                        while True: # Menu for Properties
                                            counter = counter + 1
                                            if counter == 1:
                                                cont = f"{notif}```py\n'Menu for Properties - {vc.name}'\n```\n`1.)` `Channel Name` - **{vc.name}**\n`2.)` `Channel Bitrate` - **{vc.bitrate}kbps**\n`3.)` `User Limit` - **{vc.user_limit}**\n`4.)` `Category` `/` `Position` - **{vc.category}** / **{vc.position}**\n`5.)` `Overwrite Permissions`\n\n```py\n# Properties of the voice channel that can be changed\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                msg = await ctx.send(cont)
                                            mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                            mmc = mm.content.lower()

                                            if mmc == '1' or 'name' in mmc:
                                                await msg.delete()
                                                counter = 0
                                                while True: # Menu for Name
                                                    counter = counter + 1
                                                    if counter == 1:
                                                        cont = f"```py\n'Menu for Name - {vc.name}'\n```\nEnter a `message` to be the name for the selected voice channel\n\n```py\n# Displays the user's input as the voice channel's name | Name will always be in lower case due to discord limitations\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                        msg = await ctx.send(cont)
                                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                    mmc = mm.content.lower()

                                                    if mmc == 'back':
                                                        counter = 0
                                                        await msg.delete()
                                                        break

                                                    elif mmc == 'exit':
                                                        await msg.delete()
                                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                        return

                                                    elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                                        await msg.delete()
                                                        return

                                                    else:
                                                        await msg.delete()
                                                        await vc.edit(name=mmc, reason="Name Changed")
                                                        await ctx.send(f"```py\n# Properties - {vc.name} | {vc.id}\n```\n💌 ** NAME CHANGED** 💌\n\n```py\n# new name: {vc.name}\n```")
                                                        return

                                                    # End of Channel Name

                                            elif mmc == '2' or 'bitrate' in mmc:
                                                await msg.delete()
                                                counter = 0
                                                while True: # Menu for Bitrate
                                                    counter = counter + 1
                                                    if counter == 1:
                                                        cont = f"```py\n'Menu for Bitrate - {vc.name}'\n```\nSelect a number between `8000-96000`\n\n```py\n# Default for voice channels is 64000kbps | Higher number is better audio quality yet requires better internet connection vice versa\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                        msg = await ctx.send(cont)
                                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                    mmc = mm.content.lower()

                                                    if mm.content.isdigit() == True and int(mmc) >= 8000 and int(mmc) <= 96000:
                                                        await msg.delete()
                                                        await vc.edit(bitrate=int(mmc), reason="Bitrate Changed")
                                                        await ctx.send(f"```py\n# Properties - {vc.name} | {vc.id}\n```\n💌 **BITRATE CHANGED** 💌\n\n```py\n# new bitrate: {vc.bitrate}\n```")
                                                        return

                                                    elif mmc == 'back':
                                                        counter = 0
                                                        await msg.delete()
                                                        break

                                                    elif mmc == 'exit':
                                                        await msg.delete()
                                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                        return

                                                    else:
                                                        await ctx.send(invalid)

                                                    # End of Bitrate

                                            elif mmc == '3' or 'user limit' in mmc:
                                                await msg.delete()
                                                counter = 0
                                                while True: # Menu for User Limit
                                                    counter = counter + 1
                                                    if counter == 1:
                                                        cont = f"```py\n'Menu for User Limit - {vc.name}'\n```\nSelect a number between `0-99`\n\n```py\n# 0 is limitless users\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                        msg = await ctx.send(cont)
                                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                    mmc = mm.content.lower()

                                                    if mm.content.isdigit() == True and int(mmc) >= 0 and int(mmc) <= 99:
                                                        await msg.delete()
                                                        await vc.edit(user_limit=int(mmc), reason="User Limit Changed")
                                                        await ctx.send(f"```py\n# Properties - {vc.name} | {vc.id}\n```\n💌 **USER LIMIT CHANGED** 💌\n\n```py\n# new user limit : {vc.user_limit}\n```")
                                                        return

                                                    elif mmc == 'back':
                                                        counter = 0
                                                        await msg.delete()
                                                        break

                                                    elif mmc == 'exit':
                                                        await msg.delete()
                                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                        return

                                                    elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                                        await msg.delete()
                                                        return

                                                    else:
                                                        await ctx.send(invalid)

                                                    # End of User Limit

                                            elif mmc == '4' or 'position' in mmc:
                                                await msg.delete()
                                                counter = 0
                                                while True: # Menu for Category
                                                    counter = counter + 1
                                                    extra = ""
                                                    cat = ""
                                                    option = "💌 Enter 'skip' to move on to positions\n"
                                                    empty = False
                                                    num, cname, cid = [], [], []
                                                    for n, g in enumerate(ctx.guild.categories):
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
                                                        cont = f"```py\n'Menu for Position - {vc.name}'\n```\n{extra}{cat}\n```py\n# A category is a group of channels that is usually related to said category\n{option}💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                        msg = await ctx.send(cont)
                                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                    mmc = mm.content.lower()

                                                    if mmc == 'back':
                                                        counter = 0
                                                        await msg.delete()
                                                        break

                                                    elif mmc == 'exit':
                                                        await msg.delete()
                                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                        return

                                                    elif mmc in num or mmc in cname or mmc in cid or mmc == 'skip' or mmc == 'none' and empty == False:
                                                        await msg.delete()
                                                        if mmc in num or mmc in cname or mmc in cid:
                                                            if mmc in num:
                                                                pos = num.index(mmc)
                                                            elif mmc in cname:
                                                                pos = cname.index(mmc)
                                                            elif mmc in cid:
                                                                pos = cid.index(mmc)
                                                            catchl = self.bot.get_channel(int(cid[pos]))
                                                            await vc.edit(category=catchl, reason="Moving to Category")
                                                        elif mmc == 'none':
                                                            catchl = None
                                                            await vc.edit(category=catchl, reason="Moving out of Category")
                                                        counter = 0
                                                        while True: # Menu for Position
                                                            counter = counter + 1
                                                            posvc = ""
                                                            num, vname, vid = [], [], []
                                                            if vc.category == None:
                                                                for n, p in enumerate(ctx.guild.voice_channels):
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
                                                                cont = f"```py\n'Menu for Position - {vc.name}'\n```\nChoose a **channel's** position to be on top of them\n\n{posvc}{pnumb}\n```py\n# Position number is the channel's current position in the category\n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                                msg = await ctx.send(cont)
                                                            mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                            mmc = mm.content.lower()

                                                            if mmc == 'back':
                                                                counter = 0
                                                                await msg.delete()
                                                                break
                                                            
                                                            elif mmc == 'exit':
                                                                await msg.delete()
                                                                await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                                return

                                                            elif mmc in num or mmc in vname or mmc in vid or mmc == str(len(num) + 1):
                                                                await msg.delete()
                                                                if mmc in num or mmc in vname or mmc in vid:
                                                                    if mmc in num:
                                                                        pos = num.index(mmc)
                                                                    elif mmc in vname:
                                                                        pos = vname.index(mmc)
                                                                    elif mmc in vid:
                                                                        pos = vid.index(mmc)
                                                                    newpos = 0
                                                                    pvc = self.bot.get_channel(int(vid[pos]))
                                                                elif mmc == str(len(num) + 1):
                                                                    newpos = 1
                                                                    pvc = self.bot.get_channel(int(vid[-1]))
                                                                await vc.edit(position=pvc.position + newpos, reason="Moving Channel")
                                                                await ctx.send(f"```py\n# Properties - {vc.name} | {vc.id}\n```\n💌 **CHANNEL MOVED** 💌\n\n```py\n# new category / position: {vc.category.name} / {vc.position}\n```")
                                                                return

                                                            else:
                                                                await ctx.send(invalid)

                                                            # End of position

                                                    else:
                                                        await ctx.send(invalid)

                                                # End of Category

                                            elif mmc == '5' or 'overwrite' in mmc or 'permission' in mmc:
                                                await msg.delete()
                                                counter = 0
                                                while True: # Menu for Overwrite Permissions
                                                    counter = counter + 1
                                                    if counter == 1:
                                                        cont = f"```py\n'Menu for Overwrite Permissions - {vc.name}'\n```\nWork in progress\n\n```py\n# \n💌 Enter 'back' to go back a menu\n💌 Enter 'exit' to leave menu\n```"
                                                        msg = await ctx.send(cont)
                                                    mm = await self.bot.wait_for('message', timeout=60, check=menu)
                                                    mmc = mm.content.lower()

                                                    if mmc == 'back':
                                                        counter = 0
                                                        await msg.delete()
                                                        break

                                                    elif mmc == 'exit':
                                                        await msg.delete()
                                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                        return

                                                    else:
                                                        await ctx.send(invalid)

                                                # End of Overwrite Permissions

                                            elif mmc == 'back':
                                                counter = 0
                                                await msg.delete()
                                                break

                                            elif mmc == 'exit':
                                                await msg.delete()
                                                await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                                return

                                            elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                                await msg.delete()
                                                return

                                            else:
                                                await ctx.send(invalid)

                                        # End of Properties

                                    elif mmc == 'back':
                                        counter = 0
                                        await msg.delete()
                                        break

                                    elif mmc == 'exit':
                                        await msg.delete()
                                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                        return

                                    elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                        await msg.delete()
                                        return

                                    else:
                                        await ctx.send(invalid)

                                    # End of Managing for Personal Voice Channel

                            elif mmc == 'back':
                                counter = 0
                                await msg.delete()
                                break

                            elif mmc == 'exit':
                                await msg.delete()
                                await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                                return

                            elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                                await msg.delete()
                                return

                            else:
                                await ctx.send(invalid)

                        # End of Menu for Personal Voice Channel
                    
                    elif mmc == 'exit':
                        await msg.delete()
                        await ctx.send(f"💌 | {ctx.author.mention}'s " + menuexit)
                        return
                    
                    elif mm.content == f'{fix}vc' or mm.content == f'{fix}VC' or mm.content == f'{fix}Vc' or mm.content == f'{fix}vC':
                        await msg.delete()
                        return

                    else:
                        await ctx.send(invalid)

                    # End of Menu for User

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(f"💌 | {ctx.author.mention} " + menutimeout)
            finally:
                conn.commit()
                cur.close()
                conn.close()
    @vc.error
    async def vc_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(f"💌 | {ctx.author.mention} " + menuerror)
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        else:
            raise error

def setup(bot):
    bot.add_cog(Settings(bot))