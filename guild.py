import json
import asyncio
import discord
import psycopg2
import os
from discord.ext import commands

TestServerID = 648977487744991233 # ID is the test server ID. Feel free to change it
MissingPerm = "Missing permissions. Please make sure I have all the necessary permissions to properly work!\nPermissions such as: `Manage Channels`, `Read Text Channels & See Voice Channels`, `Send Messages`, `Manage Messages`, `Use External Emojis`, `Connect`, `Move Members`"
menuexit = 'Menu has been exited.'
menutimeout = 'Menu has been exited due to timeout.'

class Settings(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name='Prefix', help='Allows to change the default prefix to a custom one.')
    @commands.guild_only()
    async def prefix(self, ctx, changeprefix):
        try:
            if ctx.channel.permissions_for(ctx.author).manage_guild == True:
                if len(changeprefix) <= 9:
                    with open('guilds.json', 'r') as f:
                        cstmguild = json.load(f)
                    cstmguild[str(ctx.guild.id)]['Custom Prefix'] = changeprefix
                    await ctx.send(f"Prefix for `{ctx.guild.name}` has been changed to **{changeprefix}**")
                    with open('guilds.json', 'w') as f:
                        json.dump(cstmguild, f)
                    try:
                        DATABASE_URL = os.environ['DATABASE_URL']
                        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                    except KeyError:
                        conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                    finally:
                        cur = conn.cursor()
                        cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                        conn.commit()
                        cur.close()
                        conn.close()
                else:
                    await ctx.send("Please make the prefix less than 10 characters long.")
            else:
                await ctx.send("This command requires the user to have `Manage Server` permissions to use.")
        except discord.Forbidden:
            try:
                await ctx.send(MissingPerm)
            except:
                return
    @prefix.error
    async def prefix_error(self, ctx, error):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        if isinstance(error, commands.MissingRequiredArgument):
            prefixmsg = cstmguild[str(ctx.guild.id)]['Custom Prefix']
            if ctx.channel.permissions_for(ctx.author).manage_guild == True:
                await ctx.send(f"The current prefix for this server is **{prefixmsg}**\n\nIn order to change the prefix of the server, Type `{prefixmsg}prefix [TEXT]`")
            else:
                await ctx.send(f"The current prefix for the server is **{prefixmsg}**")

    @commands.command(name='Status', help="Changes bot's status message.") # Anyone can use this command and it changes the bot's status.
    @commands.guild_only()
    async def status(self, ctx, *, changestatus=None): # example(*, args) : ex. "Example text" | example(*args) : ex. "Example" "text"
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
        finally:
            cur =conn.cursor()
            with open('guilds.json', 'r') as f:
                cstmguild = json.load(f)
            if changestatus == None:
                cur.execute("UPDATE bot SET message = '' WHERE name = 'Status';")
                conn.commit()
                await self.bot.change_presence(activity=discord.Game(''))
                with open('guilds.json', 'w') as f:
                        json.dump(cstmguild, f)
            elif len(changestatus) <= 128:
                if 'https://' in changestatus:
                    await ctx.send('No links.')
                else:
                    cur.execute(f"UPDATE bot SET message = '{changestatus}' WHERE name = 'Status';")
                    conn.commit()
                    await self.bot.change_presence(activity=discord.Game(changestatus))
                    with open('guilds.json', 'w') as f:
                        json.dump(cstmguild, f)
            elif len(changestatus) >= 128:
                await ctx.send(f"Character limit is 128. You reached {len(changestatus)} characters.")
            cur.close()
            conn.close()


    @commands.command(name='Vc', help="Allows the use of personal voice channels.\n'Vc' while not in a voice channel will bring up the 'User Menu'.\n'Vc' while in a normal voice channel will bring up the 'Main Menu'.\n'Vc' while in a personal voice channel will bring up the 'Voice Channel Setting Menu'.\n'Vc [argument]' while in a personal voice channel will bring up the 'Member Menu'.") # False = empty | True = not empty
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def vc(self, ctx, *menu):
        try:
            with open('guilds.json', 'r') as f:
                cstmguild = json.load(f)
            try:
                chl = ctx.channel
                aut = ctx.author
                if bool(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']) == False: # Checks if there is a main automated voice channel or not | True = runs if not empty | False = runs if empty
                    if ctx.author.voice.channel.permissions_for(ctx.author).manage_channels == True:
                        def autovc(m):
                            return m.content and m.channel == chl and m.author == aut
                        try:
                            startcount = 0
                            while True:
                                startcount = startcount + 1
                                if startcount == 1:
                                    startmenu = await ctx.send(f"```\nWould you like the current VC '{ctx.author.voice.channel.name}' to be the main automated voice channel?\nDoing so will also use the '{ctx.channel.name.upper()}' channel for any of the bot's purposes.\n\n1.) Yes\n2.) No\n\nPlease enter one of the corresponding numbers.\n```")
                                autovcwait = await self.bot.wait_for('message', timeout=120, check=autovc)
                                if autovcwait.content == '1' or autovcwait.content.lower() == 'yes':
                                    await startmenu.delete()
                                    await ctx.send(f"```\nCurrent voice channel '{ctx.author.voice.channel.name}' has been set to the main automated voice channel.\nPlease re-join the voice channel to put it into effect.\n```\n{menuexit}")
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)] = {}
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Channel'] = ctx.channel.id
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Message'] = False # Keep this false until AutoMenu is fixed | Original: ctx.message.id
                                    await ctx.author.move_to(None)
                                    break
                                elif autovcwait.content == '2' or autovcwait.content.lower() == 'no':
                                    await startmenu.delete()
                                    await ctx.send(f'```\nThere is currently no automated voice channel set.\n```\n{menuexit}')
                                    break
                                elif autovcwait.content != '1' or autovcwait.content.lower() != 'yes' or autovcwait.content != '2' or autovcwait.content.lower() != 'no':
                                    await ctx.send('Please choose one of the corresponding numbers!')
                                    continue
                        except asyncio.TimeoutError:
                            await ctx.send(menutimeout)
                            return
                    else:
                        await ctx.send(f"`Manage Channel` permissions required to access automated voice channel menu for '{ctx.author.voice.channel.name}'!")
                elif bool(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']) == True: # Checks if there is a main automated voice channel or not | True = runs if not empty | False = runs if empty
                    for lelist in cstmguild[str(ctx.guild.id)]['VC']['VCList']:
                        temp = self.bot.get_channel(int(lelist))
                        if temp.id == ctx.author.voice.channel.id:
                            for leowner in cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist]:
                                ownertemp = ctx.guild.get_member(int(leowner))
                                if ownertemp.id == ctx.author.id:
                                    #for quickmenupull in menu:
                                    #    if quickmenupull.lower() == 'user':
                                    #        usercheck = True
                                    #    else:
                                    #        usercheck = False
                                    if len(menu) != 0: # Runs if there were any arguments
                                        try:
                                            def setmember(m):
                                                return m.content and m.channel == chl and m.author == aut
                                            listcount = 0
                                            cleanlist = []
                                            while True:
                                                # Work in progress
                                                for argmember in menu:
                                                    for listmember in ctx.guild.members:
                                                        if listmember.name.lower() in argmember.lower() or listmember.mention in argmember or str(listmember.id) in argmember or listmember.display_name.lower() in argmember.lower() or str(listmember) in argmember:
                                                            cleanlist += [str(listmember)]
                                                            continue
                                                        else:
                                                            pass
                                                reallist = [index_list for number_list, index_list in enumerate(cleanlist) if index_list not in cleanlist[:number_list]]
                                                listcount = listcount + 1
                                                if listcount == 1:
                                                    membermsg = ""
                                                    for templist in reallist:
                                                        membermsg += f"{str(templist)}\n"
                                                    if membermsg == "":
                                                        membermsg = "No Members Selected\n"
                                                        notlist = "\n"
                                                        addmore = "\nPlease add members to this list!\n\n"
                                                    else:
                                                        notlist = "\nList of members:\n\n"
                                                        addmore = "\nWhat would you like to do with everyone in the list?\n\n"
                                                    listmenu = await ctx.send(f"```{notlist}{membermsg}{addmore}1.) Add more members to the list\n\nPlease enter one of the corresponding numbers.\nType 'exit' to cancel settings.\n```")
                                                listcheck = await self.bot.wait_for('message', timeout=120, check=setmember)
                                                if listcheck.content == '1' or 'add' in listcheck.content.lower():
                                                    await listmenu.delete()
                                                    addmenu = 0
                                                    def addcheck(m):
                                                        return m.content and m.channel == chl and m.author == aut
                                                    while True:
                                                        listcount = 0
                                                        addmenu = addmenu + 1
                                                        if addmenu == 1:
                                                            addoptions = await ctx.send(f"```\nEnter valid users to add to list:\n\n{membermsg}\nType 'back' to go back.\nType 'exit' to cancel settings.\n```")
                                                        addwait = await self.bot.wait_for('message', timeout=120, check=addcheck)
                                                        inlist = []
                                                        for addmember in ctx.guild.members:
                                                            if addmember.name.lower() in addwait.content.lower() or addmember.mention in addwait.content or str(addmember.id) in addwait.content or addmember.display_name.lower() in addwait.content.lower() or str(addmember) in addwait.content:
                                                                if not str(addmember) in membermsg:
                                                                    membermsg += f"{str(addmember)}\n"
                                                                    cleanlist += [str(addmember)]
                                                                    replacemembermsg = 'No Members Selected\n'
                                                                    await addoptions.edit(content=f"```\nEnter valid users to add to list:\n\n{membermsg.replace(replacemembermsg, '')}\nType 'back' to go back.\nType 'exit' to cancel settings.\n```")
                                                                    continue
                                                                else:
                                                                    inlist += [f"**{str(addmember)}**"]
                                                                    continue
                                                        if inlist != []:
                                                            msginlist = ""
                                                            for nmberinlist, takeoutinlist in enumerate(inlist):
                                                                if len(inlist) == 1:
                                                                    msginlist += f"{takeoutinlist} "
                                                                else:
                                                                    if nmberinlist+1 != len(inlist):
                                                                        msginlist += f"{takeoutinlist}, "
                                                                    else:
                                                                        msginlist += f"and {takeoutinlist} "
                                                            if len(inlist) == 1:
                                                                word = 'is'
                                                            else:
                                                                word = 'are'
                                                            await ctx.send(f"{msginlist}{word} already in list!")
                                                        if addwait.content.lower() == 'back':
                                                            await addoptions.delete()
                                                            break
                                                        elif addwait.content.lower() == 'exit':
                                                            await addoptions.delete()
                                                            await ctx.send(menuexit)
                                                            return
                                                elif listcheck.content.lower() == 'exit':
                                                    await listmenu.delete()
                                                    await ctx.send(menuexit)
                                                    return
                                                elif listcheck.content != '1' or not 'add' in listcheck.content.lower() or listcheck.content.lower() != 'exit':
                                                    await ctx.send('Please choose one of the corresponding numbers!')
                                                    continue
                                        except asyncio.TimeoutError:
                                            await ctx.send(menutimeout)
                                            return
                                    else:
                                        if cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["Static"] == False:
                                            staticmsg = "Permanent VC is Disabled"
                                            staticstatus = True
                                            staticend = f"```\n'{temp.name}' is now a permanent voice channel.\nIt will not be deleted when the voice channel is empty.\n```\n{menuexit}"
                                        else:
                                            staticmsg = "Permanent VC is Enabled"
                                            staticstatus = False
                                            staticend = f"```\n'{temp.name}' is no longer a permanent voice channel.\nIt will get deleted when the voice channel is empty.\n```\n{menuexit}"
                                        for checkmsg in cstmguild[str(ctx.guild.id)]['VC']['AutoVC']:
                                            if cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][checkmsg]['Message'] == False:
                                                automenumsg = ''
                                            elif cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["AutoMenu"] == True and cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][checkmsg]['Message'] != False:
                                                automenumsg = "\n4.) Quick Menu is Turned On"
                                                automenustatus = False
                                                automenuend = f"```\n'{temp.name}' will no longer bother the owner whenever they join.\nIt will not bring up the menu for the owner and not mention them when they join.\n```\n{menuexit}"
                                            elif cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["AutoMenu"] == False and cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][checkmsg]['Message'] != False:
                                                automenumsg = "\n4.) Quick Menu is Turned Off"
                                                automenustatus = True
                                                automenuend = f"```\n'{temp.name}' will now bother the owner whenever they join.\nIt will bring up the menu for the owner and mention them when they join.\n```\n{menuexit}"
                                            def settings(m):
                                                return m.content and m.channel == chl and m.author == aut
                                            try:
                                                firstcount = 0
                                                while True:
                                                    firstcount = firstcount + 1
                                                    if firstcount == 1:
                                                        if temp.user_limit == 0:
                                                            userlimit = 'Limitless'
                                                        else:
                                                            userlimit = str(temp.user_limit)
                                                        first_menu = await ctx.send(f"```\nVoice channel - {temp.name} | Owner - {ctx.author}\n\n1.) User Limit - Current: {userlimit}\n2.) Change Name - Current: {temp.name}\n3.) {staticmsg}{automenumsg}\n\nPlease enter one of the corresponding numbers.\nType 'exit' to cancel settings.\n```")
                                                    waitsetting = await self.bot.wait_for('message', timeout=120, check=settings)
                                                    if waitsetting.content == '1' or waitsetting.content.lower() == 'user limit':
                                                        await first_menu.delete()
                                                        def setlimit(m):
                                                            return m.content and m.channel == chl and m.author == aut
                                                        usercount = 0
                                                        while True:
                                                            firstcount = 0
                                                            usercount = usercount + 1
                                                            if usercount == 1:
                                                                limit_menu = await ctx.send(f"```\nSet the user limit for '{temp.name}' by entering a number! 0 is limitless users.\n\nMaxinum number is 99\nMinimum number is 0\n\nType 'back' to go back.\nType 'exit' to cancel settings.\n```")
                                                            userlimit = await self.bot.wait_for('message', timeout=120, check=setlimit)
                                                            if userlimit.content.isdigit() == True:
                                                                limitnumber = int(userlimit.content)
                                                                if limitnumber == 0:
                                                                    afternumber = 'limitless'
                                                                else:
                                                                    afternumber = str(limitnumber)
                                                                if limitnumber <= 99:
                                                                    if limitnumber == temp.user_limit:
                                                                        await ctx.send(f'Please choose a number other than the current user limit! Current: {temp.user_limit}')
                                                                        continue
                                                                    else:
                                                                        await limit_menu.delete()
                                                                        await temp.edit(reason="Changing user limit", user_limit=limitnumber)
                                                                        await ctx.send(f"```\n'{temp.name}' user limit has been set to {afternumber}!\n```\n{menuexit}")
                                                                        return
                                                            elif userlimit.content.lower() == 'exit':
                                                                await limit_menu.delete()
                                                                await ctx.send(menuexit)
                                                                return
                                                            elif userlimit.content.lower() == 'back':
                                                                await limit_menu.delete()
                                                                break
                                                            elif userlimit.content.isdigit() == False or limitnumber >= 100:
                                                                await ctx.send('Please choose a number between 0-99!')
                                                                continue
                                                    elif waitsetting.content == '2' or waitsetting.content.lower() == 'change name':
                                                        await first_menu.delete()
                                                        def setname(m):
                                                            return m.content and m.channel == chl and m.author == aut
                                                        changecount = 0
                                                        while True:
                                                            firstcount = 0
                                                            changecount = changecount + 1
                                                            if changecount == 1:
                                                                name_menu = await ctx.send(f"```\nChange the name by entering in a message! Current voice channel name: {temp.name}\n\nType 'back' to go back.\nType 'exit' to cancel settings.\n```")
                                                            changename = await self.bot.wait_for('message', timeout=120, check=setname)
                                                            if changename.content.lower() == 'exit':
                                                                await name_menu.delete()
                                                                await ctx.send(menuexit)
                                                                return
                                                            elif changename.content.lower() == 'back':
                                                                await name_menu.delete()
                                                                break
                                                            elif changename.content.lower() != 'exit' or changename.content.lower() != 'back':
                                                                await name_menu.delete()
                                                                await temp.edit(reason='Change name', name=changename.content)
                                                                await ctx.send(f"```\nVoice channel's name has been changed to '{temp.name}'\n```\n{menuexit}")
                                                                return
                                                    elif waitsetting.content == '3' or 'permanent' in waitsetting.content.lower():
                                                        await first_menu.delete()
                                                        cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["Static"] = staticstatus
                                                        await ctx.send(staticend)
                                                        with open('guilds.json', 'w') as f:
                                                            json.dump(cstmguild, f)
                                                        try:
                                                            DATABASE_URL = os.environ['DATABASE_URL']
                                                            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                                        except KeyError:
                                                            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                                        finally:
                                                            cur = conn.cursor()
                                                            cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                                            conn.commit()
                                                            cur.close()
                                                            conn.close()
                                                        return
                                                    elif waitsetting.content == '4' and cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][checkmsg]['Message'] != False or 'quick menu' in waitsetting.content.lower() and cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][checkmsg]['Message'] != False:
                                                        await first_menu.delete()
                                                        cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]['AutoMenu'] = automenustatus
                                                        await ctx.send(automenuend)
                                                        with open('guilds.json', 'w') as f:
                                                            json.dump(cstmguild, f)
                                                        try:
                                                            DATABASE_URL = os.environ['DATABASE_URL']
                                                            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                                        except KeyError:
                                                            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                                        finally:
                                                            cur = conn.cursor()
                                                            cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                                            conn.commit()
                                                            cur.close()
                                                            conn.close()
                                                        return
                                                    elif waitsetting.content.lower() == 'exit':
                                                        await first_menu.delete()
                                                        await ctx.send(menuexit)
                                                        return
                                                    elif waitsetting.content != '1' or waitsetting.content.lower() != 'user limit' or waitsetting.content.lower() != 'exit' or waitsetting.content.lower() != 'back':
                                                        await ctx.send('Please choose one of the corresponding numbers!')
                                                        continue
                                            except asyncio.TimeoutError:
                                                await ctx.send(menutimeout)
                                                return
                                elif ownertemp.id != ctx.author.id:
                                    if not ownertemp in ctx.author.voice.channel.members and cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]['Static'] == False:
                                        cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][ctx.author.id] = cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]
                                        del cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]
                                        await ctx.send(f"**{ctx.author.name}** is the new owner of '{ctx.author.voice.channel.name}'!\nOld owner was **{ownertemp.name}**.")
                                        with open('guilds.json', 'w') as f:
                                            json.dump(cstmguild, f)
                                        try:
                                            DATABASE_URL = os.environ['DATABASE_URL']
                                            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                        except KeyError:
                                            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                        finally:
                                            cur = conn.cursor()
                                            cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                            conn.commit()
                                            cur.close()
                                            conn.close()
                                        return
                                    else:
                                        await ctx.send(f"**{ownertemp.name}** is the owner of '{temp.name}', __NOT__ **{ctx.author.name}**!\nCan not claim ownership unless owner is not in voice channel and it's not set to permanent.")
                                        return
                    if ctx.author.voice.channel.permissions_for(ctx.author).manage_channels == True:
                        mainvc = ''
                        for vcname in cstmguild[str(ctx.guild.id)]['VC']['AutoVC']:
                            vcid = self.bot.get_channel(int(vcname))
                            mainvc +=  vcid.name
                        def newvc(m):
                            return m.content and m.channel == chl and m.author == aut
                        try:
                            overwritecount = 0
                            while True:
                                overwritecount = overwritecount + 1
                                if overwritecount == 1:
                                    overmenu = await ctx.send(f"```\nWould you like to overwrite the main automated voice channel '{mainvc}' with the new voice channel '{ctx.author.voice.channel.name}'?\nDoing so will also use the '{ctx.channel.name.upper()}' channel for any of the bot's purposes.\n\n1.) Yes\n2.) No\n3.) Deprecate Main Automated Voice Channel: {mainvc} \n\nPlease enter one of the corresponding numbers.\n```")
                                autovcwait = await self.bot.wait_for('message', timeout=120, check=newvc)
                                if autovcwait.content == '1' or autovcwait.content.lower() == 'yes':
                                    await overmenu.delete()
                                    for oldvc in list(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']):
                                        del cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][oldvc]
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)] = {}
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Channel'] = ctx.channel.id
                                    cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Message'] = ctx.message.id
                                    await ctx.send(f"```\nCurrent voice channel '{ctx.author.voice.channel.name}' has been set to the main automated voice channel.\nPlease re-join the voice channel to put it into effect.\n```\n{menuexit}")
                                    await ctx.author.move_to(None)
                                    break
                                elif autovcwait.content == '2' or autovcwait.content.lower() == 'no':
                                    await overmenu.delete()
                                    await ctx.send(f"```\nMain automated voice channel '{mainvc}' has not been changed.\n```\n{menuexit}")
                                    break
                                elif autovcwait.content == '3' or autovcwait.content.lower() == 'deprecate main automated voice channel':
                                    await overmenu.delete()
                                    for oldvc in list(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']):
                                        del cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][oldvc]
                                    await ctx.send(f'```\nThere is no longer any main automated voice channel.\n```\n{menuexit}')
                                    break
                                elif autovcwait.content != '1' or autovcwait.content.lower() != 'yes' or autovcwait.content.lower() != '2' or autovcwait.content.lower() != 'no':
                                    await ctx.send('Please choose one of the corresponding numbers!')
                                    continue
                        except asyncio.TimeoutError:
                            await ctx.send(menutimeout)
                            return
                    else:
                        await ctx.send(f"`Manage Channel` permissions required to access automated voice channel menu for '{ctx.author.voice.channel.name}'!")
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f)
                try:
                    DATABASE_URL = os.environ['DATABASE_URL']
                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                except KeyError:
                    conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                finally:
                    cur = conn.cursor()
                    cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                    conn.commit()
                    cur.close()
                    conn.close()
            except AttributeError:
                # Work in progress
                if bool(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']) == False:
                    outautoempty = 'There is currently no automated voice channel.'
                else:
                    for outauto in cstmguild[str(ctx.guild.id)]['VC']['AutoVC']:
                        outgetvc = self.bot.get_channel(int(outauto))
                        outautoempty = f'Current automated voice channel: {outgetvc.name}'
                def outautofunc(m):
                    return m.content and m.channel == chl and m.author == aut
                try:
                    outfirst_menu = 0
                    while True:
                        outfirst_menu = outfirst_menu + 1
                        if outfirst_menu == 1:
                            outmenu = await ctx.send(f"```\n{outautoempty}\n\n1.) Work in progress\n\nPlease enter one of the corresponding numbers.\nType 'exit' to cancel settings.\n```")
                        outautowait = await self.bot.wait_for('message', timeout=120, check=outautofunc)
                        if outautowait.content == '1':
                            await outmenu.delete()
                            await ctx.send('work in progress')
                            return
                        if outautowait.content.lower() == 'exit':
                            await outmenu.delete()
                            await ctx.send(menuexit)
                            return
                        elif outautowait.content.lower() != 'exit':
                            await ctx.send('Please choose one of the corresponding numbers!')
                            continue
                except asyncio.TimeoutError:
                    await ctx.send(menutimeout)
                    return
        except discord.Forbidden:
            try:
                await ctx.send(MissingPerm)
            except:
                return

    @commands.command(name='Wg', help="User interface for setting up welcome and goodbye messages for users.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def wg(self, ctx):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        chl = ctx.channel
        aut = ctx.author
        def first_menu(m):
            return m.content and m.channel == chl and m.author == aut
        try:
            firstcount = 0
            while True:
                firstcount = firstcount + 1
                if firstcount == 1:
                    if bool(cstmguild[str(ctx.guild.id)]['Welcome']) == True:
                        for welcomequickchl in cstmguild[str(ctx.guild.id)]['Welcome']:
                            welcomegrabchl = self.bot.get_channel(int(welcomequickchl))
                        welcomechlname = welcomegrabchl.name
                    else:
                        welcomechlname = 'None'
                    if bool(cstmguild[str(ctx.guild.id)]['Goodbye']) == True:
                        for goodbyequickchl in cstmguild[str(ctx.guild.id)]['Goodbye']:
                            goodbyegrabchl = self.bot.get_channel(int(goodbyequickchl))
                        goodbyechlname = goodbyegrabchl.name
                    else:
                        goodbyechlname = 'None'
                    firstmenu = await ctx.send(f"```\nThe Welcome and Goodbye Annoucement Settings\n\n1.) Welcome Channel - Current: {welcomechlname} \n2.) Welcome Message\n3.) Goodbye Channel - Current: {goodbyechlname}\n4.) Goodbye Message\n\nPlease choose one of the corresponding numbers!\nType 'exit' to cancel settings.\n```")
                firstwait = await self.bot.wait_for('message', timeout=120, check=first_menu)
                if firstwait.content == '1':
                    await firstmenu.delete()
                    firstcount = 0
                    def welcome_menu(m):
                        return m.content and m.channel == chl and m.author == aut
                    welcomecount = 0
                    if bool(cstmguild[str(ctx.guild.id)]['Welcome']) == True:
                        removeoption = "Type 'remove' to get rid of welcome channel.\n"
                    else:
                        removeoption = ""
                    while True:
                        welcomecount = welcomecount + 1
                        if welcomecount == 1:
                            welcomemenu = await ctx.send(f"```\nPlease enter a valid channel either by mention, ID, etc. that you wish to be the welcome channel\n\n{removeoption}Type 'back' to go back.\nType 'exit' to cancel settings.\n```")
                        welcomewait = await self.bot.wait_for('message', timeout=120, check=welcome_menu)
                        for allchannel in ctx.guild.channels:
                            if welcomewait.content == allchannel.mention or welcomewait.content == str(allchannel.id) or welcomewait.content == allchannel.name:
                                await welcomemenu.delete()
                                await ctx.send(f"```\n'{allchannel.name}' has been set as the welcome channel!\nDon't forget to set a welcome message.\n```\n{menuexit}")
                                if bool(cstmguild[str(ctx.guild.id)]['Welcome']) == False:
                                    cstmguild[str(ctx.guild.id)]['Welcome'][allchannel.id] = "Welcome **{}**!"
                                else:
                                    for replacechl in list(cstmguild[str(ctx.guild.id)]['Welcome']):
                                        cstmguild[str(ctx.guild.id)]['Welcome'][allchannel.id] = cstmguild[str(ctx.guild.id)]['Welcome'][replacechl]
                                        del cstmguild[str(ctx.guild.id)]['Welcome'][replacechl]
                                with open('guilds.json', 'w') as f:
                                    json.dump(cstmguild, f)
                                try:
                                    DATABASE_URL = os.environ['DATABASE_URL']
                                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                except KeyError:
                                    conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                finally:
                                    cur = conn.cursor()
                                    cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                return
                        if welcomewait.content == 'remove':
                            if bool(cstmguild[str(ctx.guild.id)]['Welcome']) == True:
                                await welcomemenu.delete()
                                for welcomedelchl in list(cstmguild[str(ctx.guild.id)]['Welcome']):
                                    welcomedelname = self.bot.get_channel(int(welcomedelchl))
                                    await ctx.send(f"```\n'{welcomedelname.name}' will no longer receive welcome messages!\n```\n{menuexit}")
                                    del cstmguild[str(ctx.guild.id)]['Welcome'][welcomedelchl]
                                with open('guilds.json', 'w') as f:
                                    json.dump(cstmguild, f)
                                try:
                                    DATABASE_URL = os.environ['DATABASE_URL']
                                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                except KeyError:
                                    conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                finally:
                                    cur = conn.cursor()
                                    cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                return
                        elif welcomewait.content == 'back':
                            await welcomemenu.delete()
                            break
                        elif welcomewait.content == 'exit':
                            await welcomemenu.delete()
                            await ctx.send(menuexit)
                            return
                        if firstwait.content == 'remove' and bool(cstmguild[str(ctx.guild.id)]['Welcome']) == False or welcomewait.content != allchannel.mention or welcomewait.content != str(allchannel.id) or welcomewait.content != allchannel.name or welcomewait.content != 'back' or welcomewait.content != 'exit':
                            await ctx.send('Please enter a valid channel!')
                            continue
                elif firstwait.content == '2':
                    await firstmenu.delete()
                    firstcount = 0
                    def welcomemsg_menu(m):
                        return m.content and m.channel == chl and m.author == aut
                    welcomemsgcount = 0
                    while True:
                        welcomemsgcount = welcomemsgcount + 1
                        if welcomemsgcount == 1:
                            for welcomelist in cstmguild[str(ctx.guild.id)]['Welcome']:
                                getwelcome = self.bot.get_channel(int(welcomelist))
                            welcomemsgmenu = await ctx.send(f"```\nPlease enter a message to be the welcome message for the '{getwelcome.name}' channel.\n\nType 'embed' to make your welcome message an embed.\nType 'reset' to reset the welcome message.\nType 'back' to go back.\nType 'exit' to cancel settings.\n```\nCurrent welcome message:\n{cstmguild[str(ctx.guild.id)]['Welcome'][welcomelist]}")
                        welcomemsgwait = await self.bot.wait_for('message', timeout=300, check=welcomemsg_menu)
                        if welcomemsgwait.content.lower() == 'embed':
                            await welcomemsgmenu.delete()
                            await ctx.send('work in progress')
                            return
                        elif welcomemsgwait.content.lower() == 'reset':
                            await welcomemsgmenu.delete()
                            cstmguild[str(ctx.guild.id)]['Welcome'][welcomelist] = "Welcome {}!"
                            await ctx.send(f"```\nWelcome message has been set back to default:\n```\n{cstmguild[str(ctx.guild.id)]['Welcome'][welcomelist]}\n\n{menuexit}")
                            with open('guilds.json', 'w') as f:
                                json.dump(cstmguild, f)
                            try:
                                DATABASE_URL = os.environ['DATABASE_URL']
                                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                            except KeyError:
                                conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                            finally:
                                cur = conn.cursor()
                                cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                conn.commit()
                                cur.close()
                                conn.close()
                            return
                        elif welcomemsgwait.content.lower() == 'back':
                            await welcomemsgmenu.delete()
                            break
                        elif welcomemsgwait.content.lower() == 'exit':
                            await welcomemsgmenu.delete()
                            await ctx.send(menuexit)
                            return
                        elif welcomemsgwait.content.lower() != 'reset' or welcomemsgwait.content.lower() != 'back' or welcomemsgwait.content.lower() != 'exit':
                            await welcomemsgmenu.delete()
                            await ctx.send(f"```\nWelcome message set!\n```\n{welcomemsgwait.content}\n\n{menuexit}")
                            cstmguild[str(ctx.guild.id)]['Welcome'][welcomelist] = welcomemsgwait.content
                            with open('guilds.json', 'w') as f:
                                json.dump(cstmguild, f)
                            try:
                                DATABASE_URL = os.environ['DATABASE_URL']
                                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                            except KeyError:
                                conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                            finally:
                                cur = conn.cursor()
                                cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                conn.commit()
                                cur.close()
                                conn.close()
                            return
                elif firstwait.content == '3':
                    await firstmenu.delete()
                    firstcount = 0
                    def goodbye_menu(m):
                        return m.content and m.channel == chl and m.author == aut
                    goodbyecount = 0
                    if bool(cstmguild[str(ctx.guild.id)]['Goodbye']) == True:
                        removeoption = "Type 'remove' to get rid of goodbye channel.\n"
                    else:
                        removeoption = ""
                    while True:
                        goodbyecount = goodbyecount + 1
                        if goodbyecount == 1:
                            goodbyemenu = await ctx.send(f"```\nPlease enter a valid channel either by mention, ID, etc. that you wish to be the goodbye channel\n\n{removeoption}Type 'back' to go back.\nType 'exit' to cancel settings.\n```")
                        goodbyewait = await self.bot.wait_for('message', timeout=120, check=goodbye_menu)
                        for allchannel in ctx.guild.channels:
                            if goodbyewait.content == allchannel.mention or goodbyewait.content == str(allchannel.id) or goodbyewait.content == allchannel.name:
                                await goodbyemenu.delete()
                                await ctx.send(f"```\n'{allchannel.name}' has been set as the goodbye channel!\nDon't forget to set a goodbye message.\n```\n{menuexit}")
                                if bool(cstmguild[str(ctx.guild.id)]['Goodbye']) == False:
                                    cstmguild[str(ctx.guild.id)]['Goodbye'][allchannel.id] = "Goodbye **{}**!"
                                else:
                                    for replacechl in list(cstmguild[str(ctx.guild.id)]['Goodbye']):
                                        cstmguild[str(ctx.guild.id)]['Goodbye'][allchannel.id] = cstmguild[str(ctx.guild.id)]['Goodbye'][replacechl]
                                        del cstmguild[str(ctx.guild.id)]['Goodbye'][replacechl]
                                with open('guilds.json', 'w') as f:
                                    json.dump(cstmguild, f)
                                try:
                                    DATABASE_URL = os.environ['DATABASE_URL']
                                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                except KeyError:
                                    conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                finally:
                                    cur = conn.cursor()
                                    cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                return
                        if goodbyewait.content == 'remove':
                            if bool(cstmguild[str(ctx.guild.id)]['Goodbye']) == True:
                                await goodbyemenu.delete()
                                for goodbyedelchl in list(cstmguild[str(ctx.guild.id)]['Goodbye']):
                                    goodbyedelname = self.bot.get_channel(int(goodbyedelchl))
                                    await ctx.send(f"```\n'{goodbyedelname.name}' will no longer receive goodbye messages!\n```\n{menuexit}")
                                    del cstmguild[str(ctx.guild.id)]['Goodbye'][goodbyedelchl]
                                with open('guilds.json', 'w') as f:
                                    json.dump(cstmguild, f)
                                try:
                                    DATABASE_URL = os.environ['DATABASE_URL']
                                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                                except KeyError:
                                    conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
                                finally:
                                    cur = conn.cursor()
                                    cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                return
                        elif goodbyewait.content == 'back':
                            await goodbyemenu.delete()
                            break
                        elif goodbyewait.content == 'exit':
                            await goodbyemenu.delete()
                            await ctx.send(menuexit)
                            return
                        if goodbyewait.content != allchannel.mention or goodbyewait.content != str(allchannel.id) or goodbyewait.content != allchannel.name or goodbyewait.content != 'back' or goodbyewait.content != 'exit':
                            await ctx.send('Please enter a valid channel!')
                            continue
                elif firstwait.content == '4':
                    await ctx.send('work in progress')
                    return
                elif firstwait.content == 'exit':
                    await firstmenu.delete()
                    await ctx.send(menuexit)
                    return
                elif firstwait.content == 'remove' and bool(cstmguild[str(ctx.guild.id)]['Goodbye']) == False or firstwait.content != '1' or firstwait.content != '2' or firstwait.content != '3' or firstwait.content != '4':
                    await ctx.send('Please choose one of the corresponding numbers!')
                    continue
        except asyncio.TimeoutError:
            await ctx.send(menutimeout)
            return
    @wg.error
    async def wg_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("This command requires the user to have `Manage Channel` permissions to use.")

def setup(bot):
    bot.add_cog(Settings(bot))