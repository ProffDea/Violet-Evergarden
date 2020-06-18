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
                            title = "Hangman",
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
                            await ctx.send(">>> Take turns with another player to guess each other's words and see if you both win or lose and keep track of your stats through each game")
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

    async def select(self, ctx, cur):
        host = hangman_player(ctx.author)
        def verify(v):
            return v.content and v.author == host.user and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == host.user and reaction.message.id == msg.id

        counter = 0
        while True:
            counter = counter + 1
            if counter == 1:
                msg = await ctx.send("Please **mention** a user to invite as a player.\nReact with the emoji to cancel.")
                await msg.add_reaction("⬅️")

            try:
                done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=300, check=verify),
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
                elif len(result.mentions) == 1 and [user for user in result.mentions if user.bot == False and user != host.user] != []:
                    await msg.delete()
                    player = hangman_player(result.mentions[0])
                    def verify_p(reaction, user):
                        return user == player.user and reaction.message.id == msg.id
                    counter = 0
                    while True:
                        counter = counter + 1
                        if counter == 1:
                            msg = await ctx.send(f"**{host.user.name}** would like to play with you, do you accept **{player.user.name}**?")
                            await msg.add_reaction("✅")
                            await msg.add_reaction("❌")

                        try:
                            result = await self.bot.wait_for('reaction_add', timeout=300, check=verify_p)

                            if '✅' in str(result):
                                await msg.delete()
                                await host.word_choice(self.bot, ctx, host, player)
                                if host.quit == True or player.quit == True:
                                    return
                                await player.word_choice(self.bot, ctx, host, player)
                                if player.quit == True or host.quit == True:
                                    return
                                while True:
                                    await host.game_loop(self.bot, ctx, cur, host, player)
                                    await player.game_loop(self.bot, ctx, cur, host, player)
                                    if host.progress != None and player.progress != None:
                                        await hangman.over(self, ctx, host, player)
                                        host.update_db(cur)
                                        player.update_db(cur)
                                        return
                            elif '❌' in str(result):
                                await msg.delete()
                                await ctx.send(f"**{player.user.name}** declined your request to play, {host.user.mention}")
                                return

                        except asyncio.TimeoutError:
                            await msg.delete()
                            await ctx.send(player.timeout())
                            return
                else:
                    await result.add_reaction("❌")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(menu.timeout(self, ctx))
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

    async def over(self, ctx, host, player):
        host_game = host.user_game_status()
        player_game = player.user_game_status()
        e = discord.Embed(
            title = f"{host.user.name} has {host_game}!\n{player.user.name} has {player_game}!",
            description = f"Thank you for playing Hangman",
            color = discord.Color.purple()
        )
        e.set_author(name=f"Game Over", icon_url=host.user.avatar_url)
        e.set_footer(text=f'💌', icon_url=player.user.avatar_url)
        e.add_field(name=f"{host.user.name}'s Session Stats", value=f'```py\nWord: {host.word}\nStrikes: {host.strikes}\nGuesses: {len(host.guesses)}\n```', inline=False)
        e.add_field(name=f"{player.user.name}'s Session Stats", value=f'```py\nWord: {player.word}\nStrikes: {player.strikes}\nGuesses: {len(player.guesses)}\n```', inline=False)
        await ctx.send(embed=e)
        return

class hangman_player(hangman):
    def __init__(self, user):
        self.user = user
        self.word = None
        self.strikes = 0
        self.guesses = []
        self.progress = None
        self.quit = False
        self.out = False

    def timeout(self):
        return f"**{self.user.name}** took too long to respond"

    def hangman_word(self, word):
        self.word = word

    def add_strike(self):
        self.strikes = self.strikes + 1

    def add_guess(self, guess):
        self.guesses += [guess]
    
    def victory(self):
        self.progress = True
    
    def failure(self):
        self.progress = False

    def exit_game(self):
        self.quit = True

    def game_over(self):
        self.out = True

    async def word_choice(self, bot, ctx, host, player):
        if self.word == None:
            await self.word_input(bot, ctx, host, player)
        return

    async def game_loop(self, bot, ctx, cur, host, player):
        if self.quit == True and self.progress == None and self.out == False:
            self.game_over()
            self.failure()
        if self.progress == None and self.out == False:
            await self.game(bot, ctx, host, player)

    def list_guesses(self):
        guesses = ''
        for guess in self.guesses:
            guesses += guess if self.guesses[-1] == guess else f"{guess}, "
        return guesses

    def list_guessed_words(self, word):
        if self.quit != True:
            letters = ''
            for n, letter in enumerate(word):
                if letter.lower() in self.guesses:
                    if n + 1 == len(word):
                        letters += letter
                    else:
                        letters += f'{letter} ' if word[n + 1].isalpha() else letter
                else:
                    if letter.isalpha() and n + 1 != len(word):
                        letters += '_ ' if word[n + 1].isalpha() else '_'
                    elif letter.isalpha() and n + 1 == len(word):
                        letters += '_'
                    else:
                        letters += letter if letter != ' ' or  n + 1 == len(word) else '  '
            return letters

    def update_db(self, cur):
        cur.execute(f"INSERT INTO members (user_id) VALUES ('{self.user.id}') ON CONFLICT (user_id) DO NOTHING;")
        cur.execute(f"SELECT * FROM members WHERE user_id = '{self.user.id}';")
        stats = cur.fetchall()
        win_stat = 1 if self.progress == True else 0
        lost_stat = 1 if self.progress == False else 0
        cur.execute(f"UPDATE members SET hm_wins = '{stats[0][4] + win_stat}', hm_losses = '{stats[0][5] + lost_stat}', hm_guesses = '{stats[0][6] + len(self.guesses)}', hm_strikes = '{stats[0][7] + self.strikes}' WHERE user_id = '{self.user.id}';")
        return

    def user_game_status(self):
        if self.quit == True:
            user_status = 'left the game'
        elif self.progress == True:
            user_status = 'Won'
        elif self.progress == False:
            user_status = 'Lost'
        else:
            user_status = 'been Undecided'
        return user_status

    async def word_input(self, bot, ctx, host, player):
        def verify(v):
            return v.content and v.author == self.user and v.guild == None
        def verify_r(reaction, user):
            return user == host.user and reaction.message.id == msg.id or user == player.user and reaction.message.id == msg.id
        
        counter = 0
        sent = 0
        while True:
            counter = counter + 1
            if counter == 1:
                try:
                    dm = await self.user.send("💌 | Please enter your word for hangman")
                    msg = await ctx.send(f"Check your DMs **{self.user.name}**!\n\n🇽 to cancel")
                    handle = False
                except:
                    msg = await ctx.send(f"""If you didn't get a DM {self.user.mention}, please allow me to DM you
Then react with the 🔄 emoji when done setting up\n\n🇽 to cancel""")
                    await msg.add_reaction("🔄")
                    handle = True
                await msg.add_reaction("🇽")

            try:
                done, pending = await asyncio.wait([
                                bot.wait_for('message', timeout=300, check=verify),
                                bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🔄' in str(result) and sent < 2 and handle == True:
                    sent = sent + 1
                    await msg.remove_reaction("🔄", self.user)
                    if sent == 2:
                        await msg.clear_reaction("🔄")
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        dm = await self.user.send("💌 | Please enter your word for hangman")
                        await msg.edit(content=f"Check your DMs **{self.user.name}**!\n\n🇽 to cancel")
                        try:
                            await msg.clear_reaction("🔄")
                        except:
                            pass
                    except:
                        pass
                elif '🇽' in str(result) and host.quit != True and result[1] == host.user or '🇽' in str(result) and player.quit != True and result[1] == player.user:
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await ctx.send(f"**{result[1].name}** has canceled the game")
                    if result[1] == player.user:
                        player.exit_game()
                    elif result[1] == host.user:
                        host.exit_game()
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif '_' not in result.content:
                    try:
                        await dm.delete()
                    except:
                        pass
                    try:
                        await msg.delete()
                    except:
                        pass
                    await result.add_reaction("✅")
                    self.hangman_word(' '.join(result.content.split()))
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
                await ctx.send(self.timeout())
                host.exit_game()
                player.exit_game()
                return

    async def game(self, bot, ctx, host, player):
        def verify(v):
            return v.content and v.author == self.user and v.channel == ctx.channel
        def verify_r(reaction, user):
            return user == host.user and reaction.message.id == msg.id or user == player.user and reaction.message.id == msg.id

        counter = 0
        picture = ['https://cdn.discordapp.com/attachments/649823748652007441/721317050747977818/strike0.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318070223765515/strike1.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318081510506556/strike2.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318089852977192/strike3.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318099395149844/strike4.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318108895117312/strike5.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318117795561532/strike6.png']
        while True:
            counter = counter + 1
            if counter == 1:
                guesses = self.list_guesses()
                word = player.word if self.user == host.user else host.word
                letters = self.list_guessed_words(word)
                e = discord.Embed(
                    title = f"{len(word.replace(' ', ''))} Letters",
                    description = f"```\n{letters}\n```\n🇽 Exit Game",
                    color = discord.Color.purple()
                )
                e.set_author(name=f"{self.user.name}'s turn", icon_url=self.user.avatar_url)
                e.set_footer(text=f'Guesses:\n{guesses}')
                e.set_image(url=picture[self.strikes])
                msg = await ctx.send(embed=e)
                await msg.add_reaction("🇽")
            
            try:
                done, pending = await asyncio.wait([
                                bot.wait_for('message', timeout=300, check=verify),
                                bot.wait_for('reaction_add', check=verify_r)
                                ], return_when=asyncio.FIRST_COMPLETED)
                result = done.pop().result()
                for future in pending:
                    future.cancel()

                if '🇽' in str(result) and host.quit != True and result[1] == host.user or '🇽' in str(result) and player.quit != True and result[1] == player.user:
                    await msg.delete()
                    await ctx.send(f"**{result[1].name}** has left the game")
                    if host.user == result[1]:
                        host.exit_game()
                    elif player.user == result[1]:
                        player.exit_game()
                    return
                elif str(type(result)) == "<class 'tuple'>":
                    pass
                elif result.content.lower() == word.lower() or len(result.content) == 1 and result.content.isalpha() and result.content.lower() in word.lower() and result.content.lower() not in self.guesses:
                    await msg.delete()
                    await result.add_reaction("✅")
                    self.guesses += [result.content.lower()]
                    correct = 0
                    for letter in set(word.lower()):
                        if letter.isalpha():
                            correct = correct + 1 if letter in self.guesses else correct
                        else:
                            correct = correct + 1
                    if result.content.lower() == word.lower() or len(set(word.lower())) == correct:
                        self.victory()
                    await asyncio.sleep(1)
                    return
                elif result.content and result.content.lower() not in self.guesses or len(result.content) == 1 and result.content.isalpha() and result.content.lower() not in self.guesses:
                    self.add_strike()
                    await msg.delete()
                    await result.add_reaction("❌")
                    if self.strikes == 7:
                        self.failure()
                    self.guesses += [result.content.lower()]
                    await asyncio.sleep(1)
                    return
                else:
                    await result.add_reaction("🚫")

            except asyncio.TimeoutError:
                await msg.delete()
                await ctx.send(self.timeout())
                self.exit_game()
                return

def setup(bot):
    bot.add_cog(Commands(bot))