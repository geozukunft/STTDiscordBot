import random
from discord.ext import commands


def __init__(self, bot):
    self.bot = bot


def setup(bot):
    bot.add_command(roll)
    bot.add_command(choose)


@commands.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception as error:
        print(error)
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for _ in range(rolls))
    await ctx.send(result)


@commands.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))
