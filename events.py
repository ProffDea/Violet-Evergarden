import json
from discord.ext import commands

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
            await ctx.send("<:IDontKnowThatCommand:676544628274757633>") # Emoji is from the test server. Anime girl with question marks.
            return
        if hasattr(ctx.command, 'on_error'):
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
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        await guild_data(cstmguild, user)
        with open('guilds.json', 'w') as f:
                json.dump(cstmguild, f, indent=4)

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