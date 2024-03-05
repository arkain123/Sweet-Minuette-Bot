import disnake
from disnake.ext import commands
from view.console_out import log, important, warning, error
from view.classes import Button, DropdownView


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        important("COGS module Events connected")


def setup(bot):
    bot.add_cog(Events(bot))
