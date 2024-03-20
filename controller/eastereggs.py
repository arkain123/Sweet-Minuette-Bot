from disnake.ext import commands
from view.console_out import log, important, warning, error


class EasterEggs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        important("COGS module EasterEggs connected")


def setup(bot):
    bot.add_cog(EasterEggs(bot))
