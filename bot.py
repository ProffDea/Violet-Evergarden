import os
import discord
import __main__
import time
import datetime
import logging
from discord.ext import commands
from dotenv import load_dotenv
from postgresql import database

print("Creating logs...")
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf=8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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

print("Loading cogs...")
for cog in ['events', 'utility', 'games']:
    try:
        bot.load_extension(cog)
    except Exception as error:
        print(f'Failed to load {cog}\n{error}')

print("Booting up...")
@bot.event
async def on_ready():
    print("Connecting database...")
    db = database()
    db.connect()
    try:
        print("Checking database...")
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
                    user_id BIGINT UNIQUE NOT NULL,
                    experience INT NOT NULL DEFAULT 0,
                    last_message TIMESTAMP,
                    last_voice TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS hangman (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    user_reference INT UNIQUE NOT NULL REFERENCES users(id),
                    wins INT NOT NULL DEFAULT 0,
                    losses INT NOT NULL DEFAULT 0,
                    guesses INT NOT NULL DEFAULT 0,
                    strikes INT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                user_reference INT UNIQUE NOT NULL REFERENCES users(id),
                name_list TEXT []
            );

            CREATE TABLE IF NOT EXISTS guild_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT UNIQUE NOT NULL REFERENCES guilds(id),
                name_list TEXT []
            );

            CREATE TABLE IF NOT EXISTS guild_users (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT NOT NULL REFERENCES guilds(id),
                user_reference INT NOT NULL REFERENCES users(id),
                experience INT NOT NULL DEFAULT 0,
                last_message TIMESTAMP,
                last_voice TIMESTAMP,
                UNIQUE (guild_reference, user_reference)
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
        print("Success")
    finally:
        db.close()
    Help(bot)
    print(f"\n{bot.user.name} online\nTotal guilds: {len(bot.guilds)} guilds\nCurrent ping: {round(bot.latency * 1000)} ms\n")

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Logout', aliases=['Lg'])
    @commands.is_owner()
    async def logout(self, ctx):
        print("Shutting down...")
        counter = 0 # Increase number to delay shutdown
        while counter > 0:
            print(counter)
            time.sleep(1)
            counter = counter - 1
        time.sleep(1)
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