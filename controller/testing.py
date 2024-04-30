import disnake
from disnake.ext import commands
from view.console_out import log, important, warning, error
from view.classes import Button


class Testing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        important("COGS module Testing connected")

    @commands.command()
    async def embedtest(self, ctx):
        view = Button()
        embed = disnake.Embed(
            title=f"Embed title",
            description=f"description",
            color=0xfffff
        )
        await ctx.send(embed=embed, view=view)
        log(f"{ctx.author.name} used /embedtest")
        await view.wait()

        if view.value is None:
            await ctx.send("Кнопки не нажаты")
        elif view.value:
            await ctx.send("Зелёная кнопка нажата")
        else:
            await ctx.send("Красная кнопка нажата")

    @commands.command()
    async def dropdowntest(self, ctx):
        log(f"{ctx.author.name} used /dropdowntest")
        await ctx.send("Выберите, что желаете заказать:", view=DropdownView())


def setup(bot):
    bot.add_cog(Testing(bot))
