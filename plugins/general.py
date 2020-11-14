from discord.ext import commands

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(list)
    bot.add_command(generaterules)


@commands.command(name='list', hidden=True)
@commands.dm_only()
async def list(ctx):
    for guild in ctx.bot.guilds:
        if guild.id == Tokens.GUILD:
            break

    user = ctx.message.author

    for member in guild.members:
        for role in member.roles:
            if role.name == "Schildkröte":
                await ctx.send(member.nick + " " + "`" + str(member.id) + "`")


@commands.command(name='generaterules', hidden=True)
@commands.has_role('Social Media Manager')
async def generaterules(ctx):
    pool = ctx.bot.pool

    message = await ctx.send("FUCKING LANGER RULES TEXT BLA BLA BLA \n"
                             "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, \n"
                             "sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, \n"
                             "sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. \n"
                             "Stet clita kasd gubergren,\n"
                             "Zu Risiken und Nebenwirkungen lesen Sie die Packungsbeilage und fragen Sie Ihren Gott "
                             "oder Geo\n "
                             "Mit der Reaktion auf die Nachricht treten sie sämtliche Rechte ihres Lebens ab.")
    await message.add_reaction('✅')

    async with pool.acquire() as conn:
        await conn.execute('INSERT INTO reactions VALUES ($1, $2)', message.id, "RULES")
    print("test")


"""
@commands.command(name='ign', help='Update deinen ingame namen')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def ign(ctx, ign):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT firstname FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        await ctx.author.edit(nick=ign + " | " + row[0])
        async with pool.acquire() as conn:
            await conn.execute('UPDATE playerdata SET gametag = $1 WHERE idplayer = $2', ign, ctx.author.id)
        await ctx.send("Dein Nickname sieht nun folgendermaßen aus: `" + ctx.author.nick + "`")
    else:
        await ctx.send("Du scheinst noch nicht registriert zu sein bitte tu dies zuerst mit !register")
"""
