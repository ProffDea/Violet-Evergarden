import os
import discord
import __main__
import time
import datetime
import logging
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from async_postgresql import async_database

print("Creating logs...")
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf=8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def custom_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or('v.')(bot, message)
    else:
        db = async_database()
        await db.connect()
        try:
            db_guild = await db.con.fetch('''
                SELECT
                    guild,
                    prefix
                FROM
                    guilds
                INNER JOIN guild_settings
                    ON guilds.id = guild_settings.guild_reference
                WHERE
                    guilds.guild = '%s';
            ''' %
            (message.guild.id,)
            )
            guild_prefix = db_guild[0][1] if message.guild.id == db_guild[0][0] else 'v.'
            return commands.when_mentioned_or(guild_prefix)(bot, message)
        finally:
            await db.close()

intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.bans = False
intents.emojis = False
intents.integrations = False
intents.webhooks = False
intents.invites = False
intents.voice_states = True
intents.presences = False
intents.messages = True
intents.guild_messages = True
intents.dm_messages = True
intents.reactions = True
intents.guild_reactions = True
intents.dm_reactions = True
intents.typing = False
intents.guild_typing = False
intents.dm_typing = False

bot = commands.Bot(command_prefix=custom_prefix, intents=intents, member_cache_flags=discord.MemberCacheFlags.from_intents(intents), chunk_guilds_at_startup=True, description='Violet Evergarden Overhaul', case_insensitive=True)
bot.startup_time = datetime.now()

print("Loading cogs...")
for cog in ['events', 'utility', 'games', 'music', 'epic_seven', 'error_handler']:
    try:
        bot.load_extension(cog)
    except Exception as error:
        print('Failed to load %s\n%s' % (cog, error))

print("Booting up...")
@bot.event
async def on_ready():
    print("Connecting database...")
    db = async_database()
    await db.connect()
    try:
        print("Checking database...")
        await db.con.execute('''
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
                    guild BIGINT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    user_id BIGINT UNIQUE NOT NULL,
                    experience INT NOT NULL DEFAULT 0,
                    last_message TIMESTAMP,
                    last_voice TIMESTAMP,
                    last_deafen TIMESTAMP,
                    voice_duration INT DEFAULT 0,
                    deafen_duration INT DEFAULT 0,
                    deafen_amount INT DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS hangman (
                    id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                    user_reference INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    wins INT NOT NULL DEFAULT 0,
                    losses INT NOT NULL DEFAULT 0,
                    guesses INT NOT NULL DEFAULT 0,
                    strikes INT NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                user_reference INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name_list TEXT []
            );

            CREATE TABLE IF NOT EXISTS guild_randomizer (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT UNIQUE NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
                name_list TEXT []
            );

            CREATE TABLE IF NOT EXISTS guild_users (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
                user_reference INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                experience INT NOT NULL DEFAULT 0,
                last_message TIMESTAMP,
                last_voice TIMESTAMP,
                last_deafen TIMESTAMP,
                voice_duration INT DEFAULT 0,
                deafen_duration INT DEFAULT 0,
                deafen_amount INT DEFAULT 0,
                UNIQUE (guild_reference, user_reference)
            );

            CREATE TABLE IF NOT EXISTS voice (
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                channel BIGINT UNIQUE NOT NULL,
                guild_reference INT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
                owner INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                permanent_channel BOOLEAN NOT NULL DEFAULT false
            );

            CREATE TABLE IF NOT EXISTS voice_roles(
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
                channel BIGINT UNIQUE NOT NULL,
                role BIGINT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS muted_users(
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                user_reference INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                guild_reference INT NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
                channel BIGINT NOT NULL,
                mute_duration TIMESTAMP NOT NULL,
                UNIQUE (user_reference, guild_reference, channel)
            );

            CREATE TABLE IF NOT EXISTS guild_settings(
                id SERIAL PRIMARY KEY UNIQUE NOT NULL,
                guild_reference INT NOT NULL UNIQUE REFERENCES guilds(id) ON DELETE CASCADE,
                prefix TEXT NOT NULL DEFAULT 'v.',
                auto_voice BIGINT UNIQUE,
                dc_afk BOOLEAN NOT NULL DEFAULT false,
                welcome_channel BIGINT,
                goodbye_channel BIGINT
            );
        ''')
        bot_status = await db.con.fetch('''
            SELECT
                message
            FROM
                bot
            WHERE
                name = 'Bot Status Message';
        ''')

        if bot_status[0][0] != None:
            await bot.change_presence(activity=discord.Game(bot_status[0][0]))

        db_guilds = await db.con.fetch('''
            SELECT
                guild
            FROM
                guilds;
        ''')

        missing_guilds = [bot_guild.id for bot_guild in bot.guilds if bot_guild.id not in [db_guild[0] for db_guild in db_guilds]]
        if missing_guilds != []:
            for missing_guild in missing_guilds:
                await db.con.execute('''
                    INSERT INTO guilds (guild)
                    VALUES
                            ('%s')
                    ON CONFLICT (guild)
                    DO NOTHING;

                    INSERT INTO guild_settings (guild_reference)
                    SELECT
                        id
                    FROM
                        guilds
                    ON CONFLICT (guild_reference)
                    DO NOTHING;
                ''' %
                (missing_guild,)
                )

        invalid_guilds = [db_guild[0] for db_guild in db_guilds if bot.get_guild(db_guild[0]) == None]
        if invalid_guilds != []:
            for invalid_guild in invalid_guilds:
                await db.con.execute('''
                    DELETE FROM guilds
                    WHERE guild = '%s';
                ''' %
                (invalid_guild,)
                )
        print("Success")
    finally:
        await db.close()

    # Epic seven guild for personal use
    owner_guild = bot.get_guild(647205092029759488)
    bot.owner_invites = await owner_guild.invites()

    Help(bot)
    print("\n%s online\nTotal guilds: %s guilds\nCurrent ping: %s ms\n" % (bot.user.name, len(bot.guilds), round(bot.latency * 1000)))

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Close')
    @commands.is_owner()
    async def close(self, ctx, player):
        await self.bot.wavelink.destroy_node(identifier=player)

    @commands.command(name='Logout', aliases=['Lg'])
    @commands.is_owner()
    async def logout(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        print("Shutting down...")
        try:
            await self.bot.wavelink.destroy_node(identifier=os.getenv('WL_ID'))
        except:
            print("No nodes to destroy, skipping")
        counter = 0 # Increase number to delay shutdown
        while counter > 0:
            print(counter)
            time.sleep(1)
            counter = counter - 1
        time.sleep(1)
        print("%s went offline" % (self.bot.user.name,))
        await bot.wait_until_ready()
        await self.bot.logout()
        await self.bot.close()

    @commands.command(name='Load', aliases=['L'])
    @commands.is_owner()
    async def load(self, ctx, cog):
        try:
            await ctx.message.delete()
        except:
            pass
        if cog == __main__.__file__.replace('.py', ''):
            print('Impossible to load %s' % (cog,))
        else:
            try:
                self.bot.load_extension(cog)
                print('Done loading %s' % (cog,))
            except Exception as error:
                print('Failed to load %s\n%s' % (cog, error))

    @commands.command(name='Unload', aliases=['U'])
    @commands.is_owner()
    async def unload(self, ctx, cog):
        try:
            await ctx.message.delete()
        except:
            pass
        if cog == __main__.__file__.replace('.py', ''):
            print('Impossible to unload %s' % (cog,))
        else:
            try:
                self.bot.unload_extension(cog)
                print('Done unloading %s' % (cog,))
            except Exception as error:
                print('Failed to unload %s\n%s' % (cog, error))

    @commands.command(name='Reload', aliases=['R'])
    @commands.is_owner()
    async def reload(self, ctx, cog):
        try:
            await ctx.message.delete()
        except:
            pass
        if cog == __main__.__file__.replace('.py', ''):
            print('Impossible to reload %s' % (cog,))
        else:
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
                print('Done reloading %s' % (cog,))
            except Exception as error:
                print('Failed to reload %s\n%s' % (cog, error))

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