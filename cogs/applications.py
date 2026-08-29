from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# EHRP/VC | RECRUITMENT SYSTEM
# DM APPLICATION SYSTEM
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
INFO_COLOR = 0x3498DB


# ============================================================
# CHANNELS
# ============================================================

# Interne schriftliche Bewerbungen
APPLICATION_REVIEW_CHANNEL_ID = 1526942850778923181

# Terminplanung nach angenommener schriftlicher Bewerbung
INTERVIEW_PLANNING_CHANNEL_ID = 1543000219321503844

# Final bestätigte Bewerbungsgespräche
CONFIRMED_INTERVIEW_CHANNEL_ID = 1526951239269744870


# ============================================================
# ROLES
# ============================================================

# Zuständiges Bewerbungs-/Gesprächsteam
INTERVIEW_ROLE_ID = 1526955827770949793

# Rolle nach angenommener schriftlicher Bewerbung
APPLICATION_ACCEPTED_ROLE_ID = 1526957615765127412

# Rolle nach bestandenem Bewerbungsgespräch
TEAM_ACCEPTED_ROLE_ID = 1526957502078652496


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
# QUESTIONS
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
        "category": "👤 Persönliche Angaben",
        "min_length": 3,
        "max_length": 500,
    },
    {
        "title": (
            "Wie viele Stunden pro Woche können Sie ungefähr "
            "auf EHRP/VC aktiv sein?"
        ),
        "category": "👤 Persönliche Angaben",
        "min_length": 2,
        "max_length": 500,
    },
    {
        "title": (
            "Hatten Sie bereits Erfahrung als Teammitglied "
            "auf einem anderen RP-Server?"
        ),
        "category": "🧩 Erfahrung",
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
            "Welche Stärken bringen Sie für die Arbeit "
            "im Team mit?"
        ),
        "category": "💬 Motivation",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Welche Schwächen haben Sie und wie gehen Sie "
            "damit um?"
        ),
        "category": "💬 Motivation",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Ein Spieler beleidigt Sie nach einer Sanktion. "
            "Wie reagieren Sie?"
        ),
        "category": "🧠 Situationsfragen",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Sie sehen, dass ein anderes Teammitglied seine Rechte "
            "ausnutzt oder einen Spieler unfair behandelt. "
            "Wie handeln Sie?"
        ),
        "category": "🧠 Situationsfragen",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Ein guter Freund von Ihnen verstößt eindeutig gegen "
            "das Regelwerk. Wie gehen Sie damit um?"
        ),
        "category": "🧠 Situationsfragen",
        "min_length": 30,
        "max_length": 2000,
    },
    {
        "title": (
            "Zwei Spieler beschuldigen sich gegenseitig und Sie können "
            "zunächst nicht feststellen, wer die Wahrheit sagt. "
            "Wie gehen Sie vor?"
        ),
        "category": "🧠 Situationsfragen",
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
# LOAD DATA
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
            "❌ Recruitment Daten konnten "
            f"nicht geladen werden: {error}"
        )

        return {
            "applications_open": True,
            "counter": 0,
            "applications": {},
            "sessions": {},
        }


DATA = load_data()


# ============================================================
# SAVE DATA
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
            "❌ Recruitment Daten konnten "
            f"nicht gespeichert werden: {error}"
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


def find_application_by_review_message(
    message_id: int,
):

    for (
        application_id,
        application,
    ) in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "review_message_id"
            )
            == message_id
        ):

            return (
                application_id,
                application,
            )

    return (
        None,
        None,
    )


def find_application_by_interview_message(
    message_id: int,
):

    for (
        application_id,
        application,
    ) in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "interview_message_id"
            )
            == message_id
        ):

            return (
                application_id,
                application,
            )

    return (
        None,
        None,
    )


def find_application_by_result_message(
    message_id: int,
):

    for (
        application_id,
        application,
    ) in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "result_message_id"
            )
            == message_id
        ):

            return (
                application_id,
                application,
            )

    return (
        None,
        None,
    )


# ============================================================
# OPEN APPLICATION CHECK
# ============================================================

def has_open_application(
    user_id: int,
) -> bool:

    active_statuses = {
        "pending",
        "claimed",
        "interview_planning",
        "interview_confirmed",
        "interview_running",
    }

    for application in DATA[
        "applications"
    ].values():

        if (
            application.get(
                "user_id"
            )
            != user_id
        ):
            continue

        if application.get(
            "status"
        ) in active_statuses:

            return True

    return False


# ============================================================
# INTERVIEW STAFF CHECK
# ============================================================

def is_interview_staff(
    member: discord.Member,
) -> bool:

    return any(
        role.id
        == INTERVIEW_ROLE_ID

        for role
        in member.roles
    )


# ============================================================
# APPLICATION NUMBER
# ============================================================

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


# ============================================================
# ROLE HELPERS
# ============================================================

async def add_role_safe(
    member: discord.Member,
    role_id: int,
    reason: str,
) -> bool:

    role = (
        member.guild.get_role(
            role_id
        )
    )

    if role is None:

        print(
            "❌ Rolle nicht gefunden: "
            f"{role_id}"
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
            "❌ Rolle konnte nicht "
            f"hinzugefügt werden ({role_id}): "
            f"{error}"
        )

        return False


async def remove_role_safe(
    member: discord.Member,
    role_id: int,
    reason: str,
) -> bool:

    role = (
        member.guild.get_role(
            role_id
        )
    )

    if role is None:

        print(
            "❌ Rolle nicht gefunden: "
            f"{role_id}"
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
            "❌ Rolle konnte nicht "
            f"entfernt werden ({role_id}): "
            f"{error}"
        )

        return False


# ============================================================
# PUBLIC APPLICATION PANEL
# ============================================================

def build_application_panel() -> discord.Embed:

    if DATA.get(
        "applications_open",
        True,
    ):

        application_status = (
            "🟢 **GEÖFFNET**"
        )

    else:

        application_status = (
            "🔴 **GESCHLOSSEN**"
        )

    embed = discord.Embed(
        title=(
            "📨 EHRP/VC • TEAM RECRUITMENT"
        ),
        description=(
            "# Werden Sie Teil des EHRP/VC-Teams\n\n"

            "Sie möchten Verantwortung übernehmen, "
            "unsere Community unterstützen und aktiv "
            "am Aufbau von **EHRP/VC** mitwirken?\n\n"

            "Dann können Sie hier Ihre Bewerbung starten.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📋 Voraussetzungen\n\n"

            "• Mindestalter: **13 Jahre**\n"
            "• Funktionierendes Mikrofon\n"
            "• Aktiver Discord-Account\n"
            "• Sehr gute Rechtschreibung und Grammatik\n"
            "• Kommunikation in der **Sie-Form**\n"
            "• Ca. **15 Stunden pro Woche** verfügbar\n"
            "• Grundkenntnisse im Roleplay\n"
            "• Sicherer Umgang mit Discord\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 💬 So funktioniert die Bewerbung\n\n"

            "Die Bewerbung wird vollständig über eine "
            "**private Unterhaltung mit dem Bot** durchgeführt.\n\n"

            "Nach dem Start erhalten Sie die Fragen per DM.\n"
            "Sie antworten dort einfach **ganz normal mit einer Nachricht**.\n\n"

            "Sobald Ihre Antwort gültig ist, erhalten Sie "
            "**automatisch die nächste Frage**.\n\n"

            "Es müssen während der Bewerbung keine "
            "Weiter-Buttons gedrückt werden.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## ⚠️ Hinweise\n\n"

            "• Antworten Sie vollständig und ehrlich.\n"
            "• Sehr kurze oder offensichtlich lustlose Antworten "
            "können zur Ablehnung führen.\n"
            "• Mehrere gleichzeitig laufende Bewerbungen "
            "sind nicht möglich.\n"
            "• Ihre Direktnachrichten müssen aktiviert sein.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📡 Bewerbungsstatus\n\n"

            f"{application_status}"
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System"
        )
    )

    return embed


# ============================================================
# REQUIREMENTS EMBED
# ============================================================

def build_requirements_embed() -> discord.Embed:

    embed = discord.Embed(
        title=(
            "📋 Voraussetzungen bestätigen"
        ),
        description=(
            "# EHRP/VC • TEAMBEWERBUNG\n\n"

            "Bevor die Bewerbung per DM beginnt, "
            "müssen Sie bestätigen, dass Sie die "
            "Voraussetzungen gelesen haben.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## Voraussetzungen\n\n"

            "✅ Mindestalter **13 Jahre**\n"
            "✅ Funktionierendes Mikrofon\n"
            "✅ Aktiver Discord-Account\n"
            "✅ Sehr gute Rechtschreibung und Grammatik\n"
            "✅ Kommunikation in der **Sie-Form**\n"
            "✅ Ca. **15 Stunden pro Woche** verfügbar\n"
            "✅ Grundkenntnisse im Roleplay\n"
            "✅ Sicherer Umgang mit Discord\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Mit Ihrer Bestätigung erklären Sie, "
            "dass Sie diese Voraussetzungen gelesen "
            "haben und grundsätzlich erfüllen."
        ),
        color=WARNING_COLOR,
    )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System"
        )
    )

    return embed


# ============================================================
# DM QUESTION EMBED
# ============================================================

def build_dm_question_embed(
    question_index: int,
) -> discord.Embed:

    question = QUESTIONS[
        question_index
    ]

    current_number = (
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

    bar_length = 10

    filled = round(
        (
            progress
            / 100
        )
        * bar_length
    )

    progress_bar = (
        "🟩" * filled
        + "⬜" * (
            bar_length
            - filled
        )
    )

    embed = discord.Embed(
        title=(
            "📨 EHRP/VC • TEAMBEWERBUNG"
        ),
        description=(
            f"# Frage {current_number} von {total}\n\n"

            f"## {question['category']}\n\n"

            f"### {question['title']}\n\n"

            "Schreiben Sie Ihre Antwort jetzt "
            "**einfach als normale Nachricht in diesen Chat**.\n\n"

            "Sobald Ihre Antwort gespeichert wurde, "
            "erhalten Sie automatisch die nächste Frage."
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
                "Bitte beantworten Sie diese Frage "
                "ausführlich. Eine sehr kurze Antwort "
                "wird nicht akzeptiert."
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System • "
            f"Frage {current_number}/{total}"
        )
    )

    return embed


# ============================================================
# DM START EMBED
# ============================================================

def build_dm_start_embed() -> discord.Embed:

    embed = discord.Embed(
        title=(
            "✅ Bewerbung gestartet"
        ),
        description=(
            "# Willkommen im EHRP/VC Recruitment\n\n"

            "Ihre Bewerbung wurde erfolgreich gestartet.\n\n"

            "Ab jetzt läuft die Bewerbung vollständig "
            "über diesen privaten Chat.\n\n"

            "## 💬 Wichtig\n\n"

            "Sie müssen keine Buttons drücken.\n\n"

            "Beantworten Sie jede Frage einfach mit "
            "einer **normalen Discord-Nachricht**.\n\n"

            "Nach jeder gültigen Antwort wird automatisch "
            "die nächste Frage gesendet.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Bitte beantworten Sie alle Fragen "
            "vollständig und ehrlich."
        ),
        color=SUCCESS_COLOR,
    )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System"
        )
    )

    return embed

# ============================================================
# APPLICATION PANEL VIEW
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
        style=discord.ButtonStyle.primary,
        custom_id="ehrp:application:start",
    )
    async def start_application(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.guild:

            await interaction.response.send_message(
                "❌ Diese Funktion kann nur auf dem Server verwendet werden.",
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
                    "Derzeit werden keine neuen Teambewerbungen angenommen."
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
                    "Sie besitzen bereits eine offene oder laufende Bewerbung.\n\n"
                    "Bitte warten Sie, bis diese vollständig abgeschlossen wurde."
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
                    "Sie haben bereits eine laufende Bewerbung per DM."
                ),
                ephemeral=True,
            )

            return

        session = {
            "user_id": interaction.user.id,
            "guild_id": interaction.guild.id,
            "current_question": 0,
            "answers": {},
            "requirements_confirmed": False,
            "awaiting_final_submit": False,
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
# REQUIREMENTS VIEW
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
                    "❌ Ihre Bewerbungssitzung wurde nicht gefunden.\n"
                    "Bitte starten Sie die Bewerbung erneut."
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

                        "Der Bot konnte Ihnen keine Direktnachricht senden.\n\n"

                        "Bitte aktivieren Sie auf diesem Server "
                        "**Direktnachrichten von Servermitgliedern** "
                        "und starten Sie die Bewerbung anschließend erneut."
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
                        "Die Bewerbung konnte technisch nicht gestartet werden.\n\n"
                        "Bitte versuchen Sie es später erneut."
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
                    "# Bitte prüfen Sie Ihre Direktnachrichten\n\n"

                    "Die Bewerbung wurde erfolgreich gestartet.\n\n"

                    "Sie erhalten die Fragen jetzt **privat per DM**.\n\n"

                    "Antworten Sie dort einfach mit normalen Nachrichten.\n"
                    "Die nächste Frage wird automatisch gesendet."
                ),
                color=SUCCESS_COLOR,
            ),
            view=None,
        )


# ============================================================
# DM ANSWER VALIDATION
# ============================================================

def validate_dm_answer(
    question: dict,
    answer: str,
):

    answer = answer.strip()

    if not answer:

        return (
            False,
            "❌ Ihre Antwort darf nicht leer sein."
        )

    if len(
        answer
    ) < question[
        "min_length"
    ]:

        return (
            False,
            (
                "❌ Ihre Antwort ist zu kurz.\n\n"
                f"Bitte verwenden Sie mindestens "
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
                "❌ Ihre Antwort ist zu lang.\n\n"
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
                    "❌ Bitte geben Sie Ihr Alter "
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
                (
                    "❌ Bitte geben Sie ein gültiges Alter an."
                ),
            )

    return (
        True,
        None,
    )


# ============================================================
# DM FINAL REVIEW EMBED
# ============================================================

def build_dm_final_review_embed(
    user_id: int,
) -> discord.Embed:

    session = get_session(
        user_id
    )

    embed = discord.Embed(
        title="✅ Bewerbung vollständig",
        description=(
            "# 📋 Abschlusskontrolle\n\n"

            "Sie haben alle Fragen beantwortet.\n\n"

            "Bitte prüfen Sie Ihre Antworten noch einmal.\n\n"

            "Wenn alles korrekt ist, klicken Sie unten auf "
            "**Bewerbung absenden**.\n\n"

            "Falls Sie eine Antwort ändern möchten, "
            "können Sie über das Auswahlfeld die entsprechende Frage auswählen."
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
        ) > 220:

            answer = (
                answer[:217]
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
        text="EHRP/VC | Recruitment System"
    )

    return embed


# ============================================================
# DM QUESTION SELECT FOR EDIT
# ============================================================

class DMReviewQuestionSelect(
    discord.ui.Select
):

    def __init__(self):

        options = []

        for index, question in enumerate(
            QUESTIONS
        ):

            options.append(
                discord.SelectOption(
                    label=f"Frage {index + 1}",
                    description=question[
                        "title"
                    ][:90],
                    value=str(index),
                )
            )

        super().__init__(
            placeholder="Antwort zum Bearbeiten auswählen …",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.send_message(
                "❌ Bewerbungssitzung nicht gefunden.",
                ephemeral=True,
            )

            return

        question_index = int(
            self.values[
                0
            ]
        )

        session[
            "edit_question"
        ] = question_index

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.send_modal(
            DMEditAnswerModal(
                interaction.user.id,
                question_index,
            )
        )


# ============================================================
# DM EDIT ANSWER MODAL
# ============================================================

class DMEditAnswerModal(
    discord.ui.Modal
):

    def __init__(
        self,
        user_id: int,
        question_index: int,
    ):

        self.user_id = user_id
        self.question_index = question_index

        question = QUESTIONS[
            question_index
        ]

        session = get_session(
            user_id
        )

        current_answer = ""

        if session:

            current_answer = session.get(
                "answers",
                {},
            ).get(
                str(
                    question_index
                ),
                "",
            )

        super().__init__(
            title=(
                f"Frage {question_index + 1} ändern"
            )
        )

        style = (
            discord.TextStyle.paragraph
            if question[
                "max_length"
            ] > 500
            else discord.TextStyle.short
        )

        self.answer_input = (
            discord.ui.TextInput(
                label=question[
                    "title"
                ][:45],
                style=style,
                required=True,
                min_length=question[
                    "min_length"
                ],
                max_length=min(
                    question[
                        "max_length"
                    ],
                    4000,
                ),
                default=current_answer[
                    :4000
                ],
            )
        )

        self.add_item(
            self.answer_input
        )

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:

            await interaction.response.send_message(
                "❌ Bewerbungssitzung nicht gefunden.",
                ephemeral=True,
            )

            return

        question = QUESTIONS[
            self.question_index
        ]

        answer = str(
            self.answer_input.value
        ).strip()

        valid, error = validate_dm_answer(
            question,
            answer,
        )

        if not valid:

            if error == "UNDER_13":

                remove_session(
                    interaction.user.id
                )

                await interaction.response.send_message(
                    (
                        "# ❌ Bewerbung beendet\n\n"
                        "Das Mindestalter für eine Bewerbung "
                        "bei **EHRP/VC** beträgt **13 Jahre**."
                    ),
                    ephemeral=True,
                )

                return

            await interaction.response.send_message(
                error,
                ephemeral=True,
            )

            return

        session[
            "answers"
        ][
            str(
                self.question_index
            )
        ] = answer

        session.pop(
            "edit_question",
            None,
        )

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=build_dm_final_review_embed(
                interaction.user.id
            ),
            view=DMFinalReviewView(),
        )


# ============================================================
# DM FINAL REVIEW VIEW
# ============================================================

class DMFinalReviewView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=1800
        )

        self.add_item(
            DMReviewQuestionSelect()
        )

    @discord.ui.button(
        label="Bewerbung absenden",
        emoji="📨",
        style=discord.ButtonStyle.success,
        row=1,
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
                "❌ Bewerbungssitzung nicht gefunden.",
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
                "❌ Bitte beantworten Sie zuerst alle Fragen.",
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
                "❌ Der EHRP/VC Server wurde nicht gefunden.",
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
                    "❌ Der interne Bewerbungs-Channel "
                    "wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        application_id = application_number()

        application = {
            "application_id": application_id,
            "user_id": interaction.user.id,
            "answers": answers.copy(),
            "status": "pending",
            "claimed_by": 0,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "review_message_id": 0,
            "interview_message_id": 0,
            "result_message_id": 0,
            "proposal_date": "",
            "proposal_time": "",
            "proposal_note": "",
            "proposal_by": 0,
            "applicant_confirmed": False,
            "team_confirmed": False,
            "interviewer_id": 0,
            "confirmed_message_sent": False,
            "interview_result": "",
            "result_reason": "",
            "result_by": 0,
        }

        DATA[
            "applications"
        ][
            application_id
        ] = application

        save_data()

        # Wird in Teil 3 gebaut
        review_embeds = build_review_embeds(
            guild,
            application,
        )

        review_message = (
            await review_channel.send(
                content=(
                    "📨 **Neue Teambewerbung:** "
                    f"<@{interaction.user.id}>"
                ),
                embeds=review_embeds,
                view=ApplicationReviewView(),
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    roles=False,
                    everyone=False,
                ),
            )
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

        result_embed = discord.Embed(
            title="✅ Bewerbung eingegangen",
            description=(
                "# Vielen Dank für Ihre Bewerbung\n\n"

                "Ihre Bewerbung wurde erfolgreich "
                "an das zuständige Team von **EHRP/VC** weitergeleitet.\n\n"

                f"**Bewerbungs-ID:** `{application_id}`\n"
                "**Status:** 🟡 Ausstehend\n\n"

                "Sobald eine Entscheidung getroffen wurde, "
                "werden Sie automatisch per DM informiert."
            ),
            color=SUCCESS_COLOR,
        )

        result_embed.set_footer(
            text="EHRP/VC | Recruitment System"
        )

        await interaction.response.edit_message(
            embed=result_embed,
            view=None,
        )


# ============================================================
# PROCESS NORMAL DM MESSAGE
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

    question = QUESTIONS[
        current_question
    ]

    answer = message.content.strip()

    valid, error = validate_dm_answer(
        question,
        answer,
    )

    if not valid:

        if error == "UNDER_13":

            remove_session(
                message.author.id
            )

            embed = discord.Embed(
                title="❌ Bewerbung beendet",
                description=(
                    "# Mindestalter nicht erfüllt\n\n"

                    "Leider erfüllen Sie aktuell nicht "
                    "die Mindestvoraussetzungen für eine Bewerbung "
                    "bei **EHRP/VC**.\n\n"

                    "Das Mindestalter beträgt **13 Jahre**."
                ),
                color=ERROR_COLOR,
            )

            await message.channel.send(
                embed=embed
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

    # ========================================================
    # NEXT QUESTION
    # ========================================================

    if next_question < len(
        QUESTIONS
    ):

        await message.channel.send(
            embed=build_dm_question_embed(
                next_question
            )
        )

        return True

    # ========================================================
    # ALL QUESTIONS COMPLETED
    # ========================================================

    session[
        "awaiting_final_submit"
    ] = True

    set_session(
        message.author.id,
        session,
    )

    await message.channel.send(
        embed=build_dm_final_review_embed(
            message.author.id
        ),
        view=DMFinalReviewView(),
    )

    return True
# ============================================================
# INTERNAL REVIEW EMBEDS
# ============================================================

def build_review_embeds(
    guild: discord.Guild,
    application: dict,
) -> list[discord.Embed]:

    member = guild.get_member(
        application[
            "user_id"
        ]
    )

    if member:

        applicant_text = (
            member.mention
        )

    else:

        applicant_text = (
            f"<@{application['user_id']}>"
        )

    status_map = {
        "pending":
            "🟡 AUSSTEHEND",

        "claimed":
            "🟠 IN BEARBEITUNG",

        "rejected":
            "🔴 ABGELEHNT",

        "interview_planning":
            "🔵 GESPRÄCHSPLANUNG",

        "interview_running":
            "🟣 GESPRÄCH AUSSTEHEND",

        "completed":
            "✅ AUFGENOMMEN",

        "failed":
            "❌ NICHT BESTANDEN",
    }

    claimed_by = application.get(
        "claimed_by",
        0,
    )

    if claimed_by:

        claimed_text = (
            f"<@{claimed_by}>"
        )

    else:

        claimed_text = (
            "Noch nicht übernommen"
        )

    # ========================================================
    # EMBED 1
    # ========================================================

    first_embed = discord.Embed(
        title=(
            "📨 TEAMBEWERBUNG • "
            f"{application['application_id']}"
        ),
        description=(
            "# Neue Teambewerbung\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"**Person:** {applicant_text}\n"
            f"**Discord-ID:** "
            f"`{application['user_id']}`\n\n"

            "## 📡 Bearbeitung\n\n"

            f"**Status:** "
            f"{status_map.get(application['status'], application['status'])}\n"

            f"**Bearbeiter:** "
            f"{claimed_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📋 Antworten • Teil 1"
        ),
        color=WARNING_COLOR,
    )

    if member:

        first_embed.set_thumbnail(
            url=member.display_avatar.url
        )

    # Fragen 1 bis 5
    for index in range(
        0,
        5,
    ):

        question = QUESTIONS[
            index
        ]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        first_embed.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    first_embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System • "
            "Teil 1/3"
        )
    )

    # ========================================================
    # EMBED 2
    # ========================================================

    second_embed = discord.Embed(
        title="📋 Antworten • Teil 2",
        color=INFO_COLOR,
    )

    # Fragen 6 bis 10
    for index in range(
        5,
        10,
    ):

        question = QUESTIONS[
            index
        ]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        second_embed.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    second_embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System • "
            "Teil 2/3"
        )
    )

    # ========================================================
    # EMBED 3
    # ========================================================

    third_embed = discord.Embed(
        title="📋 Antworten • Teil 3",
        color=INFO_COLOR,
    )

    # Fragen 11 bis 14
    for index in range(
        10,
        len(
            QUESTIONS
        ),
    ):

        question = QUESTIONS[
            index
        ]

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        third_embed.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )

    third_embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System • "
            "Teil 3/3"
        )
    )

    return [
        first_embed,
        second_embed,
        third_embed,
    ]


# ============================================================
# REJECT MODAL
# ============================================================

class RejectModal(
    discord.ui.Modal
):

    def __init__(
        self,
    ):

        super().__init__(
            title="Bewerbung ablehnen"
        )

        self.reason = discord.ui.TextInput(
            label="Grund der Ablehnung",
            placeholder=(
                "Bitte geben Sie den Ablehnungsgrund ein."
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

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Sie dürfen keine Bewerbungen ablehnen.",
                ephemeral=True,
            )

            return

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Die Bewerbungsnachricht wurde nicht gefunden.",
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
        ) in {
            "rejected",
            "interview_planning",
            "interview_running",
            "completed",
            "failed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits abgeschlossen oder weitergeleitet.",
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
        # EXACT AUTOMATIC REJECTION MESSAGE
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

        updated_embeds[
            0
        ].color = ERROR_COLOR

        updated_embeds[
            0
        ].add_field(
            name="❌ Ablehnung",
            value=(
                f"**Abgelehnt von:** "
                f"{interaction.user.mention}\n\n"

                f"**Grund:**\n{reason}"
            ),
            inline=False,
        )

        await interaction.response.edit_message(
            embeds=updated_embeds,
            view=None,
        )


# ============================================================
# APPLICATION REVIEW VIEW
# ============================================================

class ApplicationReviewView(
    discord.ui.View
):

    def __init__(
        self,
    ):

        super().__init__(
            timeout=None
        )


    # ========================================================
    # CLAIM
    # ========================================================

    @discord.ui.button(
        label="Übernehmen",
        emoji="👤",
        style=discord.ButtonStyle.secondary,
        custom_id="ehrp:application:claim",
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

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Sie dürfen keine Bewerbungen bearbeiten.",
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
                "⚠️ Diese Bewerbung befindet sich nicht mehr in der schriftlichen Prüfung.",
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
                    "✅ Sie haben diese Bewerbung bereits übernommen.",
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


    # ========================================================
    # ACCEPT WRITTEN APPLICATION
    # ========================================================

    @discord.ui.button(
        label="Annehmen",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:application:accept",
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

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Sie dürfen keine Bewerbungen annehmen.",
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

        # ====================================================
        # CHECK PLANNING CHANNEL BEFORE CHANGING STATUS/ROLE
        # ====================================================

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
                (
                    "❌ Der Channel für die Gesprächsplanung "
                    "wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return

        # ====================================================
        # GIVE ACCEPTED APPLICATION ROLE
        # ====================================================

        role_success = (
            await add_role_safe(
                applicant,
                APPLICATION_ACCEPTED_ROLE_ID,
                (
                    "EHRP Recruitment: "
                    "Schriftliche Bewerbung angenommen"
                ),
            )
        )

        if not role_success:

            await interaction.response.send_message(
                (
                    "❌ Die Bewerberrolle konnte nicht vergeben werden.\n\n"
                    "Prüfen Sie bitte die Rollen-Hierarchie des Bots."
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
        # AUTOMATIC ACCEPTANCE DM
        # ====================================================

        acceptance_text = (
            "# ✅ Bewerbung angenommen\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Bewerbung und Ihr Interesse an einer "
            "Position im Team von **EHRP/VC**.\n\n"

            "Wir freuen uns, Ihnen mitteilen zu können, dass Ihre Bewerbung "
            "**angenommen wurde**.\n\n"

            "## 📞 Nächster Schritt: Bewerbungsgespräch\n\n"

            "Als nächsten Schritt bitten wir Sie, gemeinsam mit unserem "
            "zuständigen Gesprächsteam einen Termin für Ihr "
            "Bewerbungsgespräch zu vereinbaren.\n\n"

            "Im Kanal **Gespräch Termin** können sowohl Sie als auch das "
            "zuständige Team einen Termin vorschlagen.\n\n"

            "Ein Termin gilt erst dann als verbindlich, wenn "
            "**beide Seiten diesen bestätigt haben**.\n\n"

            "Sollten Sie einen vereinbarten Termin nicht wahrnehmen können, "
            "informieren Sie das Team bitte rechtzeitig.\n\n"

            "Wir freuen uns auf das Gespräch mit Ihnen und wünschen Ihnen "
            "weiterhin viel Erfolg.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        try:

            await applicant.send(
                acceptance_text
            )

        except discord.HTTPException:

            pass

        # ====================================================
        # CREATE INTERVIEW PLANNING MESSAGE
        # ====================================================

        interview_message = (
            await planning_channel.send(
                content=(
                    f"{applicant.mention} "
                    f"<@&{INTERVIEW_ROLE_ID}>"
                ),
                embed=build_interview_embed(
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
        )

        application[
            "interview_message_id"
        ] = interview_message.id

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

        updated_embeds[
            0
        ].color = SUCCESS_COLOR

        updated_embeds[
            0
        ].add_field(
            name="✅ Schriftliche Bewerbung angenommen",
            value=(
                f"**Angenommen von:** "
                f"{interaction.user.mention}\n\n"

                "Der Bewerber wurde automatisch "
                "in die Gesprächsplanung weitergeleitet."
            ),
            inline=False,
        )

        await interaction.response.edit_message(
            embeds=updated_embeds,
            view=None,
        )


    # ========================================================
    # REJECT
    # ========================================================

    @discord.ui.button(
        label="Ablehnen",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:application:reject",
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

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                "❌ Sie dürfen keine Bewerbungen ablehnen.",
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
            RejectModal()
        )


# ============================================================
# INTERVIEW EMBED
# ============================================================

def build_interview_embed(
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

    if (
        proposal_date
        and proposal_time
    ):

        proposal_text = (
            "## 📅 Aktueller Terminvorschlag\n\n"

            f"**Datum:** {proposal_date}\n"
            f"**Uhrzeit:** {proposal_time} Uhr\n"

            f"**Vorgeschlagen von:** "
            f"<@{proposal_by}>\n"
        )

        if proposal_note:

            proposal_text += (
                f"**Hinweis:** "
                f"{proposal_note}\n"
            )

    else:

        proposal_text = (
            "## 📅 Terminvereinbarung\n\n"

            "**Es wurde noch kein Termin vorgeschlagen.**\n\n"

            "Sowohl der Bewerber als auch das "
            "Gesprächsteam können einen Termin vorschlagen."
        )

    applicant_status = (
        "✅ Bestätigt"
        if applicant_confirmed
        else "⏳ Noch nicht bestätigt"
    )

    team_status = (
        "✅ Bestätigt"
        if team_confirmed
        else "⏳ Noch nicht bestätigt"
    )

    if interviewer_id:

        interviewer_text = (
            f"<@{interviewer_id}>"
        )

    else:

        interviewer_text = (
            "Noch nicht festgelegt"
        )

    if (
        applicant_confirmed
        and team_confirmed
    ):

        final_status = (
            "# 🟢 TERMIN BESTÄTIGT\n\n"

            "Der Termin wurde von beiden Seiten bestätigt."
        )

        embed_color = SUCCESS_COLOR

    else:

        final_status = (
            "⚠️ Der Termin wird erst verbindlich, "
            "wenn **beide Seiten bestätigt haben**."
        )

        embed_color = INFO_COLOR

    embed = discord.Embed(
        title=(
            "📞 BEWERBUNGSGESPRÄCH • "
            f"{application['application_id']}"
        ),
        description=(
            "# Gesprächsplanung\n\n"

            "Die schriftliche Bewerbung wurde angenommen.\n\n"

            "Nun muss gemeinsam ein Termin für das "
            "Bewerbungsgespräch vereinbart werden.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"<@{applicant_id}>\n\n"

            "## 🧑‍💼 Gesprächsteam\n\n"

            f"<@&{INTERVIEW_ROLE_ID}>\n\n"

            f"**Gesprächsführer:** "
            f"{interviewer_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{proposal_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 🔐 Bestätigungsstatus\n\n"

            f"**Bewerber:** "
            f"{applicant_status}\n"

            f"**Gesprächsteam:** "
            f"{team_status}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{final_status}"
        ),
        color=embed_color,
    )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System"
        )
    )

    return embed

# ============================================================
# INTERVIEW PROPOSAL MODAL
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
            placeholder="z. B. 02.09.2026",
            min_length=8,
            max_length=10,
        )

        self.time_input = discord.ui.TextInput(
            label="Uhrzeit",
            placeholder="z. B. 18:30",
            min_length=4,
            max_length=5,
        )

        self.note_input = discord.ui.TextInput(
            label="Zusätzlicher Hinweis",
            placeholder=(
                "Optional, z. B. Ich kann zwischen "
                "18:00 und 20:00 Uhr."
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
                "❌ Gesprächsnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_interview_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Das Bewerbungsgespräch wurde nicht gefunden.",
                ephemeral=True,
            )

            return

        is_applicant = (
            interaction.user.id
            == application[
                "user_id"
            ]
        )

        is_team = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_interview_staff(
                interaction.user
            )
        )

        if not is_applicant and not is_team:

            await interaction.response.send_message(
                "❌ Sie gehören nicht zu diesem Bewerbungsgespräch.",
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
                f"{proposal_date} {proposal_time}",
                "%d.%m.%Y %H:%M",
            )

        except ValueError:

            await interaction.response.send_message(
                (
                    "❌ Datum oder Uhrzeit sind ungültig.\n\n"
                    "Bitte verwenden Sie zum Beispiel:\n"
                    "**Datum:** `02.09.2026`\n"
                    "**Uhrzeit:** `18:30`"
                ),
                ephemeral=True,
            )

            return

        if parsed_datetime < datetime.now():

            await interaction.response.send_message(
                (
                    "❌ Der vorgeschlagene Termin "
                    "liegt bereits in der Vergangenheit."
                ),
                ephemeral=True,
            )

            return

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

        # Neuer Vorschlag = beide Bestätigungen zurücksetzen
        application[
            "applicant_confirmed"
        ] = False

        application[
            "team_confirmed"
        ] = False

        application[
            "confirmed_message_sent"
        ] = False

        # Wer den Vorschlag macht, bestätigt automatisch
        if is_applicant:

            application[
                "applicant_confirmed"
            ] = True

        if is_team:

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
            embed=build_interview_embed(
                interaction.guild,
                application,
            ),
            view=InterviewPlanningView(),
        )

        if (
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

            await send_confirmed_interview(
                interaction.guild,
                application,
            )


# ============================================================
# INTERVIEW PLANNING VIEW
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
        custom_id="ehrp:application:interview_propose",
    )
    async def propose_interview(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Gesprächsnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_interview_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Das Bewerbungsgespräch wurde nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) == "interview_running":

            await interaction.response.send_message(
                (
                    "⚠️ Der Gesprächstermin wurde bereits "
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

        is_team = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_interview_staff(
                interaction.user
            )
        )

        if not is_applicant and not is_team:

            await interaction.response.send_message(
                (
                    "❌ Sie dürfen für dieses Gespräch "
                    "keinen Termin vorschlagen."
                ),
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
        custom_id="ehrp:application:interview_confirm",
    )
    async def confirm_interview(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Gesprächsnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_interview_message(
                interaction.message.id
            )
        )

        if not application:

            await interaction.response.send_message(
                "❌ Das Bewerbungsgespräch wurde nicht gefunden.",
                ephemeral=True,
            )

            return

        if application.get(
            "status"
        ) == "interview_running":

            await interaction.response.send_message(
                (
                    "✅ Dieser Gesprächstermin wurde bereits "
                    "vollständig bestätigt."
                ),
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
                "⚠️ Es wurde noch kein Termin vorgeschlagen.",
                ephemeral=True,
            )

            return

        if (
            interaction.user.id
            == application[
                "user_id"
            ]
        ):

            if application.get(
                "applicant_confirmed"
            ):

                await interaction.response.send_message(
                    (
                        "✅ Sie haben diesen Termin "
                        "bereits bestätigt."
                    ),
                    ephemeral=True,
                )

                return

            application[
                "applicant_confirmed"
            ] = True

        elif (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and is_interview_staff(
                interaction.user
            )
        ):

            if application.get(
                "team_confirmed"
            ):

                await interaction.response.send_message(
                    (
                        "✅ Das Gesprächsteam hat diesen "
                        "Termin bereits bestätigt."
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
                "❌ Sie dürfen diesen Termin nicht bestätigen.",
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
            embed=build_interview_embed(
                interaction.guild,
                application,
            ),
            view=self,
        )

        if (
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

            await send_confirmed_interview(
                interaction.guild,
                application,
            )


# ============================================================
# SEND CONFIRMED INTERVIEW
# ============================================================

async def send_confirmed_interview(
    guild: discord.Guild,
    application: dict,
):

    if application.get(
        "confirmed_message_sent",
        False,
    ):

        return

    confirmed_channel = (
        guild.get_channel(
            CONFIRMED_INTERVIEW_CHANNEL_ID
        )
    )

    if not isinstance(
        confirmed_channel,
        discord.TextChannel,
    ):

        print(
            "❌ Channel für bestätigte "
            "Bewerbungsgespräche nicht gefunden."
        )

        return

    embed = discord.Embed(
        title="📅 BEWERBUNGSGESPRÄCH BESTÄTIGT",
        description=(
            "# ✅ Verbindlicher Gesprächstermin\n\n"

            "Der Gesprächstermin wurde von "
            "**beiden Seiten bestätigt**.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"<@{application['user_id']}>\n\n"

            "## 🧑‍💼 Gesprächsführer\n\n"

            f"<@{application['interviewer_id']}>\n\n"

            "## 🗓️ Termin\n\n"

            f"**Datum:** "
            f"{application['proposal_date']}\n"

            f"**Uhrzeit:** "
            f"{application['proposal_time']} Uhr\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Bitte erscheinen Sie rechtzeitig "
            "zum vereinbarten Bewerbungsgespräch.\n\n"

            "Nach dem Gespräch trägt das zuständige "
            "Gesprächsteam das Ergebnis unten ein."
        ),
        color=SUCCESS_COLOR,
    )

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System"
        )
    )

    result_message = (
        await confirmed_channel.send(
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
    )

    application[
        "result_message_id"
    ] = result_message.id

    application[
        "confirmed_message_sent"
    ] = True

    application[
        "status"
    ] = "interview_running"

    DATA[
        "applications"
    ][
        application[
            "application_id"
        ]
    ] = application

    save_data()

    # Planung sperren, damit danach kein zweiter Termin erzeugt wird
    planning_message_id = application.get(
        "interview_message_id"
    )

    planning_channel = guild.get_channel(
        INTERVIEW_PLANNING_CHANNEL_ID
    )

    if (
        planning_message_id
        and isinstance(
            planning_channel,
            discord.TextChannel,
        )
    ):

        try:

            planning_message = (
                await planning_channel.fetch_message(
                    planning_message_id
                )
            )

            await planning_message.edit(
                embed=build_interview_embed(
                    guild,
                    application,
                ),
                view=None,
            )

        except discord.HTTPException:

            pass


# ============================================================
# INTERVIEW FAILED MODAL
# ============================================================

class InterviewFailedModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Gespräch nicht bestanden"
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

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                (
                    "❌ Nur das zuständige Gesprächsteam "
                    "darf das Ergebnis festlegen."
                ),
                ephemeral=True,
            )

            return

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Ergebnisnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_result_message(
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

        applicant = (
            interaction.guild.get_member(
                application[
                    "user_id"
                ]
            )
        )

        reason = str(
            self.reason.value
        ).strip()

        if applicant:

            await remove_role_safe(
                applicant,
                APPLICATION_ACCEPTED_ROLE_ID,
                (
                    "EHRP Recruitment: "
                    "Bewerbungsgespräch nicht bestanden"
                ),
            )

        application[
            "status"
        ] = "failed"

        application[
            "interview_result"
        ] = "failed"

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

        failed_text = (
            "# ❌ Bewerbungsgespräch nicht bestanden\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank, dass Sie sich die Zeit "
            "für das Bewerbungsgespräch bei "
            "**EHRP/VC** genommen haben.\n\n"

            "Nach Auswertung des Gespräches müssen "
            "wir Ihnen leider mitteilen, dass Sie "
            "das Bewerbungsgespräch zum jetzigen "
            "Zeitpunkt **nicht bestanden haben**.\n\n"

            "## 📋 Grund\n\n"

            f"**- {reason}**\n\n"

            "Diese Entscheidung bedeutet nicht, "
            "dass eine spätere Bewerbung grundsätzlich "
            "ausgeschlossen ist.\n\n"

            "Sie können sich zu einem späteren Zeitpunkt "
            "erneut bewerben.\n\n"

            "Wir bedanken uns für Ihr Verständnis "
            "und wünschen Ihnen weiterhin viel Spaß "
            "auf **EHRP/VC**.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        if applicant:

            try:

                await applicant.send(
                    failed_text
                )

            except discord.HTTPException:

                pass

        embed = discord.Embed(
            title=(
                "❌ BEWERBUNGSGESPRÄCH "
                "NICHT BESTANDEN"
            ),
            description=(
                "# Bewerbungsverfahren beendet\n\n"

                f"**Bewerber:** "
                f"<@{application['user_id']}>\n"

                f"**Gesprächsführer:** "
                f"<@{application['interviewer_id']}>\n"

                f"**Entscheidung von:** "
                f"{interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📋 Grund\n\n"

                f"{reason}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "**Status:** 🔴 Nicht aufgenommen"
            ),
            color=ERROR_COLOR,
        )

        embed.set_footer(
            text=(
                "EHRP/VC | Recruitment System"
            )
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )


# ============================================================
# INTERVIEW RESULT VIEW
# ============================================================

class InterviewResultView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )


    @discord.ui.button(
        label="Gespräch bestanden",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ehrp:application:interview_passed",
    )
    async def interview_passed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                (
                    "❌ Nur das zuständige Gesprächsteam "
                    "darf das Ergebnis festlegen."
                ),
                ephemeral=True,
            )

            return

        if not interaction.message:

            await interaction.response.send_message(
                "❌ Ergebnisnachricht nicht gefunden.",
                ephemeral=True,
            )

            return

        app_id, application = (
            find_application_by_result_message(
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
                (
                    "❌ Der Bewerber befindet sich "
                    "nicht mehr auf dem Server."
                ),
                ephemeral=True,
            )

            return

        # Erst neue Rolle hinzufügen
        role_added = (
            await add_role_safe(
                applicant,
                TEAM_ACCEPTED_ROLE_ID,
                (
                    "EHRP Recruitment: "
                    "Bewerbungsgespräch bestanden"
                ),
            )
        )

        if not role_added:

            await interaction.response.send_message(
                (
                    "❌ Die neue Rolle konnte nicht "
                    "vergeben werden.\n\n"
                    "Bitte prüfen Sie die Rollen-Hierarchie."
                ),
                ephemeral=True,
            )

            return

        # Danach Bewerberrolle entfernen
        await remove_role_safe(
            applicant,
            APPLICATION_ACCEPTED_ROLE_ID,
            (
                "EHRP Recruitment: "
                "Bewerbungsverfahren abgeschlossen"
            ),
        )

        application[
            "status"
        ] = "completed"

        application[
            "interview_result"
        ] = "passed"

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

        passed_text = (
            "# 🎉 Bewerbungsgespräch bestanden\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "wir freuen uns, Ihnen mitteilen zu können, "
            "dass Sie Ihr Bewerbungsgespräch bei "
            "**EHRP/VC erfolgreich bestanden haben**.\n\n"

            "Damit wurde Ihr Bewerbungsverfahren "
            "erfolgreich abgeschlossen.\n\n"

            "Ihre neue Rolle wurde automatisch vergeben.\n\n"

            "Wir gratulieren Ihnen herzlich und wünschen "
            "Ihnen viel Erfolg bei Ihren kommenden Aufgaben.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )

        try:

            await applicant.send(
                passed_text
            )

        except discord.HTTPException:

            pass

        embed = discord.Embed(
            title=(
                "🎉 BEWERBUNG ERFOLGREICH "
                "ABGESCHLOSSEN"
            ),
            description=(
                "# ✅ Bewerbungsgespräch bestanden\n\n"

                f"**Bewerber:** "
                f"{applicant.mention}\n"

                f"**Gesprächsführer:** "
                f"<@{application['interviewer_id']}>\n"

                f"**Entscheidung bestätigt von:** "
                f"{interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 🔐 Rollenänderung\n\n"

                f"<@&{APPLICATION_ACCEPTED_ROLE_ID}> "
                "❌ entfernt\n"

                f"<@&{TEAM_ACCEPTED_ROLE_ID}> "
                "✅ hinzugefügt\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📡 Status\n\n"

                "**🟢 Bewerbungsverfahren "
                "erfolgreich abgeschlossen**"
            ),
            color=SUCCESS_COLOR,
        )

        embed.set_footer(
            text=(
                "EHRP/VC | Recruitment System"
            )
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )


    @discord.ui.button(
        label="Nicht bestanden",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ehrp:application:interview_failed",
    )
    async def interview_failed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if not is_interview_staff(
            interaction.user
        ):

            await interaction.response.send_message(
                (
                    "❌ Nur das zuständige Gesprächsteam "
                    "darf das Ergebnis festlegen."
                ),
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            InterviewFailedModal()
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

        # Persistent views
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
    # NORMAL DM LISTENER
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):

        if message.author.bot:
            return

        # Nur DMs
        if message.guild is not None:
            return

        try:

            handled = await process_application_dm(
                self.bot,
                message,
            )

            if handled:
                return

        except Exception as error:

            print(
                "❌ Fehler im DM Recruitment Flow: "
                f"{type(error).__name__}: {error}"
            )

            try:

                await message.channel.send(
                    (
                        "❌ Bei der Verarbeitung Ihrer "
                        "Bewerbungsantwort ist ein Fehler aufgetreten.\n\n"
                        "Bitte versuchen Sie es erneut."
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
            "Erstellt das EHRP/VC Bewerbungsportal."
        ),
    )
    async def bewerbung_panel(
        self,
        interaction: discord.Interaction,
    ):

        if not isinstance(
            interaction.user,
            discord.Member,
        ):

            return

        if (
            not is_interview_staff(
                interaction.user
            )
            and not interaction.user.guild_permissions.administrator
        ):

            await interaction.response.send_message(
                (
                    "❌ Sie dürfen das "
                    "Bewerbungsportal nicht erstellen."
                ),
                ephemeral=True,
            )

            return

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                "❌ Dieser Befehl funktioniert nur in einem Text-Channel.",
                ephemeral=True,
            )

            return

        await interaction.channel.send(
            embed=build_application_panel(),
            view=ApplicationPanelView(),
        )

        await interaction.response.send_message(
            (
                "✅ Das Bewerbungsportal wurde "
                "erfolgreich erstellt."
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

        if (
            not is_interview_staff(
                interaction.user
            )
            and not interaction.user.guild_permissions.administrator
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
                "ab sofort wieder eingereicht werden."
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

        if (
            not is_interview_staff(
                interaction.user
            )
            and not interaction.user.guild_permissions.administrator
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

                "Neue Teambewerbungen können derzeit "
                "nicht eingereicht werden."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNG_STATUS
    # ========================================================

    @app_commands.command(
        name="bewerbung_status",
        description=(
            "Zeigt den Status des Recruitment Systems."
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

        if (
            not is_interview_staff(
                interaction.user
            )
            and not interaction.user.guild_permissions.administrator
        ):

            await interaction.response.send_message(
                "❌ Keine Berechtigung.",
                ephemeral=True,
            )

            return

        applications = DATA[
            "applications"
        ]

        total = len(
            applications
        )

        pending = sum(
            1
            for application
            in applications.values()
            if application.get(
                "status"
            )
            in {
                "pending",
                "claimed",
            }
        )

        interviews = sum(
            1
            for application
            in applications.values()
            if application.get(
                "status"
            )
            in {
                "interview_planning",
                "interview_running",
            }
        )

        completed = sum(
            1
            for application
            in applications.values()
            if application.get(
                "status"
            )
            == "completed"
        )

        failed = sum(
            1
            for application
            in applications.values()
            if application.get(
                "status"
            )
            in {
                "rejected",
                "failed",
            }
        )

        active_dm_sessions = len(
            DATA[
                "sessions"
            ]
        )

        if DATA.get(
            "applications_open",
            True,
        ):

            open_status = (
                "🟢 Geöffnet"
            )

        else:

            open_status = (
                "🔴 Geschlossen"
            )

        embed = discord.Embed(
            title=(
                "⚙️ EHRP/VC | RECRUITMENT SYSTEM"
            ),
            description=(
                "# Systemstatus\n\n"

                f"**Bewerbungen:** "
                f"{open_status}\n\n"

                f"💬 **Laufende DM-Bewerbungen:** "
                f"{active_dm_sessions}\n"

                f"📨 **Eingereichte Bewerbungen:** "
                f"{total}\n"

                f"🟡 **Zu bearbeiten:** "
                f"{pending}\n"

                f"📞 **Gesprächsphase:** "
                f"{interviews}\n"

                f"✅ **Aufgenommen:** "
                f"{completed}\n"

                f"❌ **Abgelehnt / nicht bestanden:** "
                f"{failed}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "🟢 DM-Bewerbungssystem: Online\n"
                "🟢 Automatische nächste Frage: Aktiv\n"
                "🟢 Antwortprüfung: Aktiv\n"
                "🟢 Interne Bewerbungsprüfung: Online\n"
                "🟢 Automatische Ablehnungs-DM: Aktiv\n"
                "🟢 Rollen-Automation: Online\n"
                "🟢 Termin-System: Online\n"
                "🟢 Doppelte Terminbestätigung: Aktiv\n"
                "🟢 Gesprächsauswertung: Online"
            ),
            color=SUCCESS_COLOR,
        )

        embed.set_footer(
            text=(
                "EHRP/VC | Recruitment System"
            )
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
