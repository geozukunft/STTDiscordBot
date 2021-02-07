import asyncio

from discord.ext import commands

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


class GeneralCog(commands.Cog, name='Admin'):
    """Admin Stuff"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='list', hidden=True)
    @commands.dm_only()
    @commands.is_owner()
    async def listmembers(self, ctx):
        guild = ""
        for guild in ctx.bot.guilds:
            if guild.id == Tokens.GUILD:
                break

        for member in guild.members:
            for role in member.roles:
                if role.name == "Schildkröte":
                    await ctx.send(member.nick + " " + "`" + str(member.id) + "`")

    @commands.command(name='generaterules', hidden=True)
    @commands.has_role('Social Media Manager')
    async def generaterules(self, ctx):
        pool = ctx.bot.pool

        message = await ctx.send("**REGELN**\n\n"
                                 "DEUTSCHSPRACHIGER SERVER / GERMAN SPEAKING SERVER\n"
                                 "1. Einhaltung der Netiquette \n"
                                 "2. Kanalbeschreibungen lesen! Topics nur in die dafür vorgesehenen Kanäle \n"
                                 "3. Streaming ist, zum Schutz der Privatsphäre unserer Mitglieder, nur im dafür vorgesehenen Bereich erlaubt.\n"
                                 "4. Das einladen von Freunden oder Bekannten ist jeder Schildkröte erlaubt.\n"
                                 "5. Um Schildkröte zu werden, und Zugriff auf den Server zu erhalten reagiere bitte auf diese Regeln.\n\n"
                                 "Anschließend kannst du mit unserem Bot <@757955495251279954> deine Name auf dem Server ändern, Rollen erhalten und "
                                 "deinen League of Legends Account verknüpfen.\n ")
        await message.add_reaction('✅')

        await asyncio.sleep(2)

        async with pool.acquire() as conn:
            await conn.execute('INSERT INTO reactions VALUES ($1, $2)', message.id, "RULES")
        print("test")

    @commands.command(name='generatelanes', hidden=True)
    @commands.has_role('Social Media Manager')
    async def generatelanes(self, ctx):
        pool = ctx.bot.pool

        message = await ctx.send('Reagiere bitte auf diese Nachricht welche Lanes du in League spielst.')
        await message.add_reaction('<:TopLane:777326001964974080>')
        await message.add_reaction('<:Jungle:777326001965105162>')
        await message.add_reaction('<:MidLane:777326001902059561>')
        await message.add_reaction('<:BotLane:777326001877286922>')
        await message.add_reaction('<:Support:777326002061180928>')

        await asyncio.sleep(2)

        async with pool.acquire() as conn:
            await conn.execute('INSERT INTO reactions VALUES ($1, $2)', message.id, "LANES")

    @commands.command(name='generatemain', hidden=True)
    @commands.has_role('Social Media Manager')
    async def generatemain(self, ctx):
        pool = ctx.bot.pool

        message = await ctx.send('Reagiere bitte auf diese Nachricht welche Lane du primär Spielst.')
        await message.add_reaction('<:TopLane:777326001964974080>')
        await message.add_reaction('<:Jungle:777326001965105162>')
        await message.add_reaction('<:MidLane:777326001902059561>')
        await message.add_reaction('<:BotLane:777326001877286922>')
        await message.add_reaction('<:Support:777326002061180928>')

        await asyncio.sleep(2)

        async with pool.acquire() as conn:
            await conn.execute('INSERT INTO reactions VALUES ($1, $2)', message.id, "MAINLANE")

    @commands.command(name='generateclash', hidden=True)
    @commands.has_role('Social Media Manager')
    async def generateclash(self, ctx):
        pool = ctx.bot.pool
        message = await ctx.send('Reagiere bitte auf diese Nachricht wenn du bei Organisierten Clash Events teilnehmen '
                                 'möchtest. \n**Wichtig du musst dazu bereits einen verknüpften und auch verifzierten '
                                 'League Account haben!**')
        await message.add_reaction('<:clash:783486810760282193>')

        await asyncio.sleep(2)

        async with pool.acquire() as conn:
            await conn.execute('INSERT INTO reactions VALUES ($1, $2)', message.id, "ROLES")

    @commands.command(name='listemojis', hidden=True)
    @commands.has_role('Social Media Manager')
    async def listemojis(self, ctx):
        for emoji in ctx.guild.emojis:
            await ctx.send(emoji.name + " " + str(emoji.id))
            await ctx.send(emoji)
        return


def setup(bot):
    bot.add_cog(GeneralCog(bot))