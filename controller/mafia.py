import disnake
import random
import math

from disnake.ui import select

from view.classes import DropdownMenu
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


async def show_dropdown_menu(ctx, options):
    view = DropdownMenu(options)

    select_options = [disnake.SelectOption(label=str(opt), value=str(opt)) for opt in options]
    view.children[0].options = select_options

    message = await ctx.send('Выберите элемент:', view=view)

    try:
        interaction = await ctx.bot.wait("select_option",
                                         check=lambda i: i.component.id == select.id and i.message.id == message.id,
                                         timeout=60)

        selected_values = interaction.data["values"]
        selected_option = next(opt.label for opt in view.children[0].options if opt.value == selected_values[0])

        await interaction.edit_origin(content=f"Выбран элемент: {selected_option}")

    except TimeoutError:
        await message.edit(content="Превышено время ожидания выбора элемента")


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
            1: "CHANGE",
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
        embed_gen = disnake.Embed(
            title="Регистрация",
            description=f"{self.mafiarole.role.mention}, добро пожаловать в игру. Сейчас идёт **фаза регистрации**. Во время этой фазы ведущий набирает игроков. **Ждите начала игры!** Если вы передумали участвовать в игре - напишите `/leave`",
            color=0x4682B4
        )
        embed_gen.add_field(
            name="General",
            value="Канал **general** предназначен для общения игроков во время дневной фазы. Этот канал видят также и наблюдатели. Мертвые игроки писать в него не могут!",
            inline=False
        )
        embed_gen.add_field(
            name="Spectating",
            value="Канал **spectating** канал предназначеный для мертвых игроков и наблюдателей. В этом чате вы можете спокойно раскрывать свою роль и обсуждать игровые моменты",
            inline=False
        )
        embed_spec = disnake.Embed(
            title="Spectators",
            description=f"{self.spectatorrole.role.mention} Этот канал предназначен для общения мертвых игроков и наблюдателей. **Старайтесь не мешать игре!**",
            color=0x4682B4
        )
        embed_com = disnake.Embed(
            title="Commands",
            description=f"{self.gmrole.role.mention} Команды и заметки, которые вам могут пригодиться во время игры пишите сюда.",
            color=0x4682B4
        )
        await self.generalchannel.channel.send(embed=embed_gen)
        await self.spectatorchannel.channel.send(embed=embed_spec)
        await self.commandschannel.channel.send(embed=embed_com)

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
        embed = disnake.Embed(
            title="Новый наблюдатель",
            description=f"**{ctx.author.name}** зашел в наблюдатели!",
            color=0x33ff3f
        )
        embed.set_thumbnail(url=f"{self.regplayers[ctx.author.id].member.avatar.url}")
        await self.generalchannel.channel.send(embed=embed)
        await ctx.send("Вы наблюдаете за игрой!")

    async def leave_success(self, ctx):
        await ctx.author.remove_roles(self.mafiarole.role)
        log(f"removed role {self.mafiarole.role.name} from {ctx.author.name}")
        await ctx.author.remove_roles(self.spectatorrole.role)
        log(f"removed role {self.spectatorrole.role.name} from {ctx.author.name}")
        embed = disnake.Embed(
            title="Игрок вышел",
            description=f"**{ctx.author.name}** покинул игру!",
            color=0xff3333
        )
        embed.set_thumbnail(url=f"{self.regplayers[ctx.author.id].member.avatar.url}")
        await self.generalchannel.channel.send(embed=embed)
        self.regplayers.pop(ctx.author.id)
        log(f"removed {ctx.author.name} from regplayers")
        await ctx.send("Вы покинули игру Мафия")

    async def join_success(self, ctx):
        self.regplayers[ctx.author.id] = Player(ctx.author)
        log(f"{ctx.author.name} added to regplayers")
        embed = disnake.Embed(
            title="Присоединился к игре",
            description=f"**{ctx.author.name}** зашел в игру!",
            color=0x33ff3f
        )
        embed.set_thumbnail(url=f"{self.regplayers[ctx.author.id].member.avatar.url}")
        await self.generalchannel.channel.send(embed=embed)
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
                embed = disnake.Embed(
                    title="Мирная кобылка",
                    description=f"{player.member.mention}, твоя роль - **Мирная кобылка**",
                    color=0x8aff33
                )
                embed.add_field(
                    name="Игра за мирную кобылку",
                    value="Ваша цель: найти чейнджлингов, что мешают вам спокойно жить. Несмотря на ваши ограниченые возможности,"
                          " используйте вашу хитрость, логику и смекалку. Будет полезно найти себе друзей, но постарайтесь не нажить себе врагов",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)
            if player.role == self.ROLES[1]:
                embed = disnake.Embed(
                    title="Чейнджлинг",
                    description=f"{player.member.mention}, твоя роль - **Чейнджлинг**",
                    color=0xff4633
                )
                embed.add_field(
                    name="Игра за чейнджлингов",
                    value="Ваша цель: истребить весь город. Вам предстоит грамотно затесаться в ряды кобылок, чтобы избавиться от всех его жителей. "
                          "Благодаря вашей связи с гнездом, вы можете отличить других чейнджлингов от обычных поняшек. Действуйте в команде со своим ульем!",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)
                self.mafiaplayers[player.id] = self.aliveplayers[player.id]
                log(f"{self.mafiaplayers[player.id].name} was mafia! Added record to mafiaplayers dict")
            if player.role == self.ROLES[3]:
                embed = disnake.Embed(
                    title="Медсестра",
                    description=f"{player.member.mention}, твоя роль - **Медсестра**",
                    color=0x8aff33
                )
                embed.add_field(
                    name="Игра за медсестру",
                    value="Ваша цель: содействовать городу используя ваши медицинские навыки. Вы играете за сторону мирных кобылок и в ваших интересах споймать всех чейнджлингов. "
                          "Вы не можете лечить одного игрока 2 ночи подряд!",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)
            if player.role == self.ROLES[2]:
                embed = disnake.Embed(
                    title="Шериф",
                    description=f"{player.member.mention}, твоя роль - **Шериф**",
                    color=0x8aff33
                )
                embed.add_field(
                    name="Игра за шерифа",
                    value="Ваша цель: содействовать городу используя ваши детективные способности. Вы играете за сторону мирных кобылок и в ваших интересах споймать всех чейнджлингов. "
                          "Проверяйте по жителю каждую ночь и узнавайте кто из них перевертыш. Однако вам еще предстоит убедить жителей, что вы настоящий шериф...",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)
            if player.role == self.ROLES[4]:
                embed = disnake.Embed(
                    title="Маньяк",
                    description=f"{player.member.mention}, твоя роль - **Маньяк**",
                    color=0xff4633
                )
                embed.add_field(
                    name="Игра за маньяка",
                    value="Ваша цель: истребить всех. Вас никогда не волновали проблемы и празднества города. Вы мечтали избавиться от всех этих "
                          "дружбомагичных существ, и ваш час настал. Будет неплохо избавиться от ненавистников, пока город занят чейнджлингами. Однако "
                          "вам предстоит истребить абсолютно всех, без исключений...",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)
            if player.role == self.ROLES[5]:
                embed = disnake.Embed(
                    title="Помощник Шерифа",
                    description=f"{player.member.mention}, твоя роль - **Помощник Шерифа**",
                    color=0x8aff33
                )
                embed.add_field(
                    name="Игра за помощника",
                    value="Ваша цель: помогать шерифу в расследовании. Большой город в одиночку контролировать бывает сложно. Как хорошо, что существуете вы, "
                          "помощник шерифа! Совершайте проверки вместе с шерифом и ускорьте расследование в 2 раза. Однако ваш начальник может быть убит, "
                          "и вам придется быть готовым к этом и занять его место...",
                    inline=False)
                await self.personalchannels[player.id].channel.send(embed=embed)

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
            embed = disnake.Embed(
                title="Успех",
                description=f"{self.aliveplayers[int(i_id)].name} играет за сторону чейнджлингов!",
                color=0xff4633
            )
            await ctx.send(embed=embed)
            log(f"{self.aliveplayers[int(i_id)].name} playing for changelings")
        else:
            embed = disnake.Embed(
                title="Мимо",
                description=f"{self.aliveplayers[int(i_id)].name} играет за сторону кобылок!",
                color=0x8aff33
            )
            await ctx.send(embed=embed)
            log(f"{self.aliveplayers[int(i_id)].name} playing for mares")

    async def heal_success(self, ctx, h_id):
        log(f"Attempting to heal {self.aliveplayers[int(h_id)].name}!")
        await ctx.send(f"Пытаемся вылечить {self.aliveplayers[int(h_id)].name}...")
        if h_id == self.HEALID:
            await ctx.send("Игрок уже был вылечен прошлый раз!")
        else:
            self.aliveplayers[int(h_id)].alive = True
            self.HEALID = int(h_id)
            await ctx.send("Успешно излечен!")

    async def execute_success(self, e_id):
        self.aliveplayers[e_id].alive = False
        embed = disnake.Embed(
            title="Игрок казнён!",
            description=f"Игрок {self.aliveplayers[e_id].mention} был казнён! Игрок прожил с нами {self.aliveplayers[e_id].days} дней!",
            color=0xff4633
        )
        await self.generalchannel.channel.send(embed=embed)
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

    async def kill_success(self, ctx):
        options = []
        for player in self.aliveplayers.values():
            options.append(player.name)
        selected_option = await show_dropdown_menu(ctx, options)
        await ctx.send(f"{selected_option}")
        #self.aliveplayers[player].alive = False
        #log(f"Attempting to kill {self.aliveplayers[player].name}!")

    async def game_ended(self, ctx):
        log(f"Game ended!")
        embed_peace = disnake.Embed(
            title="Конец Игры!",
            description=f"{self.mafiarole.role.mention}, наши поздравления! Вы отлично справились с напастью мерзких жуков!",
            color=0x8aff33
        )
        embed_mafia = disnake.Embed(
            title="Конец Игры!",
            description=f"{self.mafiarole.role.mention}, у вас не получилось спастись от геноцида чейнджлингов... "
                        f"Рой благодарит вас за новые территории",
            color=0xff4633
        )
        embed_mafia.add_field(
            name="Дней прожито",
            value=f"{self.DAY}",
            inline=False)
        embed_peace.add_field(
            name="Дней прожито",
            value=f"{self.DAY}",
            inline=False)

        await ctx.send(f"Игра окончена!")
        players = ""
        days = ""
        roles = ""
        for playeri in self.aliveplayers:
            player = self.aliveplayers[playeri]
            players += f"{player.member.name}\n"
            player.days += 1
            days += f"{player.days}\n"
            if player.role == self.ROLES[0]:
                roles += f"Мирная кобылка\n"
            if player.role == self.ROLES[1]:
                roles += f"Чейнджлинг\n"
            if player.role == self.ROLES[2]:
                roles += f"Шериф\n"
            if player.role == self.ROLES[3]:
                roles += f"Медсестра\n"
            if player.role == self.ROLES[4]:
                roles += f"Маньяк\n"
            if player.role == self.ROLES[5]:
                roles += f"Помощник шерифа\n"

        embed_mafia.add_field(
            name="Выжившие",
            value="",
            inline=False)
        embed_mafia.add_field(
            name="Имя",
            value=f"{players}",
            inline=True)
        embed_peace.add_field(
            name="Имя",
            value=f"{players}",
            inline=True)
        embed_mafia.add_field(
            name="Дней",
            value=f"{days}",
            inline=True)
        embed_peace.add_field(
            name="Дней",
            value=f"{days}",
            inline=True)
        embed_mafia.add_field(
            name="Роль",
            value=f"{roles}",
            inline=True)
        embed_peace.add_field(
            name="Роль",
            value=f"{roles}",
            inline=True)

        if len(self.mafiaplayers) == 0:
            await self.generalchannel.channel.send(embed=embed_peace)
        else:
            await self.generalchannel.channel.send(embed=embed_mafia)

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
            embedgen = disnake.Embed(
                title="Наступает ночь...",
                description=f"На небосвод восходит луна. Пора возвращаться домой...",
                color=0x4682B4
            )
            await self.generalchannel.channel.send(embed=embedgen)
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
            embedgen = disnake.Embed(
                title="Всходит солнце...",
                description=f"На улицах наконец посветлело, значит можно снизить бдительность...",
                color=0x4682B4
            )
            embedgen.add_field(
                name="Дней прожито",
                value=f"{self.DAY}",
                inline=False
            )

            players = ""
            for player in list(self.aliveplayers.values()):
                if not player.alive:
                    log(f"{player.name} was killed!")
                    await player.member.add_roles(self.spectatorrole.role)
                    players += f"{player.name}\n"
                    embed = disnake.Embed(
                        title="Убийство!",
                        description=f"{player.name} был найден мертвым!",
                        color=0xff4633
                    )
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
                    await self.generalchannel.channel.send(embed=embed)
                else:
                    player.days += 1
            embedgen.add_field(
                name="Найдены мертвыми",
                value=f"{players}",
                inline=False)
            await self.generalchannel.channel.send(embed=embedgen)
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
            if len(self.prestplayers) < 0:
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

    # вот тут продолжить
    @commands.command(
        name="kill",
        usage="/kill {id}",
        description="Убить игрока по id"
    )
    async def kill(self, ctx):
        log(f"{ctx.author.name} used /kill")
        if self.LEVEL == "START":
            if self.gmrole.role in ctx.author.roles:
                await self.kill_success(ctx)
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

# TODO: доделать embed для status и check