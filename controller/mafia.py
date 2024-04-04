import disnake
import random
import math
from disnake.ext import commands
from view.console_out import log, important, warning

# LEVELS
# 0 - ничего
# 1 - игра начинается, набор игроков, регистрация и прочее
# 2 - игра начата
random.seed(version=2)


class Player:

    def __init__(self, member):
        self.name = member.name
        self.role = None
        self.id = member.id
        self.days = 0
        self.alive = True
        self.member = member


class Channel:

    def __init__(self, channel):
        self.name = channel.name
        self.id = channel.id
        self.channel = channel


class PersonalChannel(Channel):
    p_id = None


class Category:

    def __init__(self, channel):
        self.name = channel.name
        self.id = channel.id
        self.channel = channel


class Role:

    def __init__(self, role):
        self.role = role
        self.r_id = role.id
        self.name = role.name


async def fail(ctx, user_msg, log_msg):
    await ctx.send(f"{user_msg}")
    warning(f"{log_msg}")


class Mafia(commands.Cog):

    def __init__(self, bot):
        self.mafiarole = None
        self.gmrole = None
        self.spectatorrole = None
        self.guild = None
        self.GM = None
        self.generalchannel = None
        self.commandschannel = None
        self.spectatorchannel = None
        self.voicechannel = None
        self.mafiachannel = None
        self.category = None
        self.personalchannels = {}

        self.regplayers = {}
        self.prestplayers = {}
        self.aliveplayers = {}
        self.mafiaplayers = {}
        self.bot = bot
        important("COGS module Mafia connected")
        self.DAY = 0
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
        self.mafiacount = 0

    def generate_mares(self, values):
        for person in values:
            if person.role == "NONE":
                person.role = self.ROLES[0]
                self.aliveplayers[person.id] = person
                self.prestplayers.pop(person.id)
                log(f"Assigned {self.ROLES[0]} role to {self.aliveplayers[person.id].name}")

    async def create_gen_channels(self, ctx):
        await ctx.send("Создаём каналы...")
        await self.guild.create_category("MAFIA GENERAL", overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=True, add_reactions=False),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=True)
        }, position=0)
        self.category = Category(self.guild.categories[1])
        log(f"created category {self.category.channel.name}")
        await self.guild.create_text_channel("general", category=self.category.channel, overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=True, send_messages=False,
                                                                 add_reactions=False),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=True, send_messages=False, )
        }, position=0)
        self.generalchannel = Channel(self.category.channel.channels[0])
        log(f"created channel {self.generalchannel.channel.name}")
        await self.guild.create_text_channel("spectating", category=self.category.channel, overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=True, send_messages=True),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=False)
        }, position=1)
        self.spectatorchannel = Channel(self.category.channel.channels[1])
        log(f"created channel {self.spectatorchannel.channel.name}")
        await self.guild.create_text_channel("commands", category=self.category.channel, overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=False),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=False)
        }, position=2)
        self.commandschannel = Channel(self.category.channel.channels[2])
        log(f"created channel {self.commandschannel.channel.name}")
        await self.guild.create_voice_channel("voice", category=self.category.channel, overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False, speak=False,
                                                                 use_voice_activation=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True, speak=True, use_voice_activation=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=True, speak=False,
                                                                 use_voice_activation=False),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=True, speak=True, use_voice_activation=True)
        }, position=3)
        self.voicechannel = Channel(self.category.channel.channels[3])
        log(f"created channel {self.voicechannel.channel.name}")

    async def send_gen_messages(self, ctx):
        await ctx.send("Рассылаем сообщения...")
        await self.generalchannel.channel.send(
            f"{self.mafiarole.role.mention}, добро пожаловать в игру. Сейчас идёт **фаза регистрации**. Во время этой фазы ведущий набирает игроков. **Ждите начала игры!** Если вы передумали участвовать в игре - напишите `/leave`")
        await self.generalchannel.channel.send(
            "Канал **general** предназначен для общения игроков во время дневной фазы. Этот канал видят также и наблюдатели. Мертвые игроки писать в него не могут!")
        await self.generalchannel.channel.send(
            "Канал **spectating** канал предназначеный для мертвых игроков и наблюдателей. В этом чате вы можете спокойно раскрывать свою роль и обсуждать игровые моменты")
        await self.spectatorchannel.channel.send(
            f"{self.spectatorrole.role.mention} Этот канал предназначен для общения мертвых игроков и наблюдателей. **Старайтесь не мешать игре!**")
        await self.commandschannel.channel.send(
            f"{self.gmrole.role.mention} Команды и заметки, которые вам могут пригодиться во время игры пишите сюда.")
        # await ctx.guild.categories[1].channels[4].send(f"Поздравляю, вам всем выпала роль мафии. В этом чате вы будете переговариваться и договариваться о том, кого убить")

    async def create_roles(self, ctx):
        await ctx.send("Создаём роли...")
        await self.guild.create_role(name="GM")
        self.gmrole = Role(self.guild.roles[1])
        log(f"Role {self.guild.roles[1]} created")
        await self.guild.create_role(name="spectator")
        self.spectatorrole = Role(self.guild.roles[1])
        log(f"Role {self.guild.roles[1]} created")
        await self.guild.create_role(name="mfplayer")
        self.mafiarole = Role(self.guild.roles[1])
        log(f"Role {self.guild.roles[1]} created")
        await self.GM.member.add_roles(self.gmrole.role)

    async def clear_cache(self, ctx):
        await ctx.send("Очищаем кеш прошлой игры...")
        self.regplayers.clear()
        log("regplayers cleared")
        self.aliveplayers.clear()
        log("aliveplayers cleared")
        self.mafiaplayers.clear()
        log("mafiaplayers cleared")
        self.LEVEL = "PRESTART"
        log(f"LEVEL := {self.LEVEL}")
        self.PHASE = "DAY"
        log(f"PHASE := {self.PHASE}")
        self.guild = ctx.guild
        log(f"guild := {self.guild.name}")
        self.GM = Player(ctx.author)
        log(f"GM := {self.GM.member.name}")

    async def spectate_success(self, ctx):
        self.regplayers[ctx.author.id] = Player(ctx.author)
        log(f"{ctx.author.name} added to regplayers")
        self.regplayers[ctx.author.id].role = "SPECTATOR"
        log(f"Assigned gamerole NONE to {ctx.author}")
        await ctx.author.add_roles(self.spectatorrole.role)
        log(f"role {self.spectatorrole.name} added to {ctx.author.name}")
        await self.generalchannel.channel.send(f"**{ctx.author.name} зашел в наблюдатели**")
        await ctx.send("Вы наблюдаете за игрой!")

    async def leave_success(self, ctx):
        await ctx.author.remove_roles(self.mafiarole.role)
        log(f"removed role {self.mafiarole.role.name} from {ctx.author.name}")
        await ctx.author.remove_roles(self.spectatorrole.role)
        log(f"removed role {self.spectatorrole.role.name} from {ctx.author.name}")
        await self.generalchannel.channel.send(f"**{ctx.author.name} покинул игру**")
        # if self.regplayers[inter.author.id].role == "SPECTATOR":
        #     await inter.author.remove_roles(self.spectatorrole.role)
        #     log(f"removed role {self.spectatorrole.role.name} from {inter.author.name}")
        self.regplayers.pop(ctx.author.id)
        log(f"removed {ctx.author.name} from regplayers")
        await ctx.send("Вы покинули игру Мафия")

    async def join_success(self, ctx):
        self.regplayers[ctx.author.id] = Player(ctx.author)
        log(f"{ctx.author.name} added to regplayers")
        await self.generalchannel.channel.send(f"**{ctx.author.name} зашел в игру**")
        await ctx.author.add_roles(self.spectatorrole.role)
        log(f"role {self.spectatorrole.name} added to {ctx.author.name}")
        await ctx.author.add_roles(self.mafiarole.role)
        log(f"role {self.mafiarole.name} added to {ctx.author.name}")
        self.regplayers[ctx.author.id].role = "NONE"
        log(f"Assigned gamerole NONE to {ctx.author}")
        await ctx.send("Вы зарегистрировались в игре!")

    async def spect_to_prest(self):
        for player in self.regplayers:
            if self.regplayers[player].role == "NONE":
                self.prestplayers[player] = self.regplayers[player]
                await self.prestplayers[player].member.remove_roles(self.spectatorrole.role)
                log(f"removed role {self.spectatorrole.name} from {self.prestplayers[player].name}")
                log(f"{self.prestplayers[player].name} now a player")

    async def create_personal_channels(self, ctx):
        await ctx.send("Создаём персональные каналы...")
        i = 0
        for player in self.prestplayers:
            await self.guild.create_text_channel(str(self.prestplayers[player].name), category=self.category.channel,
                                                 overwrites={
                                                     self.guild.default_role: disnake.PermissionOverwrite(
                                                         view_channel=False),
                                                     self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
                                                     self.spectatorrole.role: disnake.PermissionOverwrite(
                                                         view_channel=False),
                                                     self.mafiarole.role: disnake.PermissionOverwrite(
                                                         view_channel=False),
                                                     self.prestplayers[player].member: disnake.PermissionOverwrite(
                                                         view_channel=True)
                                                 }, position=3)
            self.personalchannels[player] = Channel(self.category.channel.channels[3 + i])
            i += 1
            log(f"created personal channel {self.personalchannels[player]} for {self.prestplayers[player].name}")

    async def give_roles(self, ctx):
        await ctx.send("Выдаём роли...")
        for i in range(self.mafiacount):
            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[1]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[1]} role to {self.aliveplayers[randomnum].name}")
        if len(self.aliveplayers) >= 4 & len(self.aliveplayers) <= 6:
            self.generate_mares(list(self.prestplayers.values()))
        elif len(self.aliveplayers) == 7:
            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[2]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[2]} role to {self.aliveplayers[randomnum].name}")

            self.generate_mares(list(self.prestplayers.values()))
        elif len(self.aliveplayers) >= 8 & len(self.aliveplayers) <= 10:
            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[2]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[2]} role to {self.aliveplayers[randomnum].name}")

            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[3]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[3]} role to {self.aliveplayers[randomnum].name}")

            self.generate_mares(list(self.prestplayers.values()))
        elif len(self.aliveplayers) > 10 & len(self.aliveplayers) <= 14:
            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[2]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[2]} role to {self.aliveplayers[randomnum].name}")

            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[3]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[3]} role to {self.aliveplayers[randomnum].name}")

            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[4]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[4]} role to {self.aliveplayers[randomnum].name}")

            self.generate_mares(list(self.prestplayers.values()))
        else:
            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[2]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[2]} role to {self.aliveplayers[randomnum].name}")

            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[3]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[3]} role to {self.aliveplayers[randomnum].name}")

            randomnum = random.choice(list(self.prestplayers))
            self.prestplayers[randomnum].role = self.ROLES[4]
            self.aliveplayers[randomnum] = self.prestplayers[randomnum]
            self.prestplayers.pop(randomnum)
            log(f"Assigned {self.ROLES[4]} role to {self.aliveplayers[randomnum].name}")

            self.generate_mares(list(self.prestplayers.values()))

    async def send_role_messages(self, ctx):
        await ctx.send("Рассылаем сообщения...")
        for playeri in self.aliveplayers:
            player = self.aliveplayers[playeri]
            log(f"{player.name} == {self.personalchannels[player.id].name}?")
            # if str(self.aliveplayers[i].name) == str(ctx.guild.categories[1].channels[3+i].name):
            if player.role == self.ROLES[0]:
                await self.personalchannels[player.id].channel.send(
                    f"{player.member.mention}, твоя роль - **Мирная кобылка**")
            if player.role == self.ROLES[1]:
                await self.personalchannels[player.id].channel.send(
                    f"{player.member.mention}, твоя роль - **Алмазный пёс**")
                self.mafiaplayers[player.id] = self.aliveplayers[player.id]
                log(f"{self.mafiaplayers[player.id].name} was mafia! Added record to mafiaplayers dict")
            if player.role == self.ROLES[3]:
                await self.personalchannels[player.id].channel.send(
                    f"{player.member.mention}, твоя роль - **Медсестра**")
            if player.role == self.ROLES[2]:
                await self.personalchannels[player.id].channel.send(f"{player.member.mention}, твоя роль - **Шериф**")
            if player.role == self.ROLES[4]:
                await self.personalchannels[player.id].channel.send(f"{player.member.mention}, твоя роль - **Маньяк**")
            if player.role == self.ROLES[5]:
                await self.personalchannels[player.id].channel.send(
                    f"{player.member.mention}, твоя роль - **Помощник шерифа**")

    async def create_mafia_channel(self):
        await self.guild.create_text_channel("mafia channel", category=self.category.channel, overwrites={
            self.guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            self.gmrole.role: disnake.PermissionOverwrite(view_channel=True),
            self.spectatorrole.role: disnake.PermissionOverwrite(view_channel=False),
            self.mafiarole.role: disnake.PermissionOverwrite(view_channel=False),
        }, position=3)
        self.mafiachannel = Channel(self.guild.channels[3])
        log(f"Channel {self.mafiachannel.name} was created!")
        for playeri in self.mafiaplayers:
            player = self.mafiaplayers[playeri]
            await self.mafiachannel.channel.set_permissions(self.guild.default_role, view_channel=False)
            await self.mafiachannel.channel.set_permissions(self.mafiarole.role, view_channel=False)
            await self.mafiachannel.channel.set_permissions(self.spectatorrole.role, view_channel=False)
            await self.mafiachannel.channel.set_permissions(self.gmrole.role, send_messages=True, view_channel=True)
            await self.mafiachannel.channel.set_permissions(player.member, send_messages=True, view_channel=True)

    async def inspect_success(self, ctx, i_id):
        if self.aliveplayers[int(i_id)].role == self.ROLES[1] or self.aliveplayers[int(i_id)].role == self.ROLES[4]:
            await ctx.send(f"{self.aliveplayers[int(i_id)].name} играет за сторону псов!")
            log(f"{self.aliveplayers[int(i_id)].name} playing for dogs")
        else:
            await ctx.send(f"{self.aliveplayers[int(i_id)].name} играет за сторону кобылок!")
            log(f"{self.aliveplayers[int(i_id)].name} playing for mares")

    async def heal_success(self, ctx, h_id):
        log(f"Attempting to heal {self.aliveplayers[int(h_id)].name}!")
        await ctx.send(f"Пытаемся вылечить {self.aliveplayers[int(h_id)].name}...")
        if h_id == self.HEALID:
            await ctx.send("Игрок уже был вылечен прошлый раз!")
        else:
            self.aliveplayers[int(h_id)].alive = True
            self.HEALID = int(h_id)

    async def execute_success(self, e_id):
        self.aliveplayers[e_id].alive = False
        await self.generalchannel.channel.send(
            f"Игрок {self.aliveplayers[e_id].mention} был казнён! Игрок прожил с нами {self.aliveplayers[e_id].days} дней!")
        # TODO: Добавить объявление роли при казни?
        log(f"{self.aliveplayers[e_id].name} was executed!")
        await self.aliveplayers[e_id].member.add_roles(self.spectatorrole.role)
        log(f"Assigned {self.spectatorrole.name} role to {self.aliveplayers[e_id].name}")
        if self.aliveplayers[e_id].role == self.ROLES[1]:
            self.mafiaplayers.pop(e_id)
            log(f"player {self.aliveplayers[e_id].name} was pop-ed from mafiaplayers dict")
            await self.mafiachannel.channel.set_permissions(self.aliveplayers[e_id].member, view_channel=False)
            log(f"Removed rights to view channel {self.mafiachannel.name} from {self.aliveplayers[e_id].name}")
        self.aliveplayers[e_id].role = "SPECTATOR"
        log(f"Assigned SPECTATOR gamerole to {self.aliveplayers[e_id].name}")
        self.aliveplayers.pop(e_id)
        log(f"player {self.aliveplayers[e_id].name} was pop-ed from aliveplayers dict")

    async def kill_success(self, ctx, k_id):
        self.aliveplayers[k_id].alive = False
        log(f"Attempting to kill {self.aliveplayers[k_id].name}!")
        self.aliveplayers[int(k_id)].alive = False
        log(f"Attempting to kill {self.aliveplayers[int(k_id)].name}!")
        await ctx.send(f"Пытаемся убить {self.aliveplayers[int(k_id)].name}...")

    async def game_ended(self, ctx):
        log(f"Game ended!")
        if len(self.mafiaplayers) == 0:
            await self.generalchannel.channel.send(
                f"{self.mafiarole.role.mention}, наши поздравления! **Победа мирных кобылок за {self.DAY} дней!!**")
        else:
            await self.generalchannel.channel.send(
                f"{self.mafiarole.role.mention}, у вас не получилось спастись от геноцида алмазных псов... **Победа алмазных псов за {self.DAY} дней!!**")

        await ctx.send(f"Игра окончена!")
        await self.generalchannel.channel.send(f"**Остались в живых:**")

        for playeri in self.aliveplayers:
            player = self.aliveplayers[playeri]
            player.days += 1
            if player.role == self.ROLES[0]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Мирная кобылка**")
            if player.role == self.ROLES[1]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Алмазный пёс**")
            if player.role == self.ROLES[2]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Шериф**")
            if player.role == self.ROLES[3]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Медсестра**")
            if player.role == self.ROLES[4]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Маньяк**")
            if player.role == self.ROLES[5]:
                await self.generalchannel.channel.send(
                    f"{player.member.mention} - **Помощник шерифа**")

        # Открытие каналов на конец игры
        await self.generalchannel.channel.set_permissions(self.mafiarole.role, view_channel=True,
                                                          send_messages=True)
        await self.generalchannel.channel.set_permissions(self.spectatorrole.role, view_channel=True,
                                                          send_messages=True)
        log(f"{self.generalchannel.name} unlocked!")
        await self.spectatorchannel.channel.set_permissions(self.mafiarole.role, view_channel=True,
                                                            send_messages=True)
        await self.spectatorchannel.channel.set_permissions(self.spectatorrole.role, view_channel=True,
                                                            send_messages=True)
        log(f"{self.spectatorchannel.name} unlocked!")
        await self.voicechannel.channel.set_permissions(self.mafiarole.role,
                                                        view_channel=True,
                                                        speak=True,
                                                        use_voice_activation=True)
        await self.voicechannel.channel.set_permissions(self.spectatorrole.role,
                                                        view_channel=True,
                                                        speak=True,
                                                        use_voice_activation=True)
        log(f"{self.voicechannel.name} unlocked!")

        await ctx.send("Готово! Игра окончена!")

    async def change_phase(self, ctx):
        if self.PHASE == "DAY":
            self.PHASE = "NIGHT"
            log(f"PHASE := {self.PHASE}")
            await ctx.guild.categories[1].channels[0].send("**Наступает ночь...**")
            await self.generalchannel.channel.set_permissions(self.mafiarole.role,
                                                              send_messages=False,
                                                              view_channel=True,
                                                              add_reactions=False)
            log(f"Locked channel: {self.generalchannel.name}")
            await self.voicechannel.channel.set_permissions(self.mafiarole.role,
                                                            view_channel=True,
                                                            speak=False,
                                                            use_voice_activation=False)
            log(f"Locked channel: {self.voicechannel.name}")
        else:
            self.PHASE = "DAY"
            self.DAY += 1
            log(f"DAY++")
            log(f"PHASE := {self.PHASE}")
            await ctx.guild.categories[1].channels[0].send("**Всходит солнце...**")
            await ctx.guild.categories[1].channels[0].send(f"**Наступает __{self.DAY}__ день**")
            await ctx.guild.categories[1].channels[0].send("На утро не проснулся(ись):")
            for player in list(self.aliveplayers.values()):
                if not player.alive:
                    log(f"{player.name} was killed!")
                    await self.generalchannel.channel.send(
                        f"{player.member.mention} - был убит и прожил с нами {player.days} дней!")
                    await player.member.add_roles(self.spectatorrole.role)
                    log(f"Assigned {self.spectatorrole.name} role to {player.name}")
                    if player.role == self.ROLES[1]:
                        self.mafiaplayers.pop(player.id)
                        log(f"player {player.name} was pop-ed from mafiaplayers dict")
                        await self.mafiachannel.channel.set_permissions(player.member, view_channel=False)
                        log(f"Removed rights to view channel {self.mafiachannel.name} from {player.name}")
                    player.role = "SPECTATOR"
                    log(f"Assigned SPECTATOR gamerole to {player.name}")
                    self.aliveplayers.pop(player.id)
                    log(f"player {player.name} was pop-ed from aliveplayers dict")
                else:
                    player.days += 1
            await self.generalchannel.channel.set_permissions(self.mafiarole.role,
                                                              send_messages=True,
                                                              view_channel=True,
                                                              add_reactions=True)
            log(f"Unlocked channel: {self.generalchannel.name}")
            await self.voicechannel.channel.set_permissions(self.mafiarole.role,
                                                            view_channel=True,
                                                            speak=True,
                                                            use_voice_activation=True)
            log(f"Unlocked channel: {self.voicechannel.name}")

    @commands.slash_command(
        name="join",
        usage="/join",
        description="Зайти в игру Мафия"
    )
    async def join(self, ctx):
        log(f"{ctx.author.name} used /join")
        if self.LEVEL == "PRESTART":
            if ctx.author.id in self.regplayers.keys():
                await fail(ctx,
                           "Вы уже зарегистрированы в игре! Используйте `/leave` для выхода.",
                           f"{ctx.author.name} already registered!")
                return 0
            await self.join_success(ctx)
        elif self.LEVEL == "NOTHING":
            await fail(ctx,
                       "Нет запущенных игр!",
                       "game wasn't started")
        else:
            await fail(ctx,
                       "Игра уже началась, если хотите зайти в наблюдатели, используйте `/spectate`",
                       "game was already started")

    @commands.slash_command(
        name="leave",
        usage="/leave",
        description="Выйти из игры Мафия"
    )
    async def leave(self, ctx):
        # TODO: ГМ не может выходить до конца игры
        log(f"{ctx.author.name} used /leave")
        if self.LEVEL != "NOTHING":
            if ctx.author.id in self.regplayers.keys():
                await self.leave_success(ctx)
                return 0
            await fail(ctx,
                       "Вам нечего покидать!",
                       f"{ctx.author.name} wasn't registered")
        else:
            await fail(ctx,
                       "Нет запущенных игр!",
                       "game wasn't started")

    @commands.slash_command(
        name="spectate",
        usage="/spectate",
        description="Наблюдать за игрой Мафия"
    )
    async def spectate(self, ctx):
        log(f"{ctx.author.name} used /spectate")
        if self.LEVEL != "NOTHING":
            if ctx.author.id in self.regplayers.keys():
                await fail(ctx,
                           "Вы уже наблюдаете за игрой! Используйте `/leave` для выхода.",
                           f"{ctx.author.name} already spectating")
                return 0
            # Успешно
            await self.spectate_success(ctx)
        else:
            await fail(ctx,
                       "Нет запущенных игр!",
                       f"game wasn't started")

    @commands.slash_command(
        name="prestmafia",
        usage="/prestmafia",
        description="Открыть набор на игру Мафия"
    )
    async def prestmafia(self, ctx):
        log(f"{ctx.author.name} used /prestmafia")

        if self.LEVEL == "NOTHING":
            # Очищаем кеш прошлой игры
            await self.clear_cache(ctx)

            # Создаём роли
            await self.create_roles(ctx)

            # Создаём каналы
            await self.create_gen_channels(ctx)

            # Рассылаем сообщения
            await self.send_gen_messages(ctx)

            await ctx.send("Готово!")
            await self.commandschannel.channel.send("Игра создана!")
            log("Game successfully created!")
        else:
            await fail(ctx,
                       "Игра уже создана",
                       "game already created")

    @commands.slash_command(
        name="stmafia",
        usage="/stmafia",
        description="Запустить игру Мафия"
    )
    async def stmafia(self, ctx):
        log(f"{ctx.author.name} used /stmafia")
        if self.gmrole.role not in ctx.author.roles:
            await fail(ctx,
                       "Вы должны быть ведущим для исполнения данной команды!",
                       f"Insufficient rights - {ctx.author.name}")
            return 0
        # Проверка на PRESTMAFIA
        if self.LEVEL == "PRESTART":
            # Проверка на количество игроков    (setting)   default=4
            if len(self.prestplayers) < 4:
                await fail(ctx,
                           f"Не можем начать, слишком мало игроков: {len(self.prestplayers)}",
                           f"Unable to start: Small players count! - {len(self.prestplayers)}")
                return 0

            await ctx.send("Начинаем игру...")

            # Удаляем у игроков роль наблюдателей и перемещаем их в словарь Prestplayers
            await self.spect_to_prest()

            self.mafiacount = math.ceil(len(self.prestplayers) / 4)
            self.HEALID = 0
            log(f"HEALID := {self.HEALID}")
            self.LEVEL = "START"
            log(f"LEVEL := {self.LEVEL}")
            self.PHASE = "DAY"
            log(f"PHASE := {self.PHASE}")
            self.DAY = 0
            log(f"DAY := {self.DAY}")

            # Создаём персональные каналы
            await self.create_personal_channels(ctx)

            # Выдаём роли
            await self.give_roles(ctx)

            # Пишем участникам об их ролях
            await self.send_role_messages(ctx)

            # Проверка необходимо ли создавать канал для общения мафии
            if len(self.aliveplayers) >= 8:
                await self.create_mafia_channel()

            await self.generalchannel.channel.send("Игра началась")
            await self.commandschannel.channel.send("Game Started!")
            log("Game succesfully started")

        elif self.LEVEL == "START":
            await fail(ctx,
                       "Игра уже началась",
                       "game already started")
        else:
            await fail(ctx,
                       "Для начала запустите регистрацию - `/prestmafia`",
                       "game wasn't created")

    @commands.slash_command(
        name="next",
        usage="/next",
        description="Следующая фаза игры"
    )
    async def next(self, ctx):
        log(f"{ctx.author.name} used /next")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                if (len(self.aliveplayers) <= len(self.mafiaplayers)) or (len(self.mafiaplayers) == 0):
                    await self.game_ended(ctx)
                    return 0
                await self.change_phase(ctx)
                await ctx.send(f"Готово! Наступает {self.PHASE}")
                log(f"Successfully changed phase to {self.PHASE}!")
            else:
                await fail(ctx,
                           "У вас недостаточно прав для этого действия! Вы должны быть ведущим игры!",
                           f"Insufficient rights - {ctx.author.name}")
        elif self.LEVEL == "PRESTART":
            await fail(ctx,
                       "Игра еще не запущена! Используйте `/stmafia`",
                       "Game wasn't started")
        else:
            await fail(ctx,
                       "Игра еще не создана! Используйте `/prestmafia`",
                       "Game wasn't created")

    @commands.command(
        name="kill",
        usage="/kill {id}",
        description="Убить игрока по id"
    )
    async def kill(self, ctx, k_id):
        log(f"{ctx.author.name} used /kill")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                await self.kill_success(ctx, k_id)
            else:
                await fail(ctx,
                           "Вы должны быть ведущим для исполнения данной команды!",
                           f"Insufficient rights - {ctx.author.name}")
        elif self.LEVEL == "PRESTART":
            await fail(ctx,
                       "Нет запущенных игр! Используйте `/stmafia`!",
                       "game wasn't started!")
        else:
            await fail(ctx,
                       "Нет созданных игр! Используйте `/prestmafia`!",
                       "game wasn't created!")

    @commands.command(
        name="execute",
        usage="/execute {id}",
        description="Казнить игрока по id"
    )
    async def execute(self, ctx, e_id):
        log(f"{ctx.author.name} used /execute")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                await self.execute_success(e_id)
            else:
                await fail(ctx,
                           "Вы должны быть ведущим для исполнения данной команды!",
                           f"Insufficient rights - {ctx.author.name}")
        elif self.LEVEL == "PRESTART":
            await fail(ctx,
                       "Нет запущенных игр! Используйте `/stmafia`!",
                       "game wasn't started!")
        else:
            await fail(ctx,
                       "Нет созданных игр! Используйте `/prestmafia`!",
                       "game wasn't created!")

    @commands.command(
        name="heal",
        usage="/heal {id}",
        description="Вылечить игрока по id"
    )
    async def heal(self, ctx, h_id):
        log(f"{ctx.author.name} used /heal")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                await self.heal_success(ctx, h_id)
            else:
                await fail(ctx,
                           "Вы должны быть ведущим для исполнения данной команды!",
                           f"Insufficient rights - {ctx.author.name}")
        elif self.LEVEL == "PRESTART":
            await fail(ctx,
                       "Нет запущенных игр! Используйте `/stmafia`!",
                       "game wasn't started!")
        else:
            await fail(ctx,
                       "Нет созданных игр! Используйте `/prestmafia`!",
                       "game wasn't created!")

    @commands.command(
        name="inspect",
        usage="/inspect {id}",
        desctiption="Проверить игрока"
    )
    async def inspect(self, ctx, i_id):
        log(f"{ctx.author.name} used /inspect")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                await self.inspect_success(ctx, i_id)
            else:
                await fail(ctx,
                           "Вы должны быть ведущим для исполнения данной команды!",
                           f"Insufficient rights - {ctx.author.name}")
        elif self.LEVEL == "PRESTART":
            await fail(ctx,
                       "Нет запущенных игр! Используйте `/stmafia`!",
                       "game wasn't started!")
        else:
            await fail(ctx,
                       "Нет созданных игр! Используйте `/prestmafia`!",
                       "game wasn't created!")

    @commands.command(
        name="endmafia",
        usage="/endmafia",
        description="Окончить игру"
    )
    async def endmafia(self, ctx):
        log(f"{ctx.author.name} used /endmafia")
        if self.LEVEL == "START" or self.LEVEL == "PRESTART":
            if self.gmrole.role in ctx.author.roles:
                self.LEVEL = "NOTHING"
                log(f"LEVEL := {self.LEVEL}")
                self.PHASE = "DAY"
                log(f"PHASE := {self.PHASE}")
                await self.mafiarole.role.delete()
                log(f"mafiarole deleted")
                await self.spectatorrole.role.delete()
                log(f"spectator deleted")
                await self.gmrole.role.delete()
                log(f"gm deleted")
                for channel in self.category.channel.channels:
                    log(f"{channel.name} deleted")
                    await channel.delete()
                log(f"{self.category.channel.name} deleted")
                await self.category.channel.delete()
                await ctx.send("Игра остановлена")
                log("game ended successfully")
            else:
                await fail(ctx,
                           "Вы должны быть ведущим для исполнения данной команды!",
                           f"Insufficient rights - {ctx.author.name}")
        else:
            await fail(ctx,
                       "Нет созданных игр! Используйте `/prestmafia`!",
                       "game wasn't created!")

    @commands.command(
        name="status",
        usage="/status",
        description="Информация по игре Мафия"
    )
    async def status(self, ctx):
        log(f"{ctx.author.name} used /status")
        if self.LEVEL == "NOTHING":
            await fail(ctx,
                       "Нет созданных игр",
                       "no existed games!")
            return 0

        if self.gmrole.role in ctx.author.roles:
            await ctx.send(f'''mafiarole = {self.mafiarole.name}
        gmrole = {self.gmrole.name}
        spectatorrole = {self.spectatorrole.name}
        guild = {self.guild.name}            
        GM = {self.GM.name}
        generalchannel = {self.generalchannel.name}
        commandschannel = {self.commandschannel.name}
        spectatorchannel = {self.spectatorchannel.name}
        voicechannel = {self.voicechannel.name}
            ''')
            try:
                await ctx.send(f"mafiachannel = {self.mafiachannel.name}")
            except BaseException:
                await ctx.send("mafiachannel = NONE")
            await ctx.send(f'''category = {self.category.name}
        LEVEL = {self.LEVEL}
        PHASE = {self.PHASE}
        HEALID = {self.HEALID}
        **Personal channels:**''')
            for channeli in self.personalchannels:
                channel = self.personalchannels[channeli]
                await ctx.send(f"{channel.name}")

            await ctx.send("**Registered players:**")
            for playeri in self.regplayers:
                player = self.regplayers[playeri]
                await ctx.send(f"{player.name}")

            await ctx.send("**Prest players:**")
            for playeri in self.prestplayers:
                player = self.prestplayers[playeri]
                await ctx.send(f"{player.name}")

            await ctx.send("**Alive players:**")
            for playeri in self.aliveplayers:
                player = self.aliveplayers[playeri]
                await ctx.send(f"{player.name}")

            await ctx.send("**Mafia players:**")
            for playeri in self.mafiaplayers:
                player = self.mafiaplayers[playeri]
                await ctx.send(f"{player.name}")
        else:
            await fail(ctx,
                       "Вы должны быть ведущим для исполнения данной команды!",
                       f"Insufficient rights - {ctx.author.name}")

    @commands.command(
        name="check",
        usage="/check",
        description="Информация по игроку"
    )
    async def check(self, ctx, p_id):
        log(f"{ctx.author} used /check")
        if self.gmrole.role in ctx.author.roles:
            await ctx.send(f"name = {self.regplayers[int(p_id)].name}")
            await ctx.send(f"role = {self.regplayers[int(p_id)].role}")
            await ctx.send(f"id = {self.regplayers[int(p_id)].id}")
            await ctx.send(f"days = {self.regplayers[int(p_id)].days}")
            await ctx.send(f"alive = {self.regplayers[int(p_id)].alive}")
        else:
            await fail(ctx,
                       "Вы должны быть ведущим для исполнения данной команды!",
                       f"Insufficient rights - {ctx.author.name}")


def setup(bot):
    bot.add_cog(Mafia(bot))
