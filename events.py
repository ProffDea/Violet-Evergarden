import json
import os
import psycopg2
import discord
import time
import random
import asyncio
from discord.ext import commands

def TestServerEmoji():
    return "<:IDontKnowThatCommand:676544628274757633>" # Emoji is from the test server

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
                cur.execute(f"INSERT INTO servers (guild, prefix, restrict_randomizer) VALUES ('{guild.id}', 'v.', false) ON CONFLICT (guild) DO NOTHING;")
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
                cur.execute("SELECT voicechl, text FROM vclist;")
                vclist = cur.fetchall()
                for vl in vclist:
                    if self.bot.get_channel(vl[0]) == None:
                        text_channel = self.bot.get_channel(vl[1])
                        if text_channel != None:
                            await asyncio.sleep(1)
                            try:
                                await text_channel.delete(reason="Voice Channel got deleted")
                            except:
                                pass
                        cur.execute(f"DELETE FROM vclist WHERE voicechl = '{vl[0]}';")
                        break
                    if vl[1] != None and self.bot.get_channel(vl[1]) == None:
                        cur.execute(f"UPDATE vclist SET text = null WHERE voicechl = '{vl[0]}';")
                        break
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
                cur.execute(f"""INSERT INTO members (user_id) VALUES ('{member.id}') ON CONFLICT (user_id) DO NOTHING;
                            SELECT voicechl FROM vclist;""")
                vclist = cur.fetchall()
                cur.execute(f"SELECT autovc, restrict_text, restrict_randomizer FROM servers WHERE guild = '{member.guild.id}';")
                autovc = cur.fetchall()

                # Checking if hard disconnecting
                if len(member.guild.channels) == 499 and autovc[0][1] == False or len(member.guild.channels) == 500 and autovc[0][1] == True:
                    pass
                elif after.channel == None:
                    pass

                # Triggers on joining a channel or an autovc except for hard disconnects
                elif before.channel == None or [item for item in autovc if after.channel.id in item] and before.channel != None:
                    
                    # Triggers on hard joining autovc or moving to autovc
                    if autovc[0][0] == None:
                        pass
                    elif len(self.bot.get_channel(autovc[0][0]).category.channels) == 49 and autovc[0][1] == False or len(self.bot.get_channel(autovc[0][0]).category.channels) == 50 and autovc[0][1] == True:
                        pass
                    elif autovc[0][0] == after.channel.id:
                        sec = int(round(time.time() - self.bot.voice_cool[member.id]['log'])) if member.id in self.bot.voice_cool else 21

                        if sec <= 20:
                            try:
                                await member.move_to(before.channel) if before.channel != None else await member.move_to(None)
                            except:
                                try:
                                    await member.move_to(None)
                                except:
                                    pass
                            if self.bot.voice_cool[member.id]['dm'] == False:
                                try:
                                    plural = 'second' if 20 - sec == 1 else 'seconds'
                                    await member.send(f"💌 | Please wait **{20 - sec}** {plural} for a new channel. Thank you.", delete_after=20)
                                except:
                                    pass
                                self.bot.voice_cool[member.id]['dm'] = True
                            return
                        else:
                            self.bot.voice_cool.update({member.id : {'log' : time.time(), 'dm' : False}})
                            cur.execute(f"SELECT unnest(name_randomizer) FROM servers WHERE guild = '{member.guild.id}';")
                            server_name_list = cur.fetchall()
                            cur.execute(f"SELECT unnest(name_generator) FROM members WHERE user_id = '{member.id}';")
                            name_list = cur.fetchall()
                            default_names = ['💌CH Postal Company', '💌Leidenschaftlich', '💌Kazaly', '💌Intense', '💌Shaher Headquarters'
                                            '💌Roswell', '💌Machtig', '💌Enchaine' ,'💌Eustitia', '💌Lechernt']
                            if autovc[0][2] == False:
                                if name_list == []:
                                    vc_name = random.choice(default_names) if server_name_list == [] else random.choice(server_name_list)[0]
                                else:
                                    vc_name = random.choice(name_list)[0]
                            elif autovc[0][2] == True:
                                vc_name = random.choice(default_names) if server_name_list == [] else random.choice(server_name_list)[0]
                            clone = await after.channel.clone(name=vc_name, reason=f"{member.name} has created this VC.")
                            try:
                                await member.move_to(clone)
                            except:
                                pass
                            await asyncio.sleep(1)
                            cur.execute(f"""INSERT INTO vclist (voicechl, owner, static) VALUES ('{clone.id}', '{member.id}', 'FALSE');
                                        SELECT auto_text FROM members WHERE user_id = '{member.id}';""")
                            auto_text = cur.fetchall()
                            if autovc[0][1] == False and auto_text[0][0] == True:
                                permissions = {member.guild.default_role : discord.PermissionOverwrite(view_channel=False),
                                            member : discord.PermissionOverwrite(view_channel=True),
                                            member.guild.me : discord.PermissionOverwrite(view_channel=True)}
                                text = await member.guild.create_text_channel(name=clone.name, overwrites=permissions, category=clone.category, topic=f"{member.name}'s Personal Voice Channel's Text Channel", reason=f"{member.name} created a text channel")
                                cur.execute(f"UPDATE vclist SET text = '{text.id}' WHERE voicechl = '{clone.id}';")
                                await text.send(f"Your personal text channel is here, {member.mention}", delete_after=20)
                                cur.execute(f"SELECT prefix FROM servers WHERE guild = '{member.guild.id}';")
                                prefix = cur.fetchall()
                                await text.send(f"If you do not want automatic text channels, type `{prefix[0][0]}Vc Disable_Text`\nIf you want to delete this text channel, type `{prefix[0][0]}Vc Delete_Text`")

                # Checking if hard disconnecting
                if after.channel == None:
                    pass
                # Triggers on joining if VC in database
                elif [vc for vc in vclist if after.channel.id in vc]:
                    cur.execute(f"SELECT text FROM vclist WHERE voicechl = '{after.channel.id}';")
                    text = cur.fetchall()
                    if text[0][0] != None:
                        text_channel = self.bot.get_channel(text[0][0])
                        permissions = text_channel.overwrites_for(member)
                        permissions.view_channel = True
                        await text_channel.set_permissions(member, overwrite=permissions)

                # Checking if hard joining
                if before.channel == None:
                    pass
                # Triggers on moving out of VC or hard disconnecting from VC
                elif after.channel != None and [vc for vc in vclist if before.channel.id in vc] or after.channel == None and [vc for vc in vclist if before.channel.id in vc]:
                    cur.execute(f"SELECT static, voicechl FROM vclist WHERE voicechl = '{before.channel.id}';")
                    vclist = cur.fetchall()
                    
                    # Triggers on empty and non-permanent VC
                    if len(before.channel.members) == 0 and vclist[0][0] == False:
                        try:
                            await before.channel.delete(reason='VC is empty.')
                        except:
                            pass
                    # Triggers on leaving personal voice channel if not deleted
                    elif vclist[0][1] == before.channel.id:
                        cur.execute(f"SELECT text FROM vclist WHERE voicechl = '{before.channel.id}';")
                        text = cur.fetchall()
                        if text[0][0] != None:
                            text_channel = self.bot.get_channel(text[0][0])
                            permissions = text_channel.overwrites_for(member)
                            permissions = None
                            await text_channel.set_permissions(member, overwrite=permissions)

            finally:
                conn.commit()
                cur.close()
                conn.close()

def setup(bot):
    bot.add_cog(Events(bot))