"""Tab „Lernen“: Kartenwahl, Flashcard, Kartenmodus und Tippmodus."""

import random
from datetime import date

import pandas as pd
import streamlit as st

from daten import als_datum
from karte import zeige_flashcard
from konfig import DE_RU, MAX_BOX, MIXED, M_GEMISCHT, M_TIPPEN, RU_DE
from leitner import grade, is_due
from tastenfeld import zeige_tastenfeld
from vergleich import bewerten


def ziehe_karte(pool: list[str]) -> None:
    """Zieht eine neue Karte - nur von den Bewertungs-Buttons bzw. bei Filterwechsel."""
    if not pool:
        st.session_state.karte = None
        return
    kandidaten = [w for w in pool if w != st.session_state.karte] or pool
    st.session_state.karte = random.choice(kandidaten)
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
    heute = date.today()
    gefiltert = df[df["niveau"].isin(niveaus) & df["wortart"].isin(wortarten)]

    sig = (tuple(sorted(niveaus)), tuple(sorted(wortarten)), st.session_state.alle_ueben, modus)
    filter_geaendert = sig != st.session_state.filter_sig
    st.session_state.filter_sig = sig

    faellig = [w for w in gefiltert["russisch"] if is_due(w, progress, heute)]
    pool = list(gefiltert["russisch"]) if st.session_state.alle_ueben else faellig

    if filter_geaendert or st.session_state.karte not in pool:
        ziehe_karte(pool)

    in_box5 = sum(1 for w in gefiltert["russisch"] if progress.get(w, {}).get("box") == MAX_BOX)
    boxen = [progress.get(w, {}).get("box", 1) for w in gefiltert["russisch"]]
    anteil = sum((b - 1) / (MAX_BOX - 1) for b in boxen) / len(boxen) if boxen else 0.0

    st.progress(anteil, text=f"Deck-Fortschritt: {anteil:.0%} ({len(gefiltert)} Karten im Filter)")
    m1, m2, m3 = st.columns(3)
    m1.metric("Heute fällig", len(faellig))
    m2.metric("Heute gelernt", st.session_state.gelernt_heute)
    m3.metric("In Box 5", in_box5)
    st.divider()

    if gefiltert.empty:
        st.warning("Keine Vokabeln passen zu den gewählten Filtern.")
        return

    if not pool:
        naechste = min(als_datum(progress[w]["next_due"]) for w in gefiltert["russisch"])
        st.success(
            f"Alles erledigt für heute! 🎉 Die nächsten Karten sind am "
            f"**{naechste.strftime('%d.%m.%Y')}** fällig "
            f"(in {(naechste - heute).days} Tag(en))."
        )
        if st.button("Trotzdem weiterüben", type="primary"):
            st.session_state.alle_ueben = True
            st.rerun()
        return

    if st.session_state.alle_ueben:
        st.caption("Freies Üben aktiv – alle Karten des Filters sind freigeschaltet.")

    karte = df[df["russisch"] == st.session_state.karte].iloc[0]
    aktuelle_richtung = st.session_state.karten_richtung if richtung == MIXED else richtung
    frage, antwort = (
        (karte["russisch"], karte["deutsch"])
        if aktuelle_richtung == RU_DE
        else (karte["deutsch"], karte["russisch"])
    )

    box = progress.get(karte["russisch"], {}).get("box", 1)
    tippen = st.session_state.karten_tippen if modus == M_GEMISCHT else (modus == M_TIPPEN)
    if modus == M_GEMISCHT:
        st.caption("Tippmodus" if tippen else "Karte selbst bewerten")

    zeige_flashcard(frage, antwort, karte, aktuelle_richtung, box, st.session_state.aufgedeckt)

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
