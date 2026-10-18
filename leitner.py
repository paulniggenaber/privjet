"""Box-System: gewichtete Kartenwahl und Bewertung.

- Aufstieg von Box k nach k+1 nach 2^(k-1) richtigen Antworten in Box k
  (1 → 2: einmal, 2 → 3: zweimal, 3 → 4: viermal, 4 → 5: achtmal).
- Falsch: zwei Boxen zurück (mindestens Box 1), Treffer wieder bei 0.
- Keine Fälligkeitstermine: Jede Karte kann jederzeit kommen, je höher die
  Box, desto seltener (Gewicht halbiert sich pro Box).
- Zuletzt falsch beantwortete Karten („nachholen“) kommen im offenen Modus
  FEHLER_FAKTOR-mal häufiger, bis sie einmal richtig beantwortet wurden.
"""

import random
from pathlib import Path

import streamlit as st

from daten import new_entry, save_progress
from konfig import BOX_GEWICHT, FEHLER_FAKTOR, MAX_BOX, PROGRESS_JSON


def box(word: str, progress: dict) -> int:
    return progress.get(word, {}).get("box", 1)


def treffer_noetig(b: int) -> int:
    """Richtige Antworten, die in Box b für den Aufstieg nötig sind."""
    return 2 ** (b - 1)


def stand(word: str, progress: dict) -> str:
    """Kurztext für die Karte, z. B. „Box 3/5 · 1/4“ (Treffer bis zum Aufstieg)."""
    entry = progress.get(word, {})
    b = entry.get("box", 1)
    text = f"Box {b}/{MAX_BOX}"
    if b < MAX_BOX:
        text += f" · {entry.get('treffer', 0)}/{treffer_noetig(b)}"
    if entry.get("nachholen"):
        text += " · zuletzt falsch"
    return text


def gewicht(word: str, progress: dict, fehler_bonus: bool = True) -> float:
    g = BOX_GEWICHT[box(word, progress)]
    if fehler_bonus and progress.get(word, {}).get("nachholen"):
        g *= FEHLER_FAKTOR
    return g


def waehle(
    pool: list[str], progress: dict, ausser: str | None = None, fehler_bonus: bool = True
) -> str | None:
    """Zufällige Karte aus dem Pool, gewichtet nach Box (und Fehler-Bonus);
    `ausser` kommt nicht zweimal hintereinander."""
    kandidaten = [w for w in pool if w != ausser] or pool
    if not kandidaten:
        return None
    gewichte = [gewicht(w, progress, fehler_bonus) for w in kandidaten]
    return random.choices(kandidaten, weights=gewichte, k=1)[0]


def grade(word: str, known: bool, progress: dict, pfad: Path = PROGRESS_JSON) -> None:
    """Bewertet eine Karte und schreibt den Fortschritt sofort auf die Platte."""
    entry = {**new_entry(), **progress.get(word, {})}
    if known:
        entry["richtig"] += 1
        entry["treffer"] += 1
        entry["nachholen"] = False
        if entry["box"] < MAX_BOX and entry["treffer"] >= treffer_noetig(entry["box"]):
            entry["box"] += 1
            entry["treffer"] = 0
    else:
        entry["falsch"] += 1
        entry["box"] = max(entry["box"] - 2, 1)
        entry["treffer"] = 0
        entry["nachholen"] = True
    progress[word] = entry
    save_progress(progress, pfad)
    st.session_state.gelernt_heute += 1
