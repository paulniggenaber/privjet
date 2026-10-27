"""Laden und Speichern von notion_woerter.csv, den Notion-Zusatzdaten und dem Fortschritt.

Geschrieben wird immer atomar (temporäre Datei + os.replace), gelesen
immer explizit als UTF-8. Defekte Dateien führen nie zum Absturz.
"""

import copy
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

import gist
from konfig import (
    MAX_BOX,
    NOTION_AUSGEBLENDET_JSON,
    NOTION_BEISPIELE_JSON,
    NOTION_COLUMNS,
    NOTION_CSV,
    NOTION_VERBEN_JSON,
    PROGRESS_JSON,
    SITZUNG_JSON,
)


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
def load_beispiele() -> dict:
    """Beispielsätze: "Kategorie|Wort ohne Betonung" -> {"ru": …, "de": …}."""
    try:
        roh = json.loads(NOTION_BEISPIELE_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    if not isinstance(roh, dict):
        return {}
    return {
        str(k): {"ru": str(v["ru"]).strip(), "de": str(v["de"]).strip()}
        for k, v in roh.items()
        if isinstance(v, dict) and v.get("ru") and v.get("de")
    }


@st.cache_data(show_spinner=False)
def load_konjugation() -> dict:
    """Liest notion_verben.json: Infinitiv (ohne Betonung) -> Präsensformen + Imperativ.

    Fehlt oder bricht die Datei, bleibt es leer. Einträge ohne alle sechs
    Präsensformen werden übersprungen; `imperativ` darf None sein.
    """
    try:
        roh = json.loads(NOTION_VERBEN_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    if not isinstance(roh, list):
        return {}
    personen = ("я", "ты", "он/она", "мы", "вы", "они")
    verben = {}
    for eintrag in roh:
        if not isinstance(eintrag, dict) or not eintrag.get("infinitiv"):
            continue
        formen = eintrag.get("formen")
        if not isinstance(formen, dict) or not all(str(formen.get(p) or "").strip() for p in personen):
            continue
        infinitiv = str(eintrag["infinitiv"]).strip()
        verben[infinitiv] = {
            "infinitiv": infinitiv,
            "aspekt": str(eintrag.get("aspekt") or "ipf"),
            "formen": {p: str(formen[p]).strip() for p in personen},
            "imperativ": str(eintrag["imperativ"]).strip() if eintrag.get("imperativ") else None,
            "hinweis": str(eintrag.get("hinweis") or ""),
        }
    return verben


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


def new_entry() -> dict:
    return {"box": 1, "treffer": 0, "richtig": 0, "falsch": 0, "nachholen": False}


def load_sitzung() -> dict:
    """Gespeicherter Stand der letzten Lernsitzung; fehlt/bricht die Datei: leer."""
    try:
        roh = json.loads(SITZUNG_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return roh if isinstance(roh, dict) else {}


def save_sitzung(stand: dict) -> None:
    _atomic_write(SITZUNG_JSON, json.dumps(stand, ensure_ascii=False, indent=2))


def load_ausgeblendet() -> set[str]:
    """ids der aus der Wortbank entfernten Wörter; fehlt die Datei, ist nichts entfernt."""
    try:
        roh = json.loads(NOTION_AUSGEBLENDET_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()
    return {str(i) for i in roh} if isinstance(roh, list) else set()


def save_ausgeblendet(ids: set[str]) -> None:
    _atomic_write(NOTION_AUSGEBLENDET_JSON, json.dumps(sorted(ids), ensure_ascii=False, indent=2))


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
            "treffer": max(_as_int(entry.get("treffer")), 0),
            "nachholen": bool(entry.get("nachholen", False)),
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
