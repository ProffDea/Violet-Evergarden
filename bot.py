import discord
import os
import json
from dotenv import load_dotenv
from discord.ext import commands

def cstmprefix(bot, msg):
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    if not msg.guild:
        return "v."
    else:
        if not str(msg.guild.id) in cstmguild:
            cstmguild[str(msg.guild.id)] = {}
        if not 'Custom Prefix' in cstmguild[str(msg.guild.id)]:
            cstmguild[str(msg.guild.id)]['Custom Prefix'] = "v."
        with open('guilds.json', 'w') as f:
            json.dump(cstmguild, f, indent=4)
        return commands.when_mentioned_or(cstmguild[str(msg.guild.id)]['Custom Prefix'])(bot, msg)

bot = commands.Bot(command_prefix=cstmprefix, description='List of all available commands.', case_insensitive=True)

initial_extensions = ['commands', 'settings'] # Where you put python file names when making new cogs
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
    print('Have a good day!')
    for removeguild in list(cstmguild):
        if bot.get_guild(int(removeguild)) == None:
            del cstmguild[removeguild]
    with open('guilds.json', 'w') as f:
        json.dump(cstmguild, f, indent=4)

@bot.event
async def on_guild_join(guild):
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    if not str(guild.id) in cstmguild:
        cstmguild[str(guild.id)] = {}
    with open('guilds.json', 'w') as f:
        json.dump(cstmguild, f, indent=4)

@bot.event
async def on_guild_remove(guild):
    with open('guilds.json', 'r') as f:
        cstmguild = json.load(f)
    for removeguild in list(cstmguild):
        if bot.get_guild(int(removeguild)) == None:
            del cstmguild[removeguild]
    with open('guilds.json', 'w') as f:
        json.dump(cstmguild, f, indent=4)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("<:IDontKnowThatCommand:676544628274757633>") # Emoji is from the test server. Anime girl with question marks.
        return
    if hasattr(ctx.command, 'on_error'):
        return
    else:
        raise error

load_dotenv()
bot.run(os.getenv('token'))