"""Pfade und Konstanten des Vokabeltrainers."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


VOCAB_CSV = BASE_DIR / "vocab.csv"


TEXTE_JSON = BASE_DIR / "texte.json"
NOTION_VERBEN_JSON = BASE_DIR / "notion_verben.json"


PROGRESS_JSON = BASE_DIR / "progress.json"


# Wortbank aus Notion: Daten (per notion_import.py gepflegt) und eigener Fortschritt
NOTION_CSV = BASE_DIR / "notion_woerter.csv"
NOTION_PROGRESS_JSON = BASE_DIR / "notion_progress.json"
NOTION_COLUMNS = ["kategorie", "russisch", "deutsch", "hinzugefuegt"]
NOTION_GRUPPEN = ["Substantive", "Verben", "Adjektive", "Rest"]


COLUMNS = ["russisch", "deutsch", "transkription", "wortart", "niveau", "beispiel"]


MAX_BOX = 5


BOX_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}


RU_DE, DE_RU, MIXED = "RU → DE", "DE → RU", "gemischt"


M_KARTEN, M_TIPPEN, M_GEMISCHT = "Karten", "Tippen", "gemischt"


STUFEN = {"A1": "A1 – leicht", "A2": "A2 – mittel", "B1": "B1 – fordernd"}
