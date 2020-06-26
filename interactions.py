import discord
from discord.ext import commands
from postgresql import database

class menu(object):
    def __init__(self):
        self.exit_emoji = '🇽'
        self.exit_response = 'exit'
        self.exit_display = '🇽 Exit menu'
        self.back_emoji = '⬅️'
        self.back_response = 'back'
        self.back_display = '⬅️ Go back'
        self.more_info = 'ℹ️'
        self.info_display = 'ℹ️ More information (Menu will stay intact)'

    async def interface(self, ctx, shortcut, name, interactables, manipulations, info):
        eb = discord.Embed(
            title=name,
            description=f"```py\n{interactables}\n```{manipulations}",
            color=discord.Color.purple()
        )
        eb.set_author(name=shortcut, url=ctx.author.avatar_url)
        eb.set_footer(text=f"{info}\n💌")
        return await ctx.send(embed=eb)

    def verify_message(self, ctx):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        return verify

    def verify_reaction(self, ctx, msg):
        def verify(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id
        return verify

    def type_message(self, response):
        loop = True if str(type(response)) == "<class 'discord.message.Message'>" else False
        return loop

    def type_reaction(self, response):
        loop = True if str(type(response)) == "<class 'tuple'>" and str(type(response[0])) == "<class 'discord.reaction.Reaction'>" else False
        return loop

    async def timeout(self, ctx, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await ctx.send(f"💌 | **{ctx.author.name}**'s menu has been exited due to timeout.")
        except:
            pass
        return False

    async def exit(self, ctx, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await ctx.send(f"💌 | **{ctx.author.name}**'s menu has been exited.")
        except:
            pass
        return False

    async def invalid(self, response):
        if self.type_message(response):
            try:
                await response.add_reaction('❌')
            except:
                pass