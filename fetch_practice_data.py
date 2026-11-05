"""Holt die Trainingsdaten und speichert sie mit Zeitstempel unter data/tests/.

Liest nur den Export der Data-Center-Seite. Fährt keine Runden.
Lauf: python3 fetch_practice_data.py
"""
import sys
from datetime import datetime
from pathlib import Path

from get_practice_data import get_practice_data

OUT_DIR = Path(__file__).with_name("data") / "tests"


def main():
    try:
        df = get_practice_data()
    except RuntimeError as err:
        sys.exit(str(err))
    if df is None:
        sys.exit("Abruf fehlgeschlagen. Zugangsdaten in .env und Erreichbarkeit der Seite prüfen.")
    if "Lap Time" not in df.columns:
        sys.exit("Antwort sieht nicht nach Trainingsdaten aus (Spalte Lap Time fehlt). Nichts gespeichert.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"practice_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(path, "x") as f:
        df.to_csv(f, index=False)
    print(f"{len(df)} Zeilen gespeichert: {path}")


if __name__ == "__main__":
    main()
