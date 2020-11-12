import requests
import discord
import json
from discord.ext import commands

class Epic7(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Info')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def info(self, ctx, *, hero = None):
        if hero == None:
            return await ctx.send("Please name a hero name")
        
        response = requests.get('https://api.epicsevendb.com/hero/%s' % (hero.lower().replace(' ', '-'),))

        star_rate = ''
        index = 0
        while index in range(response.json()['results'][0]['rarity']):
            star_rate += '⭐'
            index = index + 1

        embed = discord.Embed(
            title=response.json()['results'][0]['name'],
            description=response.json()['results'][0]['description'],
            color=discord.Color.blue()
        )
        embed.set_author(name=star_rate)
        embed.add_field(name='Story', value=response.json()['results'][0]['story'], inline=False)
        embed.set_image(url=response.json()['results'][0]['assets']['image'])

        try:
            await ctx.send(embed=embed)
        except KeyError:
            return await ctx.send("An error occurred. Did you enter in a valid hero name?")

    @commands.command(name='Test')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.is_owner()
    async def test(self, ctx, *, hero = None):
        if hero == None:
            return await ctx.send("Please name a valid hero")

        response = requests.get('https://api.epicsevendb.com/hero/%s' % (hero.lower().replace(' ', '-'),))
        with open('epic_seven.json', 'w') as fp:
            json.dump(response.json(), fp, indent=2)
        await ctx.message.add_reaction('✅')

def setup(bot):
    bot.add_cog(Epic7(bot))