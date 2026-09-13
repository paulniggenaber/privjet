"""Tab „Übersetzen“: Text vorlegen, übertragen, mit der Musterlösung vergleichen."""

import html
import random

import streamlit as st

from konfig import DE_RU, MIXED, RU_DE, STUFEN, TEXTE_JSON
from tastenfeld import zeige_tastenfeld
from vergleich import abgleich


def _neuer_text(pool: list[dict]) -> None:
    kandidaten = [t for t in pool if t["id"] != st.session_state.text_id] or pool
    st.session_state.text_id = random.choice(kandidaten)["id"]
    st.session_state.text_richtung = random.choice([RU_DE, DE_RU])
    st.session_state.text_geprueft = False
    # Vor dem Rendern des Textfelds zuruecksetzen - danach waere es ein Fehler.
    st.session_state.text_eingabe = ""


def tab_uebersetzen(texte: list[dict]) -> None:
    if not texte:
        st.error(
            f"`{TEXTE_JSON.name}` fehlt oder ist unlesbar. "
            "Ohne diese Datei gibt es keine Texte zum Übersetzen."
        )
        return

    stufen = sorted({t["niveau"] for t in texte})
    stufe_sp, richtung_sp, knopf = st.columns([2, 2, 1], vertical_alignment="bottom")
    niveau = stufe_sp.selectbox(
        "Schwierigkeit", stufen, format_func=lambda n: STUFEN.get(n, n), key="text_niveau"
    )
    richtung = richtung_sp.selectbox(
        "Richtung", [RU_DE, DE_RU, MIXED], key="text_richtung_wahl",
        help="RU → DE: russischen Text ins Deutsche übertragen. "
        "DE → RU: deutschen Text ins Russische. Gemischt: pro Text zufällig.",
    )
    pool = [t for t in texte if t["niveau"] == niveau]

    # Neu gezogen wird hier oben, weil _neuer_text das Eingabefeld leert und
    # das nach dem Erzeugen des Widgets nicht mehr erlaubt waere.
    sig = (niveau, len(pool), richtung)
    if (
        sig != st.session_state.text_sig
        or st.session_state.text_id not in {t["id"] for t in pool}
        or st.session_state.text_neu
    ):
        st.session_state.text_sig = sig
        st.session_state.text_neu = False
        _neuer_text(pool)
    if knopf.button("🔀 Anderer Text", width="stretch"):
        st.session_state.text_neu = True
        st.rerun()

    text = next(t for t in texte if t["id"] == st.session_state.text_id)
    aktuelle_richtung = st.session_state.text_richtung if richtung == MIXED else richtung
    nach_russisch = aktuelle_richtung == DE_RU
    quelle = text["deutsch"] if nach_russisch else text["russisch"]
    loesung = text["russisch"] if nach_russisch else text["deutsch"]
    zielsprache = "ins Russische" if nach_russisch else "ins Deutsche"

    st.caption(
        f"{STUFEN.get(text['niveau'], text['niveau'])}  ·  {aktuelle_richtung}  ·  "
        f"{len(quelle.split())} Wörter  ·  Text "
        f"{[t['id'] for t in pool].index(text['id']) + 1} von {len(pool)}"
    )
    with st.container(border=True):
        st.markdown(f"**{text['titel']}**")
        st.markdown(
            f"<div style='font-size:1.08rem;line-height:1.75;'>{html.escape(quelle)}</div>",
            unsafe_allow_html=True,
        )

    st.text_area(
        f"Deine Übersetzung {zielsprache}",
        key="text_eingabe",
        height=210,
        placeholder=f"Übersetze den Text {zielsprache}…",
    )

    if not st.session_state.text_geprueft:
        gedrueckt = st.button("Musterlösung zeigen", type="primary", width="stretch")
        if nach_russisch:
            with st.expander("⌨️ Kyrillische Tastatur"):
                zeige_tastenfeld("text_eingabe")
        if gedrueckt:
            st.session_state.text_geprueft = True
            st.rerun()
        return

    st.divider()
    st.markdown("#### Musterlösung")
    st.info(loesung)

    eingabe = st.session_state.text_eingabe.strip()
    if eingabe:
        gefunden, fehlend = abgleich(loesung, eingabe)
        gesamt = len(gefunden) + len(fehlend)
        if gesamt:
            st.progress(len(gefunden) / gesamt, text=f"{len(gefunden)} von {gesamt} Stichwörtern")
        if fehlend:
            st.caption("Nicht wiedergefunden: " + ", ".join(sorted(fehlend)))
        st.caption(
            "Nur ein grober Abgleich der Inhaltswörter – Synonyme und "
            "umgestellte Sätze erkennt er nicht. Die Bewertung bleibt bei dir."
        )
    else:
        st.caption("Du hast nichts eingegeben – vergleiche einfach selbst.")

    if st.button("Nächster Text →", type="primary", width="stretch"):
        st.session_state.text_neu = True
        st.rerun()
