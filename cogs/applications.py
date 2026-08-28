from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# EHRP/VC | RECRUITMENT SYSTEM
# ============================================================

SYSTEM_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
INFO_COLOR = 0x3498DB


# ============================================================
# CHANNELS
# ============================================================

# Fertige Bewerbungen landen hier
APPLICATION_REVIEW_CHANNEL_ID = 1526942850778923181

# Hier findet nach Annahme die Terminvereinbarung statt
INTERVIEW_PLANNING_CHANNEL_ID = 1543000219321503844

# Hier wird der final bestätigte Gesprächstermin gepostet
CONFIRMED_INTERVIEW_CHANNEL_ID = 1526951239269744870


# ============================================================
# ROLES
# ============================================================

# Rolle der Personen, die Bewerbungen / Gespräche bearbeiten
INTERVIEW_ROLE_ID = 1526955827770949793

# Wird vergeben, sobald die schriftliche Bewerbung angenommen wurde
APPLICATION_ACCEPTED_ROLE_ID = 1526957615765127412

# Wird vergeben, wenn das Bewerbungsgespräch bestanden wurde
TEAM_ACCEPTED_ROLE_ID = 1526957502078652496


# ============================================================
# DATA
# ============================================================

DATA_FILE = "applications_data.json"


# ============================================================
# FRAGEN
# ============================================================

QUESTIONS = [
    {
        "title": "Wie alt sind Sie?",
        "category": "👤 Persönliche Angaben",
        "placeholder": "Bitte geben Sie Ihr Alter an.",
        "min_length": 1,
        "max_length": 3,
        "long": False,
        "type": "age",
    },

    {
        "title": "Wie lautet Ihr Roblox-Name?",
        "category": "👤 Persönliche Angaben",
        "placeholder": "Ihr vollständiger Roblox-Benutzername.",
        "min_length": 2,
        "max_length": 100,
        "long": False,
    },

    {
        "title": "Seit wann spielen Sie Notruf Hamburg?",
        "category": "👤 Persönliche Angaben",
        "placeholder": "Zum Beispiel: Seit ca. 1 Jahr.",
        "min_length": 3,
        "max_length": 300,
        "long": False,
    },

    {
        "title": "Wie viele Stunden pro Woche können Sie ungefähr auf EHRP/VC aktiv sein?",
        "category": "👤 Persönliche Angaben",
        "placeholder": "Zum Beispiel: ca. 15–20 Stunden.",
        "min_length": 2,
        "max_length": 200,
        "long": False,
    },

    {
        "title": "Hatten Sie bereits Erfahrung als Teammitglied auf einem anderen RP-Server?",
        "category": "🧩 Erfahrung",
        "placeholder": (
            "Falls ja: Wo und welche Aufgaben hatten Sie? "
            "Falls nein: Nein."
        ),
        "min_length": 3,
        "max_length": 1000,
        "long": True,
    },

    {
        "title": "Warum möchten Sie Teil des EHRP/VC-Teams werden?",
        "category": "💬 Motivation",
        "placeholder": "Beschreiben Sie Ihre Motivation ausführlich.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": "Warum sollten wir gerade Sie auswählen?",
        "category": "💬 Motivation",
        "placeholder": "Was unterscheidet Sie von anderen Bewerbern?",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": "Welche Stärken bringen Sie für die Arbeit im Team mit?",
        "category": "💬 Motivation",
        "placeholder": "Nennen und erklären Sie Ihre wichtigsten Stärken.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": "Welche Schwächen haben Sie und wie gehen Sie damit um?",
        "category": "💬 Motivation",
        "placeholder": "Bitte beantworten Sie die Frage ehrlich.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": "Ein Spieler beleidigt Sie nach einer Sanktion. Wie reagieren Sie?",
        "category": "🧠 Situationsfragen",
        "placeholder": "Beschreiben Sie Ihr Vorgehen.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": (
            "Sie sehen, dass ein anderes Teammitglied seine Rechte "
            "ausnutzt oder einen Spieler unfair behandelt. Wie handeln Sie?"
        ),
        "category": "🧠 Situationsfragen",
        "placeholder": "Beschreiben Sie Ihr Vorgehen.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": (
            "Ein guter Freund von Ihnen verstößt eindeutig gegen "
            "das Regelwerk. Wie gehen Sie damit um?"
        ),
        "category": "🧠 Situationsfragen",
        "placeholder": "Beschreiben Sie Ihr Vorgehen.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": (
            "Zwei Spieler beschuldigen sich gegenseitig und Sie können "
            "zunächst nicht feststellen, wer die Wahrheit sagt. "
            "Wie gehen Sie vor?"
        ),
        "category": "🧠 Situationsfragen",
        "placeholder": "Beschreiben Sie Ihr Vorgehen.",
        "min_length": 30,
        "max_length": 1500,
        "long": True,
    },

    {
        "title": "Gibt es noch etwas, das wir über Sie wissen sollten?",
        "category": "📝 Abschluss",
        "placeholder": "Falls nicht, schreiben Sie bitte „Nein“.",
        "min_length": 3,
        "max_length": 1500,
        "long": True,
    },
]


# ============================================================
# DEFAULT DATA
# ============================================================

DEFAULT_DATA = {
    "applications_open": True,
    "counter": 0,
    "applications": {},
    "sessions": {},
}


# ============================================================
# LOAD / SAVE
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
            f"❌ Recruitment Daten konnten nicht geladen werden: {error}"
        )

        return {
            "applications_open": True,
            "counter": 0,
            "applications": {},
            "sessions": {},
        }


DATA = load_data()


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
            f"❌ Recruitment Daten konnten nicht gespeichert werden: {error}"
        )


# ============================================================
# SESSION HELPERS
# ============================================================

def get_session(
    user_id: int,
) -> Optional[dict]:

    return DATA["sessions"].get(
        str(user_id)
    )


def set_session(
    user_id: int,
    session: dict,
):

    DATA["sessions"][
        str(user_id)
    ] = session

    save_data()


def remove_session(
    user_id: int,
):

    DATA["sessions"].pop(
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

    for app_id, application in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "review_message_id"
            )
            == message_id
        ):
            return (
                app_id,
                application,
            )

    return (
        None,
        None,
    )


def find_application_by_interview_message(
    message_id: int,
):

    for app_id, application in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "interview_message_id"
            )
            == message_id
        ):
            return (
                app_id,
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
# STAFF CHECK
# ============================================================

def is_interview_staff(
    member: discord.Member,
) -> bool:

    return any(
        role.id == INTERVIEW_ROLE_ID
        for role in member.roles
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
        f"EHRP-"
        f"{DATA['counter']:04d}"
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
            f"❌ Rolle konnte nicht hinzugefügt werden "
            f"({role_id}): {error}"
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
            f"❌ Rolle konnte nicht entfernt werden "
            f"({role_id}): {error}"
        )

        return False


# ============================================================
# APPLICATION PANEL
# ============================================================

def build_application_panel() -> discord.Embed:

    if DATA.get(
        "applications_open",
        True,
    ):
        status = (
            "🟢 **GEÖFFNET**"
        )
    else:
        status = (
            "🔴 **GESCHLOSSEN**"
        )

    embed = discord.Embed(
        title="📨 EHRP/VC • TEAM RECRUITMENT",
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
            "• Sehr gute Rechtschreib- und Grammatikkenntnisse\n"
            "• Kommunikation in der **Sie-Form**\n"
            "• Ca. **15 Stunden pro Woche** verfügbar\n"
            "• Grundkenntnisse im Roleplay\n"
            "• Sicherer Umgang mit Discord\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## ⚠️ Wichtige Hinweise\n\n"

            "• Bewerbungen müssen vollständig und ehrlich ausgefüllt werden.\n"
            "• Sehr kurze oder offensichtlich lustlose Antworten können "
            "zur Ablehnung führen.\n"
            "• Mehrfachbewerbungen sind nicht möglich.\n"
            "• Eine Bewerbung garantiert keine Aufnahme in das Team.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 📡 Bewerbungsstatus\n\n"

            f"{status}\n\n"

            "Mit dem Button unten starten Sie den Bewerbungsprozess."
        ),
        color=SYSTEM_COLOR,
    )

    embed.set_footer(
        text="EHRP/VC | Recruitment System"
    )

    return embed

# ============================================================
# START APPLICATION
# ============================================================

class ApplicationPanelView(discord.ui.View):

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
            return

        if not DATA.get(
            "applications_open",
            True,
        ):
            await interaction.response.send_message(
                "# 🔴 Bewerbungen geschlossen\n\n"
                "Derzeit werden keine neuen Teambewerbungen angenommen.",
                ephemeral=True,
            )
            return

        if has_open_application(
            interaction.user.id
        ):
            await interaction.response.send_message(
                "# ⚠️ Bewerbung bereits vorhanden\n\n"
                "Sie besitzen bereits eine offene oder laufende Bewerbung.\n\n"
                "Bitte warten Sie, bis diese vollständig abgeschlossen wurde.",
                ephemeral=True,
            )
            return

        session = {
            "current_question": 0,
            "answers": {},
            "requirements_confirmed": False,
        }

        set_session(
            interaction.user.id,
            session,
        )

        embed = discord.Embed(
            title="📋 Voraussetzungen bestätigen",
            description=(
                "# EHRP/VC • TEAMBEWERBUNG\n\n"

                "Bevor Ihre Bewerbung beginnt, müssen Sie bestätigen, "
                "dass Sie die Voraussetzungen vollständig gelesen haben.\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📋 Voraussetzungen\n\n"

                "• Mindestalter: **13 Jahre**\n"
                "• Funktionierendes Mikrofon\n"
                "• Aktiver Discord-Account\n"
                "• Sehr gute Rechtschreib- und Grammatikkenntnisse\n"
                "• Kommunikation in der **Sie-Form**\n"
                "• Ca. **15 Stunden pro Woche** verfügbar\n"
                "• Grundkenntnisse im Roleplay\n"
                "• Sicherer Umgang mit Discord\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## ⚠️ Bestätigung\n\n"

                "Mit Ihrer Bestätigung erklären Sie, dass Sie die "
                "oben genannten Voraussetzungen vollständig gelesen "
                "haben und grundsätzlich erfüllen.\n\n"

                "Erst danach beginnt die eigentliche Bewerbung."
            ),
            color=WARNING_COLOR,
        )

        embed.set_footer(
            text="EHRP/VC | Recruitment System"
        )

        await interaction.response.send_message(
            embed=embed,
            view=RequirementsView(),
            ephemeral=True,
        )


# ============================================================
# REQUIREMENTS CONFIRMATION
# ============================================================

class RequirementsView(discord.ui.View):

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
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.\n"
                "Bitte starten Sie die Bewerbung erneut.",
                ephemeral=True,
            )
            return

        session[
            "requirements_confirmed"
        ] = True

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=build_question_embed(
                interaction.user.id
            ),
            view=QuestionView(),
        )


# ============================================================
# QUESTION EMBED
# ============================================================

def build_question_embed(
    user_id: int,
) -> discord.Embed:

    session = get_session(
        user_id
    )

    if not session:
        return discord.Embed(
            title="❌ Sitzung nicht gefunden",
            description=(
                "Ihre Bewerbungssitzung ist nicht mehr verfügbar."
            ),
            color=ERROR_COLOR,
        )

    index = int(
        session.get(
            "current_question",
            0,
        )
    )

    question = QUESTIONS[
        index
    ]

    answer = session[
        "answers"
    ].get(
        str(index)
    )

    progress = int(
        (
            (index + 1)
            / len(QUESTIONS)
        )
        * 100
    )

    progress_bar_length = 10

    filled = round(
        progress
        / 100
        * progress_bar_length
    )

    progress_bar = (
        "🟩" * filled
        + "⬜" * (
            progress_bar_length
            - filled
        )
    )

    description = (
        f"# Frage {index + 1} von {len(QUESTIONS)}\n\n"

        f"## {question['category']}\n\n"

        f"### {question['title']}\n\n"
    )

    if answer:
        description += (
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## ✅ Ihre Antwort\n\n"

            f"{answer}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Ihre Antwort wurde erfolgreich gespeichert.\n\n"
            "Sie können die Antwort noch ändern oder mit "
            "**Weiter** zur nächsten Frage wechseln."
        )
    else:
        description += (
            "Bitte beantworten Sie diese Frage vollständig und ehrlich.\n\n"

            "Klicken Sie unten auf **Antwort eingeben**, "
            "um Ihre Antwort einzutragen."
        )

    embed = discord.Embed(
        title="📨 EHRP/VC • TEAMBEWERBUNG",
        description=description,
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

    embed.set_footer(
        text=(
            "EHRP/VC | Recruitment System • "
            f"Frage {index + 1}/{len(QUESTIONS)}"
        )
    )

    return embed


# ============================================================
# ANSWER MODAL
# ============================================================

class AnswerModal(discord.ui.Modal):

    def __init__(
        self,
        user_id: int,
    ):

        session = get_session(
            user_id
        )

        index = int(
            session[
                "current_question"
            ]
        )

        self.question_index = (
            index
        )

        question = QUESTIONS[
            index
        ]

        super().__init__(
            title=(
                f"Frage {index + 1} "
                f"von {len(QUESTIONS)}"
            )
        )

        current_answer = (
            session[
                "answers"
            ].get(
                str(index)
            )
        )

        if question[
            "long"
        ]:
            style = (
                discord.TextStyle.paragraph
            )
        else:
            style = (
                discord.TextStyle.short
            )

        self.answer_input = (
            discord.ui.TextInput(
                label=(
                    question[
                        "title"
                    ][:45]
                ),
                placeholder=(
                    question[
                        "placeholder"
                    ][:100]
                ),
                style=style,
                required=True,
                min_length=(
                    question[
                        "min_length"
                    ]
                ),
                max_length=(
                    question[
                        "max_length"
                    ]
                ),
                default=(
                    current_answer
                    if current_answer
                    else None
                ),
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
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        question = QUESTIONS[
            self.question_index
        ]

        answer = str(
            self.answer_input.value
        ).strip()


        # ====================================================
        # AGE CHECK
        # ====================================================

        if question.get(
            "type"
        ) == "age":

            try:
                age = int(
                    answer
                )

            except ValueError:
                await interaction.response.send_message(
                    "❌ Bitte geben Sie Ihr Alter ausschließlich als Zahl an.",
                    ephemeral=True,
                )
                return

            if age < 13:

                remove_session(
                    interaction.user.id
                )

                await interaction.response.send_message(
                    "# ❌ Bewerbung beendet\n\n"

                    "Leider erfüllen Sie aktuell nicht die "
                    "Mindestvoraussetzungen für eine Bewerbung bei "
                    "**EHRP/VC**.\n\n"

                    "Das Mindestalter beträgt **13 Jahre**.\n\n"

                    "Ihre Bewerbung wurde daher automatisch beendet.",
                    ephemeral=True,
                )
                return


        # ====================================================
        # SAVE ANSWER
        # ====================================================

        session[
            "answers"
        ][
            str(
                self.question_index
            )
        ] = answer

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=build_question_embed(
                interaction.user.id
            ),
            view=QuestionView(),
        )


# ============================================================
# QUESTION BUTTONS
# ============================================================

class QuestionView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=1800
        )


    # ========================================================
    # ANSWER
    # ========================================================

    @discord.ui.button(
        label="Antwort eingeben",
        emoji="✍️",
        style=discord.ButtonStyle.primary,
    )
    async def answer_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:
            await interaction.response.send_message(
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            AnswerModal(
                interaction.user.id
            )
        )


    # ========================================================
    # NEXT QUESTION
    # ========================================================

    @discord.ui.button(
        label="Weiter",
        emoji="➡️",
        style=discord.ButtonStyle.success,
    )
    async def next_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:
            await interaction.response.send_message(
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        current_question = int(
            session[
                "current_question"
            ]
        )

        if (
            str(
                current_question
            )
            not in session[
                "answers"
            ]
        ):
            await interaction.response.send_message(
                "⚠️ Sie müssen die aktuelle Frage zuerst beantworten.",
                ephemeral=True,
            )
            return


        # ====================================================
        # LAST QUESTION → FINAL REVIEW
        # ====================================================

        if (
            current_question
            >= len(QUESTIONS) - 1
        ):
            await interaction.response.edit_message(
                embed=build_final_review_embed(
                    interaction.user.id
                ),
                view=FinalReviewView(),
            )
            return


        # ====================================================
        # GO NEXT
        # ====================================================

        session[
            "current_question"
        ] = (
            current_question
            + 1
        )

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=build_question_embed(
                interaction.user.id
            ),
            view=QuestionView(),
        )


    # ========================================================
    # CHANGE ANSWER
    # ========================================================

    @discord.ui.button(
        label="Antwort ändern",
        emoji="✏️",
        style=discord.ButtonStyle.secondary,
    )
    async def change_answer(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        session = get_session(
            interaction.user.id
        )

        if not session:
            await interaction.response.send_message(
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )
            return

        current_question = int(
            session[
                "current_question"
            ]
        )

        if (
            str(
                current_question
            )
            not in session[
                "answers"
            ]
        ):
            await interaction.response.send_message(
                "⚠️ Sie haben für diese Frage noch keine Antwort gespeichert.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            AnswerModal(
                interaction.user.id
            )
        )

  # ============================================================
# FINAL REVIEW
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

            "Sie haben alle Fragen erfolgreich beantwortet.\n\n"

            "Bitte prüfen Sie Ihre Angaben vor dem endgültigen Absenden.\n\n"

            "Mit dem Absenden wird Ihre Bewerbung verbindlich "
            "an das zuständige Team von **EHRP/VC** weitergeleitet.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Falls Sie noch eine Antwort ändern möchten, "
            "wählen Sie die entsprechende Frage unten aus."
        ),
        color=SUCCESS_COLOR,
    )

    if session:

        for index, question in enumerate(
            QUESTIONS
        ):

            answer = session[
                "answers"
            ].get(
                str(index),
                "Keine Antwort",
            )

            shortened = answer

            if len(
                shortened
            ) > 180:

                shortened = (
                    shortened[:177]
                    + "..."
                )

            embed.add_field(
                name=(
                    f"{index + 1}. "
                    f"{question['title']}"
                ),
                value=shortened,
                inline=False,
            )

    embed.set_footer(
        text="EHRP/VC | Recruitment System"
    )

    return embed


# ============================================================
# SELECT QUESTION TO EDIT
# ============================================================

class ReviewQuestionSelect(
    discord.ui.Select
):

    def __init__(
        self,
    ):

        options = [
            discord.SelectOption(
                label=(
                    f"Frage {index + 1}"
                ),
                description=(
                    question[
                        "title"
                    ][:90]
                ),
                value=str(
                    index
                ),
            )
            for index, question
            in enumerate(
                QUESTIONS
            )
        ]

        super().__init__(
            placeholder=(
                "Antwort auswählen und bearbeiten …"
            ),
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
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )

            return

        session[
            "current_question"
        ] = int(
            self.values[0]
        )

        set_session(
            interaction.user.id,
            session,
        )

        await interaction.response.edit_message(
            embed=build_question_embed(
                interaction.user.id
            ),
            view=QuestionView(),
        )


# ============================================================
# FINAL REVIEW VIEW
# ============================================================

class FinalReviewView(
    discord.ui.View
):

    def __init__(
        self,
    ):

        super().__init__(
            timeout=1800
        )

        self.add_item(
            ReviewQuestionSelect()
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
                "❌ Ihre Bewerbungssitzung wurde nicht gefunden.",
                ephemeral=True,
            )

            return


        # ====================================================
        # CHECK ALL ANSWERS
        # ====================================================

        if len(
            session[
                "answers"
            ]
        ) != len(
            QUESTIONS
        ):

            await interaction.response.send_message(
                "❌ Bitte beantworten Sie zuerst alle Fragen.",
                ephemeral=True,
            )

            return


        # ====================================================
        # GET REVIEW CHANNEL
        # ====================================================

        review_channel = (
            interaction.guild.get_channel(
                APPLICATION_REVIEW_CHANNEL_ID
            )
        )

        if not isinstance(
            review_channel,
            discord.TextChannel,
        ):

            await interaction.response.send_message(
                "❌ Der interne Bewerbungs-Channel wurde nicht gefunden.",
                ephemeral=True,
            )

            return


        # ====================================================
        # CREATE APPLICATION
        # ====================================================

        app_id = (
            application_number()
        )

        application = {
            "application_id": app_id,

            "user_id":
                interaction.user.id,

            "answers":
                session[
                    "answers"
                ],

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

            "interview_message_id":
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

            "confirmed_message_sent":
                False,

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
            app_id
        ] = application

        save_data()


        # ====================================================
        # SEND REVIEW MESSAGE
        # ====================================================

        review_message = (
            await review_channel.send(
                content=(
                    f"📨 **Neue Teambewerbung:** "
                    f"{interaction.user.mention}"
                ),
                embed=build_review_embed(
                    interaction.guild,
                    application,
                ),
                view=ApplicationReviewView(),
                allowed_mentions=(
                    discord.AllowedMentions(
                        users=True,
                        roles=False,
                        everyone=False,
                    )
                ),
            )
        )

        application[
            "review_message_id"
        ] = review_message.id

        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()

        remove_session(
            interaction.user.id
        )


        # ====================================================
        # USER CONFIRMATION
        # ====================================================

        result = discord.Embed(
            title="✅ Bewerbung eingegangen",
            description=(
                "# Vielen Dank für Ihre Bewerbung\n\n"

                "Ihre Bewerbung wurde erfolgreich an das "
                "zuständige Team von **EHRP/VC** weitergeleitet.\n\n"

                f"**Bewerbungs-ID:** `{app_id}`\n"
                "**Status:** 🟡 Ausstehend\n\n"

                "Bitte fragen Sie nicht nach dem aktuellen "
                "Bearbeitungsstand.\n\n"

                "Sobald eine Entscheidung getroffen wurde, "
                "werden Sie automatisch informiert."
            ),
            color=SUCCESS_COLOR,
        )

        result.set_footer(
            text="EHRP/VC | Recruitment System"
        )

        await interaction.response.edit_message(
            embed=result,
            view=None,
        )


# ============================================================
# REVIEW EMBED
# ============================================================

def build_review_embed(
    guild: discord.Guild,
    application: dict,
) -> discord.Embed:

    member = guild.get_member(
        application[
            "user_id"
        ]
    )

    if member:
        member_text = (
            member.mention
        )
    else:
        member_text = (
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

        "interview_confirmed":
            "🟢 GESPRÄCH TERMINIERT",

        "interview_running":
            "🟣 GESPRÄCH AUSSTEHEND",

        "completed":
            "✅ AUFGENOMMEN",

        "failed":
            "❌ GESPRÄCH NICHT BESTANDEN",
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
            "Nicht übernommen"
        )


    embed = discord.Embed(
        title=(
            "📨 TEAMBEWERBUNG • "
            f"{application['application_id']}"
        ),
        description=(
            "# Neue Teambewerbung\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"**Person:** {member_text}\n"
            f"**Discord-ID:** "
            f"`{application['user_id']}`\n\n"

            "## 📡 Bearbeitung\n\n"

            f"**Status:** "
            f"{status_map.get(application['status'], application['status'])}\n"

            f"**Bearbeiter:** "
            f"{claimed_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=WARNING_COLOR,
    )


    # ========================================================
    # ANSWERS
    # ========================================================

    for index, question in enumerate(
        QUESTIONS
    ):

        answer = application[
            "answers"
        ].get(
            str(index),
            "Keine Antwort",
        )

        embed.add_field(
            name=(
                f"{index + 1}. "
                f"{question['title']}"
            ),
            value=answer[:1024],
            inline=False,
        )


    if member:

        embed.set_thumbnail(
            url=(
                member
                .display_avatar
                .url
            )
        )


    embed.set_footer(
        text="EHRP/VC | Recruitment System"
    )

    return embed


# ============================================================
# REJECTION MODAL
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

        self.reason = (
            discord.ui.TextInput(
                label=(
                    "Grund der Ablehnung"
                ),
                placeholder=(
                    "Bitte geben Sie den Ablehnungsgrund an."
                ),
                style=(
                    discord.TextStyle.paragraph
                ),
                min_length=5,
                max_length=1000,
            )
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
                "❌ Sie dürfen diese Bewerbung nicht bearbeiten.",
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


        application[
            "status"
        ] = "rejected"

        application[
            "rejected_by"
        ] = interaction.user.id

        application[
            "rejection_reason"
        ] = str(
            self.reason.value
        ).strip()


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


        rejection_text = (
            "# ❌ Bewerbung abgelehnt\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Bewerbung und das damit "
            "verbundene Interesse an einer Position im Team "
            "von **EHRP/VC**.\n\n"

            "Nach sorgfältiger Prüfung müssen wir Ihnen leider "
            "mitteilen, dass Ihre Bewerbung zum jetzigen Zeitpunkt "
            "**abgelehnt wurde**.\n\n"

            "## 📋 Grund der Ablehnung\n\n"

            f"**- {application['rejection_reason']}**\n\n"

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


        await interaction.response.edit_message(
            embed=build_review_embed(
                interaction.guild,
                application,
            ),
            view=None,
        )


# ============================================================
# REVIEW BUTTONS
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
            "claimed_by"
        ):

            await interaction.response.send_message(
                (
                    "⚠️ Diese Bewerbung wurde bereits von "
                    f"<@{application['claimed_by']}> übernommen."
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
            embed=build_review_embed(
                interaction.guild,
                application,
            ),
            view=self,
        )


    # ========================================================
    # ACCEPT
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


        if application[
            "status"
        ] in {
            "interview_planning",
            "interview_confirmed",
            "interview_running",
            "completed",
        }:

            await interaction.response.send_message(
                "⚠️ Diese Bewerbung wurde bereits angenommen.",
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


        if applicant is None:

            await interaction.response.send_message(
                "❌ Der Bewerber befindet sich nicht mehr auf dem Server.",
                ephemeral=True,
            )

            return


        # ====================================================
        # GIVE APPLICATION ACCEPTED ROLE
        # ====================================================

        role_success = await add_role_safe(
            applicant,
            APPLICATION_ACCEPTED_ROLE_ID,
            (
                "EHRP Recruitment: "
                "Schriftliche Bewerbung angenommen"
            ),
        )


        if not role_success:

            await interaction.response.send_message(
                (
                    "❌ Die Bewerbung konnte nicht vollständig angenommen werden.\n\n"
                    "Die Bewerberrolle konnte nicht vergeben werden. "
                    "Bitte prüfen Sie die Rollen-Hierarchie des Bots."
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


        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()


        # ====================================================
        # ACCEPTANCE MESSAGE
        # ====================================================

        acceptance_text = (
            "# ✅ Bewerbung angenommen\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank für Ihre Bewerbung und Ihr Interesse "
            "an einer Position im Team von **EHRP/VC**.\n\n"

            "Wir freuen uns, Ihnen mitteilen zu können, "
            "dass Ihre Bewerbung **angenommen wurde**.\n\n"

            "## 📞 Nächster Schritt: Bewerbungsgespräch\n\n"

            "Als nächsten Schritt bitten wir Sie, gemeinsam mit "
            "unserem zuständigen Gesprächsteam einen Termin für "
            "Ihr Bewerbungsgespräch zu vereinbaren.\n\n"

            "Im Kanal **Gespräch Termin** können sowohl Sie als auch "
            "das zuständige Team einen Termin vorschlagen.\n\n"

            "Ein Termin gilt erst dann als verbindlich, wenn "
            "**beide Seiten diesen bestätigt haben**.\n\n"

            "Sollten Sie einen vereinbarten Termin nicht wahrnehmen "
            "können, informieren Sie das Team bitte rechtzeitig.\n\n"

            "Wir freuen uns auf das Gespräch mit Ihnen und wünschen "
            "Ihnen weiterhin viel Erfolg.\n\n"

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
        # PLANNING CHANNEL
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
                    "⚠️ Bewerbung angenommen und Rolle vergeben, "
                    "aber der Gesprächs-Channel wurde nicht gefunden."
                ),
                ephemeral=True,
            )

            return


        interview_message = (
            await planning_channel.send(
                content=(
                    f"<@{application['user_id']}> "
                    f"<@&{INTERVIEW_ROLE_ID}>"
                ),
                embed=build_interview_embed(
                    interaction.guild,
                    application,
                ),
                view=InterviewPlanningView(),
                allowed_mentions=(
                    discord.AllowedMentions(
                        users=True,
                        roles=True,
                        everyone=False,
                    )
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


        await interaction.response.edit_message(
            embed=build_review_embed(
                interaction.guild,
                application,
            ),
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
                "❌ Sie dürfen keine Bewerbungen bearbeiten.",
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

    applicant_id = application["user_id"]

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


    # ========================================================
    # TERMIN
    # ========================================================

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
            "## 📅 Terminvereinbarung\n\n"
            "**Es wurde noch kein Termin vorgeschlagen.**\n\n"
            "Sowohl der Bewerber als auch das Gesprächsteam "
            "können unten einen Termin vorschlagen."
        )


    # ========================================================
    # CONFIRMATIONS
    # ========================================================

    if applicant_confirmed:
        applicant_status = (
            "✅ Bestätigt"
        )
    else:
        applicant_status = (
            "⏳ Noch nicht bestätigt"
        )


    if team_confirmed:
        team_status = (
            "✅ Bestätigt"
        )
    else:
        team_status = (
            "⏳ Noch nicht bestätigt"
        )


    if interviewer_id:

        interviewer_text = (
            f"<@{interviewer_id}>"
        )

    else:

        interviewer_text = (
            "Noch nicht festgelegt"
        )


    # ========================================================
    # FINAL STATUS
    # ========================================================

    if (
        applicant_confirmed
        and team_confirmed
    ):

        status_text = (
            "# 🟢 TERMIN VERBINDLICH BESTÄTIGT\n\n"
            "Der Termin wurde von beiden Seiten bestätigt."
        )

        color = (
            SUCCESS_COLOR
        )

    else:

        status_text = (
            "⚠️ Ein Termin gilt erst dann als verbindlich, "
            "wenn **Bewerber und Gesprächsteam bestätigt haben**."
        )

        color = (
            INFO_COLOR
        )


    embed = discord.Embed(
        title=(
            "📞 BEWERBUNGSGESPRÄCH • "
            f"{application['application_id']}"
        ),
        description=(
            "# Gesprächsplanung\n\n"

            "Die schriftliche Bewerbung wurde erfolgreich angenommen.\n\n"

            "Nun muss gemeinsam ein Termin für das "
            "Bewerbungsgespräch vereinbart werden.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"<@{applicant_id}>\n\n"

            "## 🧑‍💼 Gesprächsteam\n\n"

            f"<@&{INTERVIEW_ROLE_ID}>\n\n"

            f"**Gesprächsführer:** {interviewer_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{proposal_text}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 🔐 Bestätigungsstatus\n\n"

            f"**Bewerber:** {applicant_status}\n"
            f"**Gesprächsteam:** {team_status}\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            f"{status_text}"
        ),
        color=color,
    )

    embed.set_footer(
        text="EHRP/VC | Recruitment System"
    )

    return embed


# ============================================================
# INTERVIEW PROPOSAL MODAL
# ============================================================

class InterviewProposalModal(
    discord.ui.Modal
):

    def __init__(
        self,
    ):

        super().__init__(
            title="Gesprächstermin vorschlagen"
        )


        self.date_input = (
            discord.ui.TextInput(
                label="Datum",
                placeholder="z. B. 02.09.2026",
                min_length=8,
                max_length=10,
            )
        )


        self.time_input = (
            discord.ui.TextInput(
                label="Uhrzeit",
                placeholder="z. B. 18:30",
                min_length=4,
                max_length=5,
            )
        )


        self.note_input = (
            discord.ui.TextInput(
                label="Zusätzlicher Hinweis",
                placeholder=(
                    "Optional, z. B. "
                    "Ich kann zwischen 18:00 und 20:00 Uhr."
                ),
                style=(
                    discord.TextStyle.paragraph
                ),
                required=False,
                max_length=500,
            )
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


        # ====================================================
        # ACCESS CHECK
        # ====================================================

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


        if (
            not is_applicant
            and not is_team
        ):

            await interaction.response.send_message(
                "❌ Sie gehören nicht zu diesem Bewerbungsgespräch.",
                ephemeral=True,
            )

            return


        # ====================================================
        # DATE / TIME
        # ====================================================

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

            parsed_datetime = (
                datetime.strptime(
                    (
                        f"{proposal_date} "
                        f"{proposal_time}"
                    ),
                    "%d.%m.%Y %H:%M",
                )
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
                "❌ Der vorgeschlagene Termin liegt bereits in der Vergangenheit.",
                ephemeral=True,
            )

            return


        # ====================================================
        # SAVE NEW PROPOSAL
        # ====================================================

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


        # ====================================================
        # RESET OLD CONFIRMATIONS
        # ====================================================

        application[
            "applicant_confirmed"
        ] = False

        application[
            "team_confirmed"
        ] = False

        application[
            "confirmed_message_sent"
        ] = False


        # ====================================================
        # PROPOSER AUTOMATICALLY CONFIRMS OWN PROPOSAL
        # ====================================================

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


        # ====================================================
        # MAYBE BOTH ALREADY CONFIRMED
        # ====================================================

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
# FINAL CONFIRMED INTERVIEW MESSAGE
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
            "❌ Channel für bestätigte Bewerbungsgespräche "
            "wurde nicht gefunden."
        )

        return


    embed = discord.Embed(
        title="📅 BEWERBUNGSGESPRÄCH BESTÄTIGT",
        description=(
            "# ✅ Verbindlicher Gesprächstermin\n\n"

            "Ein neuer Termin für ein Bewerbungsgespräch wurde "
            "von beiden Seiten verbindlich bestätigt.\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "## 👤 Bewerber\n\n"

            f"<@{application['user_id']}>\n\n"

            "## 🧑‍💼 Gesprächsführer\n\n"

            f"<@{application['interviewer_id']}>\n\n"

            "## 🗓️ Termin\n\n"

            f"**Datum:** {application['proposal_date']}\n"
            f"**Uhrzeit:** {application['proposal_time']} Uhr\n\n"

            "## ✅ Bestätigung\n\n"

            "**Bewerber:** ✅ Bestätigt\n"
            "**Gesprächsteam:** ✅ Bestätigt\n\n"

            "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            "Bitte erscheinen Sie rechtzeitig zum vereinbarten Termin.\n\n"

            "Sollte der Termin aus wichtigen Gründen nicht "
            "wahrgenommen werden können, informieren Sie die "
            "andere Seite bitte frühzeitig.\n\n"

            "Nach Abschluss des Gespräches muss das zuständige "
            "Gesprächsteam das Ergebnis unten eintragen."
        ),
        color=SUCCESS_COLOR,
    )


    embed.set_footer(
        text="EHRP/VC | Recruitment System"
    )


    result_message = (
        await confirmed_channel.send(
            content=(
                f"<@{application['user_id']}> "
                f"<@{application['interviewer_id']}>"
            ),
            embed=embed,
            view=InterviewResultView(),
            allowed_mentions=(
                discord.AllowedMentions(
                    users=True,
                    roles=False,
                    everyone=False,
                )
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


# ============================================================
# FIND APPLICATION BY RESULT MESSAGE
# ============================================================

def find_application_by_result_message(
    message_id: int,
):

    for app_id, application in DATA[
        "applications"
    ].items():

        if (
            application.get(
                "result_message_id"
            )
            == message_id
        ):

            return (
                app_id,
                application,
            )

    return (
        None,
        None,
    )


# ============================================================
# INTERVIEW PLANNING VIEW
# ============================================================

class InterviewPlanningView(
    discord.ui.View
):

    def __init__(
        self,
    ):

        super().__init__(
            timeout=None
        )


    # ========================================================
    # PROPOSE / CHANGE
    # ========================================================

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


        if (
            not is_applicant
            and not is_team
        ):

            await interaction.response.send_message(
                "❌ Sie dürfen für dieses Gespräch keinen Termin vorschlagen.",
                ephemeral=True,
            )

            return


        await interaction.response.send_modal(
            InterviewProposalModal()
        )


    # ========================================================
    # CONFIRM
    # ========================================================

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


        # ====================================================
        # APPLICANT CONFIRMATION
        # ====================================================

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
                    "✅ Sie haben diesen Termin bereits bestätigt.",
                    ephemeral=True,
                )

                return


            application[
                "applicant_confirmed"
            ] = True


        # ====================================================
        # TEAM CONFIRMATION
        # ====================================================

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
                    "✅ Das Gesprächsteam hat diesen Termin bereits bestätigt.",
                    ephemeral=True,
                )

                return


            application[
                "team_confirmed"
            ] = True

            application[
                "interviewer_id"
            ] = interaction.user.id


        # ====================================================
        # NO ACCESS
        # ====================================================

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


        # ====================================================
        # BOTH CONFIRMED
        # ====================================================

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
# INTERVIEW FAILED MODAL
# ============================================================

class InterviewFailedModal(
    discord.ui.Modal
):

    def __init__(
        self,
    ):

        super().__init__(
            title="Gespräch nicht bestanden"
        )


        self.reason = (
            discord.ui.TextInput(
                label="Grund",
                placeholder=(
                    "Warum wurde das Bewerbungsgespräch "
                    "nicht bestanden?"
                ),
                style=(
                    discord.TextStyle.paragraph
                ),
                min_length=5,
                max_length=1000,
            )
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
                "❌ Nur das zuständige Gesprächsteam darf das Ergebnis festlegen.",
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
                "⚠️ Für dieses Bewerbungsgespräch wurde bereits ein Ergebnis eingetragen.",
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


        # ====================================================
        # REMOVE APPLICATION ACCEPTED ROLE
        # ====================================================

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


        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()


        # ====================================================
        # USER MESSAGE
        # ====================================================

        failed_text = (
            "# ❌ Bewerbungsgespräch nicht bestanden\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "vielen Dank, dass Sie sich die Zeit für das "
            "Bewerbungsgespräch bei **EHRP/VC** genommen haben.\n\n"

            "Nach Auswertung des Gespräches müssen wir Ihnen leider "
            "mitteilen, dass Sie das Bewerbungsgespräch zum jetzigen "
            "Zeitpunkt **nicht bestanden haben**.\n\n"

            "## 📋 Grund\n\n"

            f"**- {reason}**\n\n"

            "Diese Entscheidung bedeutet nicht, dass eine spätere "
            "Bewerbung grundsätzlich ausgeschlossen ist.\n\n"

            "Sie können sich zu einem späteren Zeitpunkt erneut bewerben, "
            "wenn die genannten Punkte entsprechend verbessert wurden.\n\n"

            "Wir bedanken uns für Ihr Verständnis und wünschen Ihnen "
            "weiterhin viel Spaß auf **EHRP/VC**.\n\n"

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


        # ====================================================
        # UPDATE RESULT MESSAGE
        # ====================================================

        embed = discord.Embed(
            title="❌ BEWERBUNGSGESPRÄCH NICHT BESTANDEN",
            description=(
                "# Bewerbungsverfahren beendet\n\n"

                f"**Bewerber:** <@{application['user_id']}>\n"
                f"**Gesprächsführer:** <@{application['interviewer_id']}>\n"
                f"**Entscheidung von:** {interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📋 Grund\n\n"

                f"{reason}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "**Status:** 🔴 Nicht aufgenommen\n\n"

                f"<@&{APPLICATION_ACCEPTED_ROLE_ID}> wurde entfernt.\n"
                f"<@&{TEAM_ACCEPTED_ROLE_ID}> wurde **nicht** vergeben."
            ),
            color=ERROR_COLOR,
        )


        embed.set_footer(
            text="EHRP/VC | Recruitment System"
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

    def __init__(
        self,
    ):

        super().__init__(
            timeout=None
        )


    # ========================================================
    # PASSED
    # ========================================================

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
                "❌ Nur das zuständige Gesprächsteam darf das Ergebnis festlegen.",
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
                "⚠️ Für dieses Gespräch wurde bereits ein Ergebnis eingetragen.",
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


        if applicant is None:

            await interaction.response.send_message(
                "❌ Der Bewerber befindet sich nicht mehr auf dem Server.",
                ephemeral=True,
            )

            return


        # ====================================================
        # FIRST ADD NEW ROLE
        # ====================================================

        added_new_role = (
            await add_role_safe(
                applicant,
                TEAM_ACCEPTED_ROLE_ID,
                (
                    "EHRP Recruitment: "
                    "Bewerbungsgespräch bestanden"
                ),
            )
        )


        if not added_new_role:

            await interaction.response.send_message(
                (
                    "❌ Die neue Rolle konnte nicht vergeben werden.\n\n"
                    "Bitte prüfen Sie, ob die Bot-Rolle über "
                    "der neuen Rolle steht."
                ),
                ephemeral=True,
            )

            return


        # ====================================================
        # REMOVE OLD ROLE
        # ====================================================

        removed_old_role = (
            await remove_role_safe(
                applicant,
                APPLICATION_ACCEPTED_ROLE_ID,
                (
                    "EHRP Recruitment: "
                    "Bewerbungsverfahren abgeschlossen"
                ),
            )
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


        DATA[
            "applications"
        ][
            app_id
        ] = application

        save_data()


        # ====================================================
        # DM TO APPLICANT
        # ====================================================

        passed_text = (
            "# 🎉 Bewerbungsgespräch bestanden\n\n"

            "**Sehr geehrte/r Bewerber/in,**\n\n"

            "wir freuen uns, Ihnen mitteilen zu können, dass Sie "
            "Ihr Bewerbungsgespräch bei **EHRP/VC erfolgreich "
            "bestanden haben**.\n\n"

            "Damit wurde Ihr Bewerbungsverfahren erfolgreich abgeschlossen.\n\n"

            "## ✅ Aufnahme\n\n"

            "Sie wurden für die weitere Aufnahme in das "
            "**EHRP/VC-Team** freigegeben.\n\n"

            "Ihre bisherige Bewerberrolle wurde entfernt und Ihre "
            "neue Rolle wurde automatisch vergeben.\n\n"

            "Wir gratulieren Ihnen herzlich und wünschen Ihnen "
            "viel Erfolg bei Ihren kommenden Aufgaben.\n\n"

            "**Mit freundlichen Grüßen**\n"
            "**Das EHRP/VC-Team**"
        )


        try:

            await applicant.send(
                passed_text
            )

        except discord.HTTPException:

            pass


        # ====================================================
        # FINAL INTERNAL MESSAGE
        # ====================================================

        if removed_old_role:

            role_status = (
                f"<@&{APPLICATION_ACCEPTED_ROLE_ID}> ❌ entfernt\n"
                f"<@&{TEAM_ACCEPTED_ROLE_ID}> ✅ hinzugefügt"
            )

        else:

            role_status = (
                f"<@&{TEAM_ACCEPTED_ROLE_ID}> ✅ hinzugefügt\n"
                f"⚠️ <@&{APPLICATION_ACCEPTED_ROLE_ID}> konnte "
                "nicht automatisch entfernt werden."
            )


        embed = discord.Embed(
            title="🎉 BEWERBUNG ERFOLGREICH ABGESCHLOSSEN",
            description=(
                "# ✅ Bewerbungsgespräch bestanden\n\n"

                f"**Bewerber:** {applicant.mention}\n"
                f"**Gesprächsführer:** <@{application['interviewer_id']}>\n"
                f"**Entscheidung bestätigt von:** {interaction.user.mention}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 🔐 Rollenänderung\n\n"

                f"{role_status}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "## 📡 Status\n\n"

                "**🟢 Bewerbungsverfahren erfolgreich abgeschlossen**"
            ),
            color=SUCCESS_COLOR,
        )


        embed.set_footer(
            text="EHRP/VC | Recruitment System"
        )


        await interaction.response.edit_message(
            embed=embed,
            view=None,
        )


    # ========================================================
    # FAILED
    # ========================================================

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
                "❌ Nur das zuständige Gesprächsteam darf das Ergebnis festlegen.",
                ephemeral=True,
            )

            return


        await interaction.response.send_modal(
            InterviewFailedModal()
        )


# ============================================================
# COG
# ============================================================

class Applications(
    commands.Cog
):

    def __init__(
        self,
        bot: commands.Bot,
    ):

        self.bot = bot


        # ====================================================
        # PERSISTENT VIEWS
        # ====================================================

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
    # /BEWERBUNG_PANEL
    # ========================================================

    @app_commands.command(
        name="bewerbung_panel",
        description="Erstellt das EHRP/VC Bewerbungsportal.",
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
                "❌ Sie dürfen das Bewerbungsportal nicht erstellen.",
                ephemeral=True,
            )

            return


        await interaction.channel.send(
            embed=build_application_panel(),
            view=ApplicationPanelView(),
        )


        await interaction.response.send_message(
            "✅ Das Bewerbungsportal wurde erfolgreich erstellt.",
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNGEN_OEFFNEN
    # ========================================================

    @app_commands.command(
        name="bewerbungen_oeffnen",
        description="Öffnet die Teambewerbungen.",
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
                "Neue Teambewerbungen können ab sofort "
                "wieder eingereicht werden."
            ),
            ephemeral=True,
        )


    # ========================================================
    # /BEWERBUNGEN_SCHLIESSEN
    # ========================================================

    @app_commands.command(
        name="bewerbungen_schliessen",
        description="Schließt die Teambewerbungen.",
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
        description="Zeigt den Status des Recruitment Systems.",
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


        total = len(
            DATA[
                "applications"
            ]
        )


        pending = sum(
            1
            for application
            in DATA[
                "applications"
            ].values()
            if application.get(
                "status"
            ) in {
                "pending",
                "claimed",
            }
        )


        interviews = sum(
            1
            for application
            in DATA[
                "applications"
            ].values()
            if application.get(
                "status"
            ) in {
                "interview_planning",
                "interview_confirmed",
                "interview_running",
            }
        )


        completed = sum(
            1
            for application
            in DATA[
                "applications"
            ].values()
            if application.get(
                "status"
            ) == "completed"
        )


        failed = sum(
            1
            for application
            in DATA[
                "applications"
            ].values()
            if application.get(
                "status"
            ) in {
                "rejected",
                "failed",
            }
        )


        if DATA.get(
            "applications_open",
            True,
        ):

            application_status = (
                "🟢 Geöffnet"
            )

        else:

            application_status = (
                "🔴 Geschlossen"
            )


        embed = discord.Embed(
            title="⚙️ EHRP/VC | RECRUITMENT SYSTEM",
            description=(
                "# Systemstatus\n\n"

                f"**Bewerbungen:** {application_status}\n\n"

                f"📨 **Gesamt:** {total}\n"
                f"🟡 **Zu bearbeiten:** {pending}\n"
                f"📞 **Gesprächsphase:** {interviews}\n"
                f"✅ **Erfolgreich abgeschlossen:** {completed}\n"
                f"❌ **Abgelehnt / nicht bestanden:** {failed}\n\n"

                "━━━━━━━━━━━━━━━━━━━━━━\n\n"

                "🟢 Voraussetzungssystem: Online\n"
                "🟢 Frage-für-Frage-System: Online\n"
                "🟢 Review-System: Online\n"
                "🟢 Rollen-Automation: Online\n"
                "🟢 Termin-System: Online\n"
                "🟢 Doppelte Terminbestätigung: Aktiv\n"
                "🟢 Gesprächsauswertung: Online"
            ),
            color=SUCCESS_COLOR,
        )


        embed.set_footer(
            text="EHRP/VC | Recruitment System"
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
