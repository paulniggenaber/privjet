"""Vokabeltrainer Russisch-Deutsch - Einstiegspunkt.

Starten mit:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

from daten import load_progress, load_texte, load_verben, load_vocab
from konfig import DE_RU, MIXED, M_GEMISCHT, M_KARTEN, M_TIPPEN, RU_DE, VOCAB_CSV
from konjugation import DEFAULTS as KONJ_DEFAULTS
from konjugation import tab_konjugation
from lernen import tab_lernen
from uebersetzen import tab_uebersetzen
from verwalten import tab_verwalten


def init_state() -> None:
    defaults = {
        "karte": None,          # russisches Wort der aktuellen Karte
        "aufgedeckt": False,
        "karten_richtung": RU_DE,  # bei "gemischt" pro Karte einmal gewürfelt
        "karten_tippen": False,    # bei Modus "gemischt" pro Karte einmal gewürfelt
        "tipp_status": None,       # None | "richtig" | "fast" | "falsch"
        "tipp_eingabe": "",
        "tipp_pruefen": False,
        "text_id": None,
        "text_geprueft": False,
        "text_eingabe": "",
        "text_sig": None,
        "text_richtung": RU_DE,   # bei "gemischt" pro Text gewürfelt
        "text_neu": False,
        "filter_sig": None,
        "alle_ueben": False,
        "gelernt_heute": 0,
        "sitzungs_datum": date.today().isoformat(),
        **KONJ_DEFAULTS,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if st.session_state.sitzungs_datum != date.today().isoformat():
        st.session_state.sitzungs_datum = date.today().isoformat()
        st.session_state.gelernt_heute = 0


def main() -> None:
    st.set_page_config(page_title="Vokabeltrainer RU-DE", page_icon="🇷🇺", layout="centered")
    st.title("🇷🇺 Vokabeltrainer Russisch – Deutsch")
    init_state()

    if not VOCAB_CSV.exists():
        st.error(f"`{VOCAB_CSV.name}` wurde nicht gefunden. Bitte die Datei anlegen.")
        st.stop()
    try:
        df = load_vocab()
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        st.error(f"`{VOCAB_CSV.name}` konnte nicht gelesen werden: {exc}")
        st.stop()
    if df.empty:
        st.error(f"`{VOCAB_CSV.name}` enthält keine Vokabeln.")
        st.stop()

    progress = load_progress()

    with st.sidebar:
        st.header("Filter")
        alle_niveaus = sorted(n for n in df["niveau"].unique() if n)
        alle_wortarten = sorted(w for w in df["wortart"].unique() if w)
        niveaus = st.multiselect("Niveau", alle_niveaus, default=alle_niveaus)
        wortarten = st.multiselect("Wortart", alle_wortarten, default=alle_wortarten)
        richtung = st.radio("Abfragerichtung", [RU_DE, DE_RU, MIXED], index=0)
        modus = st.radio(
            "Modus",
            [M_KARTEN, M_TIPPEN, M_GEMISCHT],
            index=0,
            help="Karten: selbst bewerten. Tippen: Antwort eingeben, die App prüft. "
            "Gemischt: pro Karte zufällig das eine oder das andere.",
        )
        st.divider()
        if st.session_state.alle_ueben and st.button("Freies Üben beenden"):
            st.session_state.alle_ueben = False
            st.rerun()
        st.caption(f"{len(df)} Vokabeln · {len(progress)} davon begonnen")

    lernen, konjugation, uebersetzen, verwalten = st.tabs(
        ["Lernen", "Konjugation", "Übersetzen", "Vokabeln verwalten"]
    )
    with lernen:
        tab_lernen(
            df, progress, niveaus or alle_niveaus, wortarten or alle_wortarten, richtung, modus
        )
    with konjugation:
        tab_konjugation(load_verben())
    with uebersetzen:
        tab_uebersetzen(load_texte())
    with verwalten:
        tab_verwalten(df, progress)


if __name__ == "__main__":
    main()
