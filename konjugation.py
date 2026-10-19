"""Tab „Konjugation“: ein zufälliges Notion-Verb, alle Präsensformen + Imperativ eintippen.

Kein Box-System - nur eine Statistik für die laufende Sitzung. Die Formen
kommen aus notion_verben.json, die Verbliste aus der Notion-Wortbank.
"""

import random

import pandas as pd
import streamlit as st

from vergleich import bewerten


PERSONEN = ["я", "ты", "он/она", "мы", "вы", "они"]
IMPERATIV = "Imperativ"
SYMBOL = {"richtig": "✅", "fast": "🟡", "falsch": "❌"}

DEFAULTS = {
    "konj_verb": None,      # Infinitiv ohne Betonungszeichen
    "konj_runde": 0,        # zählt hoch - neue Widget-Keys leeren die Felder
    "konj_geprueft": False,
    "konj_antworten": {},   # beim Prüfen eingefroren - die Felder verschwinden danach
    "konj_verben": 0,
    "konj_formen_richtig": 0,
    "konj_formen_gesamt": 0,
}


def _ohne_betonung(text: str) -> str:
    return text.replace("́", "")


def _verben(notion: pd.DataFrame, konjugation: dict) -> list[dict]:
    """Notion-Verben, für die Konjugationsdaten vorliegen."""
    verben = []
    for _, zeile in notion[notion["kategorie"] == "Verben"].iterrows():
        daten = konjugation.get(_ohne_betonung(zeile["russisch"]))
        if daten:
            verben.append({**daten, "anzeige": zeile["russisch"], "deutsch": zeile["deutsch"]})
    return verben


def _neues_verb(verben: list[dict]) -> None:
    andere = [v["infinitiv"] for v in verben if v["infinitiv"] != st.session_state.konj_verb]
    st.session_state.konj_verb = random.choice(andere or [v["infinitiv"] for v in verben])
    st.session_state.konj_runde += 1
    st.session_state.konj_geprueft = False


def _felder(verb: dict) -> list[tuple[str, str]]:
    """(Beschriftung, Lösung) für alle abgefragten Formen."""
    felder = [(p, verb["formen"][p]) for p in PERSONEN]
    if verb.get("imperativ"):
        felder.append((IMPERATIV, verb["imperativ"]))
    return felder


def tab_konjugation(notion: pd.DataFrame, konjugation: dict) -> None:
    verben = _verben(notion, konjugation)
    if not verben:
        st.info("Keine Verben verfügbar – alle entfernt oder ohne Konjugationsdaten (`notion_verben.json`).")
        return

    if st.session_state.konj_verb not in {v["infinitiv"] for v in verben}:
        _neues_verb(verben)
    verb = next(v for v in verben if v["infinitiv"] == st.session_state.konj_verb)
    felder = _felder(verb)
    runde = st.session_state.konj_runde

    gesamt = st.session_state.konj_formen_gesamt
    m1, m2, m3 = st.columns(3)
    m1.metric("Verben geprüft", st.session_state.konj_verben)
    m2.metric("Formen richtig", f"{st.session_state.konj_formen_richtig}/{gesamt}")
    m3.metric("Quote", f"{st.session_state.konj_formen_richtig / gesamt:.0%}" if gesamt else "–")
    st.divider()

    st.markdown(f"## {verb['anzeige']}")
    st.caption(f"{verb['deutsch']}  ·  {len(verben)} Verben aus Notion")
    if verb.get("hinweis"):
        st.info(verb["hinweis"])
    elif verb["aspekt"] == "pf":
        st.info("Vollendetes Verb – kein Präsens. Gefragt sind die Formen des einfachen Futurs.")
    if not verb.get("imperativ"):
        st.caption("Für dieses Verb gibt es keinen gebräuchlichen Imperativ.")

    if not st.session_state.konj_geprueft:
        with st.form(f"konj_form_{runde}", enter_to_submit=False, border=False):
            for beschriftung, _ in felder:
                st.text_input(
                    beschriftung,
                    key=f"konj_{runde}_{beschriftung}",
                    placeholder="du-Form (ты)" if beschriftung == IMPERATIV else None,
                )
            geprueft = st.form_submit_button("Prüfen & Lösung zeigen", type="primary", width="stretch")
        if geprueft:
            antworten = {
                b: str(st.session_state.get(f"konj_{runde}_{b}", "")).strip() for b, _ in felder
            }
            ergebnisse = [bewerten(antworten[b], loesung) for b, loesung in felder]
            st.session_state.konj_antworten = antworten
            st.session_state.konj_geprueft = True
            st.session_state.konj_verben += 1
            st.session_state.konj_formen_richtig += ergebnisse.count("richtig")
            st.session_state.konj_formen_gesamt += len(felder)
            st.rerun()

    if not st.session_state.konj_geprueft:
        if st.button("🔀 Anderes Verb", width="stretch", key="konj_ueberspringen"):
            _neues_verb(verben)
            st.rerun()
        return

    zeilen = ["| | deine Antwort | Lösung | |", "|---|---|---|---|"]
    richtig = 0
    for beschriftung, loesung in felder:
        eingabe = st.session_state.konj_antworten.get(beschriftung, "")
        status = bewerten(eingabe, loesung)
        richtig += status == "richtig"
        zelle = lambda t: t.replace("|", "\\|")  # noqa: E731
        zeilen.append(
            f"| **{beschriftung}** | {zelle(eingabe) or '–'} | {zelle(loesung)} | {SYMBOL[status]} |"
        )
    (st.success if richtig == len(felder) else st.warning)(
        f"{richtig} von {len(felder)} Formen richtig."
    )
    st.markdown("\n".join(zeilen))
    st.caption("🟡 = fast richtig (Tippfehler). Beim Imperativ zählt die du- oder die ihr/Sie-Form.")

    if st.button("Nächstes Verb →", type="primary", width="stretch", key="konj_weiter"):
        _neues_verb(verben)
        st.rerun()
