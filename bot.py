import discord, os, psycopg2
from dotenv import load_dotenv
from discord.ext import commands

def cstmprefix(bot, msg):
    if not msg.guild:
        return "v."
    else:
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            cur.execute(f"SELECT guild, prefix FROM servers WHERE guild = '{msg.guild.id}';")
            pre = cur.fetchall()
            for p in pre:
                if msg.guild.id == p[0]:
                    vprefix = p[1]
            cur.close()
            conn.close()
            return commands.when_mentioned_or(vprefix)(bot, msg)

def miss_permission():
    return "Please make sure I have all the necessary permissions to properly work!\nPermissions such as:\nManage Channels, Read Text Channels & See Voice Channels, Send Messages, Manage Messages, Use External Emojis, Add Reactions, Connect, Move Members"

bot = commands.Bot(command_prefix=cstmprefix, description=miss_permission(), case_insensitive=True)

initial_extensions = ['commands', 'guild', 'events'] # Where you put python file names when making new cogs
if __name__ == '__main__':
    for extends in initial_extensions:
        try:
            bot.load_extension(extends)
        except Exception as error:
            print(f'{extends} cannot be loaded. [{error}]')

@bot.event
async def on_ready():
    try:
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    except KeyError:
        conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
    finally:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS bot (name TEXT UNIQUE, message TEXT); INSERT INTO bot (name) VALUES ('Status') ON CONFLICT (name) DO NOTHING; CREATE TABLE IF NOT EXISTS servers (id SERIAL PRIMARY KEY NOT NULL, guild BIGINT NOT NULL UNIQUE, prefix TEXT NOT NULL, autovc BIGINT); CREATE TABLE IF NOT EXISTS vclist (voicechl BIGINT NOT NULL UNIQUE, owner BIGINT, admin BIGINT [], members SMALLINT NOT NULL, static BOOLEAN NOT NULL);")
        cur.execute("CREATE TABLE IF NOT EXISTS members (id SERIAL PRIMARY KEY UNIQUE NOT NULL, user_id BIGINT UNIQUE NOT NULL, status BOOLEAN NOT NULL);")
        cur.execute("SELECT * FROM bot WHERE name = 'Status';")
        rows = cur.fetchall()
        for r in rows:
            if r[0] == "Status":
                cstmstatus = r[1]
                break
        await bot.change_presence(activity=discord.Game(cstmstatus))
        if len(bot.guilds) == 1:
            sver = 'server'
        else:
            sver = 'servers'
        if cstmstatus == '':
            statusmsg = 'No status'
        else:
            statusmsg = cstmstatus
        print(f'\n{bot.user.name} is online in {len(bot.guilds)} {sver}.\n\nStatus:\n{statusmsg}\n')
        for inguilds in bot.guilds:
            cur.execute(f"INSERT INTO servers (guild, prefix) VALUES ('{inguilds.id}', 'v.') ON CONFLICT (guild) DO NOTHING;")
        cur.execute("SELECT guild, autovc FROM servers;")
        allguilds = cur.fetchall()
        for g in allguilds:
            if bot.get_guild(g[0]) == None:
                cur.execute(f"DELETE FROM servers WHERE guild = '{g[0]}';")
                continue
            if g[1] == None:
                pass
            else:
                if bot.get_channel(g[1]) == None:
                    cur.execute("DELETE autovc FROM servers WHERE autovc = '{%s}';", (g[1],))
                    continue
        cur.execute("SELECT voicechl FROM vclist;")
        lists = cur.fetchall()
        for l in lists:
            if bot.get_channel(l[0]) == None:
                cur.execute(f"DELETE FROM vclist WHERE voicechl = '{l[0]}';")
                continue
        conn.commit()
        cur.close()
        conn.close()

load_dotenv()
bot.run(os.getenv('token'))