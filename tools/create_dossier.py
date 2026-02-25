"""
Dossier-Erstellungs-Tool.
Nimmt Research-Daten + Show-Info und erstellt via Claude API ein
Moderations-Dossier im definierten Format.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SHOW_INFO_PATH = PROJECT_ROOT / "Show Info DAS.md"

DOSSIER_SYSTEM_PROMPT = """# ROLLE & PERSONA
Du bist ein erfahrener Chefredakteur und Stratege für eine hochwertige Unterhaltungssendung. Deine Aufgabe ist es, Moderations-Dossiers zu erstellen, die brillant, pointiert und strategisch sind. Dein Zielpublikum ist ein Moderator, der wenig Zeit hat, aber maximal gut vorbereitet sein muss. Du hasst Langeweile, PR-Phrasen und Wikipedia-Wissen. Du suchst nach dem "Gold" in den Informationen.

# OUTPUT REGELN
* Schreibe direkt das Dossier, keine Einleitungen wie "Hier ist das Dossier".
* Sprache: Deutsch.
* Tonalität: Professionell, aber locker und direkt (TV-Sprech).
* Formatierung: Nutze Emojis sparsam zur Orientierung. Nutze Fettungen für Schlüsselwörter.
* WICHTIG: Beginne das Dossier IMMER mit dem Inhaltsverzeichnis (Navigation) wie im Format vorgegeben. Halte dich EXAKT an die vorgegebenen HTML-Anker-IDs."""

DOSSIER_USER_PROMPT = """# DEINE INPUTS

## SHOW_INFO
{show_info}

## RESEARCH_DATA
{research_data}

## ECHTZEIT-DATEN (für Freshness-Check)
{realtime_data}

# DAS ZIEL-FORMAT (DOSSIER STRUKTUR)
Erstelle das Dossier strikt nach folgender Struktur. Nutze Markdown (Fettungen, Bulletpoints), um es scannbar zu machen.

BEGINNE mit diesem EXAKTEN Inhaltsverzeichnis (ersetze nur [GASTNAME]):

# Dossier: [GASTNAME]

> **Quick Navigation:**
> [Cheat Sheet](#cheat-sheet) | [Hidden Gems](#hidden-gems) | [Gesprächsführung](#gespraechsfuehrung) | [Killer-Fragen](#killer-fragen) | [Show-Integration](#show-integration) | [Red Flags](#red-flags) | [Freshness Check](#freshness-check)

---

Danach folgen die Abschnitte. WICHTIG — Überschriften-Hierarchie STRIKT einhalten:
- Hauptabschnitte (1. THE CHEAT SHEET, 2. HIDDEN GEMS, ...): immer `#` (h1)
- Unterüberschriften innerhalb eines Abschnitts (Eisbrecher, Themen-Cluster, ...): immer `##` (h2)
- Blöcke / Detail-Ebene (BLOCK 1, BLOCK 2, ...): immer `###` (h3)

<a id="cheat-sheet"></a>
# 1. THE CHEAT SHEET (Auf einen Blick)
* **Name & Status:** (Kurz & knackig)
* **Der Hook:** Was promotet er/sie HEUTE? (Buch, Film, Tour etc.)
* **Der aktuelle Vibe:** (Basierend auf News/Social Media: Ist er auf Krawall gebürstet, emotional, euphorisch?)

---

<a id="hidden-gems"></a>
# 2. HIDDEN GEMS (Das Gold aus dem Research)
* Filtere das Research-Material. Ignoriere Standard-Biografien.
* Liste 3-4 überraschende Fakten, Talente oder skurrile Hobbys auf.
* Suche nach Brüchen (z.B. "Harter Rapper, der Rosen züchtet").

---

<a id="gespraechsfuehrung"></a>
# 3. GESPRÄCHSFÜHRUNG & DRAMATURGIE
Schlage einen Gesprächsbogen vor:

## Eisbrecher
Eine Einstiegsfrage, die sofort eine Stimmung setzt (Kein "Wie geht's").

## Themen-Cluster (Spannungsbogen)
3 Hauptthemen, sortiert nach Spannungsbogen (Lustig -> Ernst -> Emotional). Strukturiere sie als:

### BLOCK 1: [Thema]
### BLOCK 2: [Thema]
### BLOCK 3: [Thema]

---

<a id="killer-fragen"></a>
# 4. DIE "KILLER-FRAGEN" (Anti-PR)
Formuliere 3 konkrete Fragen, die den Gast aus der Reserve locken.
* Keine Standard-Fragen ("Wie war der Dreh?").
* Nutze psychologische Hebel oder hypothetische Szenarien ("Wenn du eine Sache in deiner Karriere ungeschehen machen könntest...").

---

<a id="show-integration"></a>
# 5. SHOW-INTEGRATION
* Wie passt der Gast in DIESE spezifische Sendung (basierend auf SHOW_INFO)?
* Idee für eine Aktion, ein Spiel oder eine Interaktion mit dem Publikum/Moderator.

---

<a id="red-flags"></a>
# 6. RED FLAGS
* Themen, die absolut tabu sind oder juristisch heikel (Warnung in FETT).
* Sensible Punkte (Trauerfälle, Scheidungen), die Fingerspitzengefühl erfordern.

---

<a id="freshness-check"></a>
# 7. FRESHNESS CHECK
* **Breaking News:** Gab es heute Schlagzeilen?
* **Social Media:** Was war der allerletzte Post? (Damit der Moderator sagen kann: "Ich hab gesehen, du hast heute morgen...")"""


def slugify(name: str) -> str:
    """Wandelt einen Namen in einen Dateinamen-tauglichen String um."""
    slug = name.lower().strip()
    slug = re.sub(r"[äÄ]", "ae", slug)
    slug = re.sub(r"[öÖ]", "oe", slug)
    slug = re.sub(r"[üÜ]", "ue", slug)
    slug = re.sub(r"ß", "ss", slug)
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return slug


def load_show_info() -> str:
    """Lädt die Show-Info-Datei."""
    if not SHOW_INFO_PATH.exists():
        raise FileNotFoundError(f"Show Info nicht gefunden: {SHOW_INFO_PATH}")
    return SHOW_INFO_PATH.read_text(encoding="utf-8")


def create_dossier(guest_name: str, research_path: Path, on_chunk=None) -> Path:
    """Erstellt das Dossier via Claude API. on_chunk(text) wird bei jedem Streaming-Chunk aufgerufen."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gesetzt")

    print(f"📝 Erstelle Dossier für: {guest_name}")

    # Inputs laden
    show_info = load_show_info()
    research_content = research_path.read_text(encoding="utf-8")

    # Research und Echtzeit-Daten trennen (Tavily-Teil extrahieren)
    realtime_marker = "## Echtzeit-Check (Tavily)"
    if realtime_marker in research_content:
        parts = research_content.split(realtime_marker, 1)
        research_data = parts[0].strip()
        realtime_data = realtime_marker + parts[1]
    else:
        research_data = research_content
        realtime_data = "Keine Echtzeit-Daten verfügbar."

    # Claude API aufrufen (Streaming, um Timeouts zu vermeiden)
    print("  → Claude API aufrufen (Streaming)...")
    client = anthropic.Anthropic(api_key=api_key)

    today = datetime.now().strftime("%d.%m.%Y")
    system_with_date = (
        DOSSIER_SYSTEM_PROMPT
        + f"\n\n# AKTUELLES DATUM\nHeute ist der {today}. "
        "Informationen aus 2025 und 2026 sind GEGENWART — behandle sie als aktuell. "
        "Schreibe niemals, dass etwas 'in der Zukunft' liegt oder 'noch nicht bekannt' ist, wenn es sich um Ereignisse aus 2025/2026 handelt."
    )

    dossier_content = ""
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        system=system_with_date,
        messages=[
            {
                "role": "user",
                "content": DOSSIER_USER_PROMPT.format(
                    show_info=show_info,
                    research_data=research_data,
                    realtime_data=realtime_data,
                ),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            dossier_content += text
            if on_chunk:
                on_chunk(dossier_content)

    print("  ✓ Dossier generiert")

    # Speichern
    dossier_dir = PROJECT_ROOT / "dossiers"
    dossier_dir.mkdir(exist_ok=True)
    slug = slugify(guest_name)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = dossier_dir / f"{slug}_{date_str}.md"
    output_path.write_text(dossier_content, encoding="utf-8")

    print(f"✅ Dossier gespeichert: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_dossier.py \"Gastname\" \"pfad/zur/research.md\"")
        sys.exit(1)

    guest = sys.argv[1]
    research_file = Path(sys.argv[2])
    if not research_file.exists():
        print(f"Fehler: Research-Datei nicht gefunden: {research_file}")
        sys.exit(1)

    create_dossier(guest, research_file)
