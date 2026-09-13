"""Textvergleich ohne Streamlit: Antwortprüfung und Stichwortabgleich.

Reine Funktionen, damit sie sich ohne laufende App testen lassen.
"""

import difflib
import re


ARTIKEL = r"^(?:der|die|das|den|dem|des|ein|eine|einen|einem)\s+"


UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalisieren(text: str) -> str:
    """Kleinschreibung, ё wie е, Satzzeichen und Mehrfach-Leerzeichen raus."""
    text = text.strip().lower().replace("ё", "е")
    text = re.sub(r"[!?.,;:…«»\"'()\[\]/-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _varianten(loesung: str) -> set[str]:
    """Alle Schreibweisen, die als richtig zählen.

    "das Wasser" akzeptiert auch "Wasser", "sprechen, sagen" jeden der beiden
    Teile, "Guten Tag! (höflich)" auch ohne den Klammerzusatz, und Umlaute
    dürfen umschrieben werden.
    """
    teile = [loesung, re.sub(r"\([^)]*\)", " ", loesung)]
    teile += re.split(r"[;,/]|\boder\b", loesung)
    ergebnis: set[str] = set()
    for teil in teile:
        norm = _normalisieren(teil)
        if not norm:
            continue
        for form in (norm, re.sub(ARTIKEL, "", norm)):
            ergebnis.add(form)
            ergebnis.add(form.translate(UMLAUTE))
    return {e for e in ergebnis if e}


def bewerten(eingabe: str, loesung: str) -> str:
    """'richtig', 'fast' (Tippfehler) oder 'falsch'."""
    eing = _normalisieren(eingabe)
    if not eing:
        return "falsch"
    varianten = _varianten(loesung)
    if eing in varianten or eing.translate(UMLAUTE) in varianten:
        return "richtig"
    beste = max(
        (difflib.SequenceMatcher(None, eing, v).ratio() for v in varianten), default=0.0
    )
    return "fast" if beste >= 0.82 else "falsch"


# Funktionswoerter, die fuer den Stichwortabgleich nichts hergeben.
STOPWORTE = {
    "aber", "alle", "allem", "allen", "aller", "alles", "also", "auch", "auf",
    "aus", "beim", "bereits", "dabei", "dafür", "damit", "danach", "dann",
    "dass", "dein", "deine", "dem", "den", "denn", "der", "des", "diese",
    "diesem", "diesen", "dieser", "dieses", "doch", "dort", "durch", "eine",
    "einem", "einen", "einer", "eines", "etwas", "euch", "euer", "für",
    "ganz", "gegen", "gibt", "habe", "haben", "hast", "hatte", "hatten",
    "hier", "ihre", "ihrem", "ihren", "ihrer", "immer", "jede", "jedem",
    "jeden", "jeder", "kann", "können", "mehr", "mein", "meine", "meinem",
    "meinen", "meiner", "mich", "mir", "mit", "muss", "müssen", "nach",
    "nicht", "nichts", "noch", "nur", "oder", "ohne", "schon", "sehr",
    "sein", "seine", "seinem", "seinen", "seiner", "sich", "sie", "sind",
    "über", "und", "uns", "unser", "unsere", "vom", "von", "vor", "war",
    "waren", "warst", "was", "weil", "welche", "wenn", "werden", "wie",
    "wir", "wird", "wurde", "wurden", "zum", "zur",
}


# Russische Funktionswoerter - der Abgleich laeuft in beide Richtungen.
STOPWORTE_RU = {
    "будет", "будут", "было", "были", "быть", "весь", "всех", "всем", "вся",
    "даже", "если", "ещё", "еще", "здесь", "который", "которая", "которое",
    "которые", "которых", "меня", "может", "можно", "мои", "моя", "надо",
    "наша", "наши", "него", "нему", "неё", "нее", "ним", "них", "около",
    "они", "оно", "очень", "перед", "после", "потом", "потому", "почти",
    "свои", "свой", "своя", "себя", "также", "твой", "тебя", "тогда", "тоже",
    "только", "тому", "того", "уже", "чтобы", "через", "эта", "эти", "это",
    "этом", "этот",
}


def _inhaltswoerter(text: str) -> list[str]:
    # [^\W\d_] trifft Buchstaben jeder Schrift, also auch Kyrillisch.
    woerter = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
    return [
        w.lower()
        for w in woerter
        if len(w) >= 4 and w.lower() not in STOPWORTE and w.lower() not in STOPWORTE_RU
    ]


def abgleich(referenz: str, eingabe: str) -> tuple[list[str], list[str]]:
    """Grobe Orientierung: welche Inhaltswörter der Musterlösung auftauchen.

    Bewusst tolerant (Wortstamm oder hohe Ähnlichkeit), aber blind für
    Synonyme und Umformulierungen - deshalb im UI als Hinweis, nicht als
    Bewertung ausgewiesen.
    """
    eigene = _inhaltswoerter(eingabe)
    staemme = {w[:5] for w in eigene}
    gefunden, fehlend, gesehen = [], [], set()
    for wort in _inhaltswoerter(referenz):
        if wort in gesehen:
            continue
        gesehen.add(wort)
        treffer = wort[:5] in staemme or any(
            difflib.SequenceMatcher(None, wort, e).ratio() >= 0.8 for e in eigene
        )
        (gefunden if treffer else fehlend).append(wort)
    return gefunden, fehlend
