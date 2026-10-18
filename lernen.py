"""Tab „Lernen“: Kartenwahl, Flashcard, Kartenmodus und Tippmodus."""

import random

import pandas as pd
import streamlit as st

from batch import batch_bereich
from karte import zeige_flashcard
from konfig import DE_RU, MAX_BOX, MIXED, M_GEMISCHT, M_TIPPEN, RU_DE
from leitner import box, frist_setzen, grade, stand, ziehe
from tastenfeld import zeige_tastenfeld
from vergleich import bewerten


def ziehe_karte(pool: list[str], progress: dict, offen: bool = True) -> None:
    """Zieht eine neue Karte (gewichtet nach Box) - nach dem Bewerten bzw. bei Filterwechsel."""
    zuletzt = st.session_state.karte or st.session_state.get("letzte_karte")
    st.session_state.karte = ziehe("", pool, progress, ausser=zuletzt, offen=offen)
    if st.session_state.karte is None:
        return
    st.session_state.aufgedeckt = False
    st.session_state.karten_richtung = random.choice([RU_DE, DE_RU])
    st.session_state.karten_tippen = random.choice([True, False])
    # Vor dem Rendern des Eingabefelds zuruecksetzen - danach waere es ein Fehler.
    st.session_state.tipp_status = None
    st.session_state.tipp_eingabe = ""
    st.session_state.tipp_pruefen = False


def _pruefen() -> None:
    """on_change des Eingabefelds - so löst auch die Eingabetaste aus."""
    st.session_state.tipp_pruefen = True


def tippbereich(karte, antwort: str, progress: dict, antwort_russisch: bool) -> bool:
    """Eingabefeld und Auswertung. Gibt True zurück, wenn schon bewertet wurde."""
    if st.session_state.tipp_status is None:
        st.text_input(
            "Antwort eintippen",
            key="tipp_eingabe",
            placeholder="Antwort eintippen und Eingabetaste drücken",
            label_visibility="collapsed",
            on_change=_pruefen,
        )
        gedrueckt = st.button("Prüfen", type="primary", width="stretch")
        if antwort_russisch:
            with st.expander("⌨️ Kyrillische Tastatur"):
                zeige_tastenfeld("tipp_eingabe")
        if gedrueckt or st.session_state.tipp_pruefen:
            st.session_state.tipp_pruefen = False
            st.session_state.tipp_status = bewerten(st.session_state.tipp_eingabe, antwort)
            st.session_state.aufgedeckt = True
            st.rerun()
        return False

    getippt = st.session_state.tipp_eingabe.strip()
    status = st.session_state.tipp_status
    if status == "richtig":
        st.success(f"Richtig! ✓  „{getippt}“")
    elif status == "fast":
        st.warning(f"Fast – du hattest „{getippt}“, richtig ist „{antwort}“.")
    else:
        st.error(f"„{getippt or '(nichts)'}“ – richtig wäre „{antwort}“.")
    return True


def tab_lernen(df: pd.DataFrame, progress: dict, niveaus, wortarten, richtung, modus) -> None:
    gefiltert = df[df["niveau"].isin(niveaus) & df["wortart"].isin(wortarten)]

    sig = (tuple(sorted(niveaus)), tuple(sorted(wortarten)), modus)
    filter_geaendert = sig != st.session_state.filter_sig
    st.session_state.filter_sig = sig

    pool = list(gefiltert["russisch"])
    boxen = [box(w, progress) for w in pool]
    anteil = sum((b - 1) / (MAX_BOX - 1) for b in boxen) / len(boxen) if boxen else 0.0

    st.progress(anteil, text=f"Deck-Fortschritt: {anteil:.0%} ({len(gefiltert)} Karten im Filter)")
    m1, m2, m3 = st.columns(3)
    m1.metric("In Box 1", boxen.count(1))
    m2.metric("Heute gelernt", st.session_state.gelernt_heute)
    m3.metric("In Box 5", boxen.count(MAX_BOX))
    st.divider()

    if gefiltert.empty:
        st.warning("Keine Vokabeln passen zu den gewählten Filtern.")
        return

    batch_rest = batch_bereich("", list(gefiltert["russisch"]), progress)
    if batch_rest is not None:
        vorhanden = set(df["russisch"])
        pool = [w for w in batch_rest if w in vorhanden]
        if not pool:
            return
    if filter_geaendert or st.session_state.karte not in pool:
        ziehe_karte(pool, progress, offen=batch_rest is None)

    karte = df[df["russisch"] == st.session_state.karte].iloc[0]
    aktuelle_richtung = st.session_state.karten_richtung if richtung == MIXED else richtung
    frage, antwort = (
        (karte["russisch"], karte["deutsch"])
        if aktuelle_richtung == RU_DE
        else (karte["deutsch"], karte["russisch"])
    )

    tippen = st.session_state.karten_tippen if modus == M_GEMISCHT else (modus == M_TIPPEN)
    if modus == M_GEMISCHT:
        st.caption("Tippmodus" if tippen else "Karte selbst bewerten")

    zeige_flashcard(
        frage, antwort, karte, aktuelle_richtung, stand(karte["russisch"], progress),
        st.session_state.aufgedeckt,
    )

    if tippen:
        if not tippbereich(karte, antwort, progress, aktuelle_richtung == DE_RU):
            return
        status = st.session_state.tipp_status
    else:
        if not st.session_state.aufgedeckt:
            if st.button("🔄 Karte umdrehen", type="primary", width="stretch"):
                st.session_state.aufgedeckt = True
                st.rerun()
            return
        status = None

    def bewerten(gewusst: bool) -> None:
        grade(karte["russisch"], known=gewusst, progress=progress)
        if not gewusst:
            frist_setzen("", karte["russisch"])
        st.session_state.letzte_karte = karte["russisch"]
        st.session_state.karte = None
        st.rerun()

    if status == "richtig":
        # Eindeutig richtig - kein Grund, noch einmal nachzufragen.
        if st.button("Weiter →", type="primary", width="stretch"):
            bewerten(True)
        return

    links, rechts = st.columns(2)
    nochmal_primaer = status in ("fast", "falsch")
    if links.button(
        "↺ Nochmal", width="stretch", type="primary" if nochmal_primaer else "secondary"
    ):
        bewerten(False)
    if rechts.button(
        "✓ Gewusst" if status is None else "✓ Zählt als gewusst",
        width="stretch",
        type="secondary" if nochmal_primaer else "primary",
    ):
        bewerten(True)
