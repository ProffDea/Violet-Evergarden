import discord
import time
import datetime
import asyncio
from discord.ext import commands
from postgresql import database
from interactions import menu

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='Prefix')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def prefix(self, ctx, *, new_prefix=None):
        if not ctx.guild:
            await ctx.send("💌 | My prefix is `v.` or you can just @ me")
        else:
            db = database()
            db.connect()
            try:
                if new_prefix == None:
                    db.cur.execute(f'''
                        SELECT prefix
                        FROM guilds
                        WHERE guild = '{ctx.guild.id}';
                        ''')
                    server_prefix = db.cur.fetchall()
                    await ctx.send(f"💌 | **{ctx.guild.name}**'s Prefix: `{server_prefix[0][0]}`")
                elif ctx.channel.permissions_for(ctx.author).manage_guild == True and new_prefix != None and len(new_prefix) < 10:
                    db.cur.execute(f'''
                        UPDATE guilds
                        SET prefix = '{new_prefix}'
                        WHERE guild = '{ctx.guild.id}';
                        ''')
                    await ctx.message.add_reaction('✅')
                else:
                    await ctx.message.add_reaction('❌')
            finally:
                db.close()

    @commands.command(name='Avatar', aliases=['PFP', 'Picture'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def avatar(self, ctx, *, member: discord.Member=None):
        if member == None:
            member = ctx.author
        eb = discord.Embed(
            title = f'{member}',
            description = f'[Link]({member.avatar_url})',
            color = discord.Color.purple()
        )
        eb.set_image(url=member.avatar_url)
        eb.set_footer(text='💌')
        await ctx.send(embed=eb)

    @commands.command(name='Ping', aliases=['Latency'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def ping(self, ctx):
        await ctx.send(f'💌 | Latency: **{round(self.bot.latency * 1000)}**ms')

    @commands.command(name='Uptime', aliases=['Ut'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def uptime(self, ctx):
        uptime = int(round(time.time() - self.bot.startup_time))
        orient = str(datetime.timedelta(seconds=uptime))
        await ctx.send(f"💌 | **{self.bot.user.name}**'s Uptime: `{orient}`")

    @commands.command(name='Voice', aliases=['Vc'])
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def vc(self, ctx, Menu=None, Channel=None):
        db = database()
        db.connect()
        try:
            vc = personal_voice(self.bot, ctx, db, menu())
            await vc.user()
        finally:
            db.close()

class personal_voice(object):
    def __init__(self, bot, ctx, db, menus):
        self.bot = bot
        self.ctx = ctx
        self.db = db
        self.menus = menus

    async def back(self, msg, menu):
        try:
            await msg.delete()
        except:
            pass
        await getattr(self, menu)()
        return False

    async def user(self):
        options, spread = {"Personal Voice Channel" : "personal", "User Settings" : "settings",
                        "Server Settings" : "server", "List All Menus" : "all"}, ''
        perms = self.ctx.channel.permissions_for(self.ctx.author)
        manage = perms.manage_channels
        if manage == False:
            options.pop("Server Settings")
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        msg = await self.menus.interface(
            self.ctx,
            'Vc',
            'User Menu',
            spread,
            f"\n{self.menus.exit_display}\n{self.menus.info_display}",
            f"Name: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(self.menus.exit_emoji)
        await msg.add_reaction(self.menus.more_info)
        info = False

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=60, check=self.menus.verify_message(self.ctx)),
                            self.bot.wait_for('reaction_add', check=self.menus.verify_reaction(self.ctx, msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Exit menu
                if self.menus.type_reaction(response) and self.menus.exit_emoji == response[0].emoji or self.menus.type_message(response) and self.menus.exit_response == response.content.lower():
                    loop = await self.menus.exit(self.ctx, msg)
                # More info
                elif self.menus.type_reaction(response) and self.menus.more_info == response[0].emoji and info == False:
                    info = True
                    await self.ctx.send(">>> **Personal Voice Channel**: Access everything to do with your own personal voice channels through this option" +
                                        "\n**User Settings**: Change settings correlating to your account that'll effect your personal voice channels" +
                                        "\n**Server Settings**: This option will only be visible to users with manage channel permissions. Change settings that'll help manage this server")
                # Number inbetween options
                elif self.menus.type_message(response) and response.content.isdigit() and int(response.content) <= len(options) and int(response.content) > 0:
                    await msg.delete()
                    await getattr(self, list(options.values())[int(response.content) - 1])()
                    loop = False
                else:
                    await self.menus.invalid(response)

            except asyncio.TimeoutError:
                loop = self.menus.timeout(self.ctx, msg)

    async def personal(self):
        pass

    async def settings(self):
        options, spread = {"Channel Name Randomizer" : "user_randomizer", "Text Channels" : "user_text"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        msg = await self.menus.interface(
            self.ctx,
            'Settings',
            'User Settings',
            spread,
            f"\n{self.menus.back_display}\n{self.menus.exit_display}",
            f"Name: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(self.menus.back_emoji)
        await msg.add_reaction(self.menus.exit_emoji)

        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=60, check=self.menus.verify_message(self.ctx)),
                            self.bot.wait_for('reaction_add', check=self.menus.verify_reaction(self.ctx, msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Go back
                if self.menus.type_reaction(response) and self.menus.back_emoji == response[0].emoji or self.menus.type_message(response) and self.menus.back_response == response.content.lower():
                    loop = await self.back(msg, 'user')
                # Exit menu
                elif self.menus.type_reaction(response) and self.menus.exit_emoji == response[0].emoji or self.menus.type_message(response) and self.menus.exit_response == response.content.lower():
                    loop = await self.menus.exit(self.ctx, msg)
                # Number inbetween options
                elif self.menus.type_message(response) and response.content.isdigit() and int(response.content) <= len(options) and int(response.content) > 0:
                    try:
                        await msg.delete()
                    except:
                        pass
                    await getattr(self, list(options.values())[int(response.content) - 1])()
                    loop = False
                else:
                    await self.menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await self.menus.timeout(self.ctx, msg)

    async def user_randomizer(self):
        options, spread = {"Add Names" : "user_randomizer_add",
                        "View/Edit Name List" : "user_randomizer_view"}, ''
        for num, option in enumerate(options.keys()):
            spread += f"{num + 1}.) {option}\n"

        msg = await self.menus.interface(
            self.ctx,
            'User_Randomizer',
            'Channel Name Randomizer Menu',
            spread,
            f"\n{self.menus.back_display}\n{self.menus.exit_display}",
            f"Name: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(self.menus.back_emoji)
        await msg.add_reaction(self.menus.exit_emoji)
        await msg.add_reaction(self.menus.more_info)
        info = False
        
        loop = True
        while loop:
            try:

                done, pending = await asyncio.wait([
                            self.bot.wait_for('message', timeout=60, check=self.menus.verify_message(self.ctx)),
                            self.bot.wait_for('reaction_add', check=self.menus.verify_reaction(self.ctx, msg))
                ], return_when=asyncio.FIRST_COMPLETED)
                response = done.pop().result()
                for future in pending:
                    future.cancel()

                # Go back
                if self.menus.type_reaction(response) and self.menus.back_emoji == response[0].emoji or self.menus.type_message(response) and self.menus.back_response == response.content.lower():
                    loop = await self.back(msg, 'settings')
                # Exit menu
                elif self.menus.type_reaction(response) and self.menus.exit_emoji == response[0].emoji or self.menus.type_message(response) and self.menus.exit_response == response.content.lower():
                    loop = await self.menus.exit(self.ctx, msg)
                # More info
                elif self.menus.type_reaction(response) and self.menus.more_info == response[0].emoji and info == False:
                    info = True
                    await self.ctx.send(f">>> The user (**{self.ctx.author.name}**) will be able to make and store a maximum of 30 custom made names." +
                                        "\nUpon the creation of the user's personal voice channel, 1 of these 30 names (or less) will be picked at random to represent the personal voice channel's name." +
                                        "\n\nNote: These names are global to all servers and the name will not be displayed but still stored if blacklisted in the server.")
                # Number inbetween options
                elif self.menus.type_message(response) and response.content.isdigit() and int(response.content) <= len(options) and int(response.content) > 0:
                    try:
                        await msg.delete()
                    except:
                        pass
                    await getattr(self, list(options.values())[int(response.content) - 1])()
                    loop = False
                else:
                    await self.menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await self.menus.timeout(self.ctx, msg)

    async def user_randomizer_add(self):
        self.db.cur.execute(f'''
            INSERT INTO users (user_id)
            VALUES
                    ('{self.ctx.author.id}')
            ON CONFLICT (user_id)
            DO NOTHING;

            INSERT INTO user_randomizer (user_reference)
            SELECT id
            FROM users
            WHERE user_id = '{self.ctx.author.id}'
            ON CONFLICT (user_reference)
            DO NOTHING;

            SELECT unnest(name_list)
            FROM user_randomizer
            INNER JOIN users ON user_randomizer .user_reference = users.id
            WHERE user_id = '{self.ctx.author.id}';
        ''')
        name_list = self.db.cur.fetchall()

        menus = menu()
        msg = await menus.interface(
            self.ctx,
            'User_Randomizer_Add',
            'Add Names Menu',
            "Enter a name as a 'message' one by one",
            f"\n{menus.back_display}\n{menus.exit_display}",
            f"Total Names: {len(name_list)}\nName: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(menus.back_emoji)
        await msg.add_reaction(menus.exit_emoji)

        left = 30 - len(name_list)
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

                if menus.type_reaction(response) and menus.back_emoji == response[0].emoji:
                    try:
                        await msg.delete()
                    except:
                        pass
                    await self.user_randomizer()
                    loop = False
                elif menus.type_reaction(response) and menus.exit_emoji == response[0].emoji:
                    loop = await menus.exit(self.ctx, msg)
                elif menus.type_message(response) and left > 0:
                    left = left - 1
                    self.db.cur.execute('''
                        UPDATE user_randomizer
                        SET name_list = name_list || $apostrophes${%s}$apostrophes$
                        FROM users
                        WHERE user_randomizer.user_reference = users.id AND users.user_id = %s;
                    ''' % (response.content, self.ctx.author.id))
                    await response.add_reaction('✅')
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await menus.timeout(self.ctx, msg)

    async def user_randomizer_view(self):
        self.db.cur.execute(f'''
            INSERT INTO users (user_id)
            VALUES
                    ('{self.ctx.author.id}')
            ON CONFLICT (user_id)
            DO NOTHING;

            INSERT INTO user_randomizer (user_reference)
            SELECT id
            FROM users
            WHERE user_id = '{self.ctx.author.id}'
            ON CONFLICT (user_reference)
            DO NOTHING;

            SELECT unnest(name_list)
            FROM user_randomizer
            INNER JOIN users ON user_randomizer .user_reference = users.id
            WHERE user_id = '{self.ctx.author.id}';
        ''')
        name_list, spread = self.db.cur.fetchall(), ''
        empty = False
        if name_list == []:
            spread += 'No names found'
            empty = True
        for name in name_list:
            spread += f"{name_list.index(name) + 1}.) {name[0]}\n" if name_list[-1] != name else f"{name_list.index(name) +1}.) {name[0]}"

        delete = '⚠️ Delete all names' if empty == False else ''
        menus = menu()
        msg = await menus.interface(
            self.ctx,
            'User_Randomizer_View',
            'View/Edit Name List Menu',
            spread,
            f"\nSelect number to remove name\n{menus.back_display}\n{menus.exit_display}\n{delete}",
            f"\nName: {self.ctx.author.name}\nID: {self.ctx.author.id}"
        )
        await msg.add_reaction(menus.back_emoji)
        await msg.add_reaction(menus.exit_emoji)
        if empty == False:
            await msg.add_reaction('⚠️')

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

                if menus.type_reaction(response) and menus.back_emoji == response[0].emoji or menus.type_message(response) and menus.back_response == response.content.lower():
                    try:
                        await msg.delete()
                    except:
                        pass
                    await self.user_randomizer()
                    loop = False
                elif menus.type_reaction(response) and menus.exit_emoji == response[0].emoji or menus.type_message(response) and menus.exit_response == response.content.lower():
                    loop = await menus.exit(self.ctx, msg)
                elif menus.type_reaction(response) and '⚠️' == response[0].emoji:
                    confirm = True
                    confirm_msg = await self.ctx.send(f"{self.ctx.author.mention} Are you sure you want to delete all names?")
                    await confirm_msg.add_reaction('✅')
                    await confirm_msg.add_reaction('❌')

                    while confirm:

                        done, pending = await asyncio.wait([
                                    self.bot.wait_for('message', timeout=60, check=menus.verify_message(self.ctx)),
                                    self.bot.wait_for('reaction_add', check=menus.verify_reaction(self.ctx, confirm_msg))
                        ], return_when=asyncio.FIRST_COMPLETED)
                        response = done.pop().result()
                        for future in pending:
                            future.cancel()

                        if menus.type_reaction(response) and '✅' == response[0].emoji:
                            try:
                                await msg.delete()
                            except:
                                pass
                            try:
                                await confirm_msg.delete()
                            except:
                                pass
                            self.db.cur.execute(f'''
                                UPDATE user_randomizer
                                SET name_list = NULL
                                FROM users
                                WHERE user_randomizer.user_reference = users.id AND users.user_id = '{self.ctx.author.id}';
                            ''')
                            await self.user_randomizer_view()
                            confirm = False
                            loop = False
                        elif menus.type_reaction(response) and '❌' == response[0].emoji:
                            try:
                                await confirm_msg.delete()
                            except:
                                pass
                            try:
                                await msg.remove_reaction('⚠️', self.ctx.author)
                            except:
                                pass
                            confirm = False
                        else:
                            await menus.invalid(response)
                elif menus.type_message(response) and response.content.isdigit() and int(response.content) <= len(name_list) and int(response.content) > 0:
                    try:
                        await msg.delete()
                    except:
                        pass
                    self.db.cur.execute(f'''
                        UPDATE user_randomizer
                        SET name_list = array_remove(name_list, $apostrophes${name_list[int(response.content) - 1][0]}$apostrophes$)
                        FROM users
                        WHERE user_randomizer.user_reference = users.id AND users.user_id = '{self.ctx.author.id}';
                    ''')
                    await response.add_reaction('✅')
                    await asyncio.sleep(1)
                    await self.user_randomizer_view()
                    loop = False
                else:
                    await menus.invalid(response)

            except asyncio.TimeoutError:
                loop = await menus.timeout(self.ctx, msg)
    
    async def user_text(self):
        pass
    
    async def server(self):
        pass

    async def all(self):
        pass

def setup(bot):
    bot.add_cog(Utility(bot))