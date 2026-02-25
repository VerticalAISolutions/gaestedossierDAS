"""
Research-Tool für Gästedossiers.
Führt Deep Research über einen Gast durch mittels Perplexity (Haupt-Research),
Tavily (Echtzeit-Check) und OpenAI (Fallback).

Enthält Disambiguierung: Vor dem Research wird geprüft, ob der Name eindeutig ist.
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Projekt-Root bestimmen
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RESEARCH_PROMPT_TEMPLATE = """Du bist Chef-Rechercheur für eine führende TV-Talkshow. Deine Aufgabe ist es, ein detailliertes, kritisches und gesprächsorientiertes Dossier über den folgenden Gast zu erstellen:

AKTUELLES DATUM: Heute ist der {today}. Informationen aus 2025 und 2026 sind GEGENWART, nicht Zukunft.

GAST: {guest_name}
{context_hint}

Bitte führe eine umfassende Deep Research durch (suche in Nachrichtenarchiven, Social Media, Interviews der letzten 12 Monate, Biografien) und erstelle das Dossier exakt nach folgender Struktur. Sei präzise, nenne Quellen und vermeide PR-Sprech.

WICHTIG: Stelle sicher, dass sich alle Informationen tatsächlich auf die oben genannte Person beziehen. Verwechsle sie NICHT mit Namensvetter oder ähnlich klingenden Personen.

---

### 1. Der aktuelle Aufhänger (The "Why Now")
Warum ist diese Person *jetzt gerade* relevant?
- Was hat sie in den letzten 3-6 Monaten getan, veröffentlicht oder gesagt?
- Gibt es aktuelle Skandale, virale Momente, gewonnene Preise oder neue Projekte (Buch, Film, Amt)?
- Welches Thema dominiert die aktuelle Berichterstattung über sie?

### 2. Die "Hidden Gems" (Biografie & Brüche)
Ignoriere den Standard-Wikipedia-Lebenslauf. Suche nach dem Interessanten:
- Gab es Brüche, Scheitern oder ungewöhnliche Wendungen im Leben?
- Was sind überraschende Fakten, die kaum jemand weiß (Hobbys, Marotten, frühere Jobs)?
- Gibt es ein prägendes Ereignis ("Origin Story"), das den Charakter erklärt?

### 3. Der Konflikt & Die Kritik (Die "Hard Talk" Vorbereitung)
Wo bietet die Person Angriffsfläche?
- Welche kontroversen Aussagen oder Handlungen gab es in der Vergangenheit?
- Wo widerspricht sich die Person (z.B. Aussagen von vor 5 Jahren vs. heute)?
- Welche Kritikpunkte bringen politische Gegner, Feuilletonisten oder Konkurrenten vor?

### 4. O-Töne & Narrativ (Wie spricht der Gast?)
- Zitiere 3 prägnante, steile oder emotionale Aussagen aus den letzten 12 Monaten (mit Quelle/Datum).
- Welches "Narrativ" versucht der Gast aktuell zu verkaufen (z.B. "Ich bin der Retter", "Ich bin das Opfer", "Ich bin der pragmatische Macher")?

### 5. Beziehungs-Netzwerk
- Mit wem ist der Gast verbündet? (Politische Seilschaften, beste Freunde, Geschäftspartner).
- Wer sind die Erzfeinde oder Rivalen?

---

FORMAT-VORGABE:
Nutze Markdown. Schreibe stichpunktartig aber detailreich. Füge bei kritischen Fakten oder Zitaten immer die Quelle/Datum in Klammern hinzu."""


def disambiguate_guest(guest_name: str) -> list[dict]:
    """
    Prüft via Tavily, ob es mehrere bekannte Personen mit diesem Namen gibt.
    Gibt eine Liste von Kandidaten zurück mit Name, Beschreibung und Kontext.
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY nicht in .env gesetzt")

    client = TavilyClient(api_key=api_key)

    # Breite Suche nach dem Namen
    results = client.search(
        query=f'"{guest_name}" wer ist Person Beruf',
        search_depth="advanced",
        max_results=8,
        include_answer=True,
    )

    # Ergebnisse an Claude zur Disambiguierung schicken
    import anthropic

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY nicht in .env gesetzt")

    search_context = ""
    if results.get("answer"):
        search_context += f"Zusammenfassung: {results['answer']}\n\n"
    for r in results.get("results", []):
        search_context += f"- {r.get('title', '')}: {r.get('content', '')[:400]}\n"
        search_context += f"  URL: {r.get('url', '')}\n\n"

    client_ai = anthropic.Anthropic(api_key=anthropic_key)
    message = client_ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        timeout=60.0,
        messages=[{
            "role": "user",
            "content": f"""Analysiere die folgenden Suchergebnisse zum Namen "{guest_name}".

SUCHERGEBNISSE:
{search_context}

AUFGABE: Gibt es mehrere verschiedene bekannte Personen mit diesem Namen (oder sehr ähnlichem Namen)?

Antworte AUSSCHLIESSLICH im folgenden JSON-Format, ohne zusätzlichen Text:
{{
  "candidates": [
    {{
      "name": "Voller Name der Person (exakte Schreibweise)",
      "description": "Kurze Beschreibung (Beruf, bekannt für...)",
      "context_hint": "Spezifische Suchbegriffe zur Identifikation, z.B. 'Autor Roman Schimmernder Dunst' oder 'Kinobetreiber Programmkino Rex Darmstadt'. Muss konkrete Keywords enthalten, die diese Person von Namensvetter unterscheiden."
    }}
  ],
  "is_ambiguous": true/false
}}

Regeln:
- Wenn der Name EINDEUTIG nur eine bekannte Person ergibt: is_ambiguous=false, ein Kandidat
- Wenn es MEHRERE verschiedene Personen gibt: is_ambiguous=true, alle Kandidaten auflisten
- Berücksichtige auch Schreibvarianten (ü/ue, ß/ss, etc.)
- Nur real existierende Personen, keine Vermutungen
- WICHTIG für context_hint: Verwende konkrete, suchbare Keywords (Buchtitel, Firma, Ort, Beruf), KEINE vagen Beschreibungen"""
        }],
    )

    response_text = message.content[0].text

    # JSON aus der Antwort extrahieren
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        data = json.loads(json_match.group())
        return data.get("candidates", []), data.get("is_ambiguous", False)

    # Fallback: nicht disambiguierbar
    return [{"name": guest_name, "description": "Nicht näher bestimmt", "context_hint": ""}], False


def _build_search_query(guest_name: str, context_hint: str, suffix: str = "") -> str:
    """Baut eine präzise Suchanfrage mit Kontext, um Verwechslungen zu vermeiden."""
    if context_hint:
        # Kern-Keywords aus dem context_hint extrahieren (z.B. "Autor" aus "der Autor des Romans XY")
        return f'"{guest_name}" {context_hint} {suffix}'.strip()
    return f'"{guest_name}" {suffix}'.strip()


def research_perplexity(guest_name: str, context_hint: str = "") -> str:
    """Haupt-Research via Perplexity Sonar API."""
    import requests

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY nicht in .env gesetzt")

    hint_text = ""
    if context_hint:
        hint_text = f"""
KONTEXT: Es handelt sich um {context_hint}. Recherchiere AUSSCHLIESSLICH über diese Person.
WARNUNG: Es gibt andere Personen mit ähnlichem Namen. Prüfe bei JEDER Information, ob sie sich wirklich auf die richtige Person bezieht. Im Zweifel: weglassen."""

    today = datetime.now().strftime("%d.%m.%Y")
    prompt = RESEARCH_PROMPT_TEMPLATE.format(guest_name=guest_name, context_hint=hint_text, today=today)

    # Suchanfrage mit Kontext anreichern, damit Perplexity die richtige Person findet
    search_name = f"{guest_name} {context_hint}" if context_hint else guest_name

    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": f"Du bist ein erfahrener Rechercheur für deutsche TV-Talkshows. Heute ist der {today}. Informationen aus 2025 und 2026 sind Gegenwart. Recherchiere gründlich und liefere quellenbasierte Ergebnisse auf Deutsch. WICHTIG: Du recherchierst über {search_name}. Verwechsle diese Person NICHT mit Namensvetter."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "search_recency_filter": "month",
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"]

    # Quellen anhängen wenn vorhanden
    citations = data.get("citations", [])
    if citations:
        content += "\n\n---\n### Quellen (Perplexity)\n"
        for i, url in enumerate(citations, 1):
            content += f"{i}. {url}\n"

    return content


def research_tavily(guest_name: str, context_hint: str = "") -> str:
    """Echtzeit-Check via Tavily API (News der letzten 48h, Social Media)."""
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY nicht in .env gesetzt")

    client = TavilyClient(api_key=api_key)

    # Suchanfragen MIT Kontext, um Verwechslungen zu vermeiden
    news_query = _build_search_query(guest_name, context_hint, "aktuelle News")

    # Aktuelle News suchen
    news_results = client.search(
        query=news_query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
        topic="news",
    )

    # Social Media: Gezielte Suche auf Social-Media-Plattformen
    social_domains = ["instagram.com", "twitter.com", "x.com", "linkedin.com", "tiktok.com", "facebook.com", "youtube.com"]
    social_query = _build_search_query(guest_name, context_hint, "")
    social_results = client.search(
        query=social_query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
        include_domains=social_domains,
    )

    # Zusätzliche gezielte Instagram-Suche (häufig übersehen)
    instagram_query = f"{guest_name} site:instagram.com"
    instagram_results = client.search(
        query=instagram_query,
        search_depth="basic",
        max_results=3,
        include_answer=False,
        include_domains=["instagram.com"],
    )

    output = "## Echtzeit-Check (Tavily)\n\n"
    output += "### Aktuelle News (letzte 48h)\n"
    if news_results.get("answer"):
        output += f"{news_results['answer']}\n\n"
    for result in news_results.get("results", []):
        output += f"- **{result.get('title', 'Ohne Titel')}**\n"
        output += f"  {result.get('content', '')[:300]}\n"
        output += f"  Quelle: {result.get('url', 'N/A')}\n\n"

    output += "### Social Media Profile\n"
    if social_results.get("answer"):
        output += f"{social_results['answer']}\n\n"

    # Social Media + Instagram Ergebnisse zusammenführen, Duplikate vermeiden
    seen_urls = set()
    all_social = social_results.get("results", []) + instagram_results.get("results", [])
    for result in all_social:
        url = result.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        output += f"- **{result.get('title', 'Ohne Titel')}**\n"
        output += f"  {result.get('content', '')[:300]}\n"
        output += f"  Quelle: {url}\n\n"

    if not all_social:
        output += "- Keine Social-Media-Profile gefunden.\n\n"

    return output


def research_openai_fallback(guest_name: str, context_hint: str = "") -> str:
    """Fallback-Research via OpenAI mit Web Search."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY nicht in .env gesetzt")

    client = OpenAI(api_key=api_key)

    hint = f" ({context_hint})" if context_hint else ""
    response = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=[
            {"role": "system", "content": "Du bist ein erfahrener Rechercheur für deutsche TV-Talkshows. Recherchiere gründlich auf Deutsch."},
            {"role": "user", "content": f"Recherchiere aktuelle Informationen über {guest_name}{hint}: Aktuelle Projekte, Kontroversen, überraschende Fakten, wichtige Zitate der letzten 12 Monate. Nenne immer Quellen."},
        ],
    )

    # Text aus der Response extrahieren
    text_parts = [block.text for block in response.output if hasattr(block, "text")]
    return "\n".join(text_parts) if text_parts else "Keine Ergebnisse von OpenAI."


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


def verify_research(guest_name: str, context_hint: str, research_text: str) -> str:
    """
    Verifikationsschritt: Claude prüft das gesammelte Research auf Verwechslungen
    und entfernt Informationen, die zur falschen Person gehören.
    """
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return research_text  # Ohne API-Key: ungeprüft zurückgeben

    today = datetime.now().strftime("%d.%m.%Y")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        timeout=120.0,
        messages=[{
            "role": "user",
            "content": f"""Du bist ein Faktenprüfer für Personenverwechslungen. Heute ist der {today}. Informationen aus 2025 und 2026 sind GEGENWART — behandle sie als aktuell und korrekt.

DIE ZIELPERSON:
- Name: {guest_name}
- Identifikation: {context_hint}

DAS ZU PRÜFENDE DOSSIER:
{research_text}

DEINE EINZIGE AUFGABE: Filtere Verwechslungen mit anderen Personen, die denselben oder einen ähnlichen Namen tragen.

REGELN:
1. BEHALTE alle Informationen, die plausibel zur Zielperson passen — auch wenn du sie nicht aus deiner Wissensbasis kennst. Aktuelle Informationen aus Live-Quellen (2025/2026) sind als korrekt zu behandeln.
2. ENTFERNE nur Informationen, die EINDEUTIG zu einer anderen Person gehören (klar anderer Beruf, anderes Land, völlig andere Biografie).
3. Setze [⚠️ MÖGLICHE VERWECHSLUNG] NUR wenn du eine konkrete andere Person mit gleichem Namen identifizierst, deren Daten hier fälschlicherweise auftauchen.
4. Gib das Dossier im gleichen Format zurück.

WICHTIG: Markiere NICHT, weil du eine Information nicht bestätigen kannst. Markiere NUR bei konkretem Verdacht auf eine andere Person."""
        }],
    )

    return message.content[0].text


def run_research(guest_name: str, context_hint: str = "") -> Path:
    """Führt die komplette Research-Pipeline aus und speichert das Ergebnis."""
    print(f"🔍 Starte Research für: {guest_name}")
    if context_hint:
        print(f"  Kontext: {context_hint}")

    # Schritt A: Perplexity Deep Research
    print("  → Perplexity Deep Research...")
    try:
        perplexity_result = research_perplexity(guest_name, context_hint)
        print("  ✓ Perplexity abgeschlossen")
    except Exception as e:
        print(f"  ✗ Perplexity fehlgeschlagen: {e}")
        perplexity_result = None

    # Schritt B: Tavily Echtzeit-Check (jetzt MIT Kontext)
    print("  → Tavily Echtzeit-Check...")
    try:
        tavily_result = research_tavily(guest_name, context_hint)
        print("  ✓ Tavily abgeschlossen")
    except Exception as e:
        print(f"  ✗ Tavily fehlgeschlagen: {e}")
        tavily_result = None

    # Schritt C: OpenAI Fallback (nur wenn Perplexity fehlgeschlagen)
    openai_result = None
    if perplexity_result is None:
        print("  → OpenAI Fallback-Research...")
        try:
            openai_result = research_openai_fallback(guest_name, context_hint)
            print("  ✓ OpenAI abgeschlossen")
        except Exception as e:
            print(f"  ✗ OpenAI fehlgeschlagen: {e}")

    # Ergebnisse zusammenführen
    if perplexity_result is None and openai_result is None:
        raise RuntimeError(f"Research für '{guest_name}' komplett fehlgeschlagen. Weder Perplexity noch OpenAI lieferten Ergebnisse.")

    output = f"# Research-Dossier: {guest_name}\n"
    if context_hint:
        output += f"**Identifikation:** {context_hint}\n"
    output += f"*Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}*\n\n"

    if perplexity_result:
        output += perplexity_result
    elif openai_result:
        output += "## Deep Research (OpenAI Fallback)\n\n"
        output += openai_result

    output += "\n\n---\n\n"

    if tavily_result:
        output += tavily_result

    # Speichern: Rohdaten
    tmp_dir = PROJECT_ROOT / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    slug = slugify(guest_name)
    raw_path = tmp_dir / f"{slug}_research_raw.md"
    raw_path.write_text(output, encoding="utf-8")
    print(f"  💾 Rohdaten gespeichert: {raw_path}")

    # Schritt D: Verifikation — Verwechslungen rausfiltern
    verified_output = output
    if context_hint:
        print("  → Verifikation: Prüfe auf Verwechslungen...")
        try:
            verified_output = verify_research(guest_name, context_hint, output)
            print("  ✓ Verifikation abgeschlossen")
        except Exception as e:
            print(f"  ⚠ Verifikation fehlgeschlagen (Research wird ungeprüft gespeichert): {e}")

    # Speichern: Verifizierte Version
    verified_path = tmp_dir / f"{slug}_research.md"
    verified_path.write_text(verified_output, encoding="utf-8")

    print(f"✅ Research gespeichert: {verified_path}")
    return verified_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python research_guest.py \"Gastname\"")
        sys.exit(1)

    guest = sys.argv[1]

    # Disambiguierung
    print(f"🔍 Prüfe Identität: {guest}")
    candidates, is_ambiguous = disambiguate_guest(guest)

    if is_ambiguous:
        print(f"\n⚠️  Mehrere Personen mit dem Namen '{guest}' gefunden:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c['name']} – {c['description']}")
        choice = input("\nWelche Person meinst du? (Nummer eingeben): ").strip()
        idx = int(choice) - 1
        selected = candidates[idx]
        print(f"\n✓ Ausgewählt: {selected['name']} – {selected['description']}")
        run_research(selected["name"], selected.get("context_hint", ""))
    else:
        selected = candidates[0]
        print(f"✓ Eindeutig identifiziert: {selected['name']} – {selected['description']}")
        run_research(selected["name"], selected.get("context_hint", ""))
