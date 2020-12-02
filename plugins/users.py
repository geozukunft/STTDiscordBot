from discord.ext import commands
from asyncpg.pool import Pool
import re

from main import Tokens


TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(ign)
    bot.add_command(name)



@commands.command(name='ign', help='Update deinen User/Ingamenamen')
@commands.dm_only()
async def ign(ctx, ign):
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
            row = await conn.fetchrow('SELECT firstname FROM members WHERE discord_id = $1', ctx.author.id)
        if row is not None:
            await member.edit(nick=ign + " | " + row[0])
            async with pool.acquire() as conn:
                await conn.execute('UPDATE members SET username = $1 WHERE discord_id = $2', ign, ctx.author.id)
            await ctx.send("Dein Name auf dem STT Discord sieht nun folgendermaßen aus: `" + member.nick + "`")
        else:
            await ctx.send("Du scheinst die Regeln auf dem STT Discord noch nicht akzeptiert zu haben. \n"
                           "Solltest du das bereits haben dann wende dich bitte an @geozukunft#9605 auf dem STT Discord!")
    else:
        await ctx.send("Du scheinst die Regeln auf dem STT Discord noch nicht akzeptiert zu haben. \n"
                       "Solltest du das bereits haben dann wende dich bitte an @geozukunft#9605 auf dem STT Discord!")

@commands.command(name='name', help='Update deinen Vor/Rufnamen')
@commands.dm_only()
async def name(ctx, name):
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
            row = await conn.fetchrow('SELECT username FROM members WHERE discord_id = $1', ctx.author.id)
        if row is not None:
            await member.edit(nick=row[0] + " | " + name)
            async with pool.acquire() as conn:
                await conn.execute('UPDATE members SET firstname = $1 WHERE discord_id = $2', name, ctx.author.id)
            await ctx.send("Dein Name auf dem STT Discord sieht nun folgendermaßen aus: `" + member.nick + "`")
        else:
            await ctx.send("Du scheinst die Regeln auf dem STT Discord noch nicht akzeptiert zu haben. \n"
                           "Solltest du das bereits haben dann wende dich bitte an @geozukunft#9605 auf dem STT Discord!")
    else:
        await ctx.send("Du scheinst die Regeln auf dem STT Discord noch nicht akzeptiert zu haben. \n"
                       "Solltest du das bereits haben dann wende dich bitte an @geozukunft#9605 auf dem STT Discord!")