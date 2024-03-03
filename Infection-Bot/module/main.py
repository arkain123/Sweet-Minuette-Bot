import disnake
from disnake.ext import commands
# import controller.commands
# import controller.events
import view.console_out as out
import random
from typing import Optional

f = open("TOKEN.txt", "r")

TOKEN = f.read()
PREFIX = '/'
intents = disnake.Intents().all()

bot = commands.Bot(command_prefix=PREFIX, help_command=None, intents=intents, test_guilds=[1175855563444330637])


class Button(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=10.0)
        self.value = Optional[bool]

    @disnake.ui.button(label="Green Button", style=disnake.ButtonStyle.green, emoji="🤫")
    async def green_button(self, inter: disnake.CommandInteraction):
        await inter.send("Кнопка нажата!")
        self.value = True
        self.stop()

    @disnake.ui.button(label="Red Button", style=disnake.ButtonStyle.red, emoji="🤫")
    async def red_button(self, inter: disnake.CommandInteraction):
        await inter.send("Кнопка нажата!")
        self.value = False
        self.stop()


class Dropdown(disnake.ui.StringSelect):

    def __init__(self):
        options = [
            disnake.SelectOption(label="Burger", description="Очень сочный!", emoji="🍔"),
            disnake.SelectOption(label="Sushi", description="Тают во рту!", emoji="🍣"),
            disnake.SelectOption(label="Pizza", description="Тянущийся сыр!", emoji="🍕")
        ]
        
        super().__init__(
            placeholder="MENU",
            min_values=1,
            max_values=2,
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_message(f"Вы заказали {self.values[0]}. Ожидайте доставки!")


class DropdownView(disnake.ui.View):

    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())


@bot.command()
async def dropdowntest(ctx):
    await ctx.send("Выберите, что желаете заказать:", view=DropdownView())


@bot.event
async def on_ready():
    out.log("Bot started, ready to work!")


@bot.slash_command()
async def hello(inter):
    await inter.send("world")
    out.log(f"{inter.author.mention} used /hello")


@bot.command()
async def embedtest(ctx):
    view = Button()
    embed = disnake.Embed(
        title=f"Embed title",
        description=f"description",
        color=0xfffff
    )
    await ctx.send(embed=embed, view=view)
    out.log(f"{ctx.author.mention} used /embedtest")
    await view.wait()

    if view.value is None:
        await ctx.send("Кнопки не нажаты")
    elif view.value:
        await ctx.send("Зелёная кнопка нажата")
    else:
        await ctx.send("Красная кнопка нажата")


@bot.slash_command()
async def ping(inter):
    out.log(f"{inter.author} used /test")
    out.log(f"{inter.author} testing log message")
    out.warning(f"{inter.author} testing warning message")
    out.error(f"{inter.author} testing error message")
    await inter.send("Ping successful! Check your console for more info")


@bot.slash_command()
async def roll(inter, *, dice):
    out.log(f"{inter.author} used /roll " + dice)
    try:
        inputs = dice.split()
        outputs = []
        rollsum = 0
        for i in range(len(inputs)):
            inputs[i] = int(inputs[i])
            if inputs[i] > 0:
                result = random.randint(1, int(inputs[i]))
                outputs.append(str(result))
                rollsum += result
            else:
                await inter.send(f"Указывайте числа больше нуля! Мне придётся пропустить '{inputs[i]}'")
                out.warning(f"/roll was used with incorrect parameters: negative number")

        if len(inputs) > 1:
            await inter.send(f"{inter.author.mention}, выпало {'+'.join(outputs)}=**{rollsum}**")
        else:
            await inter.send(f"{inter.author.mention}, выпало **{outputs[0]}**")
    except ValueError:
        await inter.send("Используйте только числа!")
        out.warning(f"/roll was used with incorrect parameters: string")


bot.run(TOKEN)
