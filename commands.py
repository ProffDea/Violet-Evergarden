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
        except discord.Forbidden:
            return

    @commands.command(name='Ping', help="Shows bot's latency in milliseconds.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        try:
            await ctx.send(f'Pong: {round(self.bot.latency * 1000)}ms')
        except discord.Forbidden:
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
            cur.execute(f"SELECT status FROM members WHERE user_id = '{ctx.author.id}';")
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
            cont = f"**{self.bot.user.name}'s** uptime: {up}"
            msg = await ctx.send(cont)
            counter = 0
            add_sec = 0
            while counter < 5:
                counter = counter + 1
                add_sec = add_sec + 1
                await asyncio.sleep(1)
                d = int(round(lt - self.bot.global_ft)) + add_sec
                up = str(datetime.timedelta(seconds=d))
                cont = f"**{self.bot.user.name}'s** uptime: {up}"
                await msg.edit(content=cont)
            await msg.edit(content=cont + "\n💌 | Exit")
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
        except discord.Forbidden:
            return

    @commands.command(name='BL', aliases=['Blacklist'], help="Prevents specific user by ID from using a specific command.")
    @commands.is_owner()
    async def blacklist(self, ctx, ID, Name):
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        except KeyError:
            conn = psycopg2.connect(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'))
        finally:
            cur = conn.cursor()
            try:
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
            conn.commit()
            cur.close()
            conn.close()

def setup(bot):
    bot.add_cog(Commands(bot))