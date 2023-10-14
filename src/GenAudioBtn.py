import discord.ui


class GenAudioBtn(discord.ui.View):
    """
    Generating audio button
    Just a button that can't be clicked
    """
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Generating voice message...", style=discord.ButtonStyle.gray, emoji="<a:loading:1112646025090445354>", disabled=True)
    async def gen_audio(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
