import discord
from discord.ext import commands
from postgresql import database
from progression import experience

class events(commands.Cog):

    # Status: Work in progress

    # So far manages server IDs when joining and leaving guilds
    # More needs to be added in here later

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        db = database()
        db.connect()
        try:
            xp = experience(db)
            xp.initialize(message)
            xp.message(message)
        finally:
            db.close()

def setup(bot):
    bot.add_cog(events(bot))