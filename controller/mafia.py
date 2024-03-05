import disnake
from disnake.ext import commands
from view.console_out import log, important, warning, error


class Mafia(commands.Cog):

    def __init__(self, bot):
        self.regplayers = set
        self.bot = bot
        important("COGS module Mafia connected")

    @commands.slash_command(
        name="join",
        usage="/join",
        description="Зайти в игру Мафия"
    )
    async def join(self, inter):
        await inter.reply("Вы зарегистрировались в игре!")

        log(f"{inter.author.mention} used /join")


def setup(bot):
    bot.add_cog(Mafia(bot))
