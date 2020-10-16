from discord.ext import commands


from main import Tokens
TOKEN = Tokens.TOKEN
GUILD = Tokens.GUILD
my_region = Tokens.my_region
api_key = Tokens.api_key



def __init__(self, bot):
    self.bot = bot



def setup(bot):
    bot.add_command(list)


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