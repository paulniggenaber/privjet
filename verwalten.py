"""Tab „Vokabeln verwalten“: Tabelle, CSV-Import, Fortschritt zurücksetzen."""

from collections import Counter

import pandas as pd
import streamlit as st

from daten import save_vocab
from konfig import COLUMNS, MAX_BOX, PROGRESS_JSON


def tab_verwalten(df: pd.DataFrame, progress: dict) -> None:
    st.subheader("Vokabelliste bearbeiten")
    st.caption(
        "Zeilen ändern, ergänzen oder löschen und anschließend speichern. "
        "Der Schlüssel für den Lernfortschritt ist die Spalte `russisch`."
    )
    bearbeitet = st.data_editor(
        df, num_rows="dynamic", width="stretch", hide_index=True, key="editor"
    )
    if st.button("Änderungen speichern", type="primary"):
        save_vocab(pd.DataFrame(bearbeitet))
        st.success("vocab.csv gespeichert.")
        st.rerun()

    st.divider()
    st.subheader("Eigene CSV anhängen")
    st.caption(f"Erwartete Spalten: {', '.join(COLUMNS)} – UTF-8, Komma-getrennt.")
    datei = st.file_uploader("CSV-Datei auswählen", type="csv", key="upload")
    if datei is not None and st.button("Anhängen"):
        try:
            neu = pd.read_csv(datei, encoding="utf-8", dtype=str, keep_default_na=False)
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            st.error(f"CSV konnte nicht gelesen werden: {exc}")
            return
        fehlend = [c for c in COLUMNS if c not in neu.columns]
        if fehlend:
            st.error(f"Es fehlen folgende Spalten: {', '.join(fehlend)}")
            return
        neu = neu[COLUMNS].fillna("")
        for col in COLUMNS:
            neu[col] = neu[col].astype(str).str.strip()
        neu = neu[neu["russisch"] != ""]
        bekannt = set(df["russisch"])
        frisch = neu[~neu["russisch"].isin(bekannt)].drop_duplicates(subset="russisch")
        save_vocab(pd.concat([df, frisch], ignore_index=True))
        st.success(
            f"{len(frisch)} Vokabel(n) angehängt, "
            f"{len(neu) - len(frisch)} Duplikat(e) übersprungen."
        )
        st.rerun()

    st.divider()
    st.subheader("Lernfortschritt zurücksetzen")
    bestaetigt = st.checkbox("Ja, den gesamten Lernfortschritt wirklich löschen")
    if st.button("Fortschritt zurücksetzen", disabled=not bestaetigt):
        PROGRESS_JSON.unlink(missing_ok=True)
        for key in ("karte", "aufgedeckt", "filter_sig"):
            st.session_state.pop(key, None)
        st.session_state.gelernt_heute = 0
        st.session_state.alle_ueben = False
        st.success("Fortschritt gelöscht – alle Karten starten wieder in Box 1.")
        st.rerun()

    if progress:
        st.divider()
        st.subheader("Statistik")
        verteilung = Counter(e["box"] for e in progress.values())
        st.bar_chart(
            pd.DataFrame(
                {"Karten": [verteilung.get(b, 0) for b in range(1, MAX_BOX + 1)]},
                index=[f"Box {b}" for b in range(1, MAX_BOX + 1)],
            )
        )
