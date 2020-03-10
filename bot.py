import discord
import os
import os.path
import json
import psycopg2
from dotenv import load_dotenv
from discord.ext import commands

if not os.path.isfile('guilds.json'): # JSON file stores all data required for this to work
    with open('guilds.json', 'w') as f:
        json.dump({}, f)

def cstmprefix(bot, msg):
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    if not msg.guild:
        return "v."
    else:
        return commands.when_mentioned_or(cstmguild[str(msg.guild.id)]['Custom Prefix'])(bot, msg)

helpmsg = "Please make sure I have all the necessary permissions to properly work!\nPermissions such as:\nManage Channels, Read Text Channels & See Voice Channels, Send Messages, Manage Messages, Use External Emojis, Connect, Move Members"
bot = commands.Bot(command_prefix=cstmprefix, description=helpmsg, case_insensitive=True)

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
        conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password')) # Make env file with variables
    finally:
        cur = conn.cursor()
        cur.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'jsons') THEN COPY (SELECT data FROM jsons WHERE name = 'Guilds') TO '{}'; END IF; END $$; CREATE TABLE IF NOT EXISTS jsons (id serial NOT NULL PRIMARY KEY, name TEXT UNIQUE, data json NOT NULL); INSERT INTO jsons (name, data) VALUES ('Guilds', '{}') ON CONFLICT (name) DO NOTHING; CREATE TABLE IF NOT EXISTS bot (name TEXT UNIQUE, message TEXT); INSERT INTO bot (name, message) VALUES ('Status', 'Test') ON CONFLICT (name) DO NOTHING; SELECT * FROM bot WHERE name = 'Status';".format(os.getenv('guildjson'), {}))
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
        with open('guilds.json', 'r') as f:
            cstmguild = json.load(f)
        for inguilds in bot.guilds:
            if not str(inguilds.id) in cstmguild:
                cstmguild[str(inguilds.id)] = {}
            if not 'VC' in cstmguild[str(inguilds.id)]:
                cstmguild[str(inguilds.id)]['VC'] = {}
            if not 'AutoVC' in cstmguild[str(inguilds.id)]['VC']:
                cstmguild[str(inguilds.id)]['VC']['AutoVC'] = {}
            if not 'VCList' in cstmguild[str(inguilds.id)]['VC']:
                cstmguild[str(inguilds.id)]['VC']['VCList'] = {}
            if not 'Custom Prefix' in cstmguild[str(inguilds.id)]:
                cstmguild[str(inguilds.id)]['Custom Prefix'] = 'v.'
            if not 'Welcome' in cstmguild[str(inguilds.id)]:
                cstmguild[str(inguilds.id)]['Welcome'] = {}
            if not 'Goodbye' in cstmguild[str(inguilds.id)]:
                cstmguild[str(inguilds.id)]['Goodbye'] = {}
        for removeguild in list(cstmguild):
            if bot.get_guild(int(removeguild)) == None:
                del cstmguild[removeguild]
                continue
            for removeauto in list(cstmguild[str(removeguild)]['VC']['AutoVC']):
                if bot.get_channel(int(removeauto)) == None:
                    del cstmguild[removeguild]['VC']['AutoVC'][removeauto]
            for removelist in list(cstmguild[str(removeguild)]['VC']['VCList']):
                if bot.get_channel(int(removelist)) == None:
                    del cstmguild[removeguild]['VC']['VCList'][removelist]
        with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f)
        cur.execute(f"CREATE TEMP TABLE jsonscopy as (SELECT * FROM jsons limit 0); COPY jsonscopy (data) FROM '{os.getenv('guildjson')}'; UPDATE jsons SET data = jsonscopy.data FROM jsonscopy WHERE jsons.name = 'Guilds';")
        conn.commit()
        cur.close()
        conn.close()

load_dotenv()
bot.run(os.getenv('token')) # Make env file with token variable