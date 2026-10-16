"""Übernimmt neue Wörter aus der Notion-Wortbank in notion_woerter.csv.

Aufruf:  python notion_import.py <seite.md>

<seite.md> ist der Inhalt der Notion-Seite „Wortbank“ (so wie ihn das
Notion-Fetch liefert): je Kategorie eine Überschrift `## Substantive` usw.,
darunter eine zweispaltige Tabelle Russisch | Deutsch – als HTML-<table>
oder als Markdown-Pipe-Tabelle.

Neue Einträge (Schlüssel: Kategorie + russisches Wort) werden angehängt,
geänderte deutsche Übersetzungen aktualisiert. Gelöscht wird nichts, damit
kein Lernfortschritt verloren geht. Kommt ohne Streamlit und pandas aus.
"""

import csv
import html
import io
import re
import sys
from datetime import date
from pathlib import Path

from konfig import NOTION_COLUMNS, NOTION_CSV


KOPFZEILE = {("russisch", "deutsch")}


def _zelle(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("**", "").replace("\\", "")
    return " ".join(text.split())


def parse_seite(markdown: str) -> list[dict]:
    """Liefert alle Tabellenzeilen als {kategorie, russisch, deutsch}."""
    eintraege = []
    abschnitte = re.split(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)
    # abschnitte = [vorspann, titel1, inhalt1, titel2, inhalt2, ...]
    for titel, inhalt in zip(abschnitte[1::2], abschnitte[2::2]):
        kategorie = _zelle(titel)
        zeilen = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", inhalt, flags=re.DOTALL):
            zeilen.append([_zelle(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)])
        for zeile in inhalt.splitlines():
            zeile = zeile.strip()
            if zeile.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|?", zeile):
                zeilen.append([_zelle(z) for z in zeile.strip("|").split("|")])
        for zellen in zeilen:
            if len(zellen) < 2 or not zellen[0] or not zellen[1]:
                continue
            if (zellen[0].lower(), zellen[1].lower()) in KOPFZEILE:
                continue
            eintraege.append({"kategorie": kategorie, "russisch": zellen[0], "deutsch": zellen[1]})
    return eintraege


def lade_csv(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with pfad.open(encoding="utf-8", newline="") as fh:
        return [{c: (z.get(c) or "").strip() for c in NOTION_COLUMNS} for z in csv.DictReader(fh)]


def zusammenfuehren(bestand: list[dict], notion: list[dict], heute: str) -> tuple[list[dict], int, int]:
    """Hängt neue Wörter an, aktualisiert Übersetzungen. Gibt (liste, neu, geaendert) zurück."""
    index = {(z["kategorie"], z["russisch"]): z for z in bestand}
    neu = geaendert = 0
    for e in notion:
        schluessel = (e["kategorie"], e["russisch"])
        if schluessel in index:
            if index[schluessel]["deutsch"] != e["deutsch"]:
                index[schluessel]["deutsch"] = e["deutsch"]
                geaendert += 1
            continue
        zeile = {**e, "hinzugefuegt": heute}
        bestand.append(zeile)
        index[schluessel] = zeile
        neu += 1
    return bestand, neu, geaendert


def schreibe_csv(pfad: Path, zeilen: list[dict]) -> None:
    puffer = io.StringIO()
    writer = csv.DictWriter(puffer, fieldnames=NOTION_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(zeilen)
    tmp = pfad.with_suffix(".tmp")
    tmp.write_text(puffer.getvalue(), encoding="utf-8")
    tmp.replace(pfad)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    notion = parse_seite(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not notion:
        print("FEHLER: keine Tabellenzeilen gefunden – Seitenformat prüfen, nichts geändert.")
        return 1
    bestand = lade_csv(NOTION_CSV)
    zeilen, neu, geaendert = zusammenfuehren(bestand, notion, date.today().isoformat())
    if neu or geaendert:
        schreibe_csv(NOTION_CSV, zeilen)
    print(f"Notion: {len(notion)} Zeilen · neu: {neu} · geändert: {geaendert} · gesamt: {len(zeilen)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
