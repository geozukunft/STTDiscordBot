import datetime
import uuid
import discord
from discord.ext import commands
from discord.utils import get
from pyot.models import lol
import urllib.parse

from pyot.models.lol import SummonerLeague

from main import Tokens

TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.LOL_REGION


class RiotCog(commands.Cog, name='League Account'):
    """Mit den Befehlen hier kannst du LoL Accounts hinzufügen/löschen/verifzieren und wenn du mehrere hast deinen Primären Account festlegen."""

    def __init__(self, bot):
        self.bot = bot

    # noinspection PyBroadException,PyTypeChecker
    @commands.command(name='addlol', help="!addlol <ingamename> Mit diesem Befehl kannst du einen League Account hinzufügen oder auch dessen "
                                          "Daten updaten ( "
                                          "Daten werden einmal täglich automatisch akuallisiert)! Achte hierbei auf eine korrekte "
                                          "Schreibweise sonst kann ich dich nicht finden!")
    @commands.dm_only()
    async def addlolacc(self, ctx, *, summonername):
        pool = ctx.bot.pool

        try:
            summoner = await lol.Summoner(name=summonername, platform="EUW1").get()
            summonerrank: SummonerLeague = await lol.SummonerLeague(summoner_id=summoner.id).get()
        except Exception as error:
            print(error)
            summoner = False
            summonerrank = False

        tier: str = "UNRANKED"
        rank: str = ""
        if summoner:
            if summonerrank.entries is not None:
                for entry in summonerrank.entries:
                    if entry.queue == "RANKED_SOLO_5x5":
                        tier = entry.tier
                        rank = entry.rank

            async with pool.acquire() as conn:
                lsummoner = await conn.fetchrow(
                    'SELECT "summonerName", "summonerLevel" FROM leaguesummoner WHERE puuid = $1',
                    summoner.puuid)
                member = await conn.fetchrow('SELECT firstname FROM members WHERE discord_id = $1', ctx.author.id)
            if member:
                if lsummoner is not None:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            'UPDATE leaguesummoner SET "accountID" = $1, "summonerID" = $2, "summonerName" = $3, '
                            '"profileIconId" = $4, "summonerLevel" = $5, "revisionDate" = $6, tier = $7, rank = $8 '
                            'WHERE puuid = $9',
                            summoner.account_id, summoner.id, summoner.name, summoner.profile_icon_id, summoner.level,
                            summoner.revision_date.timestamp(), tier, rank, summoner.puuid)
                        await ctx.send(
                            f'Dein Account {summoner.name} wurde geupdated dein aktuelles Level ist: {summoner.level}')
                else:
                    async with pool.acquire() as conn:
                        accounts = await conn.fetch('SELECT "summonerName" FROM leaguesummoner WHERE discord_id = $1',
                                                    ctx.author.id)
                        if not accounts:
                            await conn.execute(
                                'INSERT INTO leaguesummoner(discord_id, "accountID", "summonerID", puuid, "summonerName", '
                                '"profileIconId", "summonerLevel", "revisionDate", region, "PrimaryAcc", tier, rank) '
                                'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) ',
                                ctx.author.id, summoner.account_id, summoner.id, summoner.puuid, summoner.name,
                                summoner.profile_icon_id, summoner.level,
                                summoner.revision_date.timestamp(), summoner.platform, True, tier, rank)
                            await ctx.send(
                                f'Herzlichen Glückwunsch du hast deinen League Account {summoner.name} hinzugefügt. \n'
                                f'Du kannst mit `!addlol <ingamename>` auch noch weitere Accounts hinzufügen.\nMit '
                                f'`!changemain <ingamename>` kannst du sofern du weitere Accounts hinzufügst deinen '
                                f'primären Account '
                                f'ändern. \nMit `!verifylol <ingamename> kannst du einen Account verifzieren damit sich '
                                f'niemand '
                                f'anders als du ausgeben kann. Die Verifzierung deines Accounts ist auch nötig um sich '
                                f'für die organisierten Clash Teams anmelden zu können. \n Um einen Account wieder zu '
                                f'entfernen benutze `!removelol <ingamename>` beachte dabei solltest du dann keine '
                                f'Accounts '
                                f'mehr haben kannst du auch nicht mehr an internen Turnieren oder organisierten Clash '
                                f'Teams '
                                f'teilnehmen.')
                        else:
                            await conn.execute(
                                'INSERT INTO leaguesummoner(discord_id, "accountID", "summonerID", puuid, "summonerName", '
                                '"profileIconId", "summonerLevel", "revisionDate", region, "PrimaryAcc", tier, rank) '
                                'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) ',
                                ctx.author.id, summoner.account_id, summoner.id, summoner.puuid, summoner.name,
                                summoner.profile_icon_id, summoner.level,
                                summoner.revision_date.timestamp(), summoner.platform, False, tier, rank)
                            await ctx.send(
                                f'Herzlichen Glückwunsch du hast einen weiteren League Account mit dem Namen '
                                f'{summoner.name} hinzugefügt.\n '
                                f'Du kannst mit `!addlol <ingamename>` auch noch weitere Accounts hinzufügen.\nMit '
                                f'`!changemain <ingamename>` kannst du sofern du weitere Accounts hinzufügst deinen '
                                f'primären Account '
                                f'ändern. \nMit `!verifylol <ingamename> kannst du einen Account verifzieren damit sich '
                                f'niemand '
                                f'anders als du ausgeben kann. Die Verifzierung deines Accounts ist auch nötig um sich '
                                f'für die organisierten Clash Teams anmelden zu können. \nUm einen Account wieder zu '
                                f'entfernen benutze `!removelol <ingamename>` beachte dabei solltest du dann keine '
                                f'Accounts '
                                f'mehr haben kannst du auch nicht mehr an internen Turnieren oder organisierten Clash '
                                f'Teams '
                                f'teilnehmen.')
            else:
                await ctx.send("Du scheinst die Regeln auf dem STT Discord noch nicht akzeptiert zu haben. \n"
                               "Solltest du das bereits haben dann wende dich bitte an @geozukunft#1311 auf dem STT "
                               "Discord!")
                print(f'[WAR] ADDLOLACC {ctx.author.id}')
        else:
            await ctx.send(f'Ich konnte den Account {summonername} auf den EUW Servern nicht finden bitte achte darauf ihn '
                           f'richtig zu schreiben.')

    @commands.command(name='removelol', help='!removelol <ingamename> Mit diesem Befehl kannst du einen LoL Account wieder entferenen. Beachte wenn'
                                             ' du deinen Account entfernst kann dies dazu führen das du den Zugriff zu '
                                             'teilen des Discords verlierst. Diese Aktion ist unwiederruflich!')
    @commands.dm_only()
    async def removelolacc(self, ctx, *, summonername):
        pool = ctx.bot.pool

        async with pool.acquire() as conn:
            lsummoner = await conn.fetchrow('SELECT "summonerID", "region" , "discord_id", "puuid", verified, "PrimaryAcc" '
                                            'FROM leaguesummoner '
                                            'WHERE "summonerName" = $1 AND discord_id = $2', summonername, ctx.author.id)
            summoners = await conn.fetch(
                'SELECT * FROM leaguesummoner WHERE discord_id = $1 AND puuid != $2 ORDER BY "summonerLevel" DESC',
                ctx.author.id, lsummoner['puuid'])

            if len(summoners) == 0:
                await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                user_id = ctx.author.id
                role_name = 'Clash'
                umember = get(ctx.bot.get_all_members(), id=user_id)
                await umember.remove_roles(get(umember.guild.roles, name=role_name))
                await ctx.send(f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')
            else:
                if lsummoner['PrimaryAcc']:
                    if summoners[0]['verified']:
                        await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                        await conn.execute('UPDATE leaguesummoner SET "PrimaryAcc" = True WHERE puuid = $1',
                                           summoners[0]['puuid'])
                        await ctx.send(
                            f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')
                    else:
                        vACC = False
                        for summoner in summoners:
                            if summoner['verified']:
                                vACC = True
                        if vACC:
                            await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                            await conn.execute('UPDATE leaguesummoner SET "PrimaryAcc" = True WHERE puuid = $1',
                                               summoners[0]['puuid'])
                            await ctx.send(
                                f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')
                        else:
                            await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                            await conn.execute('UPDATE leaguesummoner SET "PrimaryAcc" = True WHERE puuid = $1',
                                               summoners[0]['puuid'])
                            user_id = ctx.author.id
                            role_name = 'Clash'
                            umember = get(ctx.bot.get_all_members(), id=user_id)
                            await umember.remove_roles(get(umember.guild.roles, name=role_name))
                            await ctx.send(
                                f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')
                else:
                    vACC = False
                    for summoner in summoners:
                        if summoner['verified']:
                            vACC = True
                    if vACC:
                        await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                        await ctx.send(
                            f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')
                    else:
                        await conn.execute('DELETE FROM leaguesummoner WHERE puuid = $1', lsummoner['puuid'])
                        user_id = ctx.author.id
                        role_name = 'Clash'
                        umember = get(ctx.bot.get_all_members(), id=user_id)
                        await umember.remove_roles(get(umember.guild.roles, name=role_name))
                        await ctx.send(
                            f'Dein League Account {summonername} wurde soeben unwiederruflich aus dem System gelöscht.')

    @commands.command(name='verifylol', help="!verifylol <ingamename> Verifiziert deinen League Account bei mir. Benötigt für die Clash Teilnahme.")
    @commands.dm_only()
    async def verifylolacc(self, ctx, *, summonername):
        pool = ctx.bot.pool

        async with pool.acquire() as conn:
            lsummoner = await conn.fetchrow(
                'SELECT "summonerID", "region" , "discord_id", "puuid", verified FROM leaguesummoner '
                'WHERE "summonerName" = $1 AND discord_id = $2', summonername, ctx.author.id)

        if lsummoner:
            if not lsummoner['verified']:
                if lsummoner['discord_id'] == ctx.author.id:
                    verify_uuid = uuid.uuid4()
                    message = await ctx.send(
                        f'Bitte öffne deinen League Client und gehe in die Einstellungen dort findest du relativ '
                        f'weit unten ein '
                        f'Menü mit dem Namen Verifikation. Dort füge bitte folgenden Code ein\n`{verify_uuid}`\n und '
                        f'klicke auf speichern. '
                        f'Danach reagiere auf diese Nachricht mit ✅ damit ich deine Eingabe überprüfen kann.')
                    await message.add_reaction('✅')
                    async with pool.acquire() as conn:
                        await conn.execute(
                            'INSERT INTO verify(discord_id, puuid, region, creationtime, code, creation) '
                            'VALUES($1,$2,$3,$4,$5,now())',
                            ctx.author.id, lsummoner['puuid'],
                            lsummoner['region'], datetime.datetime.utcnow().timestamp(), verify_uuid)
                        await conn.execute('INSERT INTO reactions VALUES ($1,$2,$3)', message.id, "VERIFY", ctx.author.id)
                else:
                    await ctx.send(f'Dieser LoL Account ist nicht unter deinem Discord Account gespeichert. Wenn du denkst das jemand anders '
                                   f'unrechtmäßig deinen Account hat melde dich bitte bei @geozukunft.')
            else:
                await ctx.send(f'Dein Account ist bereits verifiziert du brauchst nichts weiter tun.')
        else:
            await ctx.send(
                f'Ich konnte deinen Account leider nicht finden. Bitte überprüfe ob du deinen Account schon mit `!addlol` '
                f'hinzugefügt hast mit `!listlol` kannst du alle deine Accounts auflisten lassen. Sollte es trotzdem '
                f'nicht klappen melde dich bitte bei @geozukunft#9605. '
            )

    @commands.command(name='listlol', help="Listet alle deine hinzugefügten League Accounts auf.")
    @commands.dm_only()
    async def listlolacc(self, ctx):
        pool = ctx.bot.pool

        async with pool.acquire() as conn:
            summoners = await conn.fetch(
                'SELECT "summonerName", "profileIconId", "summonerLevel", "PrimaryAcc", verified, tier, rank '
                'FROM leaguesummoner WHERE discord_id = $1 ORDER BY "PrimaryAcc" DESC , "summonerLevel" DESC',
                ctx.author.id)

            if summoners:

                if summoners[0]['verified'] is True:
                    verified = "Ja"
                else:
                    verified = "Nein"
                embed_title = f'League Accounts'
                embed_desc = f'Dies sind deine registrierten League Accounts'
                embed = discord.Embed(title=embed_title, description=embed_desc)
                embed.set_thumbnail(
                    url=f'https://ddragon.leagueoflegends.com/cdn/11.3.1/img/profileicon/'
                        f'{summoners[0]["profileIconId"]}.png')
                embed.add_field(name=summoners[0]['summonerName'],
                                value=f'Level: {summoners[0]["summonerLevel"]}\n'
                                      f'Verifiziert: {verified}\n'
                                      f'Primär: Ja\n'
                                      f'Rank: {summoners[0]["tier"]} {summoners[0]["rank"]}',
                                inline=False)
                if len(summoners) > 1:
                    i: int = 1
                    for _ in summoners:
                        if i != len(summoners):
                            if summoners[i]['verified'] is True:
                                verified = "Ja"
                            else:
                                verified = "Nein"
                            embed.add_field(name=summoners[i]['summonerName'],
                                            value=f'Level: {summoners[i]["summonerLevel"]}\n'
                                                  f'Verifiziert: {verified}\n'
                                                  f'Primär: Nein\n'
                                                  f'Rank: {summoners[i]["tier"]} {summoners[i]["rank"]}',
                                            inline=False)
                        i += 1
                await ctx.send(content=None, embed=embed)

            else:
                await ctx.send("Du hast noch keine League Accounts hinzugefügt. Mit `!addlol <ingamename>` kannst du dies tun.")

    @commands.command(name='changemain', help="!changemain <accountname> Mit diesem Befehl kannst du deinen Haupt League Account ändern!")
    @commands.dm_only()
    async def changemainlolacc(self, ctx, *, summonername):
        pool = ctx.bot.pool

        async with pool.acquire() as conn:

            summoner = await conn.fetchrow('SELECT * FROM leaguesummoner WHERE "summonerName" = $1 AND discord_id = $2',
                                           summonername, ctx.author.id)

            if summoner:
                await conn.execute(
                    'UPDATE leaguesummoner SET "PrimaryAcc" = False WHERE discord_id = $1 AND "PrimaryAcc" = True',
                    ctx.author.id)
                await conn.execute('UPDATE leaguesummoner SET "PrimaryAcc" = True WHERE discord_id = $1 AND puuid = $2',
                                   ctx.author.id, summoner['puuid'])

                summoners = await conn.fetch(
                    'SELECT "summonerName", "profileIconId", "summonerLevel", "PrimaryAcc", verified, tier, rank FROM '
                    'leaguesummoner WHERE discord_id = $1 ORDER BY "PrimaryAcc" DESC, "summonerLevel" DESC', ctx.author.id)

                if summoners is not None:

                    if summoners[0]['verified'] is True:
                        verified = "Ja"
                    else:
                        verified = "Nein"
                    embed_title = f'League Accounts'
                    embed_desc = f'Dies sind deine registrierten League Accounts'
                    embed = discord.Embed(title=embed_title, description=embed_desc)
                    embed.set_thumbnail(
                        url=f'https://ddragon.leagueoflegends.com/cdn/11.3.1/img/profileicon/'
                            f'{summoners[0]["profileIconId"]}.png')
                    embed.add_field(name=summoners[0]['summonerName'],
                                    value=f'Level: {summoners[0]["summonerLevel"]}\n'
                                          f'Verifiziert: {verified}\n'
                                          f'Primär: Ja\n'
                                          f'Rank: {summoners[0]["tier"]} {summoners[0]["rank"]}',
                                    inline=False)
                    if len(summoners) > 1:
                        i: int = 1
                        for _ in summoners:
                            if i != len(summoners):
                                if summoners[i]['verified'] is True:
                                    verified = "Ja"
                                else:
                                    verified = "Nein"
                                embed.add_field(name=summoners[i]['summonerName'],
                                                value=f'Level: {summoners[i]["summonerLevel"]}\n'
                                                      f'Verifiziert: {verified}\n'
                                                      f'Primär: Nein\n'
                                                      f'Rank: {summoners[i]["tier"]} {summoners[i]["rank"]}',
                                                inline=False)
                            i += 1
                    await ctx.send(content=None, embed=embed)

            else:
                await ctx.send("Der von dir eingebene Account existiert bei mir nicht. Bitte überprüfe deine Eingabe!")

    # noinspection PyBroadException
    @commands.command(name='cl', alias=('clashlist', 'players'), help="!cl <Gegnername> Mit diesem Befehl kannst du durch Eingabe eines gegnerischen "
                                                                      "Clash Spielers das gegnerische Team als op.gg und porofessor Link generieren.")
    @commands.has_any_role('Clash', 'Social Media Manager')
    async def clashplayers(self, ctx, *, summonername):
        playernames = []
        try:
            summoner = await lol.Summoner(name=summonername, platform="EUW1").get()
            clashplayer = await lol.ClashPlayers(summoner_id=summoner.id, platform="EUW1").get()
            clashteam = await lol.ClashTeam(clashplayer.players[0].team_id, platform="EUW1").get()
            for player in clashteam.players:
                teamplayer = await lol.Summoner(id=player.summoner_id, platform="EUW1").get()
                playernames.append(teamplayer.name)

            string = ','.join(playernames)
            await ctx.send(f'`{string}`')
            await ctx.send(f'https://euw.op.gg/multi/query={urllib.parse.quote(string)}')
            await ctx.send(f'https://porofessor.gg/pregame/euw/{urllib.parse.quote(string)}')
        except Exception as error:
            print(error)
            await ctx.send("Es gab ein Problem beim Abrufen der Daten.")


def setup(bot):
    bot.add_cog(RiotCog(bot))
