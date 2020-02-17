import json
from discord.ext import commands

TestServerEmoji = "<:IDontKnowThatCommand:676544628274757633>" # Emoji is from the test server. Anime girl with question marks.

class Events(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        await guild_data(cstmguild, guild.owner)
        if not str(guild.id) in cstmguild:
            cstmguild[str(guild.id)] = {}
        with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f, indent=4)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        await guild_data(cstmguild, guild.owner)
        for removeguild in list(cstmguild):
            if self.bot.get_guild(int(removeguild)) == None:
                del cstmguild[removeguild]
        with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f, indent=4)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(TestServerEmoji)
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"{ctx.command} can not be used in DMs.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument!")
        elif isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
        elif hasattr(ctx.command, 'on_error'):
            return
        else:
            raise error

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
    async def on_message_delete(self, message):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        for automsg in cstmguild[str(message.guild.id)]['VC']['AutoVC']:
            if cstmguild[str(message.guild.id)]['VC']['AutoVC'][automsg]['Message'] == message.id:
                cstmguild[str(message.guild.id)]['VC']['AutoVC'][automsg]['Message'] = False
            with open('guilds.json', 'w') as f:
                json.dump(cstmguild, f, indent=4)

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        try:
            with open('guilds.json', 'r') as f:
                cstmguild = json.load(f)
            await guild_data(cstmguild, user)
            with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
        except AttributeError:
            return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
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
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
        for dellist in list(cstmguild[str(member.guild.id)]['VC']['VCList']):
            vclist = self.bot.get_channel(int(dellist))
            for delmember in list(cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]):
                #ownerid = member.guild.get_member(int(delmember))
                cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] = len(vclist.members)
                if cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] == 0 and cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Static'] == False:
                    if before.channel == vclist:
                        await before.channel.delete(reason='VC is empty.')
                    elif after.channel == vclist:
                        await after.channel.delete(reason='VC is empty.')
                    del cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]
                with open('guilds.json', 'w') as f:
                    json.dump(cstmguild, f, indent=4)
                #for msgctx in cstmguild[str(member.guild.id)]['VC']['AutoVC']:
                #    if after.channel == vclist and member.id == ownerid.id and cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['AutoMenu'] == True and cstmguild[str(member.guild.id)]['VC']['AutoVC'][msgctx]['Message'] != False:
                #        ctxchl = self.bot.get_channel(int(cstmguild[str(member.guild.id)]['VC']['AutoVC'][msgctx]['Channel']))
                #        getcmd = self.bot.get_command('vc')
                #        getmsgctx = await ctxchl.fetch_message(int(cstmguild[str(member.guild.id)]['VC']['AutoVC'][msgctx]['Message'])) # Only applies to the one that ran the command | Fix this
                #        ctxmsg = await self.bot.get_context(getmsgctx)
                #        await ctxmsg.invoke(getcmd)

async def guild_data(cstmguild, user):
    if not str(user.guild.id) in cstmguild:
        cstmguild[str(user.guild.id)] = {}
    if not 'VC' in cstmguild[str(user.guild.id)]:
        cstmguild[str(user.guild.id)]['VC'] = {}
    if not 'AutoVC' in cstmguild[str(user.guild.id)]['VC']:
        cstmguild[str(user.guild.id)]['VC']['AutoVC'] = {}
    if not 'VCList' in cstmguild[str(user.guild.id)]['VC']:
        cstmguild[str(user.guild.id)]['VC']['VCList'] = {}
    if not 'Custom Prefix' in cstmguild[str(user.guild.id)]:
        cstmguild[str(user.guild.id)]['Custom Prefix'] = 'v.'

def setup(bot):
    bot.add_cog(Events(bot))