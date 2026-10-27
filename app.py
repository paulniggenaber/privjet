"""Vokabeltrainer Russisch-Deutsch - Einstiegspunkt.

Starten mit:  streamlit run app.py
"""

import json
from datetime import date

import streamlit as st

from daten import (
    load_ausgeblendet,
    load_beispiele,
    load_konjugation,
    load_notion,
    load_progress,
    load_sitzung,
    save_sitzung,
)
from konfig import NOTION_PROGRESS_JSON, SITZUNG_KEYS
from konjugation import DEFAULTS as KONJ_DEFAULTS
from konjugation import tab_konjugation
from notion_woerter import DEFAULTS as NOTION_DEFAULTS
from notion_woerter import tab_notion


def init_state() -> None:
    defaults = {
        "gelernt_heute": 0,
        "sitzungs_datum": date.today().isoformat(),
        **KONJ_DEFAULTS,
        **NOTION_DEFAULTS,
    }
    # Neue Sitzung (Seite neu geladen, App neu gestartet): da weitermachen, wo
    # die letzte aufgehört hat - sonst würde mitten in der Abfrage neu gezogen.
    if "_sitzung" not in st.session_state:
        gespeichert = load_sitzung()
        for key in SITZUNG_KEYS:
            if key in gespeichert:
                st.session_state.setdefault(key, gespeichert[key])
        st.session_state._sitzung = {k: gespeichert.get(k) for k in SITZUNG_KEYS}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if st.session_state.sitzungs_datum != date.today().isoformat():
        st.session_state.sitzungs_datum = date.today().isoformat()
        st.session_state.gelernt_heute = 0


def main() -> None:
    st.set_page_config(page_title="Vokabeltrainer RU-DE", page_icon="🇷🇺", layout="centered")
    st.title("🇷🇺 Vokabeltrainer Russisch – Deutsch")
    init_state()

    notion_alle = load_notion()
    ausgeblendet = load_ausgeblendet()

    vokabeln, konjugation = st.tabs(["Vokabeln", "Konjugation"])
    with vokabeln:
        tab_notion(notion_alle, load_progress(NOTION_PROGRESS_JSON), ausgeblendet, load_beispiele())
    with konjugation:
        tab_konjugation(notion_alle[~notion_alle["id"].isin(ausgeblendet)], load_konjugation())

    sichere_sitzung()


def sichere_sitzung() -> None:
    """Schreibt den Sitzungsstand, wenn er sich seit dem letzten Mal geändert hat."""
    stand = {k: st.session_state.get(k) for k in SITZUNG_KEYS}
    if stand != st.session_state._sitzung:
        save_sitzung(stand)
        st.session_state._sitzung = json.loads(json.dumps(stand))


if __name__ == "__main__":
    main()
