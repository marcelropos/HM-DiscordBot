from typing import Optional

from discord import SelectOption, Interaction
from discord.ui import Select

from cogs.util.select_view import SelectRoleView


class CustomSelect(Select):
    def __init__(self,
                 row: int,
                 placeholder: str,
                 options: list[str],
                 response_message: str):
        self.select_view: Optional[SelectRoleView] = None
        options: list[SelectOption] = [SelectOption(label=option) for option in options]
        self.response_message = response_message
        super().__init__(placeholder=placeholder, max_values=1, min_values=1, options=options, row=row)

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message(content=self.response_message, ephemeral=True)
        self.select_view.finished_interaction(self)

    def set_view(self, select_view: SelectRoleView):
        self.select_view: SelectRoleView = select_view
