import discord
import traceback
import sys
from discord.ext import commands

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        _cog = ctx.cog
        if _cog:
            if _cog._get_overridden_method(_cog.cog_command_error) is not None:
                return

        _ignored = (commands.CommandNotFound,)
        error = getattr(error, 'original', error)

        if isinstance(error, _ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send("💌 | `%s` has been disabled" % (ctx.command,), delete_after=10)
        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send("💌 | `%s` can not be used in **Direct Messages**" % (ctx.command,), delete_after=10)
            except discord.HTTPException:
                pass
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'exampleCommandNameHere':
                pass
            await ctx.send("💌 | Sorry, please give a valid argument", delete_after=10)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send("💌 | %s" % (error), delete_after=10)
        else:
            print("Ignoring exception in command %s:" % (ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))