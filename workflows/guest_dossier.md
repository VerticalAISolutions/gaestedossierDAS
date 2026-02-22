# Workflow: Gästedossier erstellen

## Ziel
Automatisiertes Moderations-Dossier für einen Gast der Sendung DAS! (NDR) erstellen.

## Input
- Gastname (String)

## Output
- Markdown-Dossier in `dossiers/{gastname}_{datum}.md`
- Research-Rohdaten in `.tmp/{gastname}_research.md`

## Ablauf

### 1. Research ausführen
**Tool:** `tools/research_guest.py`

| Schritt | API | Zweck | Fallback |
|---------|-----|-------|----------|
| A | Perplexity Sonar Pro | Deep Research (5 Kategorien) | → OpenAI |
| B | Tavily | Echtzeit-News + Social Media | Dossier ohne Freshness |
| C | OpenAI + Web Search | Nur wenn Perplexity ausfällt | — |

**Ergebnis:** `.tmp/{gastname}_research.md`

### 2. Dossier erstellen
**Tool:** `tools/create_dossier.py`

- Liest Research-Daten + Show Info DAS.md
- Sendet alles an Claude API (Sonnet 4.5)
- Claude erstellt Dossier mit 7 Abschnitten:
  1. The Cheat Sheet
  2. Hidden Gems
  3. Gesprächsführung & Dramaturgie
  4. Killer-Fragen
  5. Show-Integration
  6. Red Flags
  7. Freshness Check

**Ergebnis:** `dossiers/{gastname}_{datum}.md`

## Schnellstart
```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. API-Keys in .env eintragen
# PERPLEXITY_API_KEY, TAVILY_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

# 3. Pipeline starten
python tools/run_pipeline.py "Gastname"
```

## Bekannte Einschränkungen
- Perplexity hat Rate Limits (ca. 50 Requests/Minute bei Pro)
- Tavily Free Tier: 1000 API Calls/Monat
- OpenAI Web Search ist nur Fallback und liefert weniger strukturierte Ergebnisse
- Social-Media-Daten über Tavily sind oft unvollständig (kein direkter API-Zugang zu Instagram/X)

## Troubleshooting
| Problem | Lösung |
|---------|--------|
| `PERPLEXITY_API_KEY nicht gesetzt` | API Key in `.env` eintragen |
| Perplexity + OpenAI beide fehlgeschlagen | API Keys prüfen, Internetverbindung checken |
| Dossier hat leeren Freshness-Check | Tavily API Key prüfen oder Gast hat keine aktuellen News |
