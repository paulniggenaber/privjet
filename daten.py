"""Laden und Speichern von vocab.csv, notion_woerter.csv, texte.json und progress.json.

Geschrieben wird immer atomar (temporäre Datei + os.replace), gelesen
immer explizit als UTF-8. Defekte Dateien führen nie zum Absturz.
"""

import copy
import json
import os
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import gist
from konfig import (
    COLUMNS,
    MAX_BOX,
    NOTION_COLUMNS,
    NOTION_CSV,
    PROGRESS_JSON,
    TEXTE_JSON,
    VERBEN_JSON,
    VOCAB_CSV,
)


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
def load_notion() -> pd.DataFrame:
    """Liest notion_woerter.csv; fehlt die Datei, bleibt die Wortbank leer.

    Schlüssel für den Fortschritt ist `id` = "kategorie|russisch", weil
    dasselbe russische Wort in mehreren Kategorien vorkommen kann (что, есть).
    """
    try:
        df = pd.read_csv(NOTION_CSV, encoding="utf-8", dtype=str, keep_default_na=False)
    except (FileNotFoundError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError):
        df = pd.DataFrame(columns=NOTION_COLUMNS)
    df = df.reindex(columns=NOTION_COLUMNS).fillna("")
    for col in NOTION_COLUMNS:
        df[col] = df[col].astype(str).str.strip()
    df = df[(df["russisch"] != "") & (df["deutsch"] != "")]
    df = df.drop_duplicates(subset=["kategorie", "russisch"], keep="first").reset_index(drop=True)
    df["id"] = df["kategorie"] + "|" + df["russisch"]
    return df


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


def _normalisiere(raw) -> dict:
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


def _gist_konfig() -> dict | None:
    """[gist] id + token aus den Streamlit-Secrets, sonst None (= lokale Datei)."""
    try:
        konfig = st.secrets.get("gist")
    except Exception:  # keine secrets.toml vorhanden
        return None
    if konfig and konfig.get("id") and konfig.get("token"):
        return {"id": str(konfig["id"]), "token": str(konfig["token"])}
    return None


def _gist_laden(konfig: dict, name: str) -> dict:
    try:
        inhalt = gist.lesen(konfig["id"], konfig["token"], name)
    except gist.GistFehler as exc:
        # Lieber anhalten als mit leerem Fortschritt weitermachen und ihn
        # beim nächsten Speichern im Gist zu überschreiben.
        st.error(f"Lernfortschritt konnte nicht aus dem Gist geladen werden: {exc}. Bitte neu laden.")
        st.stop()
    try:
        return _normalisiere(json.loads(inhalt)) if inhalt else {}
    except json.JSONDecodeError:
        return {}


def load_progress(pfad: Path = PROGRESS_JSON) -> dict:
    """Lädt den Fortschritt; bei fehlender oder defekter Datei leerer Fortschritt.

    Mit Gist-Secrets (Streamlit Cloud) kommt er aus dem Gist und wird pro
    Sitzung zwischengespeichert, damit nicht jeder Klick eine Anfrage kostet.
    """
    konfig = _gist_konfig()
    if konfig is None:
        try:
            return _normalisiere(json.loads(pfad.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
            return {}
    key = f"_gist_{pfad.name}"
    if key not in st.session_state:
        progress = _gist_laden(konfig, pfad.name)
        st.session_state[key] = progress
        st.session_state[key + "_stand"] = copy.deepcopy(progress)
    return st.session_state[key]


def save_progress(progress: dict, pfad: Path = PROGRESS_JSON) -> None:
    konfig = _gist_konfig()
    if konfig is None:
        _atomic_write(pfad, json.dumps(progress, ensure_ascii=False, indent=2))
        return
    # Nur die in dieser Sitzung geänderten Wörter in den aktuellen Gist-Stand
    # übernehmen - so überschreibt ein zweites Gerät nicht den Rest.
    key = f"_gist_{pfad.name}"
    stand = st.session_state.get(key + "_stand", {})
    aktuell = _gist_laden(konfig, pfad.name)
    for wort in set(stand) | set(progress):
        if wort not in progress:
            aktuell.pop(wort, None)
        elif progress[wort] != stand.get(wort):
            aktuell[wort] = progress[wort]
    try:
        gist.schreiben(
            konfig["id"], konfig["token"], pfad.name,
            json.dumps(aktuell, ensure_ascii=False, indent=2),
        )
    except gist.GistFehler as exc:
        st.error(f"Lernfortschritt konnte nicht im Gist gespeichert werden: {exc}")
        st.stop()
    progress.clear()
    progress.update(aktuell)
    st.session_state[key] = progress
    st.session_state[key + "_stand"] = copy.deepcopy(aktuell)
