"""Kyrillisches Tastenfeld (ЙЦУКЕН) als Eingabehilfe."""

import streamlit as st


# ЙЦУКЕН, das russische Standardlayout. Reihenlaengen 13/11/9 - die kuerzeren
# Reihen werden eingerueckt, damit es wie eine echte Tastatur aussieht.
TASTATUR_REIHEN = ["ёйцукенгшщзхъ", "фывапролджэ", "ячсмитьбю"]


TASTATUR_BREITE = 13


def _taste(zeichen: str, ziel: str, gross_key: str) -> None:
    """Callback einer Buchstabentaste - laeuft vor dem naechsten Rerun."""
    st.session_state[ziel] += zeichen.upper() if st.session_state[gross_key] else zeichen


def _zeichen_anhaengen(zeichen: str, ziel: str) -> None:
    st.session_state[ziel] += zeichen


def _ruecktaste(ziel: str) -> None:
    st.session_state[ziel] = st.session_state[ziel][:-1]


def zeige_tastenfeld(ziel: str) -> None:
    """Rendert das kyrillische Tastenfeld; schreibt in st.session_state[ziel].

    Alle Widget-Keys hängen am Zielfeld, damit zwei Tastenfelder im selben
    Durchlauf (Tippmodus und Übersetzen) nicht kollidieren.
    """
    gross_key = f"gross_{ziel}"
    st.session_state.setdefault(gross_key, False)
    gross = st.session_state[gross_key]
    for reihe in TASTATUR_REIHEN:
        versatz = (TASTATUR_BREITE - len(reihe)) // 2
        spalten = st.columns(TASTATUR_BREITE, gap="small")
        for i, zeichen in enumerate(reihe):
            spalten[versatz + i].button(
                zeichen.upper() if gross else zeichen,
                key=f"taste_{ziel}_{zeichen}",
                on_click=_taste,
                args=(zeichen, ziel, gross_key),
                width="stretch",
            )
    links, mitte, rechts = st.columns([2, 1, 1])
    links.button(
        "␣ Leerzeichen", key=f"taste_{ziel}_leer",
        on_click=_zeichen_anhaengen, args=(" ", ziel), width="stretch",
    )
    mitte.button(
        "⌫ Löschen", key=f"taste_{ziel}_back",
        on_click=_ruecktaste, args=(ziel,), width="stretch",
    )
    rechts.toggle("⇧ Groß", key=gross_key)
