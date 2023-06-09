import discord.ui


class ReGenBtn(discord.ui.View):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await self.callback()
