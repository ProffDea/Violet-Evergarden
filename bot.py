import os
import discord
import __main__
import time
from discord.ext import commands
from dotenv import load_dotenv
from postgresql import database

def custom_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or('v.')(bot, message)
    else:
        db = database()
        db.connect()
        try:
            db.cur.execute(f'''
                SELECT
                    guild,
                    prefix
                FROM
                    guilds
                WHERE
                    guild = '{message.guild.id}';
            ''')
            db_guild = db.cur.fetchall()
            guild_prefix = db_guild[0][1] if message.guild.id == db_guild[0][0] else 'v.'
            return commands.when_mentioned_or(guild_prefix)(bot, message)
        finally:
            db.close()

bot = commands.Bot(command_prefix=custom_prefix, description='Violet Evergarden Overhaul', case_insensitive=True)
bot.startup_time = time.time()

for cog in ['events', 'utility', 'games']:
    try:
        bot.load_extension(cog)
    except Exception as error:
        print(f'Failed to load {cog}\n{error}')

@bot.event
async def on_ready():
    db = database()
    db.connect()
    try:
        db.cur.execute('''
            CREATE TABLE IF NOT EXISTS bot (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    name TEXT UNIQUE,
                    message TEXT
            );

            INSERT INTO bot (name)
            VALUES
                    ('Bot Status Message')
            ON CONFLICT (name)
            DO NOTHING;

            CREATE TABLE IF NOT EXISTS guilds (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    guild BIGINT UNIQUE NOT NULL,
                    prefix TEXT NOT NULL DEFAULT 'v.',
                    restrict_randomizer BOOLEAN NOT NULL DEFAULT false,
                    restrict_text BOOLEAN NOT NULL DEFAULT false
            );

            CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    user_id BIGINT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hangman (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    user_reference INT UNIQUE REFERENCES users(id),
                    wins INT NOT NULL DEFAULT 0,
                    losses INT NOT NULL DEFAULT 0,
                    guesses INT NOT NULL DEFAULT 0,
                    strikes INT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                user_reference INT UNIQUE REFERENCES users(id),
                name_list TEXT []
            );

            CREATE TABLE IF NOT EXISTS guild_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT UNIQUE REFERENCES guilds(id),
                name_list TEXT []
            );

            SELECT
                message
            FROM
                bot
            WHERE
                name = 'Bot Status Message';
        ''')

        bot_status = db.cur.fetchall()
        if bot_status[0][0] != None:
            await bot.change_presence(activity=discord.Game(bot_status[0][0]))

        db.cur.execute('''
            SELECT
                guild
            FROM
                guilds;
        ''')

        db_guilds = db.cur.fetchall()
        missing_guilds = [bot_guild.id for bot_guild in bot.guilds if bot_guild.id not in [db_guild[0] for db_guild in db_guilds]]
        if missing_guilds != []:
            for missing_guild in missing_guilds:
                db.cur.execute(f'''
                    INSERT INTO guilds (guild)
                    VALUES
                            ('{missing_guild}')
                    ON CONFLICT (guild)
                    DO NOTHING;
                ''')

        invalid_guilds = [db_guild[0] for db_guild in db_guilds if bot.get_guild(db_guild[0]) == None]
        if invalid_guilds != []:
            for invalid_guild in invalid_guilds:
                db.cur.execute(f'''
                    DELETE FROM guilds
                    WHERE guild = '{invalid_guild}';
                ''')
    finally:
        db.close()
    Help(bot)
    print(f"{bot.user.name} online in {len(bot.guilds)} guilds")

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Logout', aliases=['Lg'])
    @commands.is_owner()
    async def logout(self, ctx):
        await self.bot.close()
        print(f"{self.bot.user.name} went offline")

    @commands.command(name='Load', aliases=['L'])
    @commands.is_owner()
    async def load(self, ctx, cog):
            if cog == __main__.__file__.replace('.py', ''):
                print(f'Impossible to load {cog}')
            else:
                try:
                    self.bot.load_extension(cog)
                    print(f'Done loading {cog}')
                except Exception as error:
                    print(f'Failed to load {cog}\n{error}')

    @commands.command(name='Unload', aliases=['U'])
    @commands.is_owner()
    async def unload(self, ctx, cog):
        if cog == __main__.__file__.replace('.py', ''):
            print(f'Impossible to unload {cog}')
        else:
            try:
                self.bot.unload_extension(cog)
                print(f'Done unloading {cog}')
            except Exception as error:
                print(f'Failed to unload {cog}\n{error}')

    @commands.command(name='Reload', aliases=['R'])
    @commands.is_owner()
    async def reload(self, ctx, cog):
        if cog == __main__.__file__.replace('.py', ''):
            print(f'Impossible to reload {cog}')
        else:
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
                print(f'Done reloading {cog}')
            except Exception as error:
                print(f'Failed to reload {cog}\n{error}')

class CustomHelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

def setup(bot):
    bot.add_cog(Owner(bot))

setup(bot)
load_dotenv()
bot.run(os.getenv('BOT_TOKEN'))