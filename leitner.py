"""Leitner-System: Fälligkeit und Bewertung einer Karte."""

from datetime import date, timedelta

import streamlit as st

from daten import als_datum, new_entry, save_progress
from konfig import BOX_INTERVALS, MAX_BOX


def is_due(word: str, progress: dict, today: date) -> bool:
    entry = progress.get(word)
    return entry is None or als_datum(entry["next_due"]) <= today


def grade(word: str, known: bool, progress: dict) -> None:
    """Bewertet eine Karte und schreibt den Fortschritt sofort auf die Platte."""
    entry = dict(progress.get(word, new_entry()))
    if known:
        entry["box"] = min(entry["box"] + 1, MAX_BOX)
        entry["richtig"] += 1
    else:
        entry["box"] = 1
        entry["falsch"] += 1
    entry["next_due"] = (date.today() + timedelta(days=BOX_INTERVALS[entry["box"]])).isoformat()
    progress[word] = entry
    save_progress(progress)
    st.session_state.gelernt_heute += 1
