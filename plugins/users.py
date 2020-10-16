from discord.ext import commands
from asyncpg.pool import Pool
import re

from main import Tokens


TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.my_region
api_key = Tokens.api_key


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(register)


@commands.command(name='register', help='Registriere dich im Spielerverzeichniss')
@commands.dm_only()
async def register(ctx):
    pool = ctx.bot.pool
    schildkroete = False
    for guild in ctx.bot.guilds:
        if guild.id == GUILD:
            break

    user = ctx.message.author

    for member in guild.members:
        if member.id == user.id:
            break
    for role in member.roles:
        if role.name == "Schildkröte":
            schildkroete = True

    if schildkroete is True:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM "playerdata" WHERE "idplayer" = $1', member.id)
        if row is None:
            if member.nick is not None:
                name = re.findall(r"(\w+)", member.nick)
                if name is not None:
                    async with pool.acquire() as conn:
                        await conn.execute('INSERT INTO playerdata VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)',
                                           member.id, name[1], name[0], False, False, False, False, False, "k.A.")
                    await ctx.send("Du bist nun Registriert du kannst nun mit !main deine Main Lane eintragen "
                                   "oder mit !top, !jgl usw. eintragen welche Lanes du Spielen kannst")
                else:
                    await ctx.send("Du hast auf dem STT Discord noch keinen Nickname nach dem Format `vorname | "
                                   "ingamename` bitte richte diesen zuerst ein bevor du dich registrierst")
            else:
                await ctx.send("Du scheinst von den Admins noch keinen Nicknamen bekommen zu haben. Bitte wende "
                               "dich an einen STT Admin.")
        else:
            await ctx.send("Du bist bereits Registriert um deinen IGN zu ändern benutze bitte !ign INGAMENAME")

    elif schildkroete is False:
        await ctx.send("Du scheinst noch keine Schildkröte auf dem STT Discord Server zu sein. Diese Funktionen "
                       "sind Schildkröten vorbehalten.")
