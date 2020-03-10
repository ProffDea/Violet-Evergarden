import json
import psycopg2
import os
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

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        for removeguild in list(cstmguild):
            if self.bot.get_guild(int(removeguild)) == None:
                del cstmguild[removeguild]
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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        if bool(cstmguild[str(member.guild.id)]['Welcome']) == True:
            for welcomechl in cstmguild[str(member.guild.id)]['Welcome']:
                sendchl = self.bot.get_channel(int(welcomechl))
                await sendchl.send(cstmguild[str(member.guild.id)]['Welcome'][welcomechl].format(member.mention))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        if bool(cstmguild[str(member.guild.id)]['Goodbye']) == True:
            for goodbyechl in cstmguild[str(member.guild.id)]['Goodbye']:
                sendchl = self.bot.get_channel(int(goodbyechl))
                await sendchl.send(cstmguild[str(member.guild.id)]['Goodbye'][goodbyechl].format(str(member)))

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
                    json.dump(cstmguild, f)
        for autovc in list(cstmguild[str(channel.guild.id)]['VC']['AutoVC']):
            if self.bot.get_channel(int(autovc)) == None:
                del cstmguild[str(channel.guild.id)]['VC']['AutoVC'][autovc]
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

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        for automsg in cstmguild[str(message.guild.id)]['VC']['AutoVC']:
            if cstmguild[str(message.guild.id)]['VC']['AutoVC'][automsg]['Message'] == message.id:
                cstmguild[str(message.guild.id)]['VC']['AutoVC'][automsg]['Message'] = False
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
                    json.dump(cstmguild, f)
        for dellist in list(cstmguild[str(member.guild.id)]['VC']['VCList']):
            vclist = self.bot.get_channel(int(dellist))
            if before.channel == vclist or after.channel == vclist:
                for delmember in list(cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]):
                    cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] = len(vclist.members)
                    if cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Members'] == 0 and cstmguild[str(member.guild.id)]['VC']['VCList'][dellist][delmember]['Static'] == False:
                        if before.channel == vclist:
                            await before.channel.delete(reason='VC is empty.')
                        elif after.channel == vclist:
                            await after.channel.delete(reason='VC is empty.')
                        del cstmguild[str(member.guild.id)]['VC']['VCList'][dellist]
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
    if not 'Welcome' in cstmguild[str(user.guild.id)]:
        cstmguild[str(user.guild.id)]['Welcome'] = {}
    if not 'Goodbye' in cstmguild[str(user.guild.id)]:
        cstmguild[str(user.guild.id)]['Goodbye'] = {}

def setup(bot):
    bot.add_cog(Events(bot))