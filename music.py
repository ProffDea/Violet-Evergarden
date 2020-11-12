import os
import discord
import wavelink
from discord.ext import commands

class Music(commands.Cog):

    # Status: Work in progress

    # Connecting to Lavalink server
    # Credentials that must be filled are as follows:
    # WL_HOST
    # WL_PORT
    # WL_URI
    # WL_PASSWORD
    # WL_ID
    # WL_REGION

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(bot=self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        await self.bot.wavelink.initiate_node(host=os.getenv('WL_HOST'),
                                            port=os.getenv('WL_PORT'),
                                            rest_uri=os.getenv('WL_URI'),
                                            password=os.getenv('WL_PASSWORD'),
                                            identifier=os.getenv('WL_ID'),
                                            region=os.getenv('WL_REGION'))

    @commands.command(name='Connect', aliases=['Join'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def connect(self, ctx, *, channel: discord.VoiceChannel = None):
        if channel == None:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                await ctx.send("💌 | Please run this command when in a voice channel or with a valid channel.")

        player = self.bot.wavelink.get_player(ctx.guild.id)
        await ctx.message.add_reaction('✅')
        await player.connect(channel.id)
    
    @commands.command(name='Play', aliases=['P'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def play(self, ctx, *, query: str):
        # No queue exists | Overwrites any current song playing.
        tracks = await self.bot.wavelink.get_tracks('ytsearch:%s' % (query,))
        if not tracks:
            return await ctx.send('💌 | Failed to find anything...')

        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            await ctx.invoke(self.connect)

        await ctx.send("💌 | ▶️ **`%s`**" % (str(tracks[0]),))
        await player.play(tracks[0])
    
    @commands.command(name='Leave', aliases=['Disconnect', 'DC'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def leave(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.message.add_reaction('❌')

        await ctx.message.add_reaction('⏹️')
        await player.destroy()

    @commands.command(name='Skip')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def skip(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.message.add_reaction('❌')
        if not player.is_playing:
            return await ctx.send("💌 | Nothing to skip")
        
        await ctx.message.add_reaction('⏩')
        await player.stop()

    @commands.command(name='Pause')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def pause(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.message.add_reaction('❌')
        if player.is_paused:
            return await ctx.send("💌 | Already paused")
        
        await ctx.message.add_reaction('⏸️')
        await player.set_pause(True)

    @commands.command(name='Resume')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def resume(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.message.add_reaction('❌')
        if not player.is_paused:
            return await ctx.send("💌 | Already playing")

        await ctx.message.add_reaction('▶️')
        await player.set_pause(False)

    @commands.command(name='Volume')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def volume(self, ctx, volume_int: int = None):
        player = self.bot.wavelink.get_player(ctx.guild.id)
        if not player.is_connected:
            return await ctx.message.add_reaction('❌')
        if volume_int == None:
            return await ctx.send("Current Volume: **`%s%%`**\nDefault Volume: **`100%%`**\nTo change the volume, run the same command with a number between `0` to `100` after it" % (str(player.volume),))

        # Any value higher than 100 distorts audio
        if volume_int >= 0 and volume_int <= 100:
            if volume_int < player.volume:
                await ctx.message.add_reaction('⬇️')
            elif volume_int > player.volume:
                await ctx.message.add_reaction('⬆️')
            elif volume_int == player.volume:
                return await ctx.send("💌 | Volume already at **`%s%%`**" % (volume_int,))
            await player.set_volume(volume_int)
        else:
            await ctx.send("💌 | Please choose a number between `0` to `100`")

def setup(bot):
    bot.add_cog(Music(bot))