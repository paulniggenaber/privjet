"""Tab „Konjugation": eine Verbform abfragen, eintippen, prüfen."""

import random

import streamlit as st

from tastenfeld import zeige_tastenfeld
from vergleich import bewerten

ZEITEN = {"praesens": "Präsens", "praeteritum": "Präteritum"}
GEMISCHT = "gemischt"
# Reihenfolge in der Lösungstabelle - dict-Reihenfolge aus der JSON reicht nicht,
# wenn jemand die Datei von Hand umsortiert.
FOLGE = {
    "praesens": ["я", "ты", "он/она", "мы", "вы", "они"],
    "praeteritum": ["он", "она", "оно", "они"],
}
HINWEIS = {"он": "он (m.)", "она": "она (f.)", "оно": "оно (n.)", "они": "они (Pl.)"}

DEFAULTS = {
    "konj_verb": None,
    "konj_zeit": "praesens",
    "konj_person": "я",
    "konj_status": None,
    "konj_status_bed": None,
    "konj_eingabe": "",
    "konj_bedeutung": "",
    "konj_mit_bedeutung": True,
    "konj_pruefen": False,
    "konj_neu": False,
    "konj_sig": None,
    "konj_richtig": 0,
    "konj_falsch": 0,
}


def _aufgabenpool(verben: list[dict], zeiten: list[str], gruppen) -> list[tuple[str, str]]:
    """Alle abfragbaren (Verb, Zeitform)-Paare. `быть` hat kein Präsens."""
    return [
        (v["infinitiv"], zeit)
        for v in verben
        if v["gruppe"] in gruppen
        for zeit in zeiten
        if v.get(zeit)
    ]


def _neue_aufgabe(pool: list[tuple[str, str]], nach_infinitiv: dict) -> None:
    if not pool:
        st.session_state.konj_verb = None
        return
    andere = [p for p in pool if p[0] != st.session_state.konj_verb] or pool
    infinitiv, zeit = random.choice(andere)
    st.session_state.konj_verb = infinitiv
    st.session_state.konj_zeit = zeit
    st.session_state.konj_person = random.choice(FOLGE[zeit])
    st.session_state.konj_status = None
    st.session_state.konj_status_bed = None
    # Vor dem Rendern der Eingabefelder leeren - danach waere es ein Fehler.
    st.session_state.konj_eingabe = ""
    st.session_state.konj_bedeutung = ""
    st.session_state.konj_pruefen = False


def _pruefen() -> None:
    """on_change des Eingabefelds - so löst auch die Eingabetaste aus."""
    st.session_state.konj_pruefen = True


def _tabelle(verb: dict, zeit: str, gefragt: str) -> str:
    zeilen = ["| | |", "|---|---|"]
    for person in FOLGE[zeit]:
        form = verb[zeit][person].replace("|", "\\|")
        beschriftung = HINWEIS.get(person, person)
        if person == gefragt:
            zeilen.append(f"| **{beschriftung}** | **{form}** |")
        else:
            zeilen.append(f"| {beschriftung} | {form} |")
    return "\n".join(zeilen)


def _rueckmeldung(titel: str, status: str, eingabe: str, loesung: str) -> None:
    getippt = eingabe.strip()
    if status == "richtig":
        st.success(f"{titel}: richtig ✓  {loesung}")
    elif status == "fast":
        st.warning(f"{titel}: fast – du hattest „{getippt}“, richtig ist „{loesung}“.")
    else:
        st.error(f"{titel}: „{getippt or '(nichts)'}“ – richtig wäre „{loesung}“.")


def tab_konjugation(verben: list[dict]) -> None:
    if not verben:
        st.error(
            "`verben.json` fehlt oder ist unlesbar. "
            "Ohne diese Datei gibt es keine Konjugationsaufgaben."
        )
        return

    nach_infinitiv = {v["infinitiv"]: v for v in verben}
    alle_gruppen = sorted({v["gruppe"] for v in verben})

    zeit_sp, gruppe_sp = st.columns([1, 2])
    zeitwahl = zeit_sp.radio(
        "Zeitform", [*ZEITEN.values(), GEMISCHT], horizontal=False, key="konj_zeitwahl"
    )
    gruppen = gruppe_sp.multiselect(
        "Verbgruppen", alle_gruppen, default=alle_gruppen, key="konj_gruppen"
    ) or alle_gruppen
    mit_bedeutung = gruppe_sp.toggle(
        "Bedeutung mit abfragen",
        key="konj_mit_bedeutung",
        help="Zusätzlich zur Verbform auch die deutsche Bedeutung eintippen.",
    )

    zeiten = (
        list(ZEITEN)
        if zeitwahl == GEMISCHT
        else [k for k, v in ZEITEN.items() if v == zeitwahl]
    )
    pool = _aufgabenpool(verben, zeiten, gruppen)

    # Neu gezogen wird hier oben, weil _neue_aufgabe das Eingabefeld leert.
    sig = (zeitwahl, tuple(sorted(gruppen)))
    if (
        sig != st.session_state.konj_sig
        or st.session_state.konj_neu
        or (st.session_state.konj_verb, st.session_state.konj_zeit) not in pool
    ):
        st.session_state.konj_sig = sig
        st.session_state.konj_neu = False
        _neue_aufgabe(pool, nach_infinitiv)

    if not st.session_state.konj_verb:
        st.warning("Keine Verben passen zu dieser Auswahl.")
        return

    gesamt = st.session_state.konj_richtig + st.session_state.konj_falsch
    m1, m2, m3 = st.columns(3)
    m1.metric("Richtig", st.session_state.konj_richtig)
    m2.metric("Falsch", st.session_state.konj_falsch)
    m3.metric("Quote", f"{st.session_state.konj_richtig / gesamt:.0%}" if gesamt else "–")
    st.divider()

    verb = nach_infinitiv[st.session_state.konj_verb]
    zeit = st.session_state.konj_zeit
    person = st.session_state.konj_person
    loesung = verb[zeit][person]

    st.caption(f"{ZEITEN[zeit]}  ·  {verb['gruppe']}  ·  {len(pool)} Aufgaben im Filter")
    # Die Bedeutung steht bewusst nicht in der Frage - sie wird mitgelernt und
    # erst zusammen mit der Auflösung gezeigt.
    st.markdown(f"### {verb['infinitiv']}")
    st.markdown(
        f"<div style='font-size:2rem;font-weight:700;margin:0.4rem 0 0.8rem;'>"
        f"{HINWEIS.get(person, person)} …</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.konj_status is None:
        st.text_input(
            "Verbform",
            key="konj_eingabe",
            placeholder="Verbform eintippen",
            label_visibility="collapsed",
            on_change=_pruefen,
        )
        if mit_bedeutung:
            st.text_input(
                "Bedeutung",
                key="konj_bedeutung",
                placeholder=f"Was heißt „{verb['infinitiv']}“ auf Deutsch?",
                label_visibility="collapsed",
                on_change=_pruefen,
            )
        pruef_sp, weiter_sp = st.columns([3, 1])
        gedrueckt = pruef_sp.button(
            "Prüfen", type="primary", width="stretch", key="konj_pruef_knopf"
        )
        # Ohne diesen Knopf käme man an einer unbekannten Form nur vorbei,
        # indem man absichtlich etwas Falsches eintippt. Zählt nicht mit.
        if weiter_sp.button("🔀 Andere Aufgabe", width="stretch", key="konj_ueberspringen"):
            st.session_state.konj_neu = True
            st.rerun()
        with st.expander("⌨️ Kyrillische Tastatur"):
            zeige_tastenfeld("konj_eingabe")
        if gedrueckt or st.session_state.konj_pruefen:
            st.session_state.konj_pruefen = False
            st.session_state.konj_status = bewerten(st.session_state.konj_eingabe, loesung)
            st.session_state.konj_status_bed = (
                bewerten(st.session_state.konj_bedeutung, verb["deutsch"])
                if mit_bedeutung
                else None
            )
            # Nur als richtig gezählt, wenn jeder abgefragte Teil stimmt.
            teile = [st.session_state.konj_status]
            if mit_bedeutung:
                teile.append(st.session_state.konj_status_bed)
            if all(t == "richtig" for t in teile):
                st.session_state.konj_richtig += 1
            else:
                st.session_state.konj_falsch += 1
            st.rerun()
        return

    _rueckmeldung("Form", st.session_state.konj_status,
                  st.session_state.konj_eingabe, loesung)
    if st.session_state.konj_status_bed is not None:
        _rueckmeldung("Bedeutung", st.session_state.konj_status_bed,
                      st.session_state.konj_bedeutung, verb["deutsch"])

    st.markdown(f"**{verb['infinitiv']} – {verb['deutsch']}**  ·  {ZEITEN[zeit]}")
    st.markdown(_tabelle(verb, zeit, person))

    if st.button("Nächste Form →", type="primary", width="stretch"):
        st.session_state.konj_neu = True
        st.rerun()
