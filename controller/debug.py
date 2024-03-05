import disnake
from disnake.ext import commands

import main
from view.console_out import log, important, warning, error


class Debug(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        important("COGS module Debug connected")

    @commands.slash_command(
        name="ping",
        usage="/ping",
        description="Проверка работы модулей бота (console)",
    )
    async def ping(self, inter):
        log(f"{inter.author} used /test")
        log(f"{inter.author} testing log message")
        warning(f"{inter.author} testing warning message")
        error(f"{inter.author} testing error message")
        if main.connections == main.nummodules:
            important(f"All modules connected!")
            await inter.send("Пинг успешен! Все модули активны. Проверьте консоль для большей информации")
        else:
            important(f"Detected unload modules!")
            await inter.send("Присутствуют неполадки в работе модулей. Проверьте консоль для большей информации")

    @commands.command(
        name="load",
        usage="/load <extension>",
        description="Подключает модуль"
    )
    # @commands.has_permissions(kick_members=True)
    async def load(self, ctx, extension):
        important(f"{ctx.author} used /load {extension}")
        try:
            self.bot.load_extension(extension)
            main.connections += 1
            important(f"COGS Module {extension} connected")
            await ctx.send(f"Модуль {extension} успешно загружен!")
        except disnake.ext.commands.errors.ExtensionNotFound:
            error(f"No connection to {extension}")
            await ctx.send(f"Не удалось загрузить модуль {extension} ({disnake.ext.commands.errors.ExtensionNotFound})")

    @commands.command(
        name="unload",
        usage="/unload <extension>",
        description="Отключает модуль"
    )
    # @commands.has_permissions(kick_members=True)
    async def unload(self, ctx, extension):
        important(f"{ctx.author} used /unload {extension}")
        try:
            self.bot.unload_extension(extension)
            main.connections -= 1
            important(f"COGS Module {extension} disconnected")
            await ctx.send(f"Модуль {extension} успешно отключен!")
        except disnake.ext.commands.errors.ExtensionNotFound:
            error(f"{extension} not founded!")
            await ctx.send(f"Не удалось отключить модуль {extension} ({disnake.ext.commands.errors.ExtensionNotFound})")

    @commands.command(
        name="reload",
        usage="/reload <extension>",
        description="Перезагружает модуль"
    )
    # @commands.has_permissions(kick_members=True)
    async def reload(self, ctx, extension):
        important(f"{ctx.author} used /reload {extension}")
        try:
            self.bot.reload_extension(extension)
            important(f"COGS Module {extension} reconnected")
            await ctx.send(f"Модуль {extension} успешно перезагружен!")
        except disnake.ext.commands.errors.ExtensionNotFound:
            error(f"{extension} not founded!")
            await ctx.send(f"Не удалось перезагрузить модуль {extension} ({disnake.ext.commands.errors.ExtensionNotFound})")


def setup(bot):
    bot.add_cog(Debug(bot))
