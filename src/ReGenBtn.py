import discord.ui


class ReGenBtn(discord.ui.View):
    def __init__(self, callback, message_obj_list: list[discord.Message]):
        super().__init__()
        self.callback = callback
        self.message_obj_list = message_obj_list

    @discord.ui.button(label="Regenerate", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        # delete msg
        for msg in self.message_obj_list:
            await msg.delete()

        await self.callback()
