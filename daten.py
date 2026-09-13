"""Laden und Speichern von vocab.csv, texte.json und progress.json.

Geschrieben wird immer atomar (temporäre Datei + os.replace), gelesen
immer explizit als UTF-8. Defekte Dateien führen nie zum Absturz.
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from konfig import COLUMNS, MAX_BOX, PROGRESS_JSON, TEXTE_JSON, VERBEN_JSON, VOCAB_CSV


@st.cache_data(show_spinner=False)
def load_vocab() -> pd.DataFrame:
    """Liest vocab.csv als UTF-8 und normalisiert die Spalten."""
    df = pd.read_csv(VOCAB_CSV, encoding="utf-8", dtype=str, keep_default_na=False)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS].fillna("")
    for col in COLUMNS:
        df[col] = df[col].astype(str).str.strip()
    df = df[df["russisch"] != ""]
    return df.drop_duplicates(subset="russisch", keep="first").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_texte() -> list[dict]:
    """Liest texte.json als UTF-8. Fehlt oder bricht die Datei, bleibt es leer."""
    try:
        roh = json.loads(TEXTE_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(roh, list):
        return []
    pflicht = ("id", "niveau", "titel", "russisch", "deutsch")
    return [
        {feld: str(eintrag[feld]).strip() for feld in pflicht}
        for eintrag in roh
        if isinstance(eintrag, dict) and all(eintrag.get(f) for f in pflicht)
    ]


@st.cache_data(show_spinner=False)
def load_verben() -> list[dict]:
    """Liest verben.json als UTF-8. Fehlt oder bricht die Datei, bleibt es leer.

    `praesens` darf None sein - быть hat im Russischen keine Präsensformen.
    """
    try:
        roh = json.loads(VERBEN_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if not isinstance(roh, list):
        return []
    verben = []
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        if not all(eintrag.get(f) for f in ("infinitiv", "deutsch", "gruppe")):
            continue
        zeiten = {
            zeit: eintrag[zeit]
            for zeit in ("praesens", "praeteritum")
            if isinstance(eintrag.get(zeit), dict)
            and all(str(f).strip() for f in eintrag[zeit].values())
        }
        if not zeiten:
            continue
        verben.append(
            {
                "infinitiv": str(eintrag["infinitiv"]).strip(),
                "deutsch": str(eintrag["deutsch"]).strip(),
                "gruppe": str(eintrag["gruppe"]).strip(),
                **zeiten,
            }
        )
    return verben


def save_vocab(df: pd.DataFrame) -> None:
    """Schreibt vocab.csv atomar als UTF-8 und leert den Cache."""
    clean = df.reindex(columns=COLUMNS).fillna("")
    for col in COLUMNS:
        clean[col] = clean[col].astype(str).str.strip()
    clean = clean[clean["russisch"] != ""].drop_duplicates(subset="russisch", keep="first")
    _atomic_write(VOCAB_CSV, clean.to_csv(index=False))
    load_vocab.clear()


def _atomic_write(path: Path, text: str) -> None:
    """Erst in eine temporäre Datei im selben Verzeichnis, dann umbenennen."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _as_int(value, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def als_datum(value) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return date.today()


def new_entry() -> dict:
    return {"box": 1, "next_due": date.today().isoformat(), "richtig": 0, "falsch": 0}


def load_progress() -> dict:
    """Lädt progress.json; bei fehlender oder defekter Datei leerer Fortschritt."""
    try:
        raw = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    progress = {}
    for word, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        box = min(max(_as_int(entry.get("box"), 1), 1), MAX_BOX)
        progress[str(word)] = {
            "box": box,
            "next_due": als_datum(entry.get("next_due")).isoformat(),
            "richtig": max(_as_int(entry.get("richtig")), 0),
            "falsch": max(_as_int(entry.get("falsch")), 0),
        }
    return progress


def save_progress(progress: dict) -> None:
    _atomic_write(PROGRESS_JSON, json.dumps(progress, ensure_ascii=False, indent=2))
