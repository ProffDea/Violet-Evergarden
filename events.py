import discord
from discord.ext import commands
from postgresql import database

class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        db = database()
        db.connect()
        try:
            db.cur.execute(f'''
                INSERT INTO guilds (guild)
                VALUES
                        ('{guild.id}')
                ON CONFLICT (guild)
                DO NOTHING;
                ''')
        finally:
            db.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        db = database()
        db.connect()
        try:
            db.cur.execute(f'''
                DELETE FROM guilds
                WHERE guild = '{guild.id}';
                ''')
        finally:
            db.close()

def setup(bot):
    bot.add_cog(events(bot))