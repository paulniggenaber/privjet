"""Tab „Konjugation“: ein zufälliges Notion-Verb, alle Präsensformen + Imperativ als Karteikarten.

Pro Verb kommen die Formen nacheinander als Karte (vorne Person + Infinitiv,
hinten die Form), bewertet wird selbst mit „Gewusst“ / „Nochmal“ - ohne
russische Tastatur. Kein Box-System, nur eine Statistik für die laufende
Sitzung. Die Formen kommen aus notion_verben.json, die Verbliste aus der
Notion-Wortbank.
"""

import random

import pandas as pd
import streamlit as st

from karte import zeige_flashcard


PERSONEN = ["я", "ты", "он/она", "мы", "вы", "они"]
IMPERATIV = "Imperativ"

DEFAULTS = {
    "konj_verb": None,          # Infinitiv ohne Betonungszeichen
    "konj_reihe": [],           # Beschriftungen der noch abzufragenden Formen, in Reihenfolge
    "konj_pos": 0,              # aktuelle Stelle in konj_reihe
    "konj_aufgedeckt": False,
    "konj_ergebnisse": {},      # Beschriftung -> gewusst (letzte Bewertung)
    "konj_gezaehlt": False,     # Verb schon in „Verben geschafft“ - Wiederholen zählt nicht doppelt
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


def _felder(verb: dict) -> list[tuple[str, str]]:
    """(Beschriftung, Lösung) für alle abgefragten Formen."""
    felder = [(p, verb["formen"][p]) for p in PERSONEN]
    if verb.get("imperativ"):
        felder.append((IMPERATIV, verb["imperativ"]))
    return felder


def _starte_runde(beschriftungen: list[str]) -> None:
    st.session_state.konj_reihe = beschriftungen
    st.session_state.konj_pos = 0
    st.session_state.konj_aufgedeckt = False


def _neues_verb(verben: list[dict]) -> None:
    andere = [v for v in verben if v["infinitiv"] != st.session_state.konj_verb]
    verb = random.choice(andere or verben)
    st.session_state.konj_verb = verb["infinitiv"]
    st.session_state.konj_ergebnisse = {}
    st.session_state.konj_gezaehlt = False
    _starte_runde([b for b, _ in _felder(verb)])


def _frage(beschriftung: str) -> str:
    return "Imperativ (du / ihr)" if beschriftung == IMPERATIV else f"{beschriftung} …"


def tab_konjugation(notion: pd.DataFrame, konjugation: dict) -> None:
    verben = _verben(notion, konjugation)
    if not verben:
        st.info("Keine Verben verfügbar – alle entfernt oder ohne Konjugationsdaten (`notion_verben.json`).")
        return

    if st.session_state.konj_verb not in {v["infinitiv"] for v in verben}:
        _neues_verb(verben)
    verb = next(v for v in verben if v["infinitiv"] == st.session_state.konj_verb)
    felder = _felder(verb)
    loesungen = dict(felder)
    reihe = [b for b in st.session_state.konj_reihe if b in loesungen]
    pos = st.session_state.konj_pos

    gesamt = st.session_state.konj_formen_gesamt
    m1, m2, m3 = st.columns(3)
    m1.metric("Verben geschafft", st.session_state.konj_verben)
    m2.metric("Formen gewusst", f"{st.session_state.konj_formen_richtig}/{gesamt}")
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

    if pos < len(reihe):
        beschriftung = reihe[pos]
        zeige_flashcard(
            _frage(beschriftung),
            loesungen[beschriftung],
            {"wortart": verb["anzeige"], "niveau": verb["deutsch"], "transkription": "", "beispiel": ""},
            "Konjugation",
            f"Form {pos + 1}/{len(reihe)}",
            st.session_state.konj_aufgedeckt,
        )
        _bisher(felder, set(reihe[pos:]))

        if not st.session_state.konj_aufgedeckt:
            if st.button("🔄 Karte umdrehen", type="primary", width="stretch", key="konj_umdrehen"):
                st.session_state.konj_aufgedeckt = True
                st.rerun()
            if st.button("🔀 Anderes Verb", width="stretch", key="konj_ueberspringen"):
                _neues_verb(verben)
                st.rerun()
            return

        def bewerten(gewusst: bool) -> None:
            st.session_state.konj_ergebnisse[beschriftung] = gewusst
            st.session_state.konj_formen_richtig += gewusst
            st.session_state.konj_formen_gesamt += 1
            st.session_state.konj_pos += 1
            st.session_state.konj_aufgedeckt = False
            if st.session_state.konj_pos >= len(reihe) and not st.session_state.konj_gezaehlt:
                st.session_state.konj_verben += 1
                st.session_state.konj_gezaehlt = True
            st.rerun()

        links, rechts = st.columns(2)
        if links.button("↺ Nochmal", width="stretch", key="konj_nochmal"):
            bewerten(False)
        if rechts.button("✓ Gewusst", width="stretch", type="primary", key="konj_gewusst"):
            bewerten(True)
        return

    # Alle Formen durch: Übersicht, falsche wiederholen oder nächstes Verb.
    ergebnisse = st.session_state.konj_ergebnisse
    falsch = [b for b, _ in felder if ergebnisse.get(b) is False]
    (st.warning if falsch else st.success)(
        f"{len(felder) - len(falsch)} von {len(felder)} Formen gewusst."
    )
    st.markdown(_tabelle(felder, ergebnisse))
    if falsch and st.button(
        f"↺ Die {len(falsch)} falschen Formen wiederholen", width="stretch", key="konj_wiederholen"
    ):
        _starte_runde(falsch)
        st.rerun()
    if st.button("Nächstes Verb →", type="primary", width="stretch", key="konj_weiter"):
        _neues_verb(verben)
        st.rerun()


def _tabelle(felder: list[tuple[str, str]], ergebnisse: dict) -> str:
    zeilen = ["| | Form | |", "|---|---|---|"]
    for beschriftung, loesung in felder:
        status = ergebnisse.get(beschriftung)
        symbol = "–" if status is None else ("✅" if status else "❌")
        zeilen.append(f"| **{beschriftung}** | {loesung.replace('|', chr(92) + '|')} | {symbol} |")
    return "\n".join(zeilen)


def _bisher(felder: list[tuple[str, str]], offen: set[str]) -> None:
    """Die schon bewerteten Formen dieses Verbs, als Gedächtnisstütze unter der Karte.
    Formen, die in dieser Runde noch kommen (`offen`), bleiben verdeckt."""
    ergebnisse = st.session_state.konj_ergebnisse
    teile = [
        f"{b} **{loesung}** {'✅' if ergebnisse[b] else '❌'}"
        for b, loesung in felder
        if b in ergebnisse and b not in offen
    ]
    if teile:
        st.caption("  ·  ".join(teile))
