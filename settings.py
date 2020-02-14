import json
import asyncio
import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name='Prefix', help='Allows to change the default prefix to a custom one.')
    @commands.guild_only()
    async def prefix(self, ctx, changeprefix):
        if ctx.channel.permissions_for(ctx.author).manage_guild == True:
            if len(changeprefix) <= 9:
                with open('guilds.json', 'r') as f:
                    cstmguild = json.load(f)
                cstmguild[str(ctx.guild.id)]['Custom Prefix'] = changeprefix
                await ctx.send(f"Prefix for `{ctx.guild.name}` has been changed to **{changeprefix}**")
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
            else:
                await ctx.send("Please make the prefix less than 10 characters long.")
        else:
            await ctx.send("This command requires `Manage Server` permissions to use.")
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

    @commands.command(name='Status', help="Changes bot's status message.")
    @commands.guild_only()
    async def status(self, ctx, *, changestatus):
        if len(changestatus) <= 128:
            if 'https://' in changestatus:
                await ctx.send('No links.')
            else:
                with open('guilds.json', 'r') as f:
                    cstmguild = json.load(f)
                if not 'Custom Status' in cstmguild[str(648977487744991233)]: # ID is the test server ID. Feel free to change it
                    cstmguild[str(648977487744991233)]['Custom Status'] = ''
                cstmguild[str(648977487744991233)]['Custom Status'] = changestatus
                await self.bot.change_presence(activity=discord.Game(changestatus))
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
        else:
            await ctx.send(f"Character limit is 128. You reached {len(changestatus)} characters.")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        for vclist in list(cstmguild[str(channel.guild.id)]['VC']['VCList']):
            if self.bot.get_channel(int(vclist)) == None:
                del cstmguild[str(channel.guild.id)]['VC']['VCList'][vclist]
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
        for autovc in list(cstmguild[str(channel.guild.id)]['VC']['AutoVC']):
            if self.bot.get_channel(int(autovc)) == None:
                del cstmguild[str(channel.guild.id)]['VC']['AutoVC'][autovc]
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        #chl = self.bot.get_channel(648977488202039297)
        await guild_data(cstmguild, member)
        for automain in cstmguild[str(member.guild.id)]['VC']['AutoVC']:
            autovc = self.bot.get_channel(int(automain))
            if after.channel == autovc:
                vcclone = await autovc.clone(name=f'💌{member.name}', reason=f"{member.name} has created this VC.")
                cstmguild[str(member.guild.id)]['VC']['VCList'][str(vcclone.id)] = {}
                cstmguild[str(member.guild.id)]['VC']['VCList'][str(vcclone.id)][str(member.id)] = {}
                cstmguild[str(member.guild.id)]['VC']['VCList'][str(vcclone.id)][str(member.id)]['Members'] = 1
                cstmguild[str(member.guild.id)]['VC']['VCList'][str(vcclone.id)][str(member.id)]['Static'] = False # False = not permanent VC | True = Permanent VC
                cstmguild[str(member.guild.id)]['VC']['VCList'][str(vcclone.id)][str(member.id)]['AutoMenu'] = True # True = Bring up menu upon joining | False = Do not bring up menu upon joining
                await vcclone.edit(reason='Moving', position=autovc.position + 1)
                await member.move_to(vcclone)
        for dellist in list(cstmguild[str(member.guild.id)]['VC']['VCList']):
            vclist = self.bot.get_channel(int(dellist))
            for delmember in cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]:
                #ownerid = member.guild.get_member(int(delmember))
                cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] = len(vclist.members)
                if cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] == 0 and cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Static'] == False:
                    del cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]
                    await vclist.delete(reason='VC is empty.')
                #if after.channel == vclist and member.id == ownerid.id and cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['AutoMenu'] == True:
                    # Do Stuff Here
        with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f, indent=4)

    @commands.command(name='Vc', help='Views settings for current voice channel. (Work in Progress)') # False = empty | True = not empty
    @commands.guild_only()
    async def vc(self, ctx):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        await guild_data(cstmguild, ctx.author)
        try:
            chl = ctx.channel
            aut = ctx.author
            if bool(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']) == False:
                if ctx.author.voice.channel.permissions_for(ctx.author).manage_channels == True:
                    def autovc(m):
                        return m.content and m.channel == chl and m.author == aut
                    try:
                        startcount = 0
                        while True:
                            startcount = startcount + 1
                            if startcount == 1:
                                startmenu = await ctx.send(f"```\nWould you like the current VC '{ctx.author.voice.channel.name}' to be the main automated voice channel?\n\n1.) Yes\n2.) No\n\nPlease enter one of the corresponding numbers.\n```")
                            autovcwait = await self.bot.wait_for('message', timeout=30, check=autovc)
                            if autovcwait.content.lower() == '1' or autovcwait.content.lower() == 'yes':
                                await startmenu.delete()
                                await ctx.send(f"```\nCurrent voice channel '{ctx.author.voice.channel.name}' has been set to the main automated voice channel.\nPlease re-join the voice channel to put it into effect.\n```\nMenu has been exited.")
                                #await ctx.author.move_to(None)
                                cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)] = {}
                                cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Channel'] = ctx.channel.id
                                break
                            elif autovcwait.content.lower() == '2' or autovcwait.content.lower() == 'no':
                                await startmenu.delete()
                                await ctx.send('```\nThere is currently no automated voice channel set.\n```\nMenu has been exited.')
                                break
                            elif autovcwait.content.lower() != '1' or autovcwait.content.lower() != 'yes' or autovcwait.content.lower() != '2' or autovcwait.content.lower() != 'no':
                                await ctx.send('Please choose one of the corresponding numbers!')
                                continue
                    except asyncio.TimeoutError:
                        await ctx.send('Menu has been exited due to timeout.')
                        return
                else:
                    await ctx.send(f"`Manage Channel` permissions required to access automated voice channel menu for '{ctx.author.voice.channel.name}'!")
            elif bool(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']) == True:
                for lelist in cstmguild[str(ctx.guild.id)]['VC']['VCList']:
                    temp = self.bot.get_channel(int(lelist))
                    if temp.id == ctx.author.voice.channel.id:
                        for leowner in cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist]:
                            ownertemp = ctx.guild.get_member(int(leowner))
                            if ownertemp.id == ctx.author.id:
                                if cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["Static"] == False:
                                    staticmsg = "Permanent VC is Disabled"
                                    staticstatus = True
                                    staticend = f"```\n'{temp.name}' is now a permanent voice channel.\nIt will not be deleted when the voice channel is empty.\n```\nMenu has been exited."
                                else:
                                    staticmsg = "Permanent VC is Enabled"
                                    staticstatus = False
                                    staticend = f"```\n'{temp.name}' is no longer a permanent voice channel.\nIt will get deleted when the voice channel is empty.\n```\nMenu has been exited."
                                if cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["AutoMenu"] == True:
                                    automenumsg = "Quick Menu is Turned On"
                                    automenustatus = False
                                    automenuend = f"```\n'{temp.name}' will no longer bother the owner whenever they join.\nIt will not bring up the menu for the owner and not mention them when they join.\n```\nMenu has been exited."
                                else:
                                    automenumsg = "Quick Menu is Turned Off"
                                    automenustatus = True
                                    automenuend = f"```\n'{temp.name}' will now bother the owner whenever they join.\nIt will bring up the menu for the owner and mention them when they join.\n```\nMenu has been exited."
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
                                            first_menu = await ctx.send(f"```\nVoice channel - {temp.name} | Owner - {ctx.author}\n\n1.) User Limit - Current: {userlimit}\n2.) Change Name - Current: {temp.name}\n3.) {staticmsg}\n4.) {automenumsg}\n\nPlease enter one of the corresponding numbers.\nType 'exit' to cancel settings.\n```")
                                        waitsetting = await self.bot.wait_for('message', timeout=30, check=settings)
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
                                                userlimit = await self.bot.wait_for('message', timeout=30, check=setlimit)
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
                                                            await ctx.send(f"```\n'{temp.name}' user limit has been set to {afternumber}!\n```\nMenu has been exited.")
                                                            return
                                                elif userlimit.content.lower() == 'exit':
                                                    await limit_menu.delete()
                                                    await ctx.send('```\nMenu has been exited.\n```')
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
                                                changename = await self.bot.wait_for('message', timeout=30, check=setname)
                                                if changename.content.lower() == 'exit':
                                                    await name_menu.delete()
                                                    await ctx.send('Menu has been exited.')
                                                    return
                                                elif changename.content.lower() == 'back':
                                                    await name_menu.delete()
                                                    break
                                                elif changename.content.lower() != 'exit' or changename.content.lower() != 'back':
                                                    await name_menu.delete()
                                                    await temp.edit(reason='Change name', name=changename.content)
                                                    await ctx.send(f"```\nVoice channel's name has been changed to '{temp.name}'\n```\nMenu has been exited.")
                                                    return
                                        elif waitsetting.content == '3' or waitsetting.content.lower() == staticmsg:
                                            await first_menu.delete()
                                            cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]["Static"] = staticstatus
                                            await ctx.send(staticend)
                                            with open('guilds.json', 'w') as f:
                                                json.dump(cstmguild, f, indent=4)
                                            return
                                        elif waitsetting.content == '4' or waitsetting.content.lower() == automenumsg:
                                            await first_menu.delete()
                                            cstmguild[str(ctx.guild.id)]['VC']['VCList'][lelist][leowner]['AutoMenu'] = automenustatus
                                            await ctx.send(automenuend)
                                            with open('guilds.json', 'w') as f:
                                                json.dump(cstmguild, f, indent=4)
                                            return
                                        elif waitsetting.content.lower() == 'exit':
                                            await first_menu.delete()
                                            await ctx.send('Menu has been exited.')
                                            return
                                        elif waitsetting.content != '1' or waitsetting.content.lower() != 'user limit' or waitsetting.content.lower() != 'exit' or waitsetting.content.lower() != 'back':
                                            await ctx.send('Please choose one of the corresponding numbers!')
                                            continue
                                except asyncio.TimeoutError:
                                    await ctx.send('Menu has been exited due to timeout.')
                                    return
                            elif ownertemp.id != ctx.author.id:
                                await ctx.send(f"**{ownertemp.name}** is the owner of '{temp.name}', not **{ctx.author.name}**!\n```")
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
                                overmenu = await ctx.send(f"```\nWould you like to overwrite the main automated voice channel '{mainvc}' with the new voice channel '{ctx.author.voice.channel.name}'?\n\n1.) Yes\n2.) No\n3.) Deprecate Main Automated Voice Channel: {mainvc} \n\nPlease enter one of the corresponding numbers.\n```")
                            autovcwait = await self.bot.wait_for('message', timeout=30, check=newvc)
                            if autovcwait.content.lower() == '1' or autovcwait.content.lower() == 'yes':
                                await overmenu.delete()
                                for oldvc in list(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']):
                                    del cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][oldvc]
                                cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)] = {}
                                cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][str(ctx.author.voice.channel.id)]['Channel'] = ctx.channel.id
                                await ctx.send(f"```\nCurrent voice channel '{ctx.author.voice.channel.name}' has been set to the main automated voice channel.\nPlease re-join the voice channel to put it into effect.\n```\nMenu has been exited.")
                                #await ctx.author.move_to(None)
                                break
                            elif autovcwait.content.lower() == '2' or autovcwait.content.lower() == 'no':
                                await overmenu.delete()
                                await ctx.send(f"```\nMain automated voice channel '{mainvc}' has not been changed.\n```\nMenu has been exited.")
                                break
                            elif autovcwait.content.lower() == '3' or autovcwait.content.lower() == 'deprecate main automated voice channel':
                                await overmenu.delete()
                                for oldvc in list(cstmguild[str(ctx.guild.id)]['VC']['AutoVC']):
                                    del cstmguild[str(ctx.guild.id)]['VC']['AutoVC'][oldvc]
                                await ctx.send('```\nThere is no longer any main automated voice channel.\n```\nMenu has been exited.')
                                break
                            elif autovcwait.content.lower() != '1' or autovcwait.content.lower() != 'yes' or autovcwait.content.lower() != '2' or autovcwait.content.lower() != 'no':
                                await ctx.send('Please choose one of the corresponding numbers!')
                                continue
                    except asyncio.TimeoutError:
                        await ctx.send('Menu has been exited due to timeout.')
                        return
                else:
                    await ctx.send(f"`Manage Channel` permissions required to access automated voice channel menu for '{ctx.author.voice.channel.name}'!")
            with open('guilds.json', 'w') as f:
                json.dump(cstmguild, f, indent=4)
        except AttributeError:
            await ctx.send('This command requires the user to be in a voice channel!')

async def guild_data(cstmguild, user):
    if not str(user.guild.id) in cstmguild:
        cstmguild[str(user.guild.id)] = {}
    if not 'VC' in cstmguild[str(user.guild.id)]:
        cstmguild[str(user.guild.id)]['VC'] = {}
    if not 'AutoVC' in cstmguild[str(user.guild.id)]['VC']:
        cstmguild[str(user.guild.id)]['VC']['AutoVC'] = {}
    if not 'VCList' in cstmguild[str(user.guild.id)]['VC']:
        cstmguild[str(user.guild.id)]['VC']['VCList'] = {}

def setup(bot):
    bot.add_cog(Settings(bot))