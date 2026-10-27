"""Pfade und Konstanten des Vokabeltrainers."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


NOTION_VERBEN_JSON = BASE_DIR / "notion_verben.json"


PROGRESS_JSON = BASE_DIR / "progress.json"


# Wortbank aus Notion: Daten (per notion_import.py gepflegt) und eigener Fortschritt
NOTION_CSV = BASE_DIR / "notion_woerter.csv"
NOTION_PROGRESS_JSON = BASE_DIR / "notion_progress.json"
# Beispielsätze (Substantive, Verben, Adjektive) - nur hier, nicht in Notion
NOTION_BEISPIELE_JSON = BASE_DIR / "notion_beispiele.json"
# Aus der Wortbank entfernte Wörter (ids) - nur ausgeblendet, weil der tägliche
# Import sie sonst aus Notion wieder in notion_woerter.csv schreiben würde
NOTION_AUSGEBLENDET_JSON = BASE_DIR / "notion_ausgeblendet.json"


# Lernsitzung (aktuelle Karten, Batches, Wiederhol-Fristen), damit ein Neuladen
# der Seite oder ein Neustart nicht mitten in der Abfrage eine neue Karte zieht
SITZUNG_JSON = BASE_DIR / "sitzung.json"
SITZUNG_KEYS = (
    "n_karte", "n_letzte_karte", "n_batch", "n_zug", "n_fristen",
    "gelernt_heute", "sitzungs_datum",
)
NOTION_COLUMNS = ["kategorie", "russisch", "deutsch", "hinzugefuegt"]
NOTION_GRUPPEN = ["Substantive", "Verben", "Adjektive", "Kleine Wörter", "Rest"]


MAX_BOX = 5


# Ziehgewicht je Box: halbiert sich pro Box, Box-5-Karten kommen 16-mal seltener als Box 1
BOX_GEWICHT = {b: 2.0 ** -(b - 1) for b in range(1, MAX_BOX + 1)}


# Zuletzt falsch beantwortete Karten kommen im offenen Modus (außerhalb eines
# Batches) so viel häufiger, bis sie einmal richtig beantwortet wurden
FEHLER_FAKTOR = 10


# ... und kommen im offenen Modus spätestens als so-und-sovielte Karte sicher wieder
WIEDERHOLEN_SPAETESTENS = 10


DE_RU = "DE → RU"
