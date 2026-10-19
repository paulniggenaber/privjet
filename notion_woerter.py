"""Tab „Notion-Wörter“: die Wortbank aus Notion als Karteikarten, immer DE → RU.

Wörter lassen sich hier aus der Wortbank entfernen (und zurückholen); sie
werden nur ausgeblendet (notion_ausgeblendet.json), damit der tägliche Import
sie nicht wieder hineinbringt.

Eigener Fortschritt in notion_progress.json, damit sich die Boxen nicht mit
vocab.csv vermischen. Alle Session-Keys tragen das Präfix `n_`, weil alle Tabs
in jedem Lauf gerendert werden und sich sonst die Karte teilen würden.
"""

from datetime import date

import pandas as pd
import streamlit as st

from batch import batch_bereich
from daten import save_ausgeblendet
from karte import zeige_flashcard
from konfig import DE_RU, MAX_BOX, NOTION_GRUPPEN, NOTION_PROGRESS_JSON
from leitner import box, frist_setzen, grade, stand, ziehe


DEFAULTS = {
    "n_karte": None,        # id der aktuellen Karte ("kategorie|russisch")
    "n_aufgedeckt": False,
    "n_filter_sig": None,
}


def _gruppe(kategorie: str) -> str:
    return kategorie if kategorie in NOTION_GRUPPEN else "Rest"


def _ziehe_karte(pool: list[str], progress: dict, offen: bool = True) -> None:
    zuletzt = st.session_state.n_karte or st.session_state.get("n_letzte_karte")
    st.session_state.n_karte = ziehe("n_", pool, progress, ausser=zuletzt, offen=offen)
    st.session_state.n_aufgedeckt = False


def _beschriftung(zeile) -> str:
    return f"{zeile['russisch']} – {zeile['deutsch']}  ({zeile['kategorie']})"


def _entfernen(ids, ausgeblendet: set[str]) -> None:
    save_ausgeblendet(ausgeblendet | set(ids))
    if st.session_state.n_karte in ids:
        st.session_state.n_karte = None
    st.rerun()


def _verwalten(alle: pd.DataFrame, ausgeblendet: set[str]) -> None:
    """Expander: Wörter gezielt entfernen oder entfernte zurückholen."""
    with st.expander(f"🗑 Wörter entfernen / zurückholen ({len(ausgeblendet)} entfernt)"):
        aktiv = alle[~alle["id"].isin(ausgeblendet)]
        namen = dict(zip(aktiv["id"], aktiv.apply(_beschriftung, axis=1)))
        weg = st.multiselect(
            "Aus der Wortbank entfernen", list(namen), format_func=namen.get,
            placeholder="Wörter suchen …", key="n_weg_auswahl",
        )
        if st.button("Entfernen", disabled=not weg, key="n_weg_knopf"):
            _entfernen(weg, ausgeblendet)

        entfernt = alle[alle["id"].isin(ausgeblendet)]
        if not entfernt.empty:
            namen = dict(zip(entfernt["id"], entfernt.apply(_beschriftung, axis=1)))
            zurueck = st.multiselect(
                "Entfernte Wörter zurückholen", list(namen), format_func=namen.get,
                key="n_zurueck_auswahl",
            )
            if st.button("Zurückholen", disabled=not zurueck, key="n_zurueck_knopf"):
                save_ausgeblendet(ausgeblendet - set(zurueck))
                st.rerun()
        st.caption(
            "Entfernte Wörter werden nur ausgeblendet (auch in der Konjugation) – so "
            "kommen sie auch dann nicht zurück, wenn sie in Notion stehen bleiben. "
            "Der Lernfortschritt bleibt erhalten."
        )


def tab_notion(alle: pd.DataFrame, progress: dict, ausgeblendet: set[str]) -> None:
    df = alle[~alle["id"].isin(ausgeblendet)]
    if df.empty:
        if not alle.empty:
            _verwalten(alle, ausgeblendet)
        st.info("Keine Notion-Wörter vorhanden.")
        return

    heute = date.today()
    gruppen = st.pills(
        "Wortart", NOTION_GRUPPEN, selection_mode="multi", default=NOTION_GRUPPEN, key="n_gruppen"
    ) or NOTION_GRUPPEN
    gefiltert = df[df["kategorie"].map(_gruppe).isin(gruppen)]

    neu_heute = int((gefiltert["hinzugefuegt"] == heute.isoformat()).sum())
    sig = tuple(sorted(gruppen))
    filter_geaendert = st.session_state.n_filter_sig is not None and sig != st.session_state.n_filter_sig
    st.session_state.n_filter_sig = sig

    ids = list(gefiltert["id"])
    pool = ids
    boxen = [box(w, progress) for w in ids]
    anteil = sum((b - 1) / (MAX_BOX - 1) for b in boxen) / len(boxen) if boxen else 0.0
    st.progress(anteil, text=f"Deck-Fortschritt: {anteil:.0%} ({len(ids)} Karten im Filter)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("In Box 1", boxen.count(1))
    m2.metric("Begonnen", sum(1 for w in ids if w in progress))
    m3.metric("In Box 5", boxen.count(MAX_BOX))
    m4.metric("Neu heute", neu_heute)
    with st.expander("Box-Verteilung"):
        st.bar_chart(
            pd.Series(boxen).value_counts().reindex(range(1, MAX_BOX + 1), fill_value=0)
            .rename_axis("Box").rename("Karten"),
            height=180,
        )
    _verwalten(alle, ausgeblendet)
    st.divider()
    if not ids:
        st.warning("Keine Wörter in dieser Auswahl.")
        return

    batch_rest = batch_bereich("n_", ids, progress)
    if batch_rest is not None:
        vorhanden = set(df["id"])
        pool = [w for w in batch_rest if w in vorhanden]
        if not pool:
            return
    if filter_geaendert or st.session_state.n_karte not in pool:
        _ziehe_karte(pool, progress, offen=batch_rest is None)

    zeile = df[df["id"] == st.session_state.n_karte].iloc[0]
    karte = {
        "wortart": zeile["kategorie"],
        "niveau": "Notion",
        "transkription": "",
        "beispiel": "",
    }
    zeige_flashcard(
        zeile["deutsch"], zeile["russisch"], karte, DE_RU, stand(zeile["id"], progress),
        st.session_state.n_aufgedeckt,
    )
    if st.button("🗑 Dieses Wort entfernen", type="tertiary", key="n_entfernen"):
        _entfernen([zeile["id"]], ausgeblendet)

    if not st.session_state.n_aufgedeckt:
        if st.button("🔄 Karte umdrehen", type="primary", width="stretch", key="n_umdrehen"):
            st.session_state.n_aufgedeckt = True
            st.rerun()
        return

    def bewerten(gewusst: bool) -> None:
        grade(zeile["id"], known=gewusst, progress=progress, pfad=NOTION_PROGRESS_JSON)
        if not gewusst:
            frist_setzen("n_", zeile["id"])
        st.session_state.n_letzte_karte = zeile["id"]
        st.session_state.n_karte = None
        st.rerun()

    links, rechts = st.columns(2)
    if links.button("↺ Nochmal", width="stretch", key="n_nochmal"):
        bewerten(False)
    if rechts.button("✓ Gewusst", width="stretch", type="primary", key="n_gewusst"):
        bewerten(True)
