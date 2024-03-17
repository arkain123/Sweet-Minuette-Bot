import disnake
from disnake.ext import commands
from view.console_out import log, important, warning, error
import random


class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        important("COGS module Commands connected")

    @commands.slash_command(
        name="hello",
        usage="/hello",
        description="Say hello to bot!"
    )
    async def hello(self, inter):
        await inter.send("world")
        log(f"{inter.author.name} used /hello")

    @commands.slash_command(
        name="roll",
        usage="/roll <number> || <number number> || <number number number>",
        description="Кинуть один или несколько кубиков",
    )
    async def roll(self, inter, *, dice):
        log(f"{inter.author} used /roll " + dice)
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
                    warning(f"/roll was used with incorrect parameters: negative number")

            if len(inputs) > 1:
                await inter.send(f"{inter.author.mention}, выпало {'+'.join(outputs)}=**{rollsum}**")
            else:
                await inter.send(f"{inter.author.mention}, выпало **{outputs[0]}**")
        except ValueError:
            await inter.send("Используйте только числа!")
            warning(f"/roll was used with incorrect parameters: string")


def setup(bot):
    bot.add_cog(Commands(bot))