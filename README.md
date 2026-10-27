# Vokabeltrainer Russisch – Deutsch

Lokale Streamlit-App zum Lernen russischer Vokabeln nach dem **Leitner-System**.
Läuft komplett offline: kein Netzwerkzugriff, keine Datenbank, nur Dateien im Projektordner.

## Setup

Voraussetzung: Python 3.11 (neuere 3.x funktionieren ebenfalls), Streamlit ab 1.49.

```bash
cd /Users/paul/Desktop/privjet
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starten

Am einfachsten per Doppelklick auf `start.command` im Finder (oder
`./start.command` im Terminal). Das Skript holt per `git pull` die neuesten
Wörter, legt bei Bedarf die virtuelle Umgebung an und startet die App.

Manuell geht es so:

```bash
streamlit run app.py
```

Die App öffnet sich unter <http://localhost:8501>. Beenden mit `Ctrl+C`.

## Dateien

| Datei | Zweck |
|---|---|
| `app.py` | Einstiegspunkt: Seite, Tabs, Session-State |
| `konfig.py` | Pfade und Konstanten (Boxen, Intervalle, Richtungen, Modi) |
| `daten.py` | Laden und Speichern von `vocab.csv`, `texte.json`, `progress.json` |
| `leitner.py` | Box-System: gewichtete Kartenwahl und Bewertung |
| `vergleich.py` | Textvergleich ohne Streamlit: Antwortprüfung, Stichwortabgleich |
| `karte.py` | die Flashcard mit der 3D-Drehung |
| `gist.py` | Lesen/Schreiben einer Datei in einem GitHub-Gist (dauerhafter Fortschritt auf Streamlit Cloud) |
| `batch.py` | Batch-Modus: N Karten einer Box üben, bis alle eine Box höher liegen |
| `tastenfeld.py` | kyrillisches Tastenfeld (ЙЦУКЕН) für den Tab „Übersetzen" |
| `notion_woerter.py` | Tab „Vokabeln" – Wortbank aus Notion, Karten DE → RU mit Beispielsatz |
| `notion_import.py` | übernimmt neue Wörter aus der Notion-Seite in `notion_woerter.csv` (ohne Streamlit) |
| `konjugation.py` | Tab „Konjugation" – Präsens + Imperativ der Notion-Verben |
| `uebersetzen.py` | Tab „Übersetzen" |
| `verwalten.py` | Tab „Vokabeln verwalten" |
| `vocab.csv` | Vokabeldaten (UTF-8) |
| `notion_woerter.csv` | Wortbank aus Notion: kategorie, russisch, deutsch, hinzugefuegt |
| `texte.json` | Übersetzungstexte mit Musterlösung (UTF-8) |
| `notion_verben.json` | Präsensformen + Imperativ der Notion-Verben (UTF-8) |
| `progress.json` | Lernfortschritt, wird beim ersten Bewerten automatisch angelegt |
| `notion_progress.json` | Lernfortschritt des Tabs „Vokabeln" |
| `notion_beispiele.json` | Beispielsätze zu Substantiven, Verben, Adjektiven (nicht in Notion) |
| `notion_ausgeblendet.json` | aus der Wortbank entfernte Wörter (nur ausgeblendet) |
| `sitzung.json` | laufende Lernsitzung (aktuelle Karten, Batches, Fristen) – übersteht Neuladen und Neustart |
| `.streamlit/config.toml` | Sitzung bleibt 24 h statt 2 min erhalten, wenn der Browser-Tab schläft |
| `requirements.txt` | Abhängigkeiten |
| `start.command` | Startskript: git pull + App starten (Doppelklick im Finder) |

Die Abhängigkeiten laufen nur in eine Richtung, es gibt keine Zyklen:

```
app  →  notion_woerter ┬→ karte, batch, leitner
        konjugation ───┼→ vergleich
        uebersetzen ───┴→ tastenfeld, vergleich
        verwalten
            └→ daten  →  konfig
```

`vergleich.py` kommt ohne Streamlit aus – die Prüflogik lässt sich also ohne
laufende App testen.

## Tab „Vokabeln"

Der Tab „Vokabeln" fragt die Wortbank der Notion-Seite
[Wortbank](https://app.notion.com/p/3f50147492c98110b057e5387d33a5ea) ab –
immer Deutsch → Russisch, als Karteikarte zum Selbstbewerten. Gefiltert wird
nach Substantiven, Verben, Adjektiven und „Rest" (alle übrigen Kategorien der
Seite). Der Fortschritt liegt in `notion_progress.json` (Schlüssel
`kategorie|russisch`, weil z. B. что als Fragewort und als Konjunktion vorkommt).

**Beispielsätze:** Nach dem Umdrehen steht bei Substantiven, Verben und
Adjektiven rechts neben der Karte ein einfacher russischer Beispielsatz mit der
deutschen Übersetzung darunter. Die Sätze liegen nur in `notion_beispiele.json`
(Schlüssel `Kategorie|Wort ohne Betonungszeichen`), nicht in Notion. Wörter ohne
Eintrag – etwa neu hinzugekommene – zeigen einfach keinen Satz.

**Wörter entfernen:** unter jeder Karte „🗑 Dieses Wort entfernen“, oder
mehrere auf einmal im Bereich „🗑 Wörter entfernen / zurückholen“ – dort lassen
sie sich auch wiederherstellen. Entfernte Wörter werden nur ausgeblendet (in
der lokalen `notion_ausgeblendet.json`, auch in der Konjugation). So bringt der
tägliche Import sie nicht zurück, auch wenn sie in Notion stehen bleiben; der
Lernfortschritt bleibt erhalten.

Neue Wörter kommen per `notion_import.py` dazu: Seiteninhalt als Markdown
speichern und `python notion_import.py seite.md` aufrufen. Das Skript hängt
nur an bzw. aktualisiert Übersetzungen – gelöscht wird nichts. Die tägliche
Claude-Routine dafür ist pausiert (seit 27.10.2026); neue Wörter kommen nur
noch dazu, wenn man den Import von Hand anstößt.

## Fortschritt auf Streamlit Cloud

Ein Push auf `main` lässt `progress.json` auf Streamlit Cloud bestehen. Ob
der Fortschritt einen kompletten Neustart übersteht (Reboot, Aufwachen nach
Inaktivität), ist nicht geprüft. Als Absicherung kann er in einem privaten
GitHub-Gist liegen, mit den Dateien `progress.json` und `notion_progress.json`.
Aktiv wird das, sobald in den Streamlit-Secrets steht:

```toml
[gist]
id = "<Gist-ID>"
token = "<Fine-grained Token, nur Account-Recht „Gists: Read and write“>"
```

Ohne diese Secrets (lokal) bleibt alles wie gehabt bei den lokalen Dateien.
Beim Speichern übernimmt die App nur die in der Sitzung geänderten Wörter in
den aktuellen Gist-Stand, sodass sich zwei Geräte nicht gegenseitig
überschreiben.

## Batch lernen

Im Tab „Vokabeln" startet „🎯 Batch lernen" jederzeit
einen Batch: Box (1 → 2, 2 → 3, …) und Batchgröße wählen, die App zieht zufällig so viele Karten aus dieser Box (im
aktuellen Filter). Sie werden so lange abgefragt, bis alle mindestens eine Box
höher liegen. Bewertet wird normal: Box k braucht 2^(k-1) Treffer, „Nochmal"
wirft die Karte zwei Boxen zurück, sie bleibt im Batch, bis sie das Ziel erreicht.

## Lernlogik (Boxen)

Jede Vokabel liegt in einer Box von 1 bis 5. Neue Karten starten in Box 1.

| Box | Treffer für den Aufstieg | Ziehgewicht |
|---|---|---|
| 1 | 1 | 1 |
| 2 | 2 | 1/2 |
| 3 | 4 | 1/4 |
| 4 | 8 | 1/8 |
| 5 | – | 1/16 |

* **Gewusst** → ein Treffer. Sind in Box k 2^(k-1) Treffer erreicht, steigt die
  Karte eine Box auf, die Treffer starten wieder bei 0. Die Karte zeigt den
  Stand oben links, z. B. „Box 3/5 · 1/4“.
* **Nochmal** → zwei Boxen zurück (mindestens Box 1), Treffer wieder 0.
* Es gibt keine Fälligkeitstermine: Jede Karte des Filters kann jederzeit
  kommen, gezogen wird zufällig nach dem Ziehgewicht – eine Karte in Box 5
  kommt 16-mal seltener als eine in Box 1. Dieselbe Karte kommt nie zweimal
  direkt hintereinander (außer sie ist die einzige im Pool).
* **Zuletzt falsch:** Eine Karte, die du falsch hattest, kommt im offenen Modus
  (außerhalb eines Batches) 10-mal häufiger, bis du sie einmal richtig hast
  (`FEHLER_FAKTOR` in `konfig.py`), und **spätestens als 10. Karte danach
  sicher** wieder (`WIEDERHOLEN_SPAETESTENS`). Die Karte zeigt dann
  „· zuletzt falsch“. Die 10-Karten-Frist gilt für die laufende Sitzung, die
  Markierung „zuletzt falsch“ bleibt gespeichert.

`progress.json` wird nach jeder Bewertung atomar geschrieben (temporäre Datei + `os.replace`).
Fehlt die Datei oder ist sie beschädigt, startet die App mit leerem Fortschritt statt abzustürzen.

## Tab „Vokabeln verwalten"

Bearbeitet die ältere Vokabelliste `vocab.csv` (russisch, deutsch,
transkription, wortart, niveau, beispiel). Seit der Tab „Lernen" entfernt ist,
wird diese Liste nicht mehr abgefragt.

## Die Karten

Jede Vokabel steht auf einer echten Flashcard, die sich beim Aufdecken um die
senkrechte Achse dreht (CSS-`rotateY`, 0,75 s Animation):

* **Vorderseite** (blau): Abfragerichtung und Box-Stand, das deutsche Wort,
  darunter die Kategorie.
* **Rückseite** (grün): das russische Wort. Der Beispielsatz steht daneben
  (siehe Tab „Vokabeln").

Gedreht wird mit dem Button **„🔄 Karte umdrehen"** direkt unter der Karte;
danach erscheinen **Nochmal** und **Gewusst**. Die Karte selbst ist bewusst
nicht anklickbar: Ein Klick im eingebetteten iframe kann Streamlit nicht
erreichen, ohne ins DOM der Elternseite zu greifen – dieser Hack bliebe draußen.

Technisch rendert `zeige_flashcard()` die Karte als in sich geschlossenes
HTML-Dokument und bettet es über `st.iframe()` ein (mit Rückfall auf
`st.components.v1.html` für ältere Streamlit-Versionen). Alle Felder werden vorher `html.escape()`-behandelt, es landet also kein
ungeprüftes Markup in der Seite. Das Farbschema der Karte ist bewusst
eigenständig und funktioniert im hellen wie im dunklen Streamlit-Theme.

## Tab „Übersetzen"

Ein russischer Text wird angezeigt, du überträgst ihn ins Deutsche, danach
erscheint die Musterlösung zum Vergleich.

* **Schwierigkeit** oben links: `A1 – leicht`, `A2 – mittel`, `B1 – fordernd`.
  Die Liste baut sich aus den Niveaus in `texte.json`, eine neue Stufe taucht
  also automatisch auf.
* **Richtung** daneben:
  * `RU → DE` – russischer Text, du übersetzt ins Deutsche.
  * `DE → RU` – deutscher Text, du übersetzt ins Russische. Unter dem
    Eingabefeld klappt dafür das kyrillische Tastenfeld auf.
  * `gemischt` – pro Text zufällig die eine oder die andere Richtung; über dem
    Text steht, was gerade dran ist.

  Beide Richtungen nutzen dieselben Texte: das jeweils andere Feld aus
  `texte.json` wird zur Musterlösung. Ein Richtungswechsel zieht einen neuen
  Text, damit im Eingabefeld nichts in der falschen Sprache stehen bleibt.
* **🔀 Anderer Text** zieht einen anderen Text derselben Stufe, nie denselben zweimal.
* Nach **Musterlösung zeigen** kommt die Referenzübersetzung, darunter ein
  Stichwort-Abgleich und die Liste der nicht wiedergefundenen Wörter.
* **Nächster Text →** leert das Eingabefeld und verdeckt die Lösung wieder.

Mitgeliefert sind **12 Texte** (je vier pro Stufe) zwischen 57 und 78 Wörtern,
alle im geforderten Rahmen von 50–100.

### Was der Stichwort-Abgleich ist – und was nicht

Eine freie Übersetzung lässt sich ohne Sprachmodell nicht sinnvoll benoten: zu
jedem Satz gibt es viele richtige Varianten. Die App zählt deshalb nur, welche
Inhaltswörter der Musterlösung in deinem Text vorkommen – tolerant gegenüber
Beugung (Wortstamm und Ähnlichkeitsvergleich), aber **blind für Synonyme und
umgestellte Sätze**. Er arbeitet in beiden Richtungen, für Deutsch wie für
Kyrillisch, mit je eigener Stoppwortliste. Eine gute Übersetzung kann also unter 100 % landen. Der
Balken taugt zum Aufspüren übersprungener Sätze, nicht als Note. **Die Bewertung
bleibt bei dir** – so steht es auch in der App.

### Eigene Texte ergänzen

`texte.json` ist eine Liste von Objekten mit genau fünf Feldern:

```json
{
  "id": "a1-mein-tag",
  "niveau": "A1",
  "titel": "Мой день",
  "russisch": "Меня зовут Анна. …",
  "deutsch": "Ich heiße Anna. …"
}
```

`id` muss eindeutig sein, `niveau` ist frei wählbar und füllt die Auswahlliste.
`russisch` und `deutsch` sind je nach Richtung Quelle oder Musterlösung – beide Felder sollten also für sich stehen können.
Einträge, bei denen ein Feld fehlt oder leer ist, werden beim Laden still
übersprungen. Fehlt die Datei ganz oder ist das JSON kaputt, zeigt der Tab eine
Meldung – der Rest der App läuft normal weiter.

## Tab „Konjugation"

Abgefragt werden nur die Verben der Notion-Wortbank. Die App zeigt ein
zufälliges Verb (Infinitiv mit Betonung und Bedeutung), du tippst alle sechs
Präsensformen (я … они) und den Imperativ (du-Form) ein. „Prüfen & Lösung
zeigen“ geht jederzeit, auch mit leeren Feldern. Danach siehst du jede Eingabe
neben der Lösung, ✅ richtig, 🟡 fast (Tippfehler), ❌ falsch.

- Vollendete Verben (стать, познако́миться, уста́ть) haben kein Präsens –
  gefragt sind dann die Formen des einfachen Futurs; bei быть ebenso das Futur.
- Verben ohne gebräuchlichen Imperativ (хоте́ть, ви́деть, нра́виться, …)
  haben nur die sechs Präsensfelder.
- ё darf als е getippt werden, Groß-/Kleinschreibung ist egal.
- Kein Box-System: Gezählt wird nur für die laufende Sitzung.

Die Formen stehen in `notion_verben.json` (Infinitiv ohne Betonungszeichen):

```json
{
  "infinitiv": "читать",
  "aspekt": "ipf",
  "formen": {"я": "читаю", "ты": "читаешь", "он/она": "читает",
             "мы": "читаем", "вы": "читаете", "они": "читают"},
  "imperativ": "читай / читайте"
}
```

Ein Notion-Verb ohne Eintrag in dieser Datei taucht im Tab nicht auf.

## Bekannte Einschränkung

Eine Tastatursteuerung (Leertaste zum Aufdecken o. Ä.) ist nicht eingebaut:
Streamlit bietet dafür keine native API, und die üblichen Lösungen brauchen
JavaScript-Injection oder Zusatzpakete. Die Bedienung läuft daher über die Buttons.
