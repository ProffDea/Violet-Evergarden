import json
import os
import psycopg2
import discord
import time
import random
from discord.ext import commands

def TestServerEmoji():
    return "<:IDontKnowThatCommand:676544628274757633>" # Emoji is from the test server. Anime girl with question marks.

class Events(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute(f"INSERT INTO servers (guild, prefix) VALUES ('{guild.id}', 'v.') ON CONFLICT (guild) DO NOTHING;")
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute(f"DELETE FROM servers WHERE guild = '{guild.id}';")
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(TestServerEmoji())
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"**{ctx.command}** can not be used in DMs.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument!")
        elif isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error, delete_after=5)
        else:
            raise error

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute(f"SELECT autovc FROM servers WHERE guild = '{channel.guild.id}';")
                autovc = cur.fetchall()
                for a in autovc:
                    if a[0] == channel.id:
                        cur.execute(f"UPDATE servers SET autovc = NULL WHERE guild = '{channel.guild.id}'")
                        break
                cur.execute("SELECT voicechl FROM vclist;")
                vclist = cur.fetchall()
                for vl in vclist:
                    if self.bot.get_channel(vl[0]) == None:
                        cur.execute(f"DELETE FROM vclist WHERE voicechl = '{vl[0]}';")
                        return
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                cur.execute("SELECT voicechl FROM vclist;")
                vclist = cur.fetchall()
                cur.execute(f"SELECT autovc FROM servers WHERE guild = '{member.guild.id}';")
                autovc = cur.fetchall()
                # Checking if hard disconnecting
                if after.channel == None:
                    pass
                # Triggers on joining a channel or an autovc except for hard disconnects
                elif before.channel == None or [item for item in autovc if after.channel.id in item] and before.channel != None:
                    # Triggers on hard joining autovc or moving to autovc
                    if [item for item in autovc if after.channel.id in item]:
                        sec = int(round(time.time() - self.bot.voice_cool[member.id]['log'])) if member.id in self.bot.voice_cool else 11
                        if sec <= 10:
                            await member.move_to(before.channel) if before.channel != None else await member.move_to(None)
                            if self.bot.voice_cool[member.id]['dm'] == False:
                                try:
                                    await member.send(f"💌 | Please wait **{10 - sec}** seconds for a new channel. Thank you.", delete_after=10)
                                except:
                                    pass
                                self.bot.voice_cool[member.id]['dm'] = True
                            return
                        else:
                            if member.guild.id == 648977487744991233: # Carter's bullshit, delete if needed
                                vc_name = random.choice(["Clappin' Salmon", 'Hand-Cranked Pickle', 'Burger Pond', 'Koi_Salad M1911 dusty drab', 'The Onion_Gamer1836',
                                                'Shaggy Shrimp (Onion layered)', 'Holy Peanut (No Shell)', 'Kinetic Kiwi (A/C Powered)', 'Perplexed Pickle (Jar included)', '5$ Crunch Box (Chalupa Craving)',
                                                'Cereal Sock', 'Tummy Pillow', 'Deck of Pears', 'Pint of Crows', 'Eel Crumbs ',
                                                'Purebred Turnip', 'Cooing_Onion1094', 'Tuna Paste', 'Unyielding_Slipper ', 'GOTHIC_ONION'])
                            else:
                                cur.execute(f"SELECT unnest(name_generator) FROM members WHERE user_id = '{member.id}';")
                                name_list = cur.fetchall()
                                default_names = ['💌CH Postal Company', '💌Leidenschaftlich', '💌Kazaly', '💌Intense', '💌Shaher Headquarters'
                                                '💌Roswell', '💌Machtig', '💌Enchaine' ,'💌Eustitia', '💌Lechernt']
                                vc_name = random.choice(default_names) if name_list == [] else random.choice(name_list)
                            clone = await after.channel.clone(name=vc_name, reason=f"{member.name} has created this VC.")
                            cur.execute(f"INSERT INTO vclist (voicechl, owner, static) VALUES ('{clone.id}', '{member.id}', 'FALSE');")
                            await member.move_to(clone)
                            self.bot.voice_cool.update({member.id : {'log' : time.time(), 'dm' : False}})
                # Checking if hard joining
                if before.channel == None:
                    pass
                # Triggers on moving out of VC or hard disconnecting from VC
                elif after.channel != None and before.channel != None and [item for item in vclist if before.channel.id in item] or after.channel == None and [item for item in vclist if before.channel.id in item]:
                    cur.execute(f"SELECT static FROM vclist WHERE voicechl = '{before.channel.id}';")
                    static = cur.fetchall()
                    # Triggers on empty and non-permanent VC
                    if len(before.channel.members) == 0 and [item for item in static if item[0] == False]:
                        await before.channel.delete(reason='VC is empty.')
                    return
            finally:
                conn.commit()
                cur.close()
                conn.close()

def setup(bot):
    bot.add_cog(Events(bot))