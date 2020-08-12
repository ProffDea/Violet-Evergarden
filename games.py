import discord
import asyncio
from discord.ext import commands
from postgresql import database
from interactions import menu

class Games(commands.Cog):

    # So far Hangman is the only game that will be added any time soon

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Hangman', aliases=['Hm'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @commands.guild_only()
    async def hangman(self, ctx):
        menus = menu()
        options, spread = {"Play with Another Player" : "create_session", "View Statistics From Your Games" : "statistics"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        msg = await menus.interface(
            ctx,
            'Hm',
            'Hangman Menu',
            spread,
            f"\n{menus.exit_display}\n{menus.info_display}",
            f"Name: {ctx.author.name}\nID: {ctx.author.id}"
        )
        await msg.add_reaction(menus.exit_emoji)
        await msg.add_reaction(menus.more_info)
        info = False

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=60, check=menus.verify_message(ctx)),
                            self.bot.wait_for('reaction_add', check=menus.verify_reaction(ctx, msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Exit menu
                if menus.type_reaction(response) and menus.exit_emoji == response[0].emoji or menus.type_message(response) and response.content.lower() == menus.exit_response:
                    loop = await menus.exit(ctx, msg)
                # More information
                elif menus.type_reaction(response) and menus.more_info == response[0].emoji and info == False:
                    info = True
                    await ctx.send(">>> Take turns with another player to guess each other's words and see if you both win or lose and keep track of your stats through each game")
                # Select options
                elif response.content.isdigit() and int(response.content) <= len(options) and int(response.content) > 0:
                    await msg.delete()
                    await getattr(hangman(self.bot, ctx), list(options.values())[int(response.content) - 1])()
                    loop = False
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await menus.timeout(ctx, msg)

class hangman(object):

    # Status: Finished

    # Handles the session of the hangman game

    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
        self.accept_emoji = '✅'
        self.accept_display = '✅ Accept Invite'
        self.reject_emoji = '❌'
        self.reject_display = '❌ Reject Invite'
        self.host = None
        self.player = None

    def host_player_message(self):
        def verify(v):
            return v.content and v.author == self.host and v.channel == self.ctx.channel
        return verify

    def host_player_reaction(self, msg):
        def verify(reaction, user):
            return user == self.host and reaction.message.id == msg.id or user == self.player and reaction.message.id == msg.id
        return verify

    def player_message(self):
        def verify(v):
            return v.content and v.author == self.player and v.channel == self.ctx.channel
        return verify
    
    def player_reaction(self, msg):
        def verify(reaction, user):
            return user == self.player and reaction.message.id == msg.id
        return verify

    async def player_timeout(self, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"💌 | **{self.player.name}** took too long to respond.")
        except:
            pass
        return False

    async def create_session(self):
        menus = menu()
        msg = await menus.interface(
            self.ctx,
            'Hm',
            'Invite Player',
            "'Mention' a user to invite them to play",
            f"\n{menus.exit_display}",
            f"Name: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(menus.back_emoji)
        await msg.add_reaction(menus.exit_emoji)

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=60, check=menus.verify_message(self.ctx)),
                            self.bot.wait_for('reaction_add', check=menus.verify_reaction(self.ctx, msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Go back
                if menus.type_reaction(response) and menus.back_emoji == response[0].emoji or menus.type_message(response) and response.content.lower() == menus.back_response:
                    try:
                        await msg.delete()
                    except:
                        pass
                    await Games.hangman(self, self.ctx)
                    loop = False
                # Exit menu
                elif menus.type_reaction(response) and menus.exit_emoji == response[0].emoji or menus.type_message(response) and response.content.lower() == menus.exit_response:
                    loop = await menus.exit(self.ctx, msg)
                # Check for 1 mention in content
                elif len(response.mentions) == 1 and [user for user in response.mentions if user.bot == False and user != self.ctx.author] != []:
                    await msg.delete()
                    self.host = self.ctx.author
                    self.player = response.mentions[0]
                    await self.pending_invite()
                    loop = False
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await menus.timeout(self.ctx, msg)

    async def pending_invite(self):
        menus = menu()
        msg = await menus.interface(
            self.ctx,
            'Hm',
            'Pending Invite',
            f"'{self.host.name}' would like to play with you, do you accept '{self.player.name}'?",
            f"\n{self.accept_display}\n{self.reject_display}",
            f"Name: {self.player.name}\nID: {self.player.id}"
        )
        await msg.add_reaction(self.accept_emoji)
        await msg.add_reaction(self.reject_emoji)

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=300, check=self.player_message()),
                            self.bot.wait_for('reaction_add', check=self.player_reaction(msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Reject invite
                if menus.type_reaction(response) and self.reject_emoji == response[0].emoji:
                    loop = await self.rejection(msg)
                # Accept invite
                elif menus.type_reaction(response) and self.accept_emoji == response[0].emoji:
                    await msg.delete()
                    await self.game_loop()
                    loop = False
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await self.player_timeout(msg)

    async def rejection(self, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"**{self.player.name}** declined your request to play, {self.host.mention}")
        except:
            pass
        return False

    async def statistics(self):
        menus = menu()
        db = database()
        db.connect()
        try:

            db.cur.execute(f'''
                SELECT
                        hangman.wins,
                        hangman.losses,
                        hangman.guesses,
                        hangman.strikes
                FROM
                        users
                INNER JOIN hangman ON users .id = hangman.user_reference
                WHERE user_id = '{self.ctx.author.id}';
            ''')
            stats = db.cur.fetchall()
            if stats == []:
                wins, losses, guesses, strikes = 0, 0, 0, 0
            else:
                wins, losses, guesses, strikes = stats[0][0], stats[0][1], stats[0][2], stats[0][3]

            msg = await menus.interface(
                self.ctx,
                'Hm',
                'Hangman Statistics',
                f'Wins: {wins}\nLosses: {losses}\nGuesses: {guesses}\nStrikes: {strikes}',
                f'\n{menus.back_display}\n{menus.exit_display}',
                f"Name: {self.ctx.author.name}\nID: {self.ctx.author.id}"
            )
            await msg.add_reaction(menus.back_emoji)
            await msg.add_reaction(menus.exit_emoji)

            loop = True
            while loop:
                try:

                    done, pending = await asyncio.wait([
                                self.bot.wait_for('message', timeout=60, check=menus.verify_message(self.ctx)),
                                self.bot.wait_for('reaction_add', check=menus.verify_reaction(self.ctx, msg))
                    ], return_when=asyncio.FIRST_COMPLETED)
                    response = done.pop().result()
                    for future in pending:
                        future.cancel()

                    # Go back
                    if menus.type_reaction(response) and menus.back_emoji == response[0].emoji or menus.type_message(response) and menus.back_response == response.content.lower():
                        try:
                            await msg.delete()
                        except:
                            pass
                        await Games.hangman(self, self.ctx)
                        loop = False
                    # Exit menu
                    elif menus.type_reaction(response) and menus.exit_emoji == response[0].emoji:
                        loop = await menus.exit(self.ctx, msg)
                    else:
                        await menus.invalid(response)

                except asyncio.TimeoutError:
                    loop = await menus.timeout(self.ctx, msg)
        
        finally:
            db.close()

    async def game_loop(self):
        host = hangman_turn(self.bot, self.ctx, self.host)
        player = hangman_turn(self.bot, self.ctx, self.player)
        host = await host.phrase_input()
        if host == False:
            return
        player = await player.phrase_input()
        if player == False:
            return
        host.guess_phrase = player.phrase
        player.guess_phrase = host.phrase
        
        loop = True
        while loop:
            if host.progress == None:
                host = await host.game()
            if player.progress == None:
                player = await player.game()
            if host.progress != None and player.progress != None:
                self.host = host
                self.player = player
                loop = False
        await self.scoreboard()
        db = database()
        db.connect()
        try:
            self.host.update_db(db)
            self.player.update_db(db)
        finally:
            db.close()
        return

    async def scoreboard(self):
        host_status = 'Won' if self.host.progress == True else 'Lost'
        player_status = 'Won' if self.player.progress == True else 'Lost'
        eb = discord.Embed(
            title = f"{self.host.player.name} has {host_status}!\n{self.player.player.name} has {player_status}!",
            description = 'Thank you for playing Hangman',
            color = discord.Color.purple()
        )
        eb.set_author(name='Game Over', icon_url=self.host.player.avatar_url)
        eb.set_footer(text='💌', icon_url=self.player.player.avatar_url)
        eb.add_field(name=f"{self.host.player.name}'s Session Stats", value=f"```\nWord: {self.host.phrase}\nStrikes: {self.host.strikes}\nGuesses: {len(self.host.guesses)}\n```", inline=False)
        eb.add_field(name=f"{self.player.player.name}'s Session Stats'", value=f"```\nWord: {self.player.phrase}\nStrikes: {self.player.strikes}\nGuesses: {len(self.player.guesses)}\n```", inline=False)
        await self.ctx.send(embed=eb)
        return

class hangman_turn(object):

    # Status: Finished

    # Handles the players of the hangman session

    def __init__(self, bot, ctx, player):
        self.bot = bot
        self.ctx = ctx
        self.player = player
        self.phrase = None
        self.guess_phrase = ''
        self.strikes = 0
        self.guesses = []
        self.progress = None

    async def phrase_timeout(self, dm, msg):
        try:
            await dm.delete()
        except:
            pass
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"**{self.player.name}** took too long to repsond.")
        except:
            pass
        return False

    async def timeout(self, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"**{self.player.name}** took too long to respond.")
        except:
            pass
        self.progress = False
        return False

    def phrase_message(self):
        def verify(v):
            return v.content and v.author == self.player and v.guild == None
        return verify

    def game_reaction(self, msg):
        def verify(reaction, user):
            return user == self.player and reaction.message.id == msg.id
        return verify

    def game_message(self):
        def verify(v):
            return v.content and v.author == self.player and v.channel == self.ctx.channel
        return verify

    async def phrase_exit(self, dm, msg):
        try:
            await dm.delete()
        except:
            pass
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"**{self.player.name}** has canceled the game.")
        except:
            pass
    
    async def phrase_log(self, dm, msg, response):
        try:
            await dm.delete()
        except:
            pass
        try:
            await msg.delete()
        except:
            pass
        try:
            await response.add_reaction('✅')
        except:
            pass
        self.phrase = ' '.join(response.content.split())

    async def phrase_input(self):
        menus = menu()
        dm = await self.player.send("💌 | Please enter your `phrase` for hangman")
        msg = await menus.interface(
            self.ctx,
            'Hm',
            'Input Phrase',
            f"Check your DMs '{self.player.name}'",
            f"\n{menus.exit_display}",
            f"Name: {self.player.name}\nID: {self.player.id}"
        )
        await msg.add_reaction(menus.exit_emoji)

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=300, check=self.phrase_message()),
                            self.bot.wait_for('reaction_add', check=self.game_reaction(msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Cancels game
                if menus.type_reaction(response) and menus.exit_emoji == response[0].emoji:
                    await self.phrase_exit(dm, msg)
                    return False
                # Logs phrase
                elif menus.type_message(response) and '_' not in response.content:
                    await self.phrase_log(dm, msg, response)
                    return self
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await self.phrase_timeout(dm, msg)

    async def game(self):
        menus = menu()
        pictures = ['https://cdn.discordapp.com/attachments/649823748652007441/721317050747977818/strike0.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318070223765515/strike1.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318081510506556/strike2.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318089852977192/strike3.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318099395149844/strike4.png', 'https://cdn.discordapp.com/attachments/649823748652007441/721318108895117312/strike5.png',
                    'https://cdn.discordapp.com/attachments/649823748652007441/721318117795561532/strike6.png']
        eb = discord.Embed(
            title = f"{len(self.guess_phrase.replace(' ', ''))} Letters",
            description = f"```\n{self.list_phrase()}\n```\n🇽 Exit Game",
            color = discord.Color.purple()
        )
        eb.set_author(name=f"{self.player.name}'s turn", icon_url=self.player.avatar_url)
        eb.set_footer(text=f"Guesses:\n{self.list_guesses()}")
        eb.set_image(url=pictures[self.strikes])
        msg = await self.ctx.send(embed=eb)
        await msg.add_reaction(menus.exit_emoji)

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=300, check=self.game_message()),
                            self.bot.wait_for('reaction_add', check=self.game_reaction(msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                if menus.type_reaction(response) and menus.exit_emoji == response[0].emoji:
                    loop = await self.quit(msg)
                elif menus.type_message(response) and response.content.lower() == self.guess_phrase.lower() or menus.type_message(response) and len(response.content) == 1 and response.content.lower() in self.guess_phrase.lower() and response.content.lower() not in self.guesses:
                    loop = await self.correct(msg, response)
                elif menus.type_message(response) and len(response.content) != 1 and response.content.lower() not in self.guesses or menus.type_message(response) and len(response.content) == 1 and response.content.isalpha() and response.content.lower() not in self.guesses:
                    loop = await self.incorrect(msg, response)
                else:
                    await menus.invalid("🚫")

            except asyncio.TimeoutError:
                loop = await self.timeout(msg)

        return self

    async def quit(self, msg):
        try:
            await msg.delete()
        except:
            pass
        try:
            await self.ctx.send(f"**{self.player.name}** left the game")
        except:
            pass
        self.progress = False
        return False

    async def correct(self, msg, response):
        try:
            await msg.delete()
        except:
            pass
        try:
            await response.add_reaction('✅')
        except:
            pass
        self.guesses += [response.content.lower()]
        right_answers = 0
        for letter in set(self.guess_phrase.lower()):
            if letter.isalpha():
                right_answers = right_answers + 1 if letter in self.guesses else right_answers
            else:
                right_answers = right_answers + 1
        if response.content.lower() == self.guess_phrase.lower() or len(set(self.guess_phrase.lower())) == right_answers:
            self.progress = True
        await asyncio.sleep(1)
        return False

    async def incorrect(self, msg, response):
        self.strikes = self.strikes + 1
        try:
            await msg.delete()
        except:
            pass
        try:
            await response.add_reaction('❌')
        except:
            pass
        if self.strikes == 7:
            self.progress = False
        self.guesses += [response.content.lower()]
        await asyncio.sleep(1)
        return False

    def list_guesses(self):
        guesses = ''
        for guess in self.guesses:
            guesses += guess if self.guesses[-1] == guess else f"{guess}, "
        return guesses

    def list_phrase(self):
        letters = ''
        for num, letter in enumerate(self.guess_phrase):
            if letter.lower() in self.guesses:
                if num + 1 == len(self.guess_phrase):
                    letters += letter
                else:
                    letters += f'{letter} ' if self.guess_phrase[num + 1].isalpha() else letter
            else:
                if letter.isalpha() and num + 1 != len(self.guess_phrase):
                    letters += '_ ' if self.guess_phrase[num + 1].isalpha() else '_'
                elif letter.isalpha() and num + 1 == len(self.guess_phrase):
                    letters += '_'
                else:
                    letters += letter if letter != ' ' or num + 1 == len(self.guess_phrase) else '  '
        return letters

    def update_db(self, db):
        db.cur.execute(f'''
            INSERT INTO users (user_id)
            VALUES
                    ('{self.player.id}')
            ON CONFLICT (user_id)
            DO NOTHING;

            INSERT INTO hangman (user_reference)
            SELECT id
            FROM users
            WHERE user_id = '{self.player.id}'
            ON CONFLICT (user_reference)
            DO NOTHING;

            SELECT wins, losses, guesses, strikes
            FROM hangman
            INNER JOIN users ON hangman .user_reference = users.id
            WHERE user_id = '{self.player.id}';
        ''')
        stats = db.cur.fetchall()
        win = 1 if self.progress == True else 0
        loss = 1 if self.progress == False else 0
        db.cur.execute(f'''
            UPDATE hangman
            SET wins = '{win + stats[0][0]}',
                losses = '{loss + stats[0][1]}',
                guesses = '{len(self.guesses) + stats[0][2]}',
                strikes = '{self.strikes + stats[0][3]}'
            FROM users
            WHERE hangman.user_reference = users.id AND users.user_id = {self.player.id};
        ''')

def setup(bot):
    bot.add_cog(Games(bot))