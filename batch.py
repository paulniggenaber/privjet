"""Batch-Modus: N Karten aus Box k ziehen und so lange üben, bis alle mindestens in Box k+1 sind.

Jederzeit startbar. Bewertet wird ganz normal über leitner.grade: Für den
Aufstieg braucht es je nach Box 1, 2, 4 oder 8 Treffer, „Nochmal“ wirft eine
Karte zwei Boxen zurück - sie bleibt im Batch, bis sie das Ziel erreicht hat.
"""

import random
from collections import Counter

import streamlit as st

from konfig import MAX_BOX


def _box(word: str, progress: dict) -> int:
    return progress.get(word, {}).get("box", 1)


def batch_bereich(prefix: str, ids: list[str], progress: dict) -> list[str] | None:
    """Rendert Start bzw. Stand des Batches.

    Gibt None zurück, wenn kein Batch läuft, sonst die Karten, die das Ziel
    noch nicht erreicht haben (leer = Batch geschafft).
    `prefix` trennt die Session-Keys der Tabs voneinander.
    """
    key = f"{prefix}batch"
    batch = st.session_state.get(key)

    if batch is None:
        with st.expander("🎯 Batch lernen – Karten gezielt eine Box höher bringen"):
            boxen = Counter(_box(w, progress) for w in ids)
            links, rechts = st.columns(2)
            von = links.selectbox(
                "Box",
                range(1, MAX_BOX),
                format_func=lambda b: f"Box {b} → {b + 1}  ({boxen[b]} Karten)",
                key=f"{prefix}batch_von",
            )
            groesse = rechts.number_input(
                "Batchgröße", min_value=1, max_value=500, value=10, key=f"{prefix}batch_groesse"
            )
            st.caption(
                "Zieht zufällig Karten aus der gewählten Box (im aktuellen Filter) und fragt sie "
                "ab, bis alle mindestens eine Box höher liegen (Box k braucht 2^(k-1) Treffer)."
            )
            if st.button(
                "Batch starten", type="primary", key=f"{prefix}batch_start", disabled=not boxen[von]
            ):
                kandidaten = [w for w in ids if _box(w, progress) == von]
                st.session_state[key] = {
                    "ids": random.sample(kandidaten, min(int(groesse), len(kandidaten))),
                    "ziel": von + 1,
                }
                st.rerun()
        return None

    ziel = batch["ziel"]
    rest = [w for w in batch["ids"] if _box(w, progress) < ziel]
    geschafft = len(batch["ids"]) - len(rest)
    st.progress(
        geschafft / len(batch["ids"]),
        text=f"🎯 Batch Box {ziel - 1} → {ziel}: {geschafft} von {len(batch['ids'])} Karten geschafft",
    )
    if not rest:
        st.success(f"Batch geschafft! 🎉 Alle {len(batch['ids'])} Karten liegen jetzt mindestens in Box {ziel}.")
        if st.button("Batch schließen", type="primary", key=f"{prefix}batch_schliessen"):
            st.session_state[key] = None
            st.rerun()
        return []
    if st.button("Batch abbrechen", key=f"{prefix}batch_abbrechen"):
        st.session_state[key] = None
        st.rerun()
    return rest
