import discord
from discord.ext import commands

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Lg', help='Bot goes offline')
    @commands.is_owner()
    @commands.guild_only()
    async def boutaheadout(self, ctx):
        await ctx.message.delete()
        await self.bot.close()

    @commands.command(name='L', help='Loads a cog.')
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            self.bot.load_extension(extension)
            await ctx.send(f'Loaded {extension}')
        except Exception as error:
            await ctx.send(f'{extension} could not be loaded. [{error}]')

    @commands.command(name='U', help='Unloads a cog.')
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
            await ctx.send(f'Unloaded {extension}')
        except Exception as error:
            await ctx.send(f'{extension} could not be unloaded. [{error}]')
    
    @commands.command(name='R', help='Reloads a cog.')
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            self.bot.unload_extension(extension)
            con = await ctx.send(f'Unloaded {extension}')
            self.bot.load_extension(extension)
            await con.edit(content=f'Reloaded {extension}')
        except Exception as error:
            await ctx.send(f'{extension} could not be reloaded. [{error}]')
    
    @commands.command(name='Rolelink', help='Link embeds for my server roles.')
    @commands.is_owner()
    async def role_link(self, ctx):
        linkembed = discord.Embed(
                title='CLICK THE LINK TO HAVE IT BRING YOU TO THE ROLES',
                description='',
                color=discord.Color.purple()
        )
        linkembed.add_field(name='`🌈 Color`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647707491169206302)', inline=True)
        linkembed.add_field(name='`🌈 Color list`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708228406345739)', inline=True)
        linkembed.add_field(name='`🤖 Bot Paradise`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708342785146930)', inline=True)
        linkembed.add_field(name='`🏳️‍🌈 Gender`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708520497807361)', inline=True)
        linkembed.add_field(name='`🔢 Age`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708744561590272)', inline=True)
        linkembed.add_field(name='`❤️ Sexuality`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708976502407179)', inline=True)
        linkembed.add_field(name='`🔒 DM Status`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647709123323887626)', inline=True)
        linkembed.add_field(name='`🗺️ Continent`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647709296284663820)', inline=True)
        linkembed.add_field(name="`🏠 Squee's House Category`", value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647709461317812246)', inline=True)

        await ctx.send(embed=linkembed)

    @commands.command(name='Test', help="For testing purposes.")
    @commands.is_owner()
    async def test(self, ctx):
        tstcmd = self.bot.get_command('tst')
        await ctx.invoke(tstcmd)
        await ctx.send(ctx)
    @commands.command(name='Tst', help="For testing purposes.")
    @commands.is_owner()
    async def tst(self, ctx):
        await ctx.send('owo')

    @commands.command(name='Ping', help="Shows bot's latency in milliseconds.")
    async def ping(self, ctx):
        await ctx.send(f'Pong: {round(self.bot.latency * 1000)}ms')

def setup(bot):
    bot.add_cog(Commands(bot))