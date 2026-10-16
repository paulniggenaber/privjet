"""Tab „Notion-Wörter“: die Wortbank aus Notion als Karteikarten, immer DE → RU.

Eigener Fortschritt in notion_progress.json, damit sich die Boxen nicht mit
vocab.csv vermischen. Alle Session-Keys tragen das Präfix `n_`, weil alle Tabs
in jedem Lauf gerendert werden und sich sonst die Karte teilen würden.
"""

import random
from datetime import date

import pandas as pd
import streamlit as st

from batch import batch_bereich
from daten import als_datum
from karte import zeige_flashcard
from konfig import DE_RU, MAX_BOX, NOTION_GRUPPEN, NOTION_PROGRESS_JSON
from leitner import grade, is_due


DEFAULTS = {
    "n_karte": None,        # id der aktuellen Karte ("kategorie|russisch")
    "n_aufgedeckt": False,
    "n_filter_sig": None,
    "n_alle_ueben": False,
}


def _gruppe(kategorie: str) -> str:
    return kategorie if kategorie in NOTION_GRUPPEN else "Rest"


def _ziehe_karte(pool: list[str]) -> None:
    if not pool:
        st.session_state.n_karte = None
        return
    kandidaten = [w for w in pool if w != st.session_state.n_karte] or pool
    st.session_state.n_karte = random.choice(kandidaten)
    st.session_state.n_aufgedeckt = False


def tab_notion(df: pd.DataFrame, progress: dict) -> None:
    if df.empty:
        st.info("Noch keine Notion-Wörter vorhanden – `notion_import.py` ausführen.")
        return

    heute = date.today()
    gruppen = st.pills(
        "Wortart", NOTION_GRUPPEN, selection_mode="multi", default=NOTION_GRUPPEN, key="n_gruppen"
    ) or NOTION_GRUPPEN
    gefiltert = df[df["kategorie"].map(_gruppe).isin(gruppen)]

    neu_heute = int((gefiltert["hinzugefuegt"] == heute.isoformat()).sum())
    sig = (tuple(sorted(gruppen)), st.session_state.n_alle_ueben)
    filter_geaendert = sig != st.session_state.n_filter_sig
    st.session_state.n_filter_sig = sig

    ids = list(gefiltert["id"])
    faellig = [w for w in ids if is_due(w, progress, heute)]
    pool = ids if st.session_state.n_alle_ueben else faellig

    boxen = [progress.get(w, {}).get("box", 1) for w in ids]
    anteil = sum((b - 1) / (MAX_BOX - 1) for b in boxen) / len(boxen) if boxen else 0.0
    st.progress(anteil, text=f"Deck-Fortschritt: {anteil:.0%} ({len(ids)} Karten im Filter)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Heute fällig", len(faellig))
    m2.metric("Begonnen", sum(1 for w in ids if w in progress))
    m3.metric("In Box 5", sum(1 for b in boxen if b == MAX_BOX))
    m4.metric("Neu heute", neu_heute)
    with st.expander("Box-Verteilung"):
        st.bar_chart(
            pd.Series(boxen).value_counts().reindex(range(1, MAX_BOX + 1), fill_value=0)
            .rename_axis("Box").rename("Karten"),
            height=180,
        )
    st.divider()

    batch_rest = batch_bereich("n_", ids, progress)
    if batch_rest is not None:
        vorhanden = set(df["id"])
        pool = [w for w in batch_rest if w in vorhanden]
        if not pool:
            return
    if filter_geaendert or st.session_state.n_karte not in pool:
        _ziehe_karte(pool)

    if not pool:
        naechste = min(als_datum(progress[w]["next_due"]) for w in ids)
        st.success(
            f"Alles erledigt für heute! 🎉 Die nächsten Karten sind am "
            f"**{naechste.strftime('%d.%m.%Y')}** fällig "
            f"(in {(naechste - heute).days} Tag(en))."
        )
        if st.button("Trotzdem weiterüben", type="primary", key="n_weiter"):
            st.session_state.n_alle_ueben = True
            st.rerun()
        return

    if st.session_state.n_alle_ueben and batch_rest is None:
        st.caption("Freies Üben aktiv – alle Karten des Filters sind freigeschaltet.")
        if st.button("Freies Üben beenden", key="n_frei_ende"):
            st.session_state.n_alle_ueben = False
            st.rerun()

    zeile = df[df["id"] == st.session_state.n_karte].iloc[0]
    karte = {
        "wortart": zeile["kategorie"],
        "niveau": "Notion",
        "transkription": "",
        "beispiel": "",
    }
    box = progress.get(zeile["id"], {}).get("box", 1)
    zeige_flashcard(
        zeile["deutsch"], zeile["russisch"], karte, DE_RU, box, st.session_state.n_aufgedeckt
    )

    if not st.session_state.n_aufgedeckt:
        if st.button("🔄 Karte umdrehen", type="primary", width="stretch", key="n_umdrehen"):
            st.session_state.n_aufgedeckt = True
            st.rerun()
        return

    def bewerten(gewusst: bool) -> None:
        grade(zeile["id"], known=gewusst, progress=progress, pfad=NOTION_PROGRESS_JSON)
        st.session_state.n_karte = None
        st.rerun()

    links, rechts = st.columns(2)
    if links.button("↺ Nochmal", width="stretch", key="n_nochmal"):
        bewerten(False)
    if rechts.button("✓ Gewusst", width="stretch", type="primary", key="n_gewusst"):
        bewerten(True)
