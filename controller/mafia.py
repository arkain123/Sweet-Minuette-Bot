import disnake
import random
from disnake.ext import commands
from view.console_out import log, important, warning, error

# LEVELS
# 0 - ничего
# 1 - игра начинается, набор игроков, регистрация и прочее
# 2 - игра начата
random.seed(version=2)


class Player:

    def __init__(self, name, role, id):
        self.name = name
        self.role = role
        self.id = id
        self.days = 0
        self.state = 0


class Mafia(commands.Cog):

    def __init__(self, bot):
        self.regplayers = []
        self.aliveplayers = []
        self.mafiaplayers = []
        self.bot = bot
        important("COGS module Mafia connected")
        self.LEVEL = "NOTHING"  # NOTHING/PRESTART/START
        self.PHASE = "DAY"  # DAY/NIGHT
        self.ROLES = {
            0: "MARE",
            1: "DOG",
            2: "SHERIFF",
            3: "NURSE",
            4: "MANIAC",
            5: "DEPUTY",
            # TODO:Add more roles (Not truly necessary)
        }
        self.HEALID = 0

    def generate_mares(self):
        for i in range(len(self.aliveplayers)):
            if self.aliveplayers[i].role == "NONE":
                self.aliveplayers[i].role = self.ROLES[0]


    @commands.slash_command(
        name="join",
        usage="/join",
        description="Зайти в игру Мафия"
    )
    async def join(self, inter):
        if self.LEVEL == "PRESTART":
            for i in range(len(self.regplayers)):
                if self.regplayers[i].name == inter.author:
                    await inter.send("Вы уже зарегистрированны в игре! Используйте `/leave` для выхода.")
                    log(f"{inter.author} used /join, but already registered")
                    return 0
            await inter.send("Вы зарегистрировались в игре!")
            self.regplayers.append(Player(inter.author, "NONE", inter.author.id))
            await inter.guild.get_member(self.regplayers[len(self.regplayers)-1].id).add_roles(inter.guild.roles[1])
            await inter.guild.get_member(self.regplayers[len(self.regplayers)-1].id).add_roles(inter.guild.roles[2])
            log(f"{self.regplayers[len(self.regplayers)-1].id},\t {self.regplayers[len(self.regplayers)-1].name}")
            log(f"{inter.author} used /join")
            log(f"Assigned role NONE to {inter.author}")
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
                    await inter.guild.get_member(self.regplayers[i].id).remove_roles(inter.guild.roles[1])
                    await inter.guild.categories[1].channels[0].send(f"{inter.author.name} покинул игру")
                    if self.regplayers[i].role == "SPECTATOR":
                        await inter.guild.get_member(self.regplayers[i].id).remove_roles(inter.guild.roles[2])
                    self.regplayers.pop(i)
                    return 0
            await inter.send("Вам нечего покидать!")
            log(f"{inter.author} used /leave, but wasn't registered")
        else:
            await inter.send("Нет запущенных игр!")
            log(f"{inter.author} used /leave, but game wasn't started")

    @commands.slash_command(
        name="spectate",
        usage="/spectate",
        description="Наблюдать за игрой Мафия"
    )
    async def spectate(self, inter):
        if self.LEVEL != "NOTHING":
            for i in range(len(self.regplayers)):
                if self.regplayers[i].name == inter.author:
                    await inter.send("Вы уже наблюдаете за игрой! Используйте `/leave` для выхода.")
                    log(f"{inter.author} used /spectate, but already spectating")
                    return 0
            await inter.send("Вы наблюдаете за игрой!")
            self.regplayers.append(Player(inter.author))
            self.regplayers[len(self.regplayers) - 1].role = "SPECTATOR"
            self.regplayers[len(self.regplayers) - 1].id = inter.author.id
            await inter.guild.get_member(self.regplayers[len(self.regplayers) - 1].id).add_roles(inter.guild.roles[1])
            log(f"{self.regplayers[len(self.regplayers) - 1].id},\t {self.regplayers[len(self.regplayers) - 1].name}")
            log(f"{inter.author} used /spectate")
            log(f"Assigned role SPECTATOR to {inter.author}")
        else:
            await inter.send("Нет запущенных игр!")
            log(f"{inter.author} used /spectate, but game wasn't started")

    @commands.slash_command(
        name="prestmafia",
        usage="/prestmafia",
        description="Открыть набор на игру Мафия"
    )
    async def prestmafia(self, ctx):
        log(f"{ctx.author} used /prestmafia")
        if self.LEVEL == "NOTHING":
            self.regplayers = []
            self.aliveplayers = []
            self.mafiaplayers = []
            self.LEVEL = "PRESTART"
            self.PHASE = "DAY"
            await ctx.guild.create_role(name="GM")
            await ctx.guild.create_role(name="spectator")
            await ctx.guild.create_role(name="mfplayer")
            await ctx.author.add_roles(ctx.guild.roles[3])
            await ctx.guild.create_category("MAFIA GENERAL", overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(send_messages=False)
            }, position=0)
            log(f"created category {ctx.guild.categories[1].name}")
            await ctx.guild.create_text_channel("general", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=False)
            }, position=0)
            log(f"created channel {ctx.guild.channels[0].name}")
            await ctx.guild.create_text_channel("spectating", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(send_messages=True, view_channel=True),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(send_messages=True, view_channel=True)
            }, position=1)
            log(f"created channel {ctx.guild.channels[1].name}")
            await ctx.guild.create_text_channel("commands", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True)
            }, position=2)
            log(f"created channel {ctx.guild.channels[2].name}")
            await ctx.guild.create_voice_channel("voice", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(speak=False)
            }, position=3)
            log(f"created channel {ctx.guild.channels[3].name}")
            await ctx.guild.create_voice_channel("voice", category=ctx.guild.categories[1], overwrites={
                ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True),
                ctx.guild.roles[2]: disnake.PermissionOverwrite(speak=False)
            }, position=4)
            log(f"created channel {ctx.guild.channels[3].name}")
            await ctx.guild.categories[1].channels[0].send(f"{ctx.guild.roles[1].mention}, добро пожаловать в игру. Сейчас идёт фаза регистрации. Во время этой фазы ведущий набирает игроков. Ждите начала игры! Если вы передумали участвовать в игре - напишите `/leave`")
            await ctx.guild.categories[1].channels[0].send("Канал general предназначен для общения игроков во время дневной фазы. Этот канал видят также и наблюдатели. Мертвые игроки писать в него не могут!")
            await ctx.guild.categories[1].channels[0].send("Канал spectating канал предназначеный для мертвых игроков и наблюдателей. В этом чате вы можете спокойно раскрывать свою роль и обсуждать игровые моменты")
            await ctx.guild.categories[1].channels[1].send(f"{ctx.guild.roles[2].mention} Этот канал предназначен для общения мертвых игроков и наблюдателей. Старайтесь не мешать игре!")
            await ctx.guild.categories[1].channels[2].send(f"{ctx.guild.roles[3].mention} Команды и заметки, которые вам могут пригодиться во время игры пишите сюда.")
            await ctx.guild.categories[1].channels[3].send(f"Поздравляю, вам всем выпала роль мафии. В этом чате вы будете переговариваться и договариваться о том, кого убить")
            await ctx.send("Игра создана!")

    @commands.slash_command(
        name="stmafia",
        usage="/stmafia",
        description="Запустить игру Мафия"
    )
    async def stmafia(self, ctx):
        # TODO: remove role "spectator" from alive players
        log(f"{ctx.author} used /stmafia")
        random.shuffle(self.aliveplayers)
        if self.LEVEL == "PRESTART":
            self.HEALID = 0
            self.LEVEL = "START"
            self.PHASE = "DAY"
            for i in range(len(self.regplayers)):
                if self.regplayers[i].role == "NONE":
                    self.aliveplayers.append(self.regplayers[i])
            if len(self.aliveplayers) < 4:
                await ctx.send("Unable to start: Small players count")
                log("Unable to start: Small players count!")
                return 0
            for i in range(len(self.aliveplayers)):
                await ctx.guild.create_text_channel(str(self.aliveplayers[i].name), category=ctx.guild.categories[1], overwrites={
                    ctx.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
                    ctx.guild.roles[1]: disnake.PermissionOverwrite(view_channel=False),
                    ctx.guild.roles[3]: disnake.PermissionOverwrite(view_channel=True),
                    ctx.guild.get_member(self.aliveplayers[i].id): disnake.PermissionOverwrite(view_channel=True)
                }, position=4)
                log(f"created personal channel {ctx.guild.channels[1].name} for {self.aliveplayers[i].name}")

            if len(self.aliveplayers) >= 4 & len(self.aliveplayers) <= 6:
                self.aliveplayers[0].role = self.ROLES[1]
                self.generate_mares()
            elif len(self.aliveplayers) == 7:
                self.aliveplayers[0].role = self.ROLES[1]
                self.aliveplayers[1].role = self.ROLES[2]
                self.generate_mares()
            elif len(self.aliveplayers) >= 8 & len(self.aliveplayers) <= 10:
                self.aliveplayers[0].role, self.aliveplayers[1].role = self.ROLES[1], self.ROLES[1]
                self.aliveplayers[2].role = self.ROLES[2]
                self.aliveplayers[3].role = self.ROLES[3]
                self.generate_mares()
            elif len(self.aliveplayers) > 10 & len(self.aliveplayers) <= 14:
                self.aliveplayers[0].role, self.aliveplayers[1].role, self.aliveplayers[2].role = self.ROLES[1], self.ROLES[1], self.ROLES[1]
                self.aliveplayers[3].role = self.ROLES[2]
                self.aliveplayers[4].role = self.ROLES[3]
                self.aliveplayers[5].role = self.ROLES[4]
            else:
                self.aliveplayers[0].role, self.aliveplayers[1].role, self.aliveplayers[2].role, self.aliveplayers[3].role = (self.ROLES[1],
                                                                                                                              self.ROLES[1],
                                                                                                                              self.ROLES[1],
                                                                                                                              self.ROLES[1])
                self.aliveplayers[4].role = self.ROLES[2]
                self.aliveplayers[5].role = self.ROLES[3]
                self.aliveplayers[6].role = self.ROLES[4]

            await ctx.guild.categories[1].channels[0].send("Игра началась")
            await ctx.send("Started!")

            for i in range(len(self.aliveplayers)):
                if self.aliveplayers[i].name == ctx.guild.categories[1].channels[4+i].name:
                    if self.aliveplayers[i].role == self.ROLES[0]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Мирная кобылка**")
                    if self.aliveplayers[i].role == self.ROLES[1]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Алмазный пёс**")
                        self.mafiaplayers.append(self.aliveplayers[i])
                    if self.aliveplayers[i].role == self.ROLES[3]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Медсестра**")
                    if self.aliveplayers[i].role == self.ROLES[2]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Шериф**")
                    if self.aliveplayers[i].role == self.ROLES[4]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Маньяк**")
                    if self.aliveplayers[i].role == self.ROLES[5]:
                        await ctx.guild.categories[1].channels[5+i].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention}, твоя роль - **Помощник шерифа**")

            for i in range(len(self.mafiaplayers)):
                if len(self.aliveplayers) >= 8:
                    ctx.guild.categories[1].channels[3].set_permissions(self.mafiaplayers[i], view_channel=True)

    @commands.slash_command(
        name="next",
        usage="/next",
        description="Следующая фаза игры"
    )
    async def next(self, ctx):
        if self.LEVEL == "START":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                if (len(self.aliveplayers) <= len(self.mafiaplayers)) or (len(self.mafiaplayers) == 0):
                    if len(self.mafiaplayers) == 0:
                        await ctx.guild.categories[1].channels[0].send(f"{ctx.guild.roles[1].mention}, наши поздравления! **Победа мирных кобылок за {self.aliveplayers[0].days} дней!!**")
                    else:
                        await ctx.guild.categories[1].channels[0].send(f"{ctx.guild.roles[1].mention}, у вас не получилось спастись от геноцида алмазных псов... **Победа алмазных псов за {self.aliveplayers[0].days} дней!!**")

                    await ctx.guild.categories[1].channels[0].send(f"**Остались в живых:**")

                    for i in range(len(self.aliveplayers)):
                        self.aliveplayers[i].days += 1
                        if self.aliveplayers[i].role == self.ROLES[0]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Мирная кобылка**")
                        if self.aliveplayers[i].role == self.ROLES[1]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Алмазный пёс**")
                        if self.aliveplayers[i].role == self.ROLES[3]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Медсестра**")
                        if self.aliveplayers[i].role == self.ROLES[2]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Шериф**")
                        if self.aliveplayers[i].role == self.ROLES[4]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Маньяк**")
                        if self.aliveplayers[i].role == self.ROLES[5]:
                            ctx.guild.categories[1].channels[0].send(
                                f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - **Помощник шерифа**")
                    await ctx.send("Готово! Игра окончена!")
                    ctx.guild.categories[1].channels[4].set_permissions(ctx.guild.roles[1], speak=True)
                    ctx.guild.categories[1].channels[0].set_permissions(ctx.guild.roles[1], send_messages=True)
                    ctx.guild.categories[1].channels[4].set_permissions(ctx.guild.roles[2], speak=True)
                    ctx.guild.categories[1].channels[0].set_permissions(ctx.guild.roles[2], send_messages=True)
                    return 0

                if self.PHASE == "DAY":
                    self.PHASE = "NIGHT"
                    ctx.guild.categories[1].channels[4].set_permissions(ctx.guild.roles[1], speak=False)
                    ctx.guild.categories[1].channels[0].set_permissions(ctx.guild.roles[1], send_messages=False)
                    ctx.guild.categories[1].channels[0].send("**Наступает ночь...**")
                else:
                    self.PHASE = "DAY"
                    ctx.guild.categories[1].channels[0].send("**Всходит солнце...**")
                    ctx.guild.categories[1].channels[0].send("На утро не проснулся(ись):")
                    for i in range(len(self.aliveplayers)):
                        if self.aliveplayers[i].state < 0:
                            ctx.guild.categories[1].channels[0].send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} - был убит и прожил с нами {self.aliveplayers[i].days} дней!")
                            ctx.guild.get_member(self.aliveplayers[i].id).add_roles(ctx.guild.roles[2])
                            if self.aliveplayers[i].role == self.ROLES[1]:
                                ctx.guild.categories[1].channels[3].set_permissions(self.aliveplayers[i],
                                                                                    view_channel=True,
                                                                                    send_messages=False)
                                for j in range(len(self.mafiaplayers)):
                                    if self.aliveplayers[i].id == self.mafiaplayers[j].id:
                                        self.mafiaplayers.pop(j)
                            self.aliveplayers[i].role = "SPECTATOR"
                            self.aliveplayers[i].pop(i)
                    ctx.guild.categories[1].channels[4].set_permissions(ctx.guild.roles[1], speak=True)
                    ctx.guild.categories[1].channels[0].set_permissions(ctx.guild.roles[1], send_messages=True)
                await ctx.send(f"Готово! Наступает {self.PHASE}")
            else:
                await ctx.send("У вас недостаточно прав для этого действия! Вы должны быть ведущим игры!")
        else:
            await ctx.send("Игра еще не запущена!")

    @commands.command(
        name="kill",
        usage="/kill {id}",
        description="Убить игрока по id"
    )
    async def kill(self, ctx, k_id):
        if self.LEVEL == "START":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                for i in range(len(self.aliveplayers)):
                    if self.aliveplayers[i].id == k_id:
                        self.aliveplayers[i].state -= 1
            else:
                ctx.send("Вы должны быть ведущим для исполнения данной команды!")
        else:
            ctx.send("Нет запущенных игр!")

    @commands.command(
        name="execute",
        usage="/execute {id}",
        description="Казнить игрока по id"
    )
    async def execute(self, ctx, e_id):
        if self.LEVEL == "START":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                for i in range(len(self.aliveplayers)):
                    if self.aliveplayers[i].id == e_id:
                        self.aliveplayers[i].role = "SPECTATOR"
                        ctx.guild.get_member(self.aliveplayers[i].id).add_roles(ctx.guild.roles[2])
                        ctx.guild.categories[1].channels[0].send(f"Игрок {ctx.guild.get_member(e_id).mention} был казнён! Игрок прожил с нами {self.aliveplayers[i].days} дней!") # TODO: Добавить объявление роли при казни?
                        self.aliveplayers.pop(i)
            else:
                ctx.send("Вы должны быть ведущим для исполнения данной команды!")
        else:
            ctx.send("Нет запущенных игр!")



    @commands.command(
        name="heal",
        usage="/heal {id}",
        description="Вылечить игрока по id"
    )
    async def heal(self, ctx, h_id):
        if self.LEVEL == "START":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                for i in range(len(self.aliveplayers)):
                    if self.aliveplayers[i].id == h_id:
                        self.aliveplayers[i].state += 1
            else:
                ctx.send("Вы должны быть ведущим для исполнения данной команды!")
        else:
            ctx.send("Нет запущенных игр!")


    @commands.command(
        name="inspect",
        usage="/inspect {id}",
        desctiption="Проверить игрока"
    )
    async def inspect(self, ctx, i_id):
        if self.LEVEL == "START":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                for i in range(len(self.aliveplayers)):
                    if self.aliveplayers[i].id == i_id:
                        if self.aliveplayers[i].role == self.ROLES[1] or self.aliveplayers[i].role == self.ROLES[4]:
                            ctx.send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} играет за сторону псов!")
                        else:
                            ctx.send(f"{ctx.guild.get_member(self.aliveplayers[i].id).mention} играет за сторону кобылок!")
            else:
                ctx.send("Вы должны быть ведущим для исполнения данной команды!")
        else:
            ctx.send("Нет запущенных игр!")


    @commands.command(
        name="endmafia",
        usage="/endmafia",
        description="Окончить игру"
    )
    async def endmafia(self, ctx):
        if self.LEVEL == "START" or self.LEVEL == "PRESTART":
            if (ctx.guild.roles[3] in ctx.author.roles) and (ctx.guild.roles[3].name == "GM"):
                self.LEVEL = "NOTHING"
                self.PHASE = "DAY"
                log(f"{ctx.author} used /endmafia!")
                if ctx.guild.roles[1].name == "mfplayer":
                    log(f"deleted role {ctx.guild.roles[1].name}")
                    await ctx.guild.roles[1].delete()
                if ctx.guild.roles[1].name == "spectator":
                    log(f"deleted role {ctx.guild.roles[1].name}")
                    await ctx.guild.roles[1].delete()
                if ctx.guild.roles[1].name == "GM":
                    log(f"deleted role {ctx.guild.roles[1].name}")
                    await ctx.guild.roles[1].delete()
                channelsToDelete = []
                for i in range(len(ctx.guild.channels)):
                    if ctx.guild.channels[i].category == ctx.guild.categories[1]:
                        channelsToDelete.append(ctx.guild.channels[i])
                for i in range(len(channelsToDelete)):
                    log(f"deleted channel {channelsToDelete[i].name}")
                    await channelsToDelete[i].delete()
                log(f"deleted category {ctx.guild.categories[1].name}")
                await ctx.guild.categories[1].delete()
                await ctx.send("Игра остановлена")
            else:
                await ctx.send("У вас нет прав на исполнение данной команды")
                log(f"{ctx.author.name} used /endmafia, but unsuccessful!")
                warning(f"{ctx.author.name} was trying to stop the game!")
        else:
            await ctx.send("Игра еще не запущена")
            log(f"{ctx.author.name} used /endmafia, but game was not started!")


    @commands.command(
        name="status",
        usage="/status",
        description="Информация по игре Мафия"
    )
    async def status(self, ctx):
        log(f"{ctx.author} used /status")
        await ctx.send(f"LEVEL={self.LEVEL}\nPHASE={self.PHASE}\nREGPLAYERS={len(self.regplayers)}\nALIVEPLAYERS={len(self.aliveplayers)}")


def setup(bot):
    bot.add_cog(Mafia(bot))

# TODO: do a full game ending mechanic?
