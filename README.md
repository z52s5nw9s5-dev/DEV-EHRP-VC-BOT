# EHRP DEV BOT — FINAL FOUNDATION

Eigener Server-Developer-Bot für EHRP / Notruf Hamburg. Moderation wie Warn/Kick/Ban bleibt bewusst bei Galaxy; dieser Bot ist für Struktur, Design, Automatisierung, Backups und Developer-Workflows gedacht.

## Fest hinterlegt
- Server-ID: `1526936313083858945`
- Owner-ID: `1294267376459714621`
- DEV-Rolle: `1536533338083426384`

## Enthalten
- DEV/Owner-Rechtesystem
- SQLite-Konfiguration direkt per Discord
- Server-, Rollen-, Rechte-, Channel- und Design-Checks
- Kategorien/Channels erstellen, klonen, umbenennen und löschen
- Topic, Slowmode, Lock/Unlock
- Aktionshistorie + `/undo`
- Vollbackup von Rollen, Channelstruktur und Permission-Overwrites
- Sicherer `restore_missing`, der Bestehendes nicht löscht
- Kategorie-Templates speichern/bauen/löschen
- komplette Projekt-/Event-Bereiche auf Knopfdruck
- Projektarchivierung
- Join-to-Create TempVoice + Owner-Steuerung (Name/Limit/Lock)
- Team-Abwesenheiten und DEV-Teamliste
- Embed- und Changelog-System
- automatische Logs für Channel-/Rollenänderungen
- automatische Statistik-Voicechannels
- dynamisches `/setup` für Log-, Backup- und Archivbereiche
- Bestätigungsbuttons für gefährliche Aktionen

## Slash Commands
`/dev`, `/ping`

`/setup anzeigen`, `/setup log_channel`, `/setup archiv`, `/setup backup_channel`

`/servercheck`, `/rollencheck`, `/channelcheck`, `/rechtecheck`, `/designcheck`

`/kategorie_erstellen`, `/channel_erstellen`, `/channel_umbenennen`, `/topic`, `/slowmode`, `/lock`, `/unlock`, `/channel_klonen`, `/channel_loeschen`, `/undo`

`/backup_erstellen`, `/backup_liste`, `/restore_missing`

`/template_speichern`, `/template_liste`, `/template_bauen`, `/template_loeschen`

`/projekt_erstellen`, `/projekt_archivieren`

`/tempvoice_setup`, `/voice_name`, `/voice_limit`, `/voice_lock`, `/voice_unlock`

`/abwesend`, `/abwesenheit_ende`, `/abwesenheiten`, `/teamliste`

`/embed_senden`, `/changelog`

`/stats_setup`, `/stats_update`

## Start
1. Python 3.11+ verwenden.
2. `pip install -r requirements.txt`
3. `.env.example` nach `.env` kopieren.
4. Token in `.env` eintragen. Token niemals posten.
5. Discord Developer Portal → Bot → Server Members Intent aktivieren.
6. Bot mit passenden Rechten einladen. Für die DEV-Funktionen braucht er mindestens Manage Channels, Manage Roles, Manage Guild, Manage Messages und View Audit Log; Administrator ist bequemer, aber sicherheitstechnisch nicht zwingend.
7. `python main.py`
8. In Discord zuerst `/setup log_channel` und optional Backup/Archiv konfigurieren.

## Sicherheitsentscheidung
Der Bot löscht nicht automatisch massenhaft Rollen/Channels und ein Restore überschreibt den Server nicht blind. Das ist absichtlich so: Ein Developer-Bot soll Zeit sparen, nicht bei einem Fehler den ganzen Server zerstören.


## Render Free Web Service

Build Command: `pip install -r requirements.txt`

Start Command: `python main.py`

Environment Variable: `DISCORD_TOKEN` = dein Bot-Token.

Der integrierte Health-Webserver lauscht automatisch auf Render `PORT`.
