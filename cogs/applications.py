from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# EHRP/VC | TEAMBEWERBUNGSSYSTEM
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
INFO_COLOR = 0x3498DB


# ============================================================
# CHANNELS
# ============================================================

# Öffentliches Bewerbungsportal
APPLICATION_PANEL_CHANNEL_ID = 1526942733753909268

# Fertige schriftliche Bewerbungen
APPLICATION_REVIEW_CHANNEL_ID = 1526942850778923181

# Terminplanung
INTERVIEW_PLANNING_CHANNEL_ID = 1543341032861868113

# Sprach-Warteraum
WAITING_ROOM_CHANNEL_ID = 1543341099282862111

# Bewerbungsgespräch Voice 1
INTERVIEW_CHANNEL_1_ID = 1543341153473142945

# Bewerbungsgespräch Voice 2
INTERVIEW_CHANNEL_2_ID = 1543349548062347406

# Recruitment Logs
APPLICATION_LOG_CHANNEL_ID = 1543341210410819755


# ============================================================
# RECRUITMENT ROLLEN
# ============================================================

# [BWL] Bewerbungsleitung
BWL_ROLE_ID = 1543346925418324198

# [Stv. BWL] Stellv. Bewerbungsleitung
STV_BWL_ROLE_ID = 1543347214221447219

# [BT] Bewerbungsteam
BT_ROLE_ID = 1543347311143297024


# ============================================================
# BEWERBUNGSSTATUS-ROLLEN
# ============================================================

# Nach angenommener schriftlicher Bewerbung
INTERVIEW_PENDING_ROLE_ID = 1526957615765127412

# Nach bestandenem Bewerbungsgespräch
TRAINING_PENDING_ROLE_ID = 1526957502078652496


# ============================================================
# RECRUITMENT PINGS
# ============================================================

RECRUITMENT_ROLE_IDS = [
    BWL_ROLE_ID,
    STV_BWL_ROLE_ID,
    BT_ROLE_ID,
]


def recruitment_ping_text() -> str:
    return " ".join(
        f"<@&{role_id}>"
        for role_id in RECRUITMENT_ROLE_IDS
    )


# ============================================================
# DATA
# ============================================================

DATA_FILE = "applications_data.json"


DEFAULT_DATA = {
    "applications_open": True,
    "counter": 0,
    "applications": {},
    "sessions": {},
}


# ============================================================
# BEWERBUNGSFRAGEN
# ============================================================

QUESTIONS = [
    {
        "title": "Wie alt sind Sie?",
        "category": "👤 Persönliche Angaben",
        "min_length": 1,
        "max_length": 3,
        "type": "age",
    },
    {
        "title": "Wie lautet Ihr Roblox-Name?",
        "category": "👤 Persönliche Angaben",
        "min_length": 2,
        "max_length": 100,
    },
    {
        "title": "Seit wann spielen Sie Notruf Hamburg?",
        "category": "🎮 Roleplay-Erfahrung",
        "min_length": 3,
        "max_length": 500,
    },
    {
        "title": (
            "Wie viele Stunden pro Woche können Sie ungefähr "
            "auf EHRP/VC aktiv sein?"
        ),
        "category": "⏰ Aktivität",
        "min_length": 2,
        "max_length": 500,
    },
    {
        "title": (
            "Hatten Sie bereits Erfahrung als Teammitglied "
            "auf einem anderen RP-Server?"
        ),
        "category": "🧩 Teamerfahrung",
        "min_length": 3,
        "max_length": 1500,
    },
    {
        "title": (
            "Warum möchten Sie Teil des EHRP/VC-Teams werden?"
        ),
        "category": "💬 Motivation",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Warum sollten wir gerade Sie auswählen?"
        ),
        "category": "💬 Motivation",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Welche Stärken bringen Sie für die Arbeit im Team mit?"
        ),
        "category": "🧠 Persönlichkeit",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Welche Schwächen haben Sie und wie gehen Sie damit um?"
        ),
        "category": "🧠 Persönlichkeit",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Ein Spieler beleidigt Sie nach einer Sanktion. "
            "Wie reagieren Sie?"
        ),
        "category": "⚖️ Situationsfrage",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Sie sehen, dass ein anderes Teammitglied seine Rechte "
            "ausnutzt oder einen Spieler unfair behandelt. "
            "Wie handeln Sie?"
        ),
        "category": "⚖️ Situationsfrage",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Ein guter Freund von Ihnen verstößt eindeutig gegen "
            "das Regelwerk. Wie gehen Sie damit um?"
        ),
        "category": "⚖️ Situationsfrage",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Zwei Spieler beschuldigen sich gegenseitig und Sie können "
            "zunächst nicht feststellen, wer die Wahrheit sagt. "
            "Wie gehen Sie vor?"
        ),
        "category": "⚖️ Situationsfrage",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Gibt es noch etwas, das wir über Sie wissen sollten?"
        ),
        "category": "📝 Abschluss",
        "min_length": 3,
        "max_length": 2000,
    },
]


# ============================================================
# DATEN LADEN
# ============================================================

def load_data() -> dict:

    if not os.path.exists(DATA_FILE):
        return {
            "applications_open": True,
            "counter": 0,
            "applications": {},
            "sessions": {},
        }

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            raw = json.load(file)

        data = {
            "applications_open": True,
            "counter": 0,
            "applications": {},
            "sessions": {},
        }

        data.update(raw)

        data.setdefault(
            "applications",
            {},
        )

        data.setdefault(
            "sessions",
            {},
        )

        return data

    except Exception as error:

        print(
            "❌ Bewerbungsdaten konnten nicht geladen werden: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "applications_open": True,
            "counter": 0,
            "applications": {},
            "sessions": {},
        }


DATA = load_data()


# ============================================================
# DATEN SPEICHERN
# ============================================================

def save_data():

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                DATA,
                file,
                indent=4,
                ensure_ascii=False,
            )

    except Exception as error:

        print(
            "❌ Bewerbungsdaten konnten nicht gespeichert werden: "
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# SESSION HELPERS
# ============================================================

def get_session(
    user_id: int,
) -> Optional[dict]:

    return DATA[
        "sessions"
    ].get(
        str(user_id)
    )


def set_session(
    user_id: int,
    session: dict,
):

    DATA[
        "sessions"
    ][
        str(user_id)
    ] = session

    save_data()


def remove_session(
    user_id: int,
):

    DATA[
        "sessions"
    ].pop(
        str(user_id),
        None,
    )

    save_data()


# ============================================================
# APPLICATION HELPERS
# ============================================================

def get_application(
    application_id: str,
) -> Optional[dict]:

    return DATA[
        "applications"
    ].get(
        application_id
    )


def application_number() -> str:

    DATA[
        "counter"
    ] = int(
        DATA.get(
            "counter",
            0,
        )
    ) + 1

    save_data()

    return (
        f"EHRP-{DATA['counter']:04d}"
    )


def has_open_application(
    user_id: int,
) -> bool:

    active_statuses = {
        "pending",
        "claimed",
        "interview_planning",
        "interview_pending",
    }

    for application in DATA[
        "applications"
    ].values():

        if application.get(
            "user_id"
        ) != user_id:

            continue

        if application.get(
            "status"
        ) in active_statuses:

            return True

    return False


def find_application_by_review_message(
    message_id: int,
):

    for (
        application_id,
        application,
    ) in DATA[
        "applications"
    ].items():

        if application.get(
            "review_message_id"
        ) == message_id:

            return (
                application_id,
                application,
            )

    return (
        None,
        None,
    )


def find_application_by_planning_message(
    message_id: int,
):

    for (
        application_id,
        application,
    ) in DATA[
        "applications"
    ].items():

        if application.get(
            "planning_message_id"
        ) == message_id:

            return (
                application_id,
                application,
            )

    return (
        None,
        None,
    )


# ============================================================
# RECRUITMENT BERECHTIGUNG
# ============================================================

def get_recruitment_level(
    member: discord.Member,
) -> int:

    role_ids = {
        role.id
        for role in member.roles
    }

    if BWL_ROLE_ID in role_ids:
        return 3

    if STV_BWL_ROLE_ID in role_ids:
        return 2

    if BT_ROLE_ID in role_ids:
        return 1

    return 0


def is_recruitment_staff(
    member: discord.Member,
) -> bool:

    return (
        get_recruitment_level(
            member
        ) > 0
        or member.guild_permissions.administrator
    )


def is_recruitment_leadership(
    member: discord.Member,
) -> bool:

    return (
        get_recruitment_level(
            member
        ) >= 2
        or member.guild_permissions.administrator
    )


# ============================================================
# ROLE HELPERS
# ============================================================

async def add_role_safe(
    member: discord.Member,
    role_id: int,
    reason: str,
) -> bool:

    role = member.guild.get_role(
        role_id
    )

    if role is None:

        print(
            f"❌ Rolle nicht gefunden: {role_id}"
        )

        return False

    if role in member.roles:
        return True

    try:

        await member.add_roles(
            role,
            reason=reason,
        )

        return True

    except discord.HTTPException as error:

        print(
            f"❌ Rolle {role_id} konnte nicht vergeben werden: "
            f"{error}"
        )

        return False


async def remove_role_safe(
    member: discord.Member,
    role_id: int,
    reason: str,
) -> bool:

    role = member.guild.get_role(
        role_id
    )

    if role is None:

        print(
            f"❌ Rolle nicht gefunden: {role_id}"
        )

        return False

    if role not in member.roles:
        return True

    try:

        await member.remove_roles(
            role,
            reason=reason,
        )

        return True

    except discord.HTTPException as error:

        print(
            f"❌ Rolle {role_id} konnte nicht entfernt werden: "
            f"{error}"
        )

        return False


# ============================================================
# LOG SYSTEM
# ============================================================

async def send_application_log(
    guild: discord.Guild,
    title: str,
    description: str,
    color: int = INFO_COLOR,
):

    channel = guild.get_channel(
        APPLICATION_LOG_CHANNEL_ID
    )

    if not isinstance(
        channel,
        discord.TextChannel,
    ):

        print(
            "⚠️ Bewerbungs-Log-Channel nicht gefunden."
        )

        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    embed.set_footer(
        text="EHRP/VC | Bewerbungssystem"
    )

    try:

        await channel.send(
            embed=embed
        )

    except discord.HTTPException as error:

        print(
            f"⚠️ Bewerbungs-Log konnte nicht gesendet werden: {error}"
        )


# ============================================================
# BEWERBUNGSPANEL
# ============================================================

def build_application_panel() -> discord.Embed:

    if DATA.get(
        "applications_open",
        True,
    ):

        status = (
            "🟢 **Bewerbungen geöffnet**"
        )

        color = SUCCESS_COLOR

    else:

        status = (
            "🔴 **Bewerbungen geschlossen**"
        )

        color = ERROR_COLOR

    embed = discord.Embed(
        title=(
            "🚀 EHRP/VC • Dein Weg ins Team"
        ),
        description=(
            "# 📨 Teambewerbung\n\n"

            "Du möchtest bei **EHRP/VC** mehr Verantwortung übernehmen, "
            "Spieler unterstützen und aktiv an unserem Server mitwirken?\n\n"

            "Dann kannst du hier deine Bewerbung für unser Team starten.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📡 Bewerbungsstatus\n\n"

            f"{status}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## ✅ Voraussetzungen\n\n"

            "• Mindestalter **13 Jahre**\n"
            "• Funktionierendes Mikrofon\n"
            "• Aktiver Discord-Account\n"
            "• Sehr gute Rechtschreibung & Grammatik\n"
            "• Kommunikation in der **Sie-Form**\n"
            "• Ca. **15 Stunden pro Woche** verfügbar\n"
            "• Grundlegende RP-Kenntnisse\n"
            "• Sicherer Umgang mit Discord\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 💬 Wie läuft die Bewerbung ab?\n\n"

            "**1.** Bewerbung starten\n"
            "**2.** Voraussetzungen bestätigen\n"
            "**3.** Fragen privat per DM beantworten\n"
            "**4.** Bewerbung überprüfen & absenden\n"
            "**5.** Prüfung durch unser Bewerbungsteam\n"
            "**6.** Bei Annahme folgt das Bewerbungsgespräch\n\n"

            "Die Fragen werden dir automatisch nacheinander per DM gesendet. "
            "Du antwortest einfach ganz normal mit einer Nachricht.\n\n"

            "Du musst während der Fragen **keine Weiter-Buttons drücken**."
        ),
        color=color,
    )

    embed.add_field(
        name="🛑 Bewerbung abbrechen",
        value=(
            "Während einer laufenden DM-Bewerbung kannst du jederzeit "
            "**`abbrechen`** schreiben.\n\n"
            "Bevor etwas gelöscht wird, musst du den Abbruch noch einmal bestätigen."
        ),
        inline=False,
    )

    embed.add_field(
        name="⚠️ Wichtig",
        value=(
            "Nimm dir ausreichend Zeit für deine Antworten. "
            "Unvollständige oder nicht ernst gemeinte Bewerbungen "
            "können abgelehnt werden.\n\n"
            "Außerdem müssen deine Direktnachrichten aktiviert sein."
        ),
        inline=False,
    )

    embed.add_field(
        name="📨 Bereit?",
        value=(
            "Klicke unten auf **Bewerbung starten**."
        ),
        inline=False,
    )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    return embed


# ============================================================
# VORAUSSETZUNGEN
# ============================================================

def build_requirements_embed() -> discord.Embed:

    embed = discord.Embed(
        title="📋 Voraussetzungen",
        description=(
            "# Bevor deine Bewerbung beginnt\n\n"

            "Bitte bestätige, dass du die folgenden Voraussetzungen "
            "gelesen hast und grundsätzlich erfüllst.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "✅ Mindestens **13 Jahre alt**\n"
            "✅ Funktionierendes Mikrofon\n"
            "✅ Aktiver Discord-Account\n"
            "✅ Sehr gute Rechtschreibung & Grammatik\n"
            "✅ Kommunikation in der **Sie-Form**\n"
            "✅ Ca. **15 Stunden pro Woche** verfügbar\n"
            "✅ Grundkenntnisse im Roleplay\n"
            "✅ Sicherer Umgang mit Discord\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Nach deiner Bestätigung schreibt dir "
            "**EHRP | SYSTEM automatisch per DM**."
        ),
        color=WARNING_COLOR,
    )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    return embed


# ============================================================
# DM START
# ============================================================

def build_dm_start_embed() -> discord.Embed:

    embed = discord.Embed(
        title="✅ Bewerbung gestartet",
        description=(
            "# Willkommen zur EHRP/VC Teambewerbung\n\n"

            "Ab jetzt läuft deine Bewerbung vollständig "
            "über diesen privaten Chat.\n\n"

            "Du antwortest auf jede Frage einfach mit einer "
            "**normalen Discord-Nachricht**.\n\n"

            "Sobald deine Antwort gültig gespeichert wurde, "
            "kommt automatisch die nächste Frage.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 🛑 Bewerbung abbrechen\n\n"

            "Falls du deine Bewerbung beenden möchtest, "
            "schreibe jederzeit:\n\n"

            "**`abbrechen`**\n\n"

            "Deine Bewerbung wird erst nach einer zusätzlichen "
            "Bestätigung wirklich gelöscht."
        ),
        color=SUCCESS_COLOR,
    )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    return embed


# ============================================================
# DM FRAGE
# ============================================================

def build_dm_question_embed(
    question_index: int,
) -> discord.Embed:

    question = QUESTIONS[
        question_index
    ]

    current = (
        question_index
        + 1
    )

    total = len(
        QUESTIONS
    )

    progress = int(
        (
            question_index
            / total
        )
        * 100
    )

    filled = round(
        progress
        / 10
    )

    progress_bar = (
        "🟩" * filled
        + "⬜" * (
            10 - filled
        )
    )

    embed = discord.Embed(
        title="📨 EHRP/VC • Teambewerbung",
        description=(
            f"# Frage {current} von {total}\n\n"

            f"## {question['category']}\n\n"

            f"### {question['title']}\n\n"

            "Schreibe deine Antwort jetzt einfach "
            "**als normale Nachricht in diesen Chat**."
        ),
        color=SYSTEM_COLOR,
    )

    embed.add_field(
        name="📊 Fortschritt",
        value=(
            f"{progress_bar}\n"
            f"**{progress}% abgeschlossen**"
        ),
        inline=False,
    )

    if question[
        "min_length"
    ] >= 30:

        embed.add_field(
            name="💡 Hinweis",
            value=(
                "Bitte beantworte diese Frage ausführlich. "
                "Sehr kurze Antworten werden nicht angenommen."
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"EHRP/VC • Frage {current}/{total} "
            "• Zum Abbrechen: „abbrechen“"
        )
    )

    return embed

# ============================================================
# VALIDIERUNG DER DM-ANTWORTEN
# ============================================================

def validate_dm_answer(
    question: dict,
    answer: str,
):

    answer = answer.strip()

    if not answer:

        return (
            False,
            "❌ Deine Antwort darf nicht leer sein."
        )

    if len(
        answer
    ) < question[
        "min_length"
    ]:

        return (
            False,
            (
                "❌ Deine Antwort ist zu kurz.\n\n"
                f"Bitte verwende mindestens "
                f"**{question['min_length']} Zeichen**."
            ),
        )

    if len(
        answer
    ) > question[
        "max_length"
    ]:

        return (
            False,
            (
                "❌ Deine Antwort ist zu lang.\n\n"
                f"Maximal erlaubt sind "
                f"**{question['max_length']} Zeichen**."
            ),
        )

    if question.get(
        "type"
    ) == "age":

        try:

            age = int(
                answer
            )

        except ValueError:

            return (
                False,
                (
                    "❌ Bitte gib dein Alter "
                    "ausschließlich als Zahl an."
                ),
            )

        if age < 13:

            return (
                False,
                "UNDER_13",
            )

        if age > 99:

            return (
                False,
                "❌ Bitte gib ein gültiges Alter an.",
            )

    return (
        True,
        None,
    )


# ============================================================
# BEWERBUNG STARTEN
# ============================================================

class ApplicationPanelView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Bewerbung starten",
        emoji="📨",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:application:start",
    )
    async def start_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.guild:

            await interaction.response.send_message(
                (
                    "❌ Diese Funktion kann nur "
                    "auf dem Server verwendet werden."
                ),
                ephemeral=True,
            )

            return

        if not DATA.get(
            "applications_open",
            True,
        ):

            await interaction.response.send_message(
                (
                    "# 🔴 Bewerbungen geschlossen\n\n"
                    "Aktuell werden keine neuen "
                    "Teambewerbungen angenommen."
                ),
                ephemeral=True,
            )

            return

        if has_open_application(
            interaction.user.id
        ):

            await interaction.response.send_message(
                (
                    "# ⚠️ Bewerbung bereits vorhanden\n\n"
                    "Du besitzt bereits eine offene "
                    "oder laufende Bewerbung."
                ),
                ephemeral=True,
            )

            return

        if get_session(
            interaction.user.id
        ):

            await interaction.response.send_message(
                (
                    "# ⚠️ Bewerbung bereits gestartet\n\n"
                    "Du hast bereits eine laufende "
                    "DM-Bewerbung."
                ),
                ephemeral=True,
            )

            return

        session = {
            "user_id":
                interaction.user.id,

            "guild_id":
                interaction.guild.id,

            "current_question":
                0,

            "answers":
                {},

            "requirements_confirmed":
                False,

            "awaiting_final_submit":
                False,
        }

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.send_message(
            embed=build_requirements_embed(),
            view=RequirementsView(),
            ephemeral=True,
        )


# ============================================================
# VORAUSSETZUNGEN BESTÄTIGEN
# ============================================================

class RequirementsView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    @discord.ui.button(
        label="Voraussetzungen gelesen",
        emoji="✅",
        style=discord.ButtonStyle.success,
    )
    async def confirm_requirements(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.send_message(
                (
                    "❌ Deine Bewerbungssitzung "
                    "wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        try:

            await interaction.user.send(
                embed=build_dm_start_embed()
            )

            await interaction.user.send(
                embed=build_dm_question_embed(
                    0
                )
            )

        except discord.Forbidden:

            remove_session(
                interaction.user.id
            )

            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Direktnachrichten deaktiviert",
                    description=(
                        "# Bewerbung konnte nicht gestartet werden\n\n"

                        "Der Bot konnte dir keine DM senden.\n\n"

                        "Bitte aktiviere Direktnachrichten "
                        "für diesen Server und versuche es erneut."
                    ),
                    color=ERROR_COLOR,
                ),
                view=None,
            )

            return

        except discord.HTTPException as error:

            remove_session(
                interaction.user.id
            )

            print(
                f"❌ DM konnte nicht gesendet werden: {error}"
            )

            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="❌ Fehler beim Start",
                    description=(
                        "Die Bewerbung konnte technisch "
                        "nicht gestartet werden."
                    ),
                    color=ERROR_COLOR,
                ),
                view=None,
            )

            return

        session[
            "requirements_confirmed"
        ] = True

        session[
            "current_question"
        ] = 0

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Bewerbung gestartet",
                description=(
                    "# Bitte prüfe deine Direktnachrichten\n\n"

                    "Die Bewerbung wurde erfolgreich gestartet.\n\n"

                    "Du bekommst jetzt alle Fragen "
                    "automatisch per DM."
                ),
                color=SUCCESS_COLOR,
            ),
            view=None,
        )

        await send_application_log(
            interaction.guild,
            "📨 Bewerbung gestartet",
            (
                f"**Bewerber:** {interaction.user.mention}\n"
                f"**Discord-ID:** `{interaction.user.id}`"
            ),
            INFO_COLOR,
        )


# ============================================================
# BEWERBUNG ABBRECHEN
# ============================================================

class CancelApplicationView(
    discord.ui.View
):

    def __init__(
        self,
        user_id: int,
    ):

        super().__init__(
            timeout=120
        )

        self.user_id = user_id


    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:

        if interaction.user.id != self.user_id:

            await interaction.response.send_message(
                (
                    "❌ Diese Bestätigung gehört "
                    "nicht zu deiner Bewerbung."
                ),
                ephemeral=True,
            )

            return False

        return True


    @discord.ui.button(
        label="Ja, Bewerbung abbrechen",
        emoji="✅",
        style=discord.ButtonStyle.danger,
    )
    async def confirm_cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.edit_message(
                content=(
                    "⚠️ Es wurde keine laufende "
                    "Bewerbung gefunden."
                ),
                embed=None,
                view=None,
            )

            return

        guild_id = session.get(
            "guild_id"
        )

        guild = interaction.client.get_guild(
            guild_id
        )

        remove_session(
            interaction.user.id
        )

        embed = discord.Embed(
            title="🛑 Bewerbung abgebrochen",
            description=(
                "# Bewerbungsprozess beendet\n\n"

                "Deine laufende Bewerbung wurde "
                "vollständig abgebrochen.\n\n"

                "Deine bisherigen Antworten wurden verworfen "
                "und nicht an das Bewerbungsteam übermittelt.\n\n"

                "Du kannst später jederzeit "
                "eine neue Bewerbung starten."
            ),
            color=ERROR_COLOR,
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=None,
        )

        if guild:

            await send_application_log(
                guild,
                "🛑 Bewerbung abgebrochen",
                (
                    f"**Bewerber:** "
                    f"<@{interaction.user.id}>\n"
                    f"**Discord-ID:** `{interaction.user.id}`"
                ),
                WARNING_COLOR,
            )


    @discord.ui.button(
        label="Nein, fortsetzen",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
    )
    async def keep_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.edit_message(
                content=(
                    "⚠️ Es wurde keine laufende "
                    "Bewerbung gefunden."
                ),
                embed=None,
                view=None,
            )

            return

        current_question = int(
            session.get(
                "current_question",
                0,
            )
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Bewerbung wird fortgesetzt",
                description=(
                    "Deine Bewerbung wurde "
                    "**nicht abgebrochen**.\n\n"

                    "Bitte beantworte weiterhin "
                    "die aktuell offene Frage."
                ),
                color=SUCCESS_COLOR,
            ),
            view=None,
        )

        if current_question < len(
            QUESTIONS
        ):

            await interaction.followup.send(
                embed=build_dm_question_embed(
                    current_question
                )
            )


# ============================================================
# FINAL REVIEW EMBED
# ============================================================

def build_final_review_embed(
    user_id: int,
) -> discord.Embed:

    session = get_session(
        user_id
    )

    embed = discord.Embed(
        title="✅ Bewerbung vollständig",
        description=(
            "# 📋 Abschlusskontrolle\n\n"

            "Du hast alle Fragen beantwortet.\n\n"

            "Prüfe deine Antworten noch einmal, "
            "bevor du die Bewerbung absendest.\n\n"

            "Wenn alles stimmt, klicke auf:\n\n"

            "**📨 Bewerbung absenden**"
        ),
        color=SUCCESS_COLOR,
    )

    if not session:

        return embed

    answers = session.get(
        "answers",
        {},
    )

    for index, question in enumerate(
        QUESTIONS
    ):

        answer = answers.get(
            str(index),
            "Keine Antwort",
        )

        if len(
            answer
        ) > 200:

            answer = (
                answer[:197]
                + "..."
            )

        embed.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer,
            inline=False,
        )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    return embed


# ============================================================
# FINAL REVIEW VIEW
# ============================================================

class FinalReviewView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=1800
        )

    @discord.ui.button(
        label="Bewerbung absenden",
        emoji="📨",
        style=discord.ButtonStyle.success,
    )
    async def submit_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.send_message(
                (
                    "❌ Bewerbungssitzung "
                    "nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        answers = session.get(
            "answers",
            {},
        )

        if len(
            answers
        ) != len(
            QUESTIONS
        ):

            await interaction.response.send_message(
                (
                    "❌ Es wurden noch nicht "
                    "alle Fragen beantwortet."
                ),
                ephemeral=True,
            )

            return

        guild_id = session.get(
            "guild_id"
        )

        guild = interaction.client.get_guild(
            guild_id
        )

        if not guild:

            await interaction.response.send_message(
                (
                    "❌ Der EHRP/VC Server "
                    "wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        review_channel = guild.get_channel(
            APPLICATION_REVIEW_CHANNEL_ID
        )

        if not isinstance(
            review_channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                (
                    "❌ Der Bewerbungs-Channel "
                    "wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        application_id = application_number()

        application = {
            "application_id":
                application_id,

            "user_id":
                interaction.user.id,

            "answers":
                answers.copy(),

            "status":
                "pending",

            "claimed_by":
                0,

            "created_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "review_message_id":
                0,

            "planning_message_id":
                0,

            "proposal_date":
                "",

            "proposal_time":
                "",

            "proposal_note":
                "",

            "proposal_by":
                0,

            "applicant_confirmed":
                False,

            "team_confirmed":
                False,

            "interviewer_id":
                0,

            "interview_result":
                "",

            "result_reason":
                "",

            "result_by":
                0,
        }

        DATA[
            "applications"
        ][
            application_id
        ] = application

        save_data()

        review_embeds = build_review_embeds(
            guild,
            application,
        )

        review_message = await review_channel.send(
            content=(
                f"{recruitment_ping_text()}\n\n"
                f"📨 **Neue Teambewerbung:** "
                f"<@{interaction.user.id}>"
            ),
            embeds=review_embeds,
            view=ApplicationReviewView(),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=True,
                everyone=False,
            ),
        )

        application[
            "review_message_id"
        ] = review_message.id

        DATA[
            "applications"
        ][
            application_id
        ] = application

        save_data()

        remove_session(
            interaction.user.id
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="✅ Bewerbung eingegangen",
                description=(
                    "# Vielen Dank für deine Bewerbung\n\n"

                    "Deine Bewerbung wurde erfolgreich "
                    "an unser Bewerbungsteam weitergeleitet.\n\n"

                    f"**Bewerbungs-ID:** `{application_id}`\n\n"

                    "Sobald eine Entscheidung getroffen wurde, "
                    "wirst du automatisch informiert."
                ),
                color=SUCCESS_COLOR,
            ),
            view=None,
        )

        await send_application_log(
            guild,
            "📨 Bewerbung abgesendet",
            (
                f"**Bewerber:** <@{interaction.user.id}>\n"
                f"**Bewerbungs-ID:** `{application_id}`\n"
                f"**Review:** {review_message.jump_url}"
            ),
            SUCCESS_COLOR,
        )


# ============================================================
# NORMALE DM-NACHRICHTEN VERARBEITEN
# ============================================================

async def process_application_dm(
    bot: commands.Bot,
    message: discord.Message,
) -> bool:

    if message.author.bot:
        return False

    if message.guild is not None:
        return False

    session = get_session(
        message.author.id
    )

    if not session:
        return False

    if not session.get(
        "requirements_confirmed",
        False,
    ):
        return False

    if session.get(
        "awaiting_final_submit",
        False,
    ):
        return True

    current_question = int(
        session.get(
            "current_question",
            0,
        )
    )

    if current_question >= len(
        QUESTIONS
    ):
        return True

    answer = message.content.strip()

    # ========================================================
    # ABBRECHEN
    # ========================================================

    if answer.lower() in {
        "abbrechen",
        "bewerbung abbrechen",
        "cancel",
    }:

        embed = discord.Embed(
            title="⚠️ Bewerbung wirklich abbrechen?",
            description=(
                "# Sicherheitsabfrage\n\n"

                "Möchtest du deine laufende Bewerbung "
                "wirklich abbrechen?\n\n"

                "Wenn du bestätigst, werden deine bisherigen "
                "Antworten gelöscht und nicht übermittelt."
            ),
            color=WARNING_COLOR,
        )

        await message.channel.send(
            embed=embed,
            view=CancelApplicationView(
                message.author.id
            ),
        )

        return True

    question = QUESTIONS[
        current_question
    ]

    valid, error = validate_dm_answer(
        question,
        answer,
    )

    if not valid:

        if error == "UNDER_13":

            remove_session(
                message.author.id
            )

            await message.channel.send(
                embed=discord.Embed(
                    title="❌ Bewerbung beendet",
                    description=(
                        "# Mindestalter nicht erfüllt\n\n"

                        "Das Mindestalter für eine Bewerbung "
                        "bei **EHRP/VC** beträgt **13 Jahre**."
                    ),
                    color=ERROR_COLOR,
                )
            )

            return True

        await message.channel.send(
            error
        )

        await message.channel.send(
            embed=build_dm_question_embed(
                current_question
            )
        )

        return True

    session[
        "answers"
    ][
        str(
            current_question
        )
    ] = answer

    next_question = (
        current_question
        + 1
    )

    session[
        "current_question"
    ] = next_question

    set_session(
        message.author.id,
        session,
    )

    await message.channel.send(
        "✅ **Antwort gespeichert.**"
    )

    if next_question < len(
        QUESTIONS
    ):

        await message.channel.send(
            embed=build_dm_question_embed(
                next_question
            )
        )

        return True

    session[
        "awaiting_final_submit"
    ] = True

    set_session(
        message.author.id,
        session,
    )

    await message.channel.send(
        embed=build_final_review_embed(
            message.author.id
        ),
        view=FinalReviewView(),
    )

    return True

# ============================================================
# REVIEW EMBEDS
# ============================================================

def build_review_embeds(
    guild: discord.Guild,
    application: dict,
) -> list[discord.Embed]:

    member = guild.get_member(
        application["user_id"]
    )

    applicant_text = (
        member.mention
        if member
        else f"<@{application['user_id']}>"
    )

    status_map = {
        "pending": "🟡 AUSSTEHEND",
        "claimed": "🟠 IN BEARBEITUNG",
        "interview_planning": "🔵 GESPRÄCHSPLANUNG",
        "interview_pending": "🟣 GESPRÄCH AUSSTEHEND",
        "completed": "✅ ERFOLGREICH",
        "rejected": "🔴 ABGELEHNT",
        "failed": "❌ NICHT BESTANDEN",
    }

    claimed_by = application.get(
        "claimed_by",
        0,
    )

    claimed_text = (
        f"<@{claimed_by}>"
        if claimed_by
        else "Noch nicht übernommen"
    )

    first = discord.Embed(
        title=(
            "📨 TEAMBEWERBUNG • "
            f"{application['application_id']}"
        ),
        description=(
            "# Neue Teambewerbung\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"**Person:** {applicant_text}\n"
            f"**Discord-ID:** `{application['user_id']}`\n\n"

            "## 📡 Bearbeitung\n\n"

            f"**Status:** "
            f"{status_map.get(application['status'], application['status'])}\n"

            f"**Bearbeiter:** {claimed_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📋 Antworten • Teil 1"
        ),
        color=WARNING_COLOR,
    )

    if member:
        first.set_thumbnail(
            url=member.display_avatar.url
        )

    for index in range(0, 5):

        question = QUESTIONS[index]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        first.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    first.set_footer(
        text="EHRP/VC • Bewerbungssystem • Teil 1/3"
    )

    second = discord.Embed(
        title="📋 Antworten • Teil 2",
        color=INFO_COLOR,
    )

    for index in range(5, 10):

        question = QUESTIONS[index]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        second.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    second.set_footer(
        text="EHRP/VC • Bewerbungssystem • Teil 2/3"
    )

    third = discord.Embed(
        title="📋 Antworten • Teil 3",
        color=INFO_COLOR,
    )

    for index in range(
        10,
        len(QUESTIONS),
    ):

        question = QUESTIONS[index]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        third.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    third.set_footer(
        text="EHRP/VC • Bewerbungssystem • Teil 3/3"
    )

    return [
        first,
        second,
        third,
    ]


# ============================================================
# ABLEHNUNG MODAL
# ============================================================

class RejectApplicationModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Bewerbung ablehnen"
        )

        self.reason = discord.ui.TextInput(
            label="Grund der Ablehnung",
            placeholder=(
                "Bitte den Ablehnungsgrund eintragen."
            ),
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=5,
            max_length=1000,
        )

        self.add_item(
            self.reason
        )


    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Bewerbungsnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_review_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) not in {
            "pending",
            "claimed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits bearbeitet.",
                ephemeral=True,
            )

            return

        reason = str(
            self.reason.value
        ).strip()

        application[
            "status"
        ] = "rejected"

        application[
            "rejection_reason"
        ] = reason

        application[
            "rejected_by"
        ] = interaction.user.id

        application[
            "rejected_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        applicant = (
            interaction.guild.get_member(
                application[
                    "user_id"
                ]
            )
        )

        # ====================================================
        # ABLEHNUNGS-VORLAGE
        # ====================================================

        rejection_text = (
            "# ❌ Bewerbung abgelehnt\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Bewerbung und das damit verbundene "
            "Interesse an einer Position im Team von **EHRP/VC**.\n\n"

            "Nach sorgfältiger Prüfung müssen wir Ihnen leider mitteilen, "
            "dass Ihre Bewerbung zum jetzigen Zeitpunkt "
            "**abgelehnt wurde**.\n\n"

            "## 📋 Grund der Ablehnung\n\n"

            f"**- {reason}**\n\n"

            "Diese Entscheidung stellt keine endgültige Ablehnung "
            "für die Zukunft dar. Sie können sich nach einer "
            "angemessenen Zeit erneut bewerben, sofern die genannten "
            "Punkte verbessert wurden.\n\n"

            "Wir bedanken uns für Ihr Verständnis und wünschen Ihnen "
            "weiterhin viel Spaß auf **EHRP/VC**.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        if applicant:

            try:
                await applicant.send(
                    rejection_text
                )

            except discord.HTTPException:
                pass

        updated_embeds = build_review_embeds(
            interaction.guild,
            application,
        )

        updated_embeds[0].color = ERROR_COLOR

        updated_embeds[0].add_field(
            name="❌ Bewerbung abgelehnt",
            value=(
                f"**Entscheidung:** {interaction.user.mention}\n\n"
                f"**Grund:**\n{reason}"
            ),
            inline=False,
        )

        await interaction.response.edit_message(
            embeds=updated_embeds,
            view=None,
        )

        await send_application_log(
            interaction.guild,
            "❌ Bewerbung abgelehnt",
            (
                f"**Bewerber:** <@{application['user_id']}>\n"
                f"**Bewerbungs-ID:** `{app_id}`\n"
                f"**Bearbeiter:** {interaction.user.mention}\n\n"
                f"**Grund:**\n{reason}"
            ),
            ERROR_COLOR,
        )


# ============================================================
# REVIEW VIEW
# ============================================================

class ApplicationReviewView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    # ========================================================
    # ÜBERNEHMEN
    # ========================================================

    @discord.ui.button(
        label="Übernehmen",
        emoji="👤",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:new_application:claim",
    )
    async def claim_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Du gehörst nicht zum Bewerbungsteam.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_review_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) not in {
            "pending",
            "claimed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits bearbeitet.",
                ephemeral=True,
            )

            return

        current_claim = application.get(
            "claimed_by",
            0,
        )

        if current_claim:

            if current_claim == interaction.user.id:

                await interaction.response.send_message(
                    "✅ Du hast diese Bewerbung bereits übernommen.",
                    ephemeral=True,
                )

            else:

                await interaction.response.send_message(
                    (
                        "⚠️ Diese Bewerbung wird bereits von "
                        f"<@{current_claim}> bearbeitet."
                    ),
                    ephemeral=True,
                )

            return

        application[
            "claimed_by"
        ] = interaction.user.id

        application[
            "status"
        ] = "claimed"

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        await interaction.response.edit_message(
            embeds=build_review_embeds(
                interaction.guild,
                application,
            ),
            view=self,
        )

        await send_application_log(
            interaction.guild,
            "👤 Bewerbung übernommen",
            (
                f"**Bewerber:** <@{application['user_id']}>\n"
                f"**Bewerbungs-ID:** `{app_id}`\n"
                f"**Bearbeiter:** {interaction.user.mention}"
            ),
            INFO_COLOR,
        )


    # ========================================================
    # ANNEHMEN
    # ========================================================

    @discord.ui.button(
        label="Annehmen",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:new_application:accept",
    )
    async def accept_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Du gehörst nicht zum Bewerbungsteam.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_review_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) not in {
            "pending",
            "claimed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits bearbeitet.",
                ephemeral=True,
            )

            return

        applicant = (
            interaction.guild.get_member(
                application[
                    "user_id"
                ]
            )
        )

        if not applicant:

            await interaction.response.send_message(
                "❌ Der Bewerber befindet sich nicht mehr auf dem Server.",
                ephemeral=True,
            )

            return

        planning_channel = (
            interaction.guild.get_channel(
                INTERVIEW_PLANNING_CHANNEL_ID
            )
        )

        if not isinstance(
            planning_channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                "❌ Der Channel für die Gesprächsplanung wurde nicht gefunden.",
                ephemeral=True,
            )

            return

        role_success = await add_role_safe(
            applicant,
            INTERVIEW_PENDING_ROLE_ID,
            "EHRP: Schriftliche Bewerbung angenommen",
        )

        if not role_success:

            await interaction.response.send_message(
                (
                    "❌ Die Rolle **Bewerbungsgespräch anstehend** "
                    "konnte nicht vergeben werden.\n\n"
                    "Bitte prüfe die Rollen-Hierarchie des Bots."
                ),
                ephemeral=True,
            )

            return

        application[
            "status"
        ] = "interview_planning"

        application[
            "accepted_by"
        ] = interaction.user.id

        application[
            "accepted_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        # ====================================================
        # ANNAHME-NACHRICHT
        # ====================================================

        acceptance_text = (
            "# ✅ Bewerbung angenommen\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Bewerbung und Ihr Interesse an einer "
            "Position im Team von **EHRP/VC**.\n\n"

            "Wir freuen uns, Ihnen mitteilen zu können, dass Ihre "
            "schriftliche Bewerbung **angenommen wurde**.\n\n"

            "## 📞 Nächster Schritt: Bewerbungsgespräch\n\n"

            "Als nächsten Schritt folgt Ihr Bewerbungsgespräch.\n\n"

            "Gemeinsam mit unserem Bewerbungsteam wird jetzt ein "
            "passender Termin vereinbart.\n\n"

            "Ein Termin gilt erst dann als verbindlich, wenn "
            "**Sie und das Bewerbungsteam diesen bestätigt haben**.\n\n"

            "Bitte achten Sie auf die weiteren Informationen auf unserem Server.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        try:

            await applicant.send(
                acceptance_text
            )

        except discord.HTTPException:
            pass

        planning_message = await planning_channel.send(
            content=(
                f"{applicant.mention}\n"
                f"{recruitment_ping_text()}"
            ),
            embed=build_interview_planning_embed(
                interaction.guild,
                application,
            ),
            view=InterviewPlanningView(),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=True,
                everyone=False,
            ),
        )

        application[
            "planning_message_id"
        ] = planning_message.id

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        updated_embeds = build_review_embeds(
            interaction.guild,
            application,
        )

        updated_embeds[0].color = SUCCESS_COLOR

        updated_embeds[0].add_field(
            name="✅ Schriftliche Bewerbung angenommen",
            value=(
                f"**Angenommen von:** {interaction.user.mention}\n\n"
                f"<@&{INTERVIEW_PENDING_ROLE_ID}> wurde vergeben.\n\n"
                "Der Bewerber befindet sich jetzt in der Gesprächsplanung."
            ),
            inline=False,
        )

        await interaction.response.edit_message(
            embeds=updated_embeds,
            view=None,
        )

        await send_application_log(
            interaction.guild,
            "✅ Schriftliche Bewerbung angenommen",
            (
                f"**Bewerber:** {applicant.mention}\n"
                f"**Bewerbungs-ID:** `{app_id}`\n"
                f"**Angenommen von:** {interaction.user.mention}\n\n"
                f"**Vergebene Rolle:** <@&{INTERVIEW_PENDING_ROLE_ID}>"
            ),
            SUCCESS_COLOR,
        )


    # ========================================================
    # ABLEHNEN
    # ========================================================

    @discord.ui.button(
        label="Ablehnen",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:new_application:reject",
    )
    async def reject_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Du gehörst nicht zum Bewerbungsteam.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_review_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) not in {
            "pending",
            "claimed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits bearbeitet.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            RejectApplicationModal()
        )


# ============================================================
# GESPRÄCHSPLANUNG EMBED
# ============================================================

def build_interview_planning_embed(
    guild: discord.Guild,
    application: dict,
) -> discord.Embed:

    applicant_id = application[
        "user_id"
    ]

    proposal_date = application.get(
        "proposal_date",
        "",
    )

    proposal_time = application.get(
        "proposal_time",
        "",
    )

    proposal_note = application.get(
        "proposal_note",
        "",
    )

    proposal_by = application.get(
        "proposal_by",
        0,
    )

    applicant_confirmed = application.get(
        "applicant_confirmed",
        False,
    )

    team_confirmed = application.get(
        "team_confirmed",
        False,
    )

    interviewer_id = application.get(
        "interviewer_id",
        0,
    )

    if proposal_date and proposal_time:

        proposal_text = (
            "## 📅 Aktueller Terminvorschlag\n\n"

            f"**Datum:** {proposal_date}\n"
            f"**Uhrzeit:** {proposal_time} Uhr\n"
            f"**Vorgeschlagen von:** <@{proposal_by}>\n"
        )

        if proposal_note:

            proposal_text += (
                f"**Hinweis:** {proposal_note}\n"
            )

    else:

        proposal_text = (
            "## 📅 Noch kein Termin\n\n"

            "Aktuell wurde noch kein Bewerbungsgespräch vorgeschlagen.\n\n"
            "Der Bewerber oder ein Mitglied des Bewerbungsteams "
            "kann unten einen Termin vorschlagen."
        )

    applicant_status = (
        "✅ Bestätigt"
        if applicant_confirmed
        else "⏳ Ausstehend"
    )

    team_status = (
        "✅ Bestätigt"
        if team_confirmed
        else "⏳ Ausstehend"
    )

    interviewer_text = (
        f"<@{interviewer_id}>"
        if interviewer_id
        else "Noch nicht festgelegt"
    )

    if (
        applicant_confirmed
        and team_confirmed
    ):

        status_text = (
            "🟢 **Termin von beiden Seiten bestätigt**"
        )

        color = SUCCESS_COLOR

    else:

        status_text = (
            "🟡 **Termin noch nicht vollständig bestätigt**"
        )

        color = INFO_COLOR

    embed = discord.Embed(
        title=(
            "📅 BEWERBUNGSGESPRÄCH • "
            f"{application['application_id']}"
        ),
        description=(
            "# Gesprächsplanung\n\n"

            f"**Bewerber:** <@{applicant_id}>\n"
            f"**Gesprächsführer:** {interviewer_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{proposal_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 🔐 Bestätigung\n\n"

            f"**Bewerber:** {applicant_status}\n"
            f"**Bewerbungsteam:** {team_status}\n\n"

            f"{status_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"**Warteraum:** <#{WAITING_ROOM_CHANNEL_ID}>\n"
            f"**Gespräch 1:** <#{INTERVIEW_CHANNEL_1_ID}>\n"
            f"**Gespräch 2:** <#{INTERVIEW_CHANNEL_2_ID}>"
        ),
        color=color,
    )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    return embed
# ============================================================
# TERMIN VORSCHLAGEN
# ============================================================

class InterviewProposalModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Gesprächstermin vorschlagen"
        )

        self.date_input = discord.ui.TextInput(
            label="Datum",
            placeholder="z. B. 05.09.2026",
            required=True,
            min_length=8,
            max_length=10,
        )

        self.time_input = discord.ui.TextInput(
            label="Uhrzeit",
            placeholder="z. B. 18:30",
            required=True,
            min_length=4,
            max_length=5,
        )

        self.note_input = discord.ui.TextInput(
            label="Hinweis",
            placeholder=(
                "Optional: zusätzliche Informationen"
            ),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        )

        self.add_item(
            self.date_input
        )

        self.add_item(
            self.time_input
        )

        self.add_item(
            self.note_input
        )


    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Gesprächsplanung nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_planning_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        is_applicant = (
            interaction.user.id
            == application[
                "user_id"
            ]
        )

        is_staff = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_recruitment_staff(
                interaction.user
            )
        )

        if not is_applicant and not is_staff:

            await interaction.response.send_message(
                (
                    "❌ Du darfst für dieses "
                    "Bewerbungsgespräch keinen Termin festlegen."
                ),
                ephemeral=True,
            )

            return

        proposal_date = str(
            self.date_input.value
        ).strip()

        proposal_time = str(
            self.time_input.value
        ).strip()

        proposal_note = str(
            self.note_input.value
            or ""
        ).strip()

        try:

            parsed_datetime = datetime.strptime(
                (
                    f"{proposal_date} "
                    f"{proposal_time}"
                ),
                "%d.%m.%Y %H:%M",
            )

        except ValueError:

            await interaction.response.send_message(
                (
                    "❌ Datum oder Uhrzeit sind ungültig.\n\n"

                    "Bitte verwende dieses Format:\n\n"

                    "**Datum:** `05.09.2026`\n"
                    "**Uhrzeit:** `18:30`"
                ),
                ephemeral=True,
            )

            return

        if parsed_datetime < datetime.now():

            await interaction.response.send_message(
                (
                    "❌ Dieser Termin liegt bereits "
                    "in der Vergangenheit."
                ),
                ephemeral=True,
            )

            return

        # Neuer Vorschlag
        application[
            "proposal_date"
        ] = proposal_date

        application[
            "proposal_time"
        ] = proposal_time

        application[
            "proposal_note"
        ] = proposal_note

        application[
            "proposal_by"
        ] = interaction.user.id

        # Bestätigungen bei Änderung zurücksetzen
        application[
            "applicant_confirmed"
        ] = False

        application[
            "team_confirmed"
        ] = False

        application[
            "interviewer_id"
        ] = 0

        # Vorschlagende Seite bestätigt automatisch
        if is_applicant:

            application[
                "applicant_confirmed"
            ] = True

        if is_staff:

            application[
                "team_confirmed"
            ] = True

            application[
                "interviewer_id"
            ] = interaction.user.id

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        await interaction.response.edit_message(
            embed=build_interview_planning_embed(
                interaction.guild,
                application,
            ),
            view=InterviewPlanningView(),
        )

        await send_application_log(
            interaction.guild,
            "📅 Gesprächstermin vorgeschlagen",
            (
                f"**Bewerber:** "
                f"<@{application['user_id']}>\n"

                f"**Bewerbungs-ID:** `{app_id}`\n"

                f"**Vorgeschlagen von:** "
                f"{interaction.user.mention}\n"

                f"**Datum:** {proposal_date}\n"
                f"**Uhrzeit:** {proposal_time} Uhr"
            ),
            INFO_COLOR,
        )

        await try_confirm_interview(
            interaction.guild,
            app_id,
            application,
            interaction.message,
        )


# ============================================================
# GESPRÄCHSPLANUNG VIEW
# ============================================================

class InterviewPlanningView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Termin vorschlagen / ändern",
        emoji="📅",
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:new_application:proposal",
    )
    async def propose_date(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.message:

            return

        app_id, application = (
            find_application_by_planning_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) == "interview_pending":

            await interaction.response.send_message(
                (
                    "⚠️ Der Termin wurde bereits "
                    "verbindlich bestätigt."
                ),
                ephemeral=True,
            )

            return

        is_applicant = (
            interaction.user.id
            == application[
                "user_id"
            ]
        )

        is_staff = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_recruitment_staff(
                interaction.user
            )
        )

        if not is_applicant and not is_staff:

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            InterviewProposalModal()
        )


    @discord.ui.button(
        label="Termin bestätigen",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:new_application:confirm_date",
    )
    async def confirm_date(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.message:

            return

        app_id, application = (
            find_application_by_planning_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) == "interview_pending":

            await interaction.response.send_message(
                "✅ Der Termin wurde bereits vollständig bestätigt.",
                ephemeral=True,
            )

            return

        if (
            not application.get(
                "proposal_date"
            )
            or not application.get(
                "proposal_time"
            )
        ):

            await interaction.response.send_message(
                (
                    "⚠️ Es wurde noch kein "
                    "Gesprächstermin vorgeschlagen."
                ),
                ephemeral=True,
            )

            return

        is_applicant = (
            interaction.user.id
            == application[
                "user_id"
            ]
        )

        is_staff = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_recruitment_staff(
                interaction.user
            )
        )

        if is_applicant:

            if application.get(
                "applicant_confirmed"
            ):

                await interaction.response.send_message(
                    "✅ Du hast diesen Termin bereits bestätigt.",
                    ephemeral=True,
                )

                return

            application[
                "applicant_confirmed"
            ] = True

        elif is_staff:

            if application.get(
                "team_confirmed"
            ):

                await interaction.response.send_message(
                    (
                        "✅ Das Bewerbungsteam hat "
                        "diesen Termin bereits bestätigt."
                    ),
                    ephemeral=True,
                )

                return

            application[
                "team_confirmed"
            ] = True

            application[
                "interviewer_id"
            ] = interaction.user.id

        else:

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        await interaction.response.edit_message(
            embed=build_interview_planning_embed(
                interaction.guild,
                application,
            ),
            view=self,
        )

        await send_application_log(
            interaction.guild,
            "✅ Gesprächstermin bestätigt",
            (
                f"**Bewerber:** "
                f"<@{application['user_id']}>\n"

                f"**Bewerbungs-ID:** `{app_id}`\n"

                f"**Bestätigt von:** "
                f"{interaction.user.mention}"
            ),
            SUCCESS_COLOR,
        )

        await try_confirm_interview(
            interaction.guild,
            app_id,
            application,
            interaction.message,
        )


# ============================================================
# TERMIN VOLLSTÄNDIG BESTÄTIGEN
# ============================================================

async def try_confirm_interview(
    guild: discord.Guild,
    app_id: str,
    application: dict,
    planning_message: discord.Message,
):

    if not (
        application.get(
            "applicant_confirmed"
        )
        and application.get(
            "team_confirmed"
        )
        and application.get(
            "interviewer_id"
        )
    ):

        return

    if application.get(
        "status"
    ) == "interview_pending":

        return

    application[
        "status"
    ] = "interview_pending"

    application[
        "confirmed_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    DATA[
        "applications"
    ][
        app_id
    ] = application

    save_data()

    embed = discord.Embed(
        title="🎙️ BEWERBUNGSGESPRÄCH BESTÄTIGT",
        description=(
            "# ✅ Termin steht fest\n\n"

            f"**Bewerber:** "
            f"<@{application['user_id']}>\n"

            f"**Gesprächsführer:** "
            f"<@{application['interviewer_id']}>\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📅 Termin\n\n"

            f"**Datum:** "
            f"{application['proposal_date']}\n"

            f"**Uhrzeit:** "
            f"{application['proposal_time']} Uhr\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 🎙️ Ablauf\n\n"

            f"Bitte zunächst in "
            f"<#{WAITING_ROOM_CHANNEL_ID}> warten.\n\n"

            "Das Bewerbungsteam holt den Bewerber "
            "anschließend in einen der Gesprächsräume:\n\n"

            f"**Gespräch 1:** "
            f"<#{INTERVIEW_CHANNEL_1_ID}>\n"

            f"**Gespräch 2:** "
            f"<#{INTERVIEW_CHANNEL_2_ID}>\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Nach dem Gespräch trägt das Bewerbungsteam "
            "das Ergebnis über die Buttons unten ein."
        ),
        color=SUCCESS_COLOR,
    )

    embed.set_footer(
        text="EHRP/VC • Bewerbungssystem"
    )

    await planning_message.edit(
        content=(
            f"<@{application['user_id']}> "
            f"<@{application['interviewer_id']}>"
        ),
        embed=embed,
        view=InterviewResultView(),
        allowed_mentions=discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False,
        ),
    )

    await send_application_log(
        guild,
        "🎙️ Bewerbungsgespräch bestätigt",
        (
            f"**Bewerber:** "
            f"<@{application['user_id']}>\n"

            f"**Bewerbungs-ID:** `{app_id}`\n"

            f"**Gesprächsführer:** "
            f"<@{application['interviewer_id']}>\n"

            f"**Datum:** "
            f"{application['proposal_date']}\n"

            f"**Uhrzeit:** "
            f"{application['proposal_time']} Uhr"
        ),
        SUCCESS_COLOR,
    )


# ============================================================
# GESPRÄCH ABLEHNEN MODAL
# ============================================================

class InterviewRejectedModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Bewerbungsgespräch ablehnen"
        )

        self.reason = discord.ui.TextInput(
            label="Grund",
            placeholder=(
                "Warum wurde das Bewerbungsgespräch "
                "nicht bestanden?"
            ),
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=5,
            max_length=1000,
        )

        self.add_item(
            self.reason
        )


    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        if not interaction.message:

            return

        app_id, application = (
            find_application_by_planning_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "interview_result"
        ):

            await interaction.response.send_message(
                (
                    "⚠️ Für dieses Bewerbungsgespräch "
                    "wurde bereits ein Ergebnis eingetragen."
                ),
                ephemeral=True,
            )

            return

        reason = str(
            self.reason.value
        ).strip()

        applicant = (
            interaction.guild.get_member(
                application[
                    "user_id"
                ]
            )
        )

        if applicant:

            await remove_role_safe(
                applicant,
                INTERVIEW_PENDING_ROLE_ID,
                (
                    "EHRP: Bewerbungsgespräch "
                    "nicht bestanden"
                ),
            )

        application[
            "status"
        ] = "failed"

        application[
            "interview_result"
        ] = "rejected"

        application[
            "result_reason"
        ] = reason

        application[
            "result_by"
        ] = interaction.user.id

        application[
            "result_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        rejection_text = (
            "# ❌ Bewerbungsgespräch nicht bestanden\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Teilnahme am "
            "Bewerbungsgespräch bei **EHRP/VC**.\n\n"

            "Nach Auswertung des Gespräches müssen wir "
            "Ihnen leider mitteilen, dass Ihr "
            "Bewerbungsgespräch **nicht erfolgreich abgeschlossen** wurde.\n\n"

            "## 📋 Grund\n\n"

            f"**- {reason}**\n\n"

            "Damit ist Ihr aktuelles Bewerbungsverfahren beendet.\n\n"

            "Wir bedanken uns für Ihr Interesse und wünschen "
            "Ihnen weiterhin viel Spaß auf **EHRP/VC**.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        if applicant:

            try:

                await applicant.send(
                    rejection_text
                )

            except discord.HTTPException:
                pass

        embed = discord.Embed(
            title="❌ BEWERBUNGSGESPRÄCH ABGELEHNT",
            description=(
                "# Bewerbungsverfahren beendet\n\n"

                f"**Bewerber:** "
                f"<@{application['user_id']}>\n"

                f"**Entscheidung von:** "
                f"{interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📋 Grund\n\n"

                f"{reason}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                f"<@&{INTERVIEW_PENDING_ROLE_ID}> "
                "**wurde entfernt.**\n\n"

                "**Status:** 🔴 Nicht aufgenommen"
            ),
            color=ERROR_COLOR,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )

        await send_application_log(
            interaction.guild,
            "❌ Bewerbungsgespräch abgelehnt",
            (
                f"**Bewerber:** "
                f"<@{application['user_id']}>\n"

                f"**Bewerbungs-ID:** `{app_id}`\n"

                f"**Entscheidung von:** "
                f"{interaction.user.mention}\n\n"

                f"**Grund:**\n{reason}"
            ),
            ERROR_COLOR,
        )


# ============================================================
# GESPRÄCHSERGEBNIS
# ============================================================

class InterviewResultView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Bewerbungsgespräch erfolgreich abgeschlossen",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:new_application:interview_success",
    )
    async def success(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        if not interaction.message:

            return

        app_id, application = (
            find_application_by_planning_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Bewerbung nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "interview_result"
        ):

            await interaction.response.send_message(
                (
                    "⚠️ Für dieses Gespräch wurde "
                    "bereits ein Ergebnis eingetragen."
                ),
                ephemeral=True,
            )

            return

        applicant = (
            interaction.guild.get_member(
                application[
                    "user_id"
                ]
            )
        )

        if not applicant:

            await interaction.response.send_message(
                "❌ Der Bewerber ist nicht mehr auf dem Server.",
                ephemeral=True,
            )

            return

        # ====================================================
        # ERST AUSBILDUNG ANSTEHEND VERGEBEN
        # ====================================================

        role_added = await add_role_safe(
            applicant,
            TRAINING_PENDING_ROLE_ID,
            (
                "EHRP: Bewerbungsgespräch "
                "erfolgreich abgeschlossen"
            ),
        )

        if not role_added:

            await interaction.response.send_message(
                (
                    "❌ Die Rolle **Ausbildung anstehend** "
                    "konnte nicht vergeben werden.\n\n"

                    "Bitte prüfe die Rollen-Hierarchie des Bots."
                ),
                ephemeral=True,
            )

            return

        # Danach Bewerbungsgespräch anstehend entfernen
        await remove_role_safe(
            applicant,
            INTERVIEW_PENDING_ROLE_ID,
            (
                "EHRP: Bewerbungsgespräch "
                "erfolgreich abgeschlossen"
            ),
        )

        application[
            "status"
        ] = "completed"

        application[
            "interview_result"
        ] = "success"

        application[
            "result_by"
        ] = interaction.user.id

        application[
            "result_at"
        ] = datetime.now(
            timezone.utc
        ).isoformat()

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        success_text = (
            "# 🎉 Bewerbungsgespräch erfolgreich abgeschlossen\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "wir freuen uns, Ihnen mitteilen zu können, "
            "dass Sie Ihr Bewerbungsgespräch bei "
            "**EHRP/VC erfolgreich abgeschlossen haben**.\n\n"

            "## 🎓 Nächster Schritt\n\n"

            "Sie befinden sich nun in der nächsten Phase "
            "Ihres Einstiegs bei EHRP/VC.\n\n"

            "Die Rolle **Ausbildung anstehend** wurde Ihnen "
            "automatisch zugewiesen.\n\n"

            "Weitere Informationen zu Ihrer Ausbildung "
            "erhalten Sie durch das zuständige Team.\n\n"

            "Wir gratulieren Ihnen und wünschen Ihnen "
            "viel Erfolg für den weiteren Verlauf.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        try:

            await applicant.send(
                success_text
            )

        except discord.HTTPException:
            pass

        embed = discord.Embed(
            title=(
                "🎉 BEWERBUNGSGESPRÄCH "
                "ERFOLGREICH ABGESCHLOSSEN"
            ),
            description=(
                "# ✅ Gespräch bestanden\n\n"

                f"**Bewerber:** "
                f"{applicant.mention}\n"

                f"**Entscheidung von:** "
                f"{interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 🎭 Rollenänderung\n\n"

                f"<@&{INTERVIEW_PENDING_ROLE_ID}> "
                "❌ entfernt\n"

                f"<@&{TRAINING_PENDING_ROLE_ID}> "
                "✅ vergeben\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "**Status:** 🟢 Ausbildung anstehend"
            ),
            color=SUCCESS_COLOR,
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )

        await send_application_log(
            interaction.guild,
            (
                "🎉 Bewerbungsgespräch "
                "erfolgreich abgeschlossen"
            ),
            (
                f"**Bewerber:** "
                f"{applicant.mention}\n"

                f"**Bewerbungs-ID:** `{app_id}`\n"

                f"**Entscheidung von:** "
                f"{interaction.user.mention}\n\n"

                f"❌ <@&{INTERVIEW_PENDING_ROLE_ID}> entfernt\n"
                f"✅ <@&{TRAINING_PENDING_ROLE_ID}> vergeben"
            ),
            SUCCESS_COLOR,
        )


    @discord.ui.button(
        label="Bewerbungsgespräch abgelehnt",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:new_application:interview_rejected",
    )
    async def rejected(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            InterviewRejectedModal()
        )


# ============================================================
# APPLICATIONS COG
# ============================================================

class Applications(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot

        # Persistent Views
        bot.add_view(
            ApplicationPanelView()
        )

        bot.add_view(
            ApplicationReviewView()
        )

        bot.add_view(
            InterviewPlanningView()
        )

        bot.add_view(
            InterviewResultView()
        )


    # ========================================================
    # DM LISTENER
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):

        if message.author.bot:
            return

        if message.guild is not None:
            return

        print(
            f"📩 DM von "
            f"{message.author} "
            f"({message.author.id})"
        )

        try:

            await process_application_dm(
                self.bot,
                message,
            )

        except Exception as error:

            print(
                "❌ Fehler im Bewerbungs-DM-System: "
                f"{type(error).__name__}: {error}"
            )

            try:

                await message.channel.send(
                    (
                        "❌ Bei der Verarbeitung deiner Antwort "
                        "ist ein Fehler aufgetreten.\n\n"

                        "Bitte versuche es erneut."
                    )
                )

            except discord.HTTPException:
                pass


    # ========================================================
    # /BEWERBUNG_PANEL
    # ========================================================

    @app_commands.command(
        name="bewerbung_panel",
        description=(
            "Erstellt das neue EHRP/VC Bewerbungsportal."
        ),
    )
    async def bewerbung_panel(
        self,
        interaction: discord.Interaction,
    ):

        if not interaction.guild:

            return

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_leadership(
            interaction.user
        ):

            await interaction.response.send_message(
                (
                    "❌ Nur die Bewerbungsleitung "
                    "kann das Panel erstellen."
                ),
                ephemeral=True,
            )

            return

        channel = interaction.guild.get_channel(
            APPLICATION_PANEL_CHANNEL_ID
        )

        if not isinstance(
            channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                (
                    "❌ Der Channel "
                    "**Team Bewerbung** wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        await channel.send(
            embed=build_application_panel(),
            view=ApplicationPanelView(),
        )

        await interaction.response.send_message(
            (
                f"✅ Bewerbungsportal wurde in "
                f"{channel.mention} erstellt."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNGEN_OEFFNEN
    # ========================================================

    @app_commands.command(
        name="bewerbungen_oeffnen",
        description=(
            "Öffnet die Teambewerbungen."
        ),
    )
    async def bewerbungen_oeffnen(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_leadership(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        DATA[
            "applications_open"
        ] = True

        save_data()

        await interaction.response.send_message(
            (
                "# 🟢 Bewerbungen geöffnet\n\n"

                "Neue Teambewerbungen können "
                "ab sofort wieder gestartet werden."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNGEN_SCHLIESSEN
    # ========================================================

    @app_commands.command(
        name="bewerbungen_schliessen",
        description=(
            "Schließt die Teambewerbungen."
        ),
    )
    async def bewerbungen_schliessen(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_leadership(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        DATA[
            "applications_open"
        ] = False

        save_data()

        await interaction.response.send_message(
            (
                "# 🔴 Bewerbungen geschlossen\n\n"

                "Neue Bewerbungen können momentan "
                "nicht gestartet werden."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNG_STATUS
    # ========================================================

    @app_commands.command(
        name="bewerbung_status",
        description=(
            "Zeigt den Status des Bewerbungssystems."
        ),
    )
    async def bewerbung_status(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_recruitment_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        applications = DATA[
            "applications"
        ]

        pending = sum(
            1
            for app
            in applications.values()
            if app.get(
                "status"
            )
            in {
                "pending",
                "claimed",
            }
        )

        planning = sum(
            1
            for app
            in applications.values()
            if app.get(
                "status"
            )
            == "interview_planning"
        )

        interviews = sum(
            1
            for app
            in applications.values()
            if app.get(
                "status"
            )
            == "interview_pending"
        )

        completed = sum(
            1
            for app
            in applications.values()
            if app.get(
                "status"
            )
            == "completed"
        )

        rejected = sum(
            1
            for app
            in applications.values()
            if app.get(
                "status"
            )
            in {
                "rejected",
                "failed",
            }
        )

        if DATA.get(
            "applications_open",
            True,
        ):

            open_text = (
                "🟢 Geöffnet"
            )

        else:

            open_text = (
                "🔴 Geschlossen"
            )

        embed = discord.Embed(
            title="⚙️ EHRP/VC • Bewerbungssystem",
            description=(
                "# 📊 Systemstatus\n\n"

                f"**Bewerbungen:** "
                f"{open_text}\n\n"

                f"💬 **Laufende DM-Bewerbungen:** "
                f"{len(DATA['sessions'])}\n"

                f"📋 **Offene Bewerbungen:** "
                f"{pending}\n"

                f"📅 **Gesprächsplanung:** "
                f"{planning}\n"

                f"🎙️ **Gespräche anstehend:** "
                f"{interviews}\n"

                f"🎓 **Erfolgreich:** "
                f"{completed}\n"

                f"❌ **Abgelehnt:** "
                f"{rejected}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "🟢 DM-System: Online\n"
                "🟢 Automatische Fragen: Aktiv\n"
                "🟢 Bewerbungsteam-Pings: Aktiv\n"
                "🟢 Terminplanung: Online\n"
                "🟢 Rollen-Automation: Online\n"
                "🟢 Logging: Online"
            ),
            color=SUCCESS_COLOR,
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
        Applications(
            bot
        )
    )
