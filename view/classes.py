import disnake
from disnake.ext import commands
from typing import Optional
from view.console_out import important


def connected():
    important("Module Classes connected")
    return 1


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