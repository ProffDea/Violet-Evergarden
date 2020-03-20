import json, os, psycopg2
from discord.ext import commands

TestServerEmoji = "<:IDontKnowThatCommand:676544628274757633>" # Emoji is from the test server. Anime girl with question marks.

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
            await ctx.send(TestServerEmoji)
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
            cur = conn.cursor()
            cur.execute(f"SELECT autovc FROM servers WHERE guild = '{channel.guild.id}';")
            vcs = cur.fetchall()
            for v in vcs:
                if v[0] == None:
                    break
                else:
                    if self.bot.get_channel(v[0]) == None:
                        cur.execute(f"UPDATE servers SET autovc = NULL WHERE guild = '{v[0]}'")
                        break
            cur.execute("SELECT voicechl FROM vclist;")
            vclistall = cur.fetchall()
            for vl in vclistall:
                if vl[0] == None:
                    break
                else:
                    if self.bot.get_channel(vl[0]) == None:
                        cur.execute(f"DELETE FROM vclist WHERE voicechl = '{vl[0]}';")
                        break
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
            cur = conn.cursor()
            if after.channel:
                cur.execute(f"SELECT autovc FROM servers WHERE guild = '{member.guild.id}';")
                vcs = cur.fetchall()
                for v in vcs:
                    if v[0] == None:
                        break
                    else:
                        autovc = self.bot.get_channel(v[0])
                        cur.execute("SELECT voicechl, owner, members, static FROM vclist;")
                        rows = cur.fetchall()
                        for r in rows:
                            if after.channel == autovc and r[1] == member.id and r[2] == 0 and r[3] == True:
                                vcclone = self.bot.get_channel(r[0])
                                await member.move_to(vcclone)
                                return
                        if after.channel == autovc:
                            vcclone = await autovc.clone(name=f'💌{member.name}', reason=f"{member.name} has created this VC.")
                            cur.execute(f"INSERT INTO vclist (voicechl, owner, members, static) VALUES ('{vcclone.id}', '{member.id}', '1', 'FALSE');")
                            await vcclone.edit(reason='Moving', position=autovc.position + 1)
                            await member.move_to(vcclone)
                            break
                        else:
                            break
            if after.channel or before.channel:
                cur.execute(f"SELECT voicechl, members, static FROM vclist;")
                vclistall = cur.fetchall()
                for vl in vclistall:
                    if vl[0] == None:
                        break
                    else:
                        vclist = self.bot.get_channel(vl[0])
                        if before.channel == vclist or after.channel == vclist:
                            cur.execute(f"UPDATE vclist SET members = '{len(vclist.members)}' WHERE voicechl = '{vl[0]}';")
                            conn.commit()
                            cur.execute("SELECT voicechl, members, static FROM vclist;")
                            vcinside = cur.fetchall()
                            for vi in vcinside:
                                if vi[1] == 0 and vi[2] == False:
                                    if before.channel == vclist:
                                        await before.channel.delete(reason='VC is empty.')
                                    elif after.channel == vclist:
                                        await after.channel.delete(reason='VC is empty.')
            conn.commit()
            cur.close()
            conn.close()

def setup(bot):
    bot.add_cog(Events(bot))