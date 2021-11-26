from discord.ext.commands import command, Cog
from py_cord_components import (
    Button,
    ButtonStyle,
    Select,
    SelectOption,
    Interaction
)

class ExampleCog(Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @command()
    async def button(self, ctx):
        msg = await ctx.reply("Buttons!", components=[Button(label="Button", custom_id="button1")])
        interaction = await self.bot.wait_for(
            "button_click", check=lambda inter: inter.custom_id == "button1"
        )
        await msg.disable_components()
        await interaction.send(content="Button Clicked")


def setup(bot):
    bot.add_cog(ExampleCog(bot))