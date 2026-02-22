"""
Hauptskript: Gästedossier-Pipeline.
Orchestriert Research und Dossier-Erstellung.

Usage:
    python tools/run_pipeline.py "Gastname"
"""

import sys
import time
from pathlib import Path

# Projekt-Root ermitteln
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from research_guest import run_research
from create_dossier import create_dossier


def run_pipeline(guest_name: str) -> Path:
    """Führt die komplette Pipeline aus: Research → Dossier."""
    print("=" * 60)
    print(f"  GÄSTEDOSSIER-PIPELINE: {guest_name}")
    print("=" * 60)
    start = time.time()

    # Schritt 1: Research
    print("\n📋 SCHRITT 1/2: Deep Research")
    print("-" * 40)
    research_path = run_research(guest_name)

    # Schritt 2: Dossier erstellen
    print(f"\n📋 SCHRITT 2/2: Dossier erstellen")
    print("-" * 40)
    dossier_path = create_dossier(guest_name, research_path)

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"  FERTIG in {elapsed:.0f} Sekunden")
    print(f"  Research:  {research_path}")
    print(f"  Dossier:   {dossier_path}")
    print("=" * 60)

    return dossier_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/run_pipeline.py \"Gastname\"")
        print("Beispiel: python tools/run_pipeline.py \"Udo Lindenberg\"")
        sys.exit(1)

    guest = sys.argv[1]
    run_pipeline(guest)
