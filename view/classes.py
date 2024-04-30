import disnake
from disnake.ext import commands
from typing import Optional
from view.console_out import important


def connected():
    important("Module Classes connected")
    return 1


class Button(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=3600)
        self.value = Optional[bool]

    @disnake.ui.button(label="Green Button", style=disnake.ButtonStyle.green, emoji="🤫")
    async def green_button(self, inter: disnake.CommandInteraction):
        await inter.send("Кнопка нажата!")
        self.value = True
        self.stop()


class DropdownMenu(disnake.ui.View):
    def __init__(self, options):
        super().__init__()
        self.options = options

    @disnake.ui.select(placeholder='Выберите элемент', options=[])
    async def dropdown_callback(self, select, interaction):
        selected_option = next(opt for opt in select.options if opt.value == select.values[0])
        return selected_option.label
