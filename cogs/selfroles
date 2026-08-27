from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config import DEV_ROLE_ID


# ============================================================
# EHRP | SYSTEM — SELF ROLES
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245


# ============================================================
# SELF ROLE CONFIG
# ============================================================

SELF_ROLES = {
    "fraktion": {
        "name": "Fraktions Ping",
        "emoji": "🏛️",
        "role_id": 1526957986696921162,
        "description": "Benachrichtigungen rund um Fraktionen.",
    },

    "rp_start": {
        "name": "RP Start Ping",
        "emoji": "🎮",
        "role_id": 1526958031349350541,
        "description": "Benachrichtigung, wenn das RP startet.",
    },

    "event": {
        "name": "Event Ping",
        "emoji": "🎉",
        "role_id": 1526958087892631632,
        "description": "Benachrichtigungen zu Server-Events.",
    },

    "gewinnspiel": {
        "name": "Gewinnspiel Ping",
        "emoji": "🎁",
        "role_id": 1526958107568377987,
        "description": "Benachrichtigungen zu Gewinnspielen.",
    },

    "partner": {
        "name": "Partner Ping",
        "emoji": "🤝",
        "role_id": 1526958133233193031,
        "description": "Benachrichtigungen zu Partnern.",
    },
}


# ============================================================
# DEV CHECK
# ============================================================

async def ensure_dev(
    interaction: discord.Interaction,
) -> bool:

    if (
        interaction.guild is None
        or not isinstance(
            interaction.user,
            discord.Member,
        )
    ):
        await interaction.response.send_message(
            "❌ Dieser Befehl kann nur auf dem Server benutzt werden.",
            ephemeral=True,
        )
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    try:
        dev_role_id = int(
            DEV_ROLE_ID
        )
    except (TypeError, ValueError):
        dev_role_id = 0

    dev_role = interaction.guild.get_role(
        dev_role_id
    )

    if (
        dev_role is not None
        and dev_role in interaction.user.roles
    ):
        return True

    await interaction.response.send_message(
        "❌ Du darfst dieses Panel nicht verwalten.",
        ephemeral=True,
    )

    return False


# ============================================================
# PANEL DESIGN
# ============================================================

def build_selfrole_embed():

    embed = discord.Embed(
        title="🔔 EHRP | SELF ROLES",
        description=(
            "## BENACHRICHTIGUNGEN\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Hier kannst du selbst auswählen, "
            "welche Benachrichtigungen du erhalten möchtest.\n\n"
            "🏛️ **Fraktions Ping**\n"
            "News und Informationen zu Fraktionen.\n\n"
            "🎮 **RP Start Ping**\n"
            "Du wirst informiert, wenn das RP startet.\n\n"
            "🎉 **Event Ping**\n"
            "Benachrichtigungen über Events.\n\n"
            "🎁 **Gewinnspiel Ping**\n"
            "Verpasse keine Gewinnspiele.\n\n"
            "🤝 **Partner Ping**\n"
            "Informationen rund um unsere Partner.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⬇️ **Wähle unten deine gewünschten Rollen aus.**\n\n"
            "Du kannst mehrere Rollen gleichzeitig auswählen "
            "und deine Auswahl jederzeit ändern."
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_footer(
        text="EHRP | System • Self Roles"
    )

    return embed


# ============================================================
# SELECT MENU
# ============================================================

class SelfRoleSelect(
    discord.ui.Select
):

    def __init__(self):

        options = []

        for key, config in SELF_ROLES.items():

            options.append(
                discord.SelectOption(
                    label=config["name"],
                    value=key,
                    emoji=config["emoji"],
                    description=config["description"][:100],
                )
            )

        super().__init__(
            placeholder="Benachrichtigungen auswählen …",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id="ehrp:selfroles:select",
        )


    async def callback(
        self,
        interaction: discord.Interaction,
    ):

        if (
            interaction.guild is None
            or not isinstance(
                interaction.user,
                discord.Member,
            )
        ):
            await interaction.response.send_message(
                "❌ Diese Auswahl funktioniert nur auf dem Server.",
                ephemeral=True,
            )
            return

        member = interaction.user

        selected_keys = set(
            self.values
        )

        added_roles = []
        removed_roles = []

        # --------------------------------------------
        # Rollen prüfen
        # --------------------------------------------

        for key, config in SELF_ROLES.items():

            role = interaction.guild.get_role(
                config["role_id"]
            )

            if role is None:
                continue

            has_role = role in member.roles
            should_have_role = key in selected_keys

            # Rolle hinzufügen
            if (
                should_have_role
                and not has_role
            ):

                try:

                    await member.add_roles(
                        role,
                        reason=(
                            "EHRP | System "
                            "Self Role ausgewählt"
                        ),
                    )

                    added_roles.append(
                        role
                    )

                except discord.Forbidden:

                    await interaction.response.send_message(
                        (
                            "❌ Der Bot darf eine der Rollen "
                            "nicht vergeben.\n"
                            "Die Bot-Rolle muss über den "
                            "Self-Roles stehen."
                        ),
                        ephemeral=True,
                    )

                    return

                except discord.HTTPException as error:

                    print(
                        f"❌ Self Role Add Fehler: {error}"
                    )

            # Rolle entfernen
            elif (
                not should_have_role
                and has_role
            ):

                try:

                    await member.remove_roles(
                        role,
                        reason=(
                            "EHRP | System "
                            "Self Role abgewählt"
                        ),
                    )

                    removed_roles.append(
                        role
                    )

                except discord.Forbidden:

                    await interaction.response.send_message(
                        (
                            "❌ Der Bot darf eine der Rollen "
                            "nicht entfernen."
                        ),
                        ephemeral=True,
                    )

                    return

                except discord.HTTPException as error:

                    print(
                        f"❌ Self Role Remove Fehler: {error}"
                    )


        # --------------------------------------------
        # Antwort
        # --------------------------------------------

        current_roles = []

        for config in SELF_ROLES.values():

            role = interaction.guild.get_role(
                config["role_id"]
            )

            if (
                role is not None
                and role in member.roles
            ):

                current_roles.append(
                    role.mention
                )


        if current_roles:

            roles_text = "\n".join(
                f"• {role}"
                for role in current_roles
            )

        else:

            roles_text = (
                "Keine Benachrichtigungsrollen ausgewählt."
            )


        embed = discord.Embed(
            title="✅ EHRP | SELF ROLES AKTUALISIERT",
            description=(
                "Deine Benachrichtigungen wurden gespeichert.\n\n"
                "### Aktive Rollen\n"
                f"{roles_text}"
            ),
            color=SUCCESS_COLOR,
        )

        embed.set_footer(
            text="EHRP | System • Self Roles"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


# ============================================================
# PERSISTENT VIEW
# ============================================================

class SelfRoleView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            SelfRoleSelect()
        )


# ============================================================
# COG
# ============================================================

class SelfRoles(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot

        # Funktioniert auch nach Bot-Neustart
        bot.add_view(
            SelfRoleView()
        )


    # ========================================================
    # /selfroles_panel
    # ========================================================

    @app_commands.command(
        name="selfroles_panel",
        description=(
            "Erstellt das EHRP Self-Roles Panel."
        ),
    )
    async def selfroles_panel(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                "❌ Bitte benutze den Befehl in einem Textkanal.",
                ephemeral=True,
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        existing_message = None

        try:

            async for message in interaction.channel.history(
                limit=50
            ):

                if (
                    self.bot.user is not None
                    and message.author.id
                    == self.bot.user.id
                    and message.embeds
                    and message.embeds[0].title
                    == "🔔 EHRP | SELF ROLES"
                ):

                    existing_message = message
                    break

        except discord.HTTPException:
            pass


        if existing_message:

            await existing_message.edit(
                embed=build_selfrole_embed(),
                view=SelfRoleView(),
            )

            await interaction.followup.send(
                "✅ Self-Roles Panel wurde aktualisiert.",
                ephemeral=True,
            )

            return


        message = await interaction.channel.send(
            embed=build_selfrole_embed(),
            view=SelfRoleView(),
        )


        await interaction.followup.send(
            (
                "✅ **Self-Roles Panel erstellt**\n"
                f"📍 {message.channel.mention}"
            ),
            ephemeral=True,
        )


    # ========================================================
    # /selfroles_status
    # ========================================================

    @app_commands.command(
        name="selfroles_status",
        description=(
            "Zeigt den Status des Self-Roles Systems."
        ),
    )
    async def selfroles_status(
        self,
        interaction: discord.Interaction,
    ):

        if not await ensure_dev(
            interaction
        ):
            return

        lines = []

        found = 0

        for config in SELF_ROLES.values():

            role = interaction.guild.get_role(
                config["role_id"]
            )

            if role is None:

                lines.append(
                    f"❌ {config['name']}"
                )

            else:

                found += 1

                lines.append(
                    f"✅ {role.mention}"
                )


        embed = discord.Embed(
            title="⚙️ EHRP | SELF ROLES STATUS",
            description=(
                "## SYSTEM STATUS\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 **System:** Online\n"
                f"🎭 **Rollen erkannt:** "
                f"{found}/{len(SELF_ROLES)}\n"
                "🔄 **Persistent:** Aktiv\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                + "\n".join(
                    lines
                )
            ),
            color=(
                SUCCESS_COLOR
                if found == len(SELF_ROLES)
                else ERROR_COLOR
            ),
        )

        embed.set_footer(
            text="EHRP | System • Self Roles"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


# ============================================================
# SETUP
# ============================================================

async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        SelfRoles(bot)
    )
