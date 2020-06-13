import discord
import os
import psycopg2
import datetime
import time
import asyncio
import __main__
import re
from discord.ext import commands
from guild import menu

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Lg', aliases=['Logout'], help='Bot goes offline')
    @commands.guild_only()
    @commands.is_owner()
    async def boutaheadout(self, ctx):
        try:
            await ctx.message.delete()
            await self.bot.close()
            print(f"{self.bot.user.name} has went offline.")
        except discord.Forbidden:
            try:
                await ctx.send("Permissions missing")
            except discord.Forbidden:
                return

    @commands.command(name='L', aliases=['Load'], help='Loads a cog.')
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            try:
                if extension != __main__.__file__.replace('.py', ''):
                    self.bot.load_extension(extension)
                    await ctx.send(f'Loaded {extension}')
                    print(f"Loaded {extension}")
                else:
                    await ctx.send(f"You can not load in the main file: {__main__.__file__.replace('.py', '')}")
            except Exception as error:
                await ctx.send(f'{extension} could not be loaded. [{error}]')
        except discord.Forbidden:
            return

    @commands.command(name='U', aliases=['Unload'], help='Unloads a cog.')
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            try:
                if extension != 'commands':
                    self.bot.unload_extension(extension)
                    await ctx.send(f'Unloaded {extension}')
                    print(f"Unloaded {extension}")
                else:
                    await ctx.send("Please try reloading this script instead!")
                    print("Please try reloading this script instead!")
            except Exception as error:
                await ctx.send(f'{extension} could not be unloaded. [{error}]')
        except discord.Forbidden:
            return
    
    @commands.command(name='R', aliases=['Reload'], help='Reloads a cog.')
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            try:
                self.bot.unload_extension(extension)
                con = await ctx.send(f'Unloaded {extension}')
                self.bot.load_extension(extension)
                await con.edit(content=f'Reloaded {extension}')
                print(f"Reloaded {extension}")
            except Exception as error:
                await ctx.send(f'{extension} could not be reloaded. [{error}]')
        except discord.Forbidden:
            return
    
    @commands.command(name='Rolelink', help='Link embeds for my server roles.') # Personal command
    @commands.is_owner()
    async def role_link(self, ctx):
        try:
            linkembed = discord.Embed(
                    title='CLICK THE LINK TO HAVE IT BRING YOU TO THE ROLES',
                    description='',
                    color=discord.Color.purple()
            )
            linkembed.add_field(name='`🌈 Color`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647707491169206302)', inline=True)
            linkembed.add_field(name='`🌈 Color list`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708228406345739)', inline=True)
            linkembed.add_field(name='`🤖 Bot Paradise`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647708342785146930)', inline=True)
            linkembed.add_field(name='`🗺️ Continent`', value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647709296284663820)', inline=True)
            linkembed.add_field(name="`🏠 Squee's House Category`", value='[Click Here](https://discordapp.com/channels/647205092029759488/647285590659694612/647709461317812246)', inline=True)

            await ctx.send(embed=linkembed)
        except:
            return

    @commands.command(name='Ping', help="Shows bot's latency in milliseconds.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        try:
            await ctx.send(f'Pong: {round(self.bot.latency * 1000)}ms')
        except:
            return

    @commands.command(name='Status', help="Changes bot's status message.") # Anyone can use this command and it changes the bot's status.
    @commands.cooldown(1, 300, commands.BucketType.default)
    async def status(self, ctx, *, changestatus=None): # example(*, args) : ex. "Example text" | example(*args) : ex. "Example" "text"
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur =conn.cursor()
            cur.execute(f"SELECT status_bl FROM members WHERE user_id = '{ctx.author.id}';")
            rows = cur.fetchall()
            for r in rows:
                if r[0] == False:
                    await ctx.send("You have been blacklisted from using this command.")
                    return
            if changestatus == None:
                cur.execute("UPDATE bot SET message = '' WHERE name = 'Status';")
                conn.commit()
                await self.bot.change_presence(activity=discord.Game(''))
                await ctx.message.add_reaction("✅")
            elif len(changestatus) <= 128:
                urls = re.findall(r'http[s]?://(?: |[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', changestatus)
                if urls:
                    await ctx.send(f'**{ctx.author.name}**! No links please, thank you.')
                else:
                    cur.execute(f"UPDATE bot SET message = '{changestatus}' WHERE name = 'Status';")
                    conn.commit()
                    await self.bot.change_presence(activity=discord.Game(changestatus))
                    await ctx.message.add_reaction("✅")
            elif len(changestatus) >= 128:
                await ctx.send(f"Character limit is 128. You reached {len(changestatus)} characters.")
            cur.close()
            conn.close()

    @commands.command(name='Uptime', help="Checks how long the bot has been online for.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def uptime(self, ctx):
        try:
            lt = time.time()
            d = int(round(lt - self.bot.global_ft))
            up = str(datetime.timedelta(seconds=d))
            await ctx.send(f"💌 | **{self.bot.user.name}'s** uptime: {up}")
        except discord.Forbidden:
            return
    @uptime.error
    async def uptime_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            return


    @commands.command(name='Avatar', aliases=['PFP', 'Picture'], help="Gets a valid user's profile picture.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(self, ctx, *, Member: discord.Member=None):
        try:
            if Member == None:
                Member = ctx.author
            e = discord.Embed(
                title=f"{Member}",
                description=f"[Link]({Member.avatar_url})",
                color=discord.Color.blue()
            )
            e.set_image(url=Member.avatar_url)
            await ctx.send(embed=e)
        except:
            return
    @avatar.error
    async def avatar_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument!")

    @commands.command(name='BL', aliases=['Blacklist'], help="Prevents specific user by ID from using a specific command.")
    @commands.is_owner()
    async def blacklist(self, ctx, ID, Name):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                try:
                    if Name.lower() == 'status':
                        member = self.bot.get_user(int(ID))
                        cur.execute(f"INSERT INTO members (user_id, status) VALUES ('{member.id}', FALSE) ON CONFLICT (user_id) DO UPDATE SET status = 'FALSE';")
                        await ctx.send(f"**{member.name}** has been blacklisted from using the **{Name.lower()}** command.")
                    else:
                        await ctx.send("Invalid command name. Current valid command names: status")
                except ValueError:
                    await ctx.send("User ID is required.")
            except AttributeError:
                await ctx.send("Member could not be found.")
            finally:
                conn.commit()
                cur.close()
                conn.close()

    @commands.command(name='Hangman', help="Play the game Hangman with another player")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def hangman(self, ctx):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            try:
                cur = conn.cursor()
                def verify(v):
                    return v.content and v.author == ctx.author and v.channel == ctx.channel
                def verify_r(reaction, user):
                    return user == ctx.author and reaction.message.id == msg.id

                options, spread = {"Play with Another Player" : "select", "View Your Game Stats" : "statistics"}, ''
                for num, option in enumerate(options.keys()):
                    spread += f"{num + 1}.) {option}\n"

                counter = 0
                info = False
                while True:
                    counter = counter + 1
                    if counter == 1:
                        e = discord.Embed(
                            title = "Play Hangman",
                            description = f"```py\n{spread}\n```\n🇽 Exit menu\nℹ️ More Information (Menu will stay intact)\n\nEnter one of the corresponding options",
                            color = discord.Color.purple()
                        )
                        e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}", icon_url=ctx.author.avatar_url)
                        msg = await ctx.send(embed=e)
                        await msg.add_reaction("🇽")
                        await msg.add_reaction("ℹ️")

                    try:
                        done, pending = await asyncio.wait([
                                        self.bot.wait_for('message', timeout=60, check=verify),
                                        self.bot.wait_for('reaction_add', check=verify_r)
                                        ], return_when=asyncio.FIRST_COMPLETED)
                        result = done.pop().result()
                        for future in pending:
                            future.cancel()

                        if '🇽' in str(result):
                            await msg.delete()
                            await ctx.send(menu.exit(self, ctx))
                            return
                        elif 'ℹ️' in str(result) and info == False:
                            info = True
                            await msg.clear_reaction("ℹ️")
                            await ctx.send("Take turns with another player to guess each other's words and see if you both win or lose and keep track of your stats through each game")
                        elif str(type(result)) == "<class 'tuple'>":
                            pass
                        elif result.content.isdigit() == False:
                            await result.add_reaction("❌")
                        elif int(result.content) <= len(options) and int(result.content) != 0:
                            await msg.delete()
                            await getattr(hangman, list(options.values())[int(result.content) - 1])(self, ctx, cur)
                            return
                        else:
                            await result.add_reaction("❌")

                    except asyncio.TimeoutError:
                        await msg.delete()
                        await ctx.send(menu.timeout(self, ctx))
                        return
            finally:
                conn.commit()
                cur.close()
                conn.close()

class hangman(object):
    def __init_(self, bot):
        self.bot = bot

    def player_timeout(self, ctx, player):
        return f"**{player.name}** took too long to respond"

    def host_timeout(self, ctx):
        return f"**{ctx.author.name}** took too long to respond"

    async def select(self, ctx, cur):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                msg = await ctx.send("Please **mention** a user to invite as a player.\nReact with the emoji to cancel.")
                await msg.add_reaction("⬅️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '⬅️' in str(result):
                    await msg.delete()
                    await Commands.hangman(self, ctx)
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif len(result.mentions) == 1 and [user for user in result.mentions if user.bot == False and user != ctx.author] != []:
                    await msg.delete()
                    player = result.mentions[0]
                    def verify_p(reaction, user):
                        return user == player and reaction.message.id == msg.id
                    counter = 0
                    while True:
                        counter = counter + 1
                        if counter == 1:
                            msg = await ctx.send(f"**{ctx.author.name}** would like to player with you, do you accept {player.mention}?")
                            await msg.add_reaction("✅")
                            await msg.add_reaction("❌")

                        try:
                            result = await self.bot.wait_for('reaction_add', timeout=180, check=verify_p)

                            if '✅' in str(result):
                                await msg.delete()
                                await hangman.host_words(self, ctx, cur, player)
                                return
                            elif '❌' in str(result):
                                await msg.delete()
                                await ctx.send(f"**{player.name}** declined your request to play, {ctx.author.mention}")
                                return

                        except asyncio.TimeoutError:
                            await msg.delete()
                            await ctx.send(hangman.player_timeout(self, ctx, player))
                            return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

    async def host_words(self, ctx, cur, player):
        def verify(v):
            return v.content and v.author == ctx.author and v.guild == None
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        counter = 0
        sent = 0
        while True:
            counter = counter + 1
            if counter == 1:
                try:
                    dm = await ctx.author.send("💌 | Please enter your word for hangman")
                    msg = await ctx.send(f"Check your DMs **{ctx.author.name}**!\n\n🇽 to cancel")
                    handle = False
                except:
                    msg = await ctx.send(f"""If you didn't get a DM {ctx.author.mention}, please allow me to DM you
Then react with the 🔄 emoji when done setting up\n\n🇽 to cancel""")
                    await msg.add_reaction("🔄")
                    handle = True
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=300, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🔄' in str(result) and sent < 2 and handle == True:
                    sent = sent + 1
                    await msg.remove_reaction("🔄", ctx.author)
                    if sent == 2:
                        await msg.clear_reaction("🔄")
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        dm = await ctx.author.send("💌 | Please enter your word for hangman")
                        await msg.edit(content=f"Check your DMs **{ctx.author.name}**!\n\n🇽 to cancel")
                        try:
                            await msg.clear_reaction("🔄")
                        except:
                            pass
                    except:
                        pass
                elif '🇽' in str(result):
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.replace(' ', '').isalpha():
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await result.add_reaction("✅")
                    await hangman.player_words(self, ctx, cur, player, ' '.join(result.content.split()))
                    return
                else:
                    await result.add_reaction("🚫")

            except asyncio.TimeoutError:
                try:
                    await msg.delete()
                except:
                    pass
                try:
                    await dm.delete()
                except:
                    pass
                await ctx.send(hangman.host_timeout(self, ctx))
                return

    async def player_words(self, ctx, cur, player, host_word):
        def verify(v):
            return v.content and v.author == player and v.guild == None
        def verify_r(reaction, user):
            return user == player and reaction.message.id == msg.id

        counter = 0
        sent = 0
        while True:
            counter = counter + 1
            if counter == 1:
                try:
                    dm = await player.send("💌 | Please enter your word for hangman")
                    msg = await ctx.send(f"Check your DMs **{player.name}**!\n\n🇽 to cancel")
                    handle = False
                except:
                    msg = await ctx.send(f"""If you didn't get a DM {player.mention}, please allow me to DM you
Then react with the 🔄 emoji when done setting up\n\n🇽 to cancel""")
                    await msg.add_reaction("🔄")
                    handle = True
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=300, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🔄' in str(result) and sent < 2 and handle == True:
                    sent = sent + 1
                    await msg.remove_reaction("🔄", player)
                    if sent == 2:
                        await msg.clear_reaction("🔄")
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        dm = await player.send("💌 | Please enter your word for hangman")
                        await msg.edit(content=f"Check your DMs **{player.name}**!\n\n🇽 to cancel")
                        try:
                            await msg.clear_reaction("🔄")
                        except:
                            pass
                    except:
                        pass
                elif '🇽' in str(result):
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await ctx.send(menu.exit(self, ctx))
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.replace(' ', '').isalpha():
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await result.add_reaction("✅")
                    await hangman.host_turn(self, ctx, cur, player, host_word, ' '.join(result.content.split()), 0, 0, [], [], None, None)
                    return
                else:
                    await result.add_reaction("🚫")

            except asyncio.TimeoutError:
                try:
                    await msg.delete()
                except:
                    pass
                try:
                    await dm.delete()
                except:
                    pass
                await ctx.send(hangman.player_timeout(self, ctx, player))
                return

    async def host_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win):
        def verify(v):
            return v.content and v.author == ctx.author and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id or user == player and reaction.message.id == msg.id

        if host_win != None and player_win == None:
            await hangman.player_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
            return
        elif host_win != None and player_win != None:
            host_game = 'Won' if host_win == True else 'Lost'
            player_game = 'Won' if player_win == True else 'Lost'
            e = discord.Embed(
                title = f"{ctx.author.name} has {host_game}!\n{player.name} has {player_game}!",
                description = f"Thank you for playing Hangman",
                color = discord.Color.purple()
            )
            e.set_author(name=f"Game Over", icon_url=ctx.author.avatar_url)
            e.set_footer(text=f'💌', icon_url=player.avatar_url)
            e.add_field(name=f"{ctx.author.name}'s Session Stats", value=f'```py\nWord: {host_word}\nStrikes: {host_strikes}\nGuesses: {len(host_guess)}\n```', inline=False)
            e.add_field(name=f"{player.name}'s Session Stats", value=f'```py\nWord: {player_word}\nStrikes: {player_strikes}\nGuesses: {len(player_guess)}\n```', inline=False)
            await ctx.send(embed=e)
            cur.execute(f"""INSERT INTO members (user_id) VALUES ('{ctx.author.id}') ON CONFLICT (user_id) DO NOTHING;
                        INSERT INTO members (user_id) VALUES ('{player.id}') ON CONFLICT (user_id) DO NOTHING;""")
            cur.execute(f"SELECT * FROM members WHERE user_id = '{ctx.author.id}';")
            host_stats = cur.fetchall()
            host_win_stat = 1 if host_win == True else 0
            host_lose_stat = 1 if host_win == False else 0
            cur.execute(f"SELECT * FROM members WHERE user_id = '{player.id}';")
            player_stats = cur.fetchall()
            player_win_stat = 1 if player_win == True else 0
            player_lose_stat = 1 if player_win == False else 0
            cur.execute(f"UPDATE members SET hm_wins = '{host_stats[0][4] + host_win_stat}', hm_losses = '{host_stats[0][5] + host_lose_stat}', hm_guesses = '{host_stats[0][6] + len(host_guess)}', hm_strikes = '{host_stats[0][7] + host_strikes}' WHERE user_id = '{ctx.author.id}';")
            cur.execute(f"UPDATE members SET hm_wins = '{player_stats[0][4] + player_win_stat}', hm_losses = '{player_stats[0][5] + player_lose_stat}', hm_guesses = '{player_stats[0][6] + len(player_guess)}', hm_strikes = '{player_stats[0][7] + player_strikes}' WHERE user_id = '{player.id}';")
            return

        counter = 0
        picture = ['https://cdn.discordapp.com/attachments/649823748652007441/721317050747977818/strike0.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318070223765515/strike1.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318081510506556/strike2.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318089852977192/strike3.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318099395149844/strike4.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318108895117312/strike5.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318117795561532/strike6.png']
        while True:
            counter = counter + 1
            if counter == 1:
                guesses = ''
                for guess in host_guess:
                    guesses += guess if host_guess[-1] == guess else f"{guess}, "
                letters = ''
                for n, letter in enumerate(player_word):
                    if letter.lower() in host_guess:
                        letters += f'{letter} '
                    else:
                        if n + 1 == len(player_word):
                            letters += '_' if letter != ' ' else '  '
                        else:
                            letters += '_ ' if letter != ' ' else '  '
                e = discord.Embed(
                    title = f"{len(player_word.replace(' ', ''))} Letters\n`{letters}`",
                    description = f"```py\nEnter a letter as a 'message' to guess\n```\n🇽 Exit menu",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"{ctx.author.name}'s turn", icon_url=ctx.author.avatar_url)
                e.set_footer(text=f'Guesses:\n{guesses}')
                e.set_image(url=picture[host_strikes])
                msg = await ctx.send(embed=e)
                await msg.add_reaction("🇽")
            
            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=300, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(f"**{result[1].name}** has left the game")
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.lower() == player_word.lower() or len(result.content) == 1 and result.content.isalpha() and result.content.lower() in player_word.lower() and result.content.lower() not in host_guess:
                    await msg.delete()
                    await result.add_reaction("✅")
                    host_guess += [result.content.lower()]
                    correct = 0
                    for letter in set(player_word.replace(' ', '').lower()):
                        correct = correct + 1 if letter in host_guess else correct
                    if result.content.lower() == player_word.lower() or len(set(player_word.replace(' ', '').lower())) == correct:
                        host_win = True
                    await asyncio.sleep(1)
                    await hangman.player_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
                    return
                elif result.content.replace(' ', '').isalpha() and result.content.lower() not in host_guess or len(result.content) == 1 and result.content.isalpha() and result.content.lower() not in host_guess:
                    host_strikes = host_strikes + 1
                    await msg.delete()
                    await result.add_reaction("❌")
                    if host_strikes == 7:
                        host_win = False
                    host_guess += [result.content.lower()]
                    await asyncio.sleep(1)
                    await hangman.player_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
                    return
                else:
                    await result.add_reaction("🚫")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(hangman.host_timeout(self, ctx))
                return

    async def player_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win):
        def verify(v):
            return v.content and v.author == player and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id or user == player and reaction.message.id == msg.id

        if player_win != None and host_win == None or host_win != None and player_win != None:
            await hangman.host_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
            return

        counter = 0
        picture = ['https://cdn.discordapp.com/attachments/649823748652007441/721317050747977818/strike0.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318070223765515/strike1.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318081510506556/strike2.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318089852977192/strike3.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318099395149844/strike4.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318108895117312/strike5.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318117795561532/strike6.png']
        while True:
            counter = counter + 1
            if counter == 1:
                guesses = ''
                for guess in player_guess:
                    guesses += guess if player_guess[-1] == guess else f"{guess}, "
                letters = ''
                for n, letter in enumerate(host_word):
                    if letter.lower() in player_guess:
                        letters += f'{letter} '
                    else:
                        if n + 1 == len(host_word):
                            letters += '_' if letter != ' ' else '  '
                        else:
                            letters += '_ ' if letter != ' ' else '  '
                e = discord.Embed(
                    title = f"{len(host_word.replace(' ', ''))} Letters\n`{letters}`",
                    description = f"```py\nEnter a letter as a 'message' to guess\n```\n🇽 Exit menu",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"{player.name}'s turn", icon_url=player.avatar_url)
                e.set_footer(text=f'Guesses:\n{guesses}')
                e.set_image(url=picture[player_strikes])
                msg = await ctx.send(embed=e)
                await msg.add_reaction("🇽")
            
            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=300, check=verify),
                                self.bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(f"**{result[1].name}** has left the game")
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.lower() == host_word.lower() or len(result.content) == 1 and result.content.isalpha() and result.content.lower() in host_word.lower() and result.content.lower() not in player_guess:
                    await msg.delete()
                    await result.add_reaction("✅")
                    player_guess += [result.content.lower()]
                    correct = 0
                    for letter in set(host_word.replace(' ', '').lower()):
                        correct = correct + 1 if letter in player_guess else correct
                    if result.content.lower() == host_word.lower() or len(set(host_word.replace(' ', '').lower())) == correct:
                        player_win = True
                    await asyncio.sleep(1)
                    await hangman.host_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
                    return
                elif result.content.replace(' ', '').isalpha() and result.content.lower() not in player_guess or len(result.content) == 1 and result.content.isalpha() and result.content.lower() not in player_guess:
                    player_strikes = player_strikes + 1
                    await msg.delete()
                    await result.add_reaction("❌")
                    if player_strikes == 7:
                        player_win = False
                    player_guess += [result.content.lower()]
                    await asyncio.sleep(1)
                    await hangman.host_turn(self, ctx, cur, player, host_word, player_word, host_strikes, player_strikes, host_guess, player_guess, host_win, player_win)
                    return
                else:
                    await result.add_reaction("🚫")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(hangman.player_timeout(self, ctx, player))
                return

    async def statistics(self, ctx, cur):
        def verify_r(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id

        cur.execute(f"INSERT INTO members (user_id) VALUES ('{ctx.author.id}') ON CONFLICT (user_id) DO NOTHING;")

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                cur.execute(f"SELECT * FROM members WHERE user_id = '{ctx.author.id}';")
                stats = cur.fetchall()
                e = discord.Embed(
                    title = "Hangman Statistics",
                    description = f"```py\nWins: {stats[0][4]}\nLosses: {stats[0][5]}\nGuesses: {stats[0][6]}\nStrikes: {stats[0][7]}\n```\n⬅️ Go back\n🇽 Exit menu",
                    color = discord.Color.purple()
                )
                e.set_footer(text=f"Name: {ctx.author.name}\nID: {ctx.author.id}", icon_url=ctx.author.avatar_url)
                msg = await ctx.send(embed=e)
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🇽")

            try:
                result = await self.bot.wait_for('reaction_add', timeout=60, check=verify_r)

                if '⬅️' in str(result):
                    await msg.delete()
                    await Commands.hangman(self, ctx)
                    return
                elif '🇽' in str(result):
                    await msg.delete()
                    await ctx.send(menu.exit(self, ctx))
                    return

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
                return

def setup(bot):
    bot.add_cog(Commands(bot))