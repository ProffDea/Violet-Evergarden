import discord
import os
import json
from dotenv import load_dotenv
from discord.ext import commands

with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
if not str(648977487744991233) in cstmguild:
    cstmguild[str(648977487744991233)] = {}
with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f, indent=4)

def cstmprefix(bot, msg):
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    if not msg.guild:
        return "v."
    else:
        return commands.when_mentioned_or(cstmguild[str(msg.guild.id)]['Custom Prefix'])(bot, msg)

bot = commands.Bot(command_prefix=cstmprefix, description='List of all available commands.', case_insensitive=True)

initial_extensions = ['commands', 'settings', 'events'] # Where you put python file names when making new cogs
if __name__ == '__main__':
    for extends in initial_extensions:
        try:
            bot.load_extension(extends)
        except Exception as error:
            print(f'{extends} cannot be loaded. [{error}]')

@bot.event
async def on_ready():
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    if not 'Custom Status' in cstmguild[str(648977487744991233)]: # ID is the test server ID. Feel free to change it
        cstmguild[str(648977487744991233)]['Custom Status'] = ''
    cstmstatus = cstmguild[str(648977487744991233)]['Custom Status']
    await bot.change_presence(activity=discord.Game(cstmstatus))
    cstmstatus = cstmguild[str(648977487744991233)]['Custom Status']
    if len(bot.guilds) == 1:
        sver = 'server'
    else:
        sver = 'servers'
    if cstmstatus == '':
        statusmsg = 'No status'
    else:
        statusmsg = cstmstatus
    print(f'\n{bot.user.name} is online.\nConnected to {len(bot.guilds)} {sver}!\n\nStatus:\n{statusmsg}')
    for removeguild in list(cstmguild):
        if not 'VC' in cstmguild[str(removeguild)]:
            cstmguild[str(removeguild)]['VC'] = {}
        if not 'AutoVC' in cstmguild[str(removeguild)]['VC']:
            cstmguild[str(removeguild)]['VC']['AutoVC'] = {}
        if not 'VCList' in cstmguild[str(removeguild)]['VC']:
            cstmguild[str(removeguild)]['VC']['VCList'] = {}
        if not 'Custom Prefix' in cstmguild[str(removeguild)]:
            cstmguild[str(removeguild)]['Custom Prefix'] = 'v.'
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
        json.dump(cstmguild, f, indent=4)

load_dotenv()
bot.run(os.getenv('token'))