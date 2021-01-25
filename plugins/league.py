from discord.ext import commands

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(mainl)
    bot.add_command(lanes)
    bot.add_command(top)
    bot.add_command(jgl)
    bot.add_command(mid)
    bot.add_command(adc)
    bot.add_command(sup)


@commands.command(name='main', help='Sende mit `!main` `top, jgl, mid, bot, sup` deine Hauptlane')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def mainl(ctx, lane):
    pool = ctx.bot.pool
    value = False

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        if lane is not None:
            lane = lane.upper()
            if lane == "TOP":
                value = True
                if row[3] is not True:
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET top = True WHERE idplayer = $1', ctx.author.id)
            elif lane == "JGL":
                value = True
                if row[4] is not True:
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET jgl = True WHERE idplayer = $1', ctx.author.id)
            elif lane == "MID":
                value = True
                if row[5] is not True:
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET mid = True WHERE idplayer = $1', ctx.author.id)
            elif lane == "BOT" or lane == "ADC":
                lane = "BOT"
                value = True
                if row[6] is not True:
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET bot = True WHERE idplayer = $1', ctx.author.id)
            elif lane == "SUP":
                value = True
                if row[7] is not True:
                    async with pool.acquire() as conn:
                        await conn.execute('UPDATE playerdata SET sup = True WHERE idplayer = $1', ctx.author.id)
            else:
                await ctx.send(
                    "Bitte überprüfe deine Eingabe! Valide Optionen sind: `TOP , JGL, MID, BOT, SUP`")
            if value is True:
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET primarylane = $1 WHERE idplayer = $2',
                                       lane.upper(), ctx.author.id)
                await ctx.send("Deine Hauptlane ist: " + lane.upper())

    else:
        await ctx.send("Du scheinst noch nicht registriert zu sein bitte tu dies zuerst mit !register")


@commands.command(name='lanes', help='Zeigt dir an welche Lanes du angegeben hast Spielen zu können')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def lanes(ctx):
    pool = ctx.bot.pool
    mainlane = ""
    top = ":x:"
    jgl = ":x:"
    mid = ":x:"
    adc = ":x:"
    sup = ":x:"

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        if row[3] is True:
            top = ":white_check_mark:"
        if row[4] is True:
            jgl = ":white_check_mark:"
        if row[5] is True:
            mid = ":white_check_mark:"
        if row[6] is True:
            adc = ":white_check_mark:"
        if row[7] is True:
            sup = ":white_check_mark:"
        if row[8] is not None:
            mainlane = row[8]
        await ctx.send("TOP  " + top + "\n" + "JGL   " + jgl + "\n" + "MID  " + mid + "\n" + "BOT  " + adc +
                       "\n" + "SUP   " + sup + "\n" + "Main Lane: " + mainlane)
    else:
        await ctx.send("Du bist noch nicht registriert bitte registriere dich zuerst mit `!register`")


@commands.command(name='top', help='Sende diesen Command um uns mitzuteilen das du Top spielen kannst')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def top(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT primarylane FROM playerdata WHERE idplayer = $1', ctx.author.id)
        if row[0] != "TOP":
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT top FROM playerdata WHERE idplayer = $1', ctx.author.id)
            if row[0] is True:
                await ctx.send('Deine Einstellung wurde geändert du spielst keine Toplane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET top = FALSE WHERE idplayer = $1', ctx.author.id)
            elif row[0] is False or row[0] is None:
                await ctx.send('Deine Einstellung wurde geändert du spielst Toplane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET top = TRUE WHERE idplayer = $1', ctx.author.id)
        else:
            await ctx.send("Diese Lane ist deine Hauptlane du kannst diese nicht deaktivieren!")
    else:
        await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")


@commands.command(name='jgl', help='Sende diesen Command um uns mitzuteilen das du Jungle spielen kannst')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def jgl(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT primarylane FROM playerdata WHERE idplayer = $1', ctx.author.id)
        if row[0] != "JGL":
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT jgl FROM playerdata WHERE idplayer = $1', ctx.author.id)
            if row[0] is True:
                await ctx.send('Deine Einstellung wurde geändert du spielst keinen Jungle')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET jgl = FALSE WHERE idplayer = $1', ctx.author.id)
            elif row[0] is False or row[0] is None:
                await ctx.send('Deine Einstellung wurde geändert du spielst Jungle')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET jgl = TRUE WHERE idplayer = $1', ctx.author.id)
        else:
            await ctx.send("Diese Lane ist deine Hauptlane du kannst diese nicht deaktivieren!")
    else:
        await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")


@commands.command(name='mid', help='Sende diesen Command um uns mitzuteilen das du Mid spielen kannst')
@commands.dm_only()
@commands.has_role('Schildkröte')
async def mid(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT primarylane FROM playerdata WHERE idplayer = $1', ctx.author.id)
        if row[0] != "MID":
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT mid FROM playerdata WHERE idplayer = $1', ctx.author.id)
            if row[0] is True:
                await ctx.send('Deine Einstellung wurde geändert du spielst keine Midlane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET mid = FALSE WHERE idplayer = $1', ctx.author.id)
            elif row[0] is False or row[0] is None:
                await ctx.send('Deine Einstellung wurde geändert du spielst Midlane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET mid = TRUE WHERE idplayer = $1', ctx.author.id)
        else:
            await ctx.send("Diese Lane ist deine Hauptlane du kannst diese nicht deaktivieren!")
    else:
        await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")


@commands.command(name='adc', help='Sende diesen Command um uns mitzuteilen das du Bot spielen kannst',
                  aliases=("bot", "adcarry", "marksman"))
@commands.dm_only()
@commands.has_role('Schildkröte')
async def adc(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT primarylane FROM playerdata WHERE idplayer = $1', ctx.author.id)
        if row[0] != "BOT":
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT bot FROM playerdata WHERE idplayer = $1', ctx.author.id)
            if row[0] is True:
                await ctx.send('Deine Einstellung wurde geändert du spielst keine Botlane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET bot = FALSE WHERE idplayer = $1', ctx.author.id)
            elif row[0] is False or row[0] is None:
                await ctx.send('Deine Einstellung wurde geändert du spielst Botlane')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET bot = TRUE WHERE idplayer = $1', ctx.author.id)
        else:
            await ctx.send("Diese Lane ist deine Hauptlane du kannst diese nicht deaktivieren!")
    else:
        await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")


@commands.command(name='sup', help='Sende diesen Command um uns mitzuteilen das du Support spielen kannst',
                  aliases=("ks", "killsteal", "griagtkagold"))
@commands.dm_only()
@commands.has_role('Schildkröte')
async def sup(ctx):
    pool = ctx.bot.pool

    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM playerdata WHERE idplayer = $1', ctx.author.id)
    if row is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT primarylane FROM playerdata WHERE idplayer = $1', ctx.author.id)
        if row[0] != "SUP":
            async with pool.acquire() as conn:
                row = await conn.fetchrow('SELECT sup FROM playerdata WHERE idplayer = $1', ctx.author.id)
            if row[0] is True:
                await ctx.send('Deine Einstellung wurde geändert du spielst keinen Support')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET sup = FALSE WHERE idplayer = $1', ctx.author.id)
            elif row[0] is False or row[0] is None:
                await ctx.send('Deine Einstellung wurde geändert du spielst Support')
                async with pool.acquire() as conn:
                    await conn.execute('UPDATE playerdata SET sup = TRUE WHERE idplayer = $1', ctx.author.id)
        else:
            await ctx.send("Diese Lane ist deine Hauptlane du kannst diese nicht deaktivieren!")
    else:
        await ctx.send("Du bist noch nicht Registriert bitte registriere dich zuerst mit !register INGAMENAME")

