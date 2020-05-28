import json, os, psycopg2
from discord.ext import commands

def TestServerEmoji():
    return "<:IDontKnowThatCommand:676544628274757633>" # Emoji is from the test server. Anime girl with question marks.

class Events(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            cur.execute(f"INSERT INTO servers (guild, prefix) VALUES ('{guild.id}', 'v.') ON CONFLICT (guild) DO NOTHING;")
            conn.commit()
            cur.close()
            conn.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM servers WHERE guild = '{guild.id}';")
            conn.commit()
            cur.close()
            conn.close()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(TestServerEmoji())
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"**{ctx.command}** can not be used in DMs.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument!")
        elif isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            cool = await ctx.send(error)
            await cool.delete(delay=5)
        else:
            raise error

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT autovc FROM servers WHERE guild = '{channel.guild.id}';")
                autovc = cur.fetchall()
                for a in autovc:
                    if a[0] == None:
                        break
                    elif self.bot.get_channel(a[0]) == None:
                        cur.execute(f"UPDATE servers SET autovc = NULL WHERE guild = '{a[0]}'")
                        return
                cur.execute("SELECT voicechl FROM vclist;")
                vclist = cur.fetchall()
                for vl in vclist:
                    if self.bot.get_channel(vl[0]) == None:
                        cur.execute(f"DELETE FROM vclist WHERE voicechl = '{vl[0]}';")
                        return
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute("SELECT voicechl FROM vclist;")
                vclist = cur.fetchall()
                cur.execute(f"SELECT autovc FROM servers WHERE guild = '{member.guild.id}';")
                autovc = cur.fetchall()
                if after.channel == None: # Checking if hard disconnecting
                    pass
                elif before.channel == None or [item for item in autovc if after.channel.id in item] and before.channel != None: # Triggers on joining a channel or an autovc except for hard disconnects
                    if [item for item in autovc if after.channel.id in item]: # Triggers on hard joining autovc or moving to autovc
                        clone = await after.channel.clone(name=f'💌{member.name}', reason=f"{member.name} has created this VC.")
                        cur.execute(f"INSERT INTO vclist (voicechl, owner, static) VALUES ('{clone.id}', '{member.id}', 'FALSE');")
                        await member.move_to(clone)
                if before.channel == None: # Checking if hard joining
                    pass
                elif after.channel != None and before.channel != None and [item for item in vclist if before.channel.id in item] or after.channel == None and [item for item in vclist if before.channel.id in item]: # Triggers on moving out of VC or hard disconnecting from VC
                    cur.execute(f"SELECT static FROM vclist WHERE voicechl = '{before.channel.id}';")
                    static = cur.fetchall()
                    if len(before.channel.members) == 0 and [item for item in static if item[0] == False]: # Triggers on empty and non-permanent VC
                        await before.channel.delete(reason='VC is empty.')
                    return
            finally:
                conn.commit()
                cur.close()
                conn.close()

def setup(bot):
    bot.add_cog(Events(bot))