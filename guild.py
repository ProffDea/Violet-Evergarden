import json
import asyncio
import discord
import os
import psycopg2
from discord.ext import commands

TestServerID = 648977487744991233 # ID is the test server ID. Feel free to change it
MissingPerm = "Missing permissions. Please make sure I have all the necessary permissions to properly work!\nPermissions such as: `Manage Channels`, `Read Text Channels & See Voice Channels`, `Send Messages`, `Manage Messages`, `Use External Emojis`, `Connect`, `Move Members`"
menuexit = 'Menu has been exited.'
menutimeout = 'Menu has been exited due to timeout.'
menuerror = 'Menu has been exited due to error (most likely menu got deleted).'

class Settings(commands.Cog):
    def __init__(self, bot):
            self.bot = bot

    @commands.command(name='Prefix', help='Allows to change the default prefix to a custom one.')
    @commands.guild_only()
    async def prefix(self, ctx, *, changeprefix=None):
        try: # Catches keyerror
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try: # Catches forbidden
                if ctx.channel.permissions_for(ctx.author).manage_guild == True and changeprefix != None:
                    if len(changeprefix) <= 9:
                        cur.execute(f"UPDATE servers SET prefix = '{changeprefix}' WHERE guild = '{ctx.guild.id}';")
                        await ctx.send(f"Prefix for `{ctx.guild.name}` has been changed to **{changeprefix}**")
                    else:
                        await ctx.send("Please make the prefix less than 10 characters long.")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == False and changeprefix != None:
                    await ctx.send("This command requires the user to have `Manage Server` permissions to use.")
                cur.execute(f"SELECT prefix FROM servers WHERE guild = '{ctx.guild.id}';")
                rows = cur.fetchall()
                for r in rows:
                    prefixmsg = r[0]
                    break
                if ctx.channel.permissions_for(ctx.author).manage_guild == True and changeprefix == None:
                    await ctx.send(f"The current prefix for this server is **{prefixmsg}**\n\nIn order to change the prefix of the server, type `{prefixmsg}prefix [TEXT]`")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == False and changeprefix == None:
                    await ctx.send(f"The current prefix for the server is **{prefixmsg}**")
            except discord.Forbidden:
                try:
                    await ctx.send(MissingPerm)
                except:
                    return
            conn.commit()
            cur.close()
            conn.close()

    @commands.command(name='Vc', help='In Beta')
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def vc(self, ctx):
        def menu(m):
            return m.content and m.author == ctx.author and m.channel == ctx.channel
        counter = 0
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try: # Catches timeout error
                while True: # Menu for the user
                    counter = counter + 1
                    if counter == 1:
                        cur.execute(f"SELECT autovc FROM servers WHERE guild = '{ctx.guild.id}';")
                        rows = cur.fetchall()
                        for r in rows:
                            if r[0] == None:
                                value = 'None'
                                break
                            else:
                                get = self.bot.get_channel(r[0])
                                value = get.name
                                break
                        cont = f"```py\n'Menu for User' - {ctx.author.name}\n```\n**`1.)`** `Auto Voice Channel :` {value}\n`2.)` `Personal Voice Channel`\n\n```py\n# Enter one of the corresponding options\nEnter 'exit' to leave menu\n```"
                        msg = await ctx.send(cont)
                    mm = await self.bot.wait_for('message', timeout=120, check=menu)
                    mmc = mm.content.lower()

                    if mmc == '1' or 'auto' in mmc:
                        await msg.delete()
                        counter = 0
                        while True: # Menu for Auto Voice Channel
                            counter = counter + 1
                            if counter == 1:
                                if value == 'None':
                                    option = ''
                                else:
                                    option = f" | Type `none` to remove *{value}*"
                                cont = f"```py\n'Menu for Auto Voice Channel' - {value}\n```\n**Please enter a valid voice channel**{option}\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining\nEnter 'back' to go back a menu\nEnter 'exit' to leave menu\n```"
                                msg = await ctx.send(cont)
                            mm = await self.bot.wait_for('message', timeout=120, check=menu)
                            mmc = mm.content.lower()
                            for chan in ctx.guild.channels:
                                isi = isinstance(chan, discord.VoiceChannel)

                                if mmc == chan.name.lower() and isi or mmc == str(chan.id) and isi or mmc == chan.mention.lower() and isi or mmc == 'none' and value != 'None':
                                    if mmc == 'none':
                                        place = 'None'
                                        clean = 'NULL'
                                    if mmc != 'none':
                                        place = chan.name
                                        clean = f"'{chan.id}'"
                                    await msg.delete()
                                    counter = 0
                                    while True: # Confirm Settings for Auto Voice Channel
                                        counter = counter + 1
                                        if counter == 1:
                                            cont = f"```py\n'Menu for Auto Voice Channel (Continued)' - {value}\n```\n`{place}` **Selected** | Type `confirm` to __save settings__\n\n```py\n# Auto Voice Channel will be the main voice channel used to create personal voice channels upon joining\nEnter 'back' to go back a menu\nEnter 'exit' to leave menu\n```"
                                            msg = await ctx.send(cont)
                                        mm = await self.bot.wait_for('message', timeout=120, check=menu)
                                        mmc = mm.content.lower()

                                        if mmc == 'confirm':
                                            await msg.delete()
                                            cur.execute(f"UPDATE servers SET autovc = {clean} WHERE guild = '{ctx.guild.id}';")
                                            cont = f"```py\n# Auto Voice Channel\n'SETTINGS SAVED'\n# from '{value}' to '{place}'\n```"
                                            await ctx.send(cont)
                                            return

                                        elif mmc == 'back':
                                            break

                                        elif mmc == 'exit':
                                            await msg.delete()
                                            await ctx.send(menuexit)
                                            return

                                        await ctx.send("Please choose a valid option.")

                                    # End of settings for Auto Voice Channel

                                else:
                                    pass

                            if mmc == 'back':
                                counter = 0
                                await msg.delete()
                                break

                            elif mmc == 'exit':
                                await msg.delete()
                                await ctx.send(menuexit)
                                return

                            await ctx.send("Please choose a valid option.")

                    # End of menu for Auto Voice Channel

                    elif mmc == '2' or 'personal' in mmc:
                        await msg.delete()
                        counter = 0
                        while True: # Menu for Personal Voice Channel
                            counter = counter + 1
                            if counter == 1:
                                cont = "```py\n'Menu for Personal Voice Channel'\n```\n`1.)` `Create voice channel`\n`2.)` `Manage voice channels`\n\n```py\n# Personal voice channels are channels made for server members to edit to their heart's content\nEnter 'back' to go back a menu\nEnter 'exit' to leave menu\n```"
                                msg = await ctx.send(cont)
                            mm = await self.bot.wait_for('message', timeout=120, check=menu)
                            mmc = mm.content.lower()

                            if mmc == '1' or 'create' in mmc:
                                await msg.delete()
                                cur.execute("SELECT owner FROM vclist;")
                                rows = cur.fetchall()
                                for r in rows:
                                    if r[0] == None:
                                        break
                                    elif r[0] == ctx.author.id:
                                        await ctx.send(f"```py\n# Personal Voice Channel\n```\n**❗CHANNEL DENIED❗**\n\n```py\n# {ctx.author.name} already has a voice channel created\n```")
                                        return
                                vc = await ctx.guild.create_voice_channel(name=f"💌{ctx.author.name}")
                                cur.execute(f"INSERT INTO vclist (voicechl, owner, members, static) VALUES ('{vc.id}', '{ctx.author.id}', '1', 'f')")
                                cont = f"```py\n# Personal Voice Channel\n```\n**CHANNEL CREATED**\n\n```py\n# name/id: {vc.name} ({vc.id})\n```"
                                msg = await ctx.send(cont)
                                return

                            elif mmc == '2' or 'manage' in mmc:
                                await msg.delete()
                                counter = 0
                                while True: # Menu for Managing
                                    counter = counter + 1
                                    if counter == 1:
                                        cont = f"```py\n'Menu for Personal Voice Channel - Manage Voice Channels'\n```\n\n\n```py\n# Change properties of voice channels that are owned by {ctx.author.name}\nEnter 'back' to go back a menu\nEnter 'exit' to leave menu\n```"
                                        msg = await ctx.send(cont)
                                    mm = await self.bot.wait_for('message', timeout=120, check=menu)
                                    mmc = mm.content.lower()

                                    if mmc == 'back':
                                        counter = 0
                                        await msg.delete()
                                        break

                                    elif mmc == 'exit':
                                        await msg.delete()
                                        await ctx.send(menuexit)
                                        return

                                    await ctx.send("Please choose a valid option.")

                            elif mmc == 'back':
                                counter = 0
                                await msg.delete()
                                break

                            elif mmc == 'exit':
                                await msg.delete()
                                await ctx.send(menuexit)
                                return

                            await ctx.send("Please choose a valid option.")

                        # End of menu for Personal Voice Channel
                    
                    elif mmc == 'exit':
                        await msg.delete()
                        await ctx.send(menuexit)
                        return

                    await ctx.send("Please choose a valid option.")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menutimeout)
            finally:
                conn.commit()
                cur.close()
                conn.close()
    @vc.error
    async def vc_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(menuerror)
            raise error
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        else:
            raise error

def setup(bot):
    bot.add_cog(Settings(bot))