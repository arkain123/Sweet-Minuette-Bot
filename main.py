import disnake
from disnake.ext import commands
import view.console_out
import random
from dotenv import load_dotenv
import os
from controller import debug, botcommands, events, testing, Sosat, eastereggs
from view import classes, console_out


def connect(module):
    try:
        bot.load_extension(module)
        return 1
    except disnake.ext.commands.errors.ExtensionNotFound:
        console_out.error(f"No connection to {module}")
        return 0


nummodules = 8
load_dotenv()
PREFIX = '/'
intents = disnake.Intents().all()
TOKEN = os.getenv('TOKEN')
connections = 0

bot = commands.Bot(command_prefix=PREFIX, help_command=None, intents=intents, test_guilds=[1175855563444330637, 715142906658422796])

connections += connect("controller.botcommands")
connections += connect("controller.debug")
connections += connect("controller.Sosat")
# connections += connect("controller.events")
connections += connect("controller.testing")
connections += connect("controller.mafia")
connections += connect("controller.eastereggs")
connections += classes.connected()
connections += console_out.connected()

# Number of successful module connections
if connections == nummodules:
    console_out.important("All modules connected!")
else:
    console_out.warning("Some modules cannot be connected!")


@bot.event
async def on_ready():
    view.console_out.important("Bot started, ready to work!")


if __name__ == '__main__':
    bot.run(TOKEN)
