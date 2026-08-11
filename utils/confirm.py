from __future__ import annotations
import discord


class ConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, timeout: float = 45):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.value: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("⛔ Diese Bestätigung gehört nicht dir.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Bestätigen", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()
