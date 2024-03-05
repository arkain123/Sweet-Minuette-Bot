import disnake
from disnake.ext import commands
from view.console_out import log, important, warning, error

# LEVELS
# 0 - ничего
# 1 - игра начинается, набор игроков, регистрация и прочее
# 2 - игра начата


class Player:

    def __init__(self, name):
        self.name = name
        self.role = "SPECTATOR"
        self.id = 0
        self.days = 0
        self.alive = 1


class Mafia(commands.Cog):

    def __init__(self, bot):
        self.regplayers = []
        self.aliveplayers = []
        self.bot = bot
        important("COGS module Mafia connected")
        self.LEVEL = "NOTHING" # NOTHING/PRESTART/START
        self.PHASE = "DAY" # DAY/NIGHT
        self.chIDS = []
        self.catID = 0

    @commands.slash_command(
        name="join",
        usage="/join",
        description="Зайти в игру Мафия"
    )
    async def join(self, inter):
        if self.LEVEL == "PRESTART":
            for i in range(len(self.regplayers)):
                if self.regplayers[i].name == inter.author:
                    await inter.send("Вы уже зарегестрированны в игре! Используйте `/leave` для выхода.")
                    log(f"{inter.author} used /join, but already registered")
                    return 0
            await inter.send("Вы зарегистрировались в игре!")
            self.regplayers.append(Player(inter.author))
            self.regplayers[len(self.regplayers)-1].role = "SPECTATOR"
            self.regplayers[len(self.regplayers)-1].id = inter.author.id
            log(f"{self.regplayers[len(self.regplayers)-1].id},\t {self.regplayers[len(self.regplayers)-1].name}")
            log(f"{inter.author} used /join")
            log(f"Assigned role SPECTATOR to {inter.author}")
        elif self.LEVEL == "NOTHING":
            await inter.send("Нет запущенных игр!")
            log(f"{inter.author} used /join, but game wasn't started")
        else:
            await inter.send("Игра уже началась, если хотите зайти в наблюдатели, используйте `/spectate`")
            log(f"{inter.author} used /join, but game was already started")


    @commands.slash_command(
        name="leave",
        usage="/leave",
        description="Выйти из игры Мафия"
    )
    async def leave(self, inter):
        if self.LEVEL != "NOTHING":
            for i in range(len(self.regplayers)):
                if self.regplayers[i].name == inter.author:
                    await inter.send("Вы покинули игру Мафия")
                    log(f"{inter.author} used /leave")
                    # self.regplayers.name = ""
                    self.regplayers.pop(i)
                    return 0
            await inter.send("Вам нечего покидать!")
            log(f"{inter.author} used /leave, but wasn't registered")
        else:
            await inter.send("Нет запущенных игр!")
            log(f"{inter.author} used /leave, but game wasn't started")

    @commands.slash_command(
        name="prestmafia",
        usage="/prestmafia",
        description="Открыть набор на игру Мафия"
    )
    async def prestmafia(self, ctx):
        if self.LEVEL == "NOTHING":
            self.regplayers = []
            self.LEVEL = "PRESTART"
            self.PHASE = "DAY"
            await ctx.guild.create_role(name="mfplayer")
            await ctx.guild.create_category("MAFIA GENERAL", overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=True)
            }, position=0)
            await ctx.guild.create_text_channel("general", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=True)
                # ctx.guild.get_member(502833677269467146): disnake.PermissionOverwrite(view_channel=True)
            }, position=0)


            await ctx.send("Игра создана!")

    @commands.slash_command(
        name="stmafia",
        usage="/stmafia",
        description="Запустить игру Мафия"
    )
    async def stmafia(self, ctx):
        if self.LEVEL == "PRESTART":
            self.LEVEL = "START"
            self.PHASE = "DAY"

        for i in range(len(self.regplayers)):
            await ctx.guild.create_text_channel(str(self.regplayers[i].name), category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.get_member(self.regplayers[i].id): disnake.PermissionOverwrite(view_channel=True)
            }, position=1)


    @commands.command(
        name="endmafia",
        usage="/endmafia",
        description="Окончить игру"
    )
    async def endmafia(self, ctx):
        if self.LEVEL == "START":
            self.LEVEL = "NOTHING"
            self.PHASE = "DAY"

            if ctx.guild.roles[1].name == "mfplayer":
                await ctx.guild.roles[1].delete()

            for i in range(len(ctx.guild.channels)):
                if ctx.guild.channels[i].category == ctx.guild.categories[1]:
                    await ctx.guild.channels[i].delete()

            await ctx.guild.categories[1].delete()

    @commands.command(
        name="status",
        usage="/status",
        description="Информация по игре Мафия"
    )
    async def status(self, ctx):
        await ctx.send(f"LEVEL={self.LEVEL}\nPHASE={self.PHASE}\nREGPLAYERS={self.regplayers.count()}\nALIVEPLAYERS={self.regplayers.count()}")


def setup(bot):
    bot.add_cog(Mafia(bot))
