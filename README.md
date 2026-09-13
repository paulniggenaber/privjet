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

```bash
streamlit run app.py
```

Die App öffnet sich unter <http://localhost:8501>. Beenden mit `Ctrl+C`.

## Dateien

| Datei | Zweck |
|---|---|
| `app.py` | Einstiegspunkt: Seite, Sidebar, Tabs, Session-State |
| `konfig.py` | Pfade und Konstanten (Boxen, Intervalle, Richtungen, Modi) |
| `daten.py` | Laden und Speichern von `vocab.csv`, `texte.json`, `progress.json` |
| `leitner.py` | Fälligkeit und Bewertung einer Karte |
| `vergleich.py` | Textvergleich ohne Streamlit: Antwortprüfung, Stichwortabgleich |
| `karte.py` | die Flashcard mit der 3D-Drehung |
| `tastenfeld.py` | kyrillisches Tastenfeld (ЙЦУКЕН) |
| `lernen.py` | Tab „Lernen" – Kartenwahl, Kartenmodus, Tippmodus |
| `konjugation.py` | Tab „Konjugation" |
| `uebersetzen.py` | Tab „Übersetzen" |
| `verwalten.py` | Tab „Vokabeln verwalten" |
| `vocab.csv` | Vokabeldaten (UTF-8) |
| `texte.json` | Übersetzungstexte mit Musterlösung (UTF-8) |
| `verben.json` | Konjugationstabellen (UTF-8) |
| `progress.json` | Lernfortschritt, wird beim ersten Bewerten automatisch angelegt |
| `requirements.txt` | Abhängigkeiten |

Die Abhängigkeiten laufen nur in eine Richtung, es gibt keine Zyklen:

```
app  →  lernen ┬→ karte, tastenfeld, vergleich
        konjugation ┤                 │
        uebersetzen ┘                 │
        verwalten             │
            └→ leitner  →  daten  →  konfig
```

`vergleich.py` kommt ohne Streamlit aus – die Prüflogik lässt sich also ohne
laufende App testen.

## Lernlogik (Leitner)

Jede Vokabel liegt in einer Box von 1 bis 5:

| Box | Intervall bis zur nächsten Abfrage |
|---|---|
| 1 | 1 Tag |
| 2 | 2 Tage |
| 3 | 4 Tage |
| 4 | 8 Tage |
| 5 | 16 Tage |

* Neue Karten starten in Box 1.
* **Gewusst** → eine Box hoch (maximal 5), `next_due = heute + Intervall der neuen Box`.
* **Nochmal** → zurück in Box 1, also morgen wieder fällig.
* Abgefragt werden nur Karten, deren `next_due` heute oder früher liegt – in zufälliger Reihenfolge.
* Ist nichts fällig, nennt die App das Datum der nächsten Fälligkeit und bietet
  **„Trotzdem weiterüben"** an, was alle Karten des aktuellen Filters freischaltet.

`progress.json` wird nach jeder Bewertung atomar geschrieben (temporäre Datei + `os.replace`).
Fehlt die Datei oder ist sie beschädigt, startet die App mit leerem Fortschritt statt abzustürzen.

## Eigene Wörter ergänzen

`vocab.csv` ist eine normale, komma-getrennte CSV in **UTF-8** mit genau diesen sechs Spalten:

| Spalte | Inhalt | Beispiel |
|---|---|---|
| `russisch` | russisches Wort – zugleich der eindeutige Schlüssel für den Fortschritt | `вода` |
| `deutsch` | deutsche Übersetzung, mehrere Bedeutungen mit Komma | `das Wasser` |
| `transkription` | deutsche Umschrift, Betonung mit Akzent markiert | `wadá` |
| `wortart` | frei wählbar, füllt den Wortart-Filter | `Substantiv` |
| `niveau` | frei wählbar, füllt den Niveau-Filter | `A1` |
| `beispiel` | Beispielsatz Russisch — deutsche Übersetzung | `Я пью воду. — Ich trinke Wasser.` |

Drei Wege, Wörter zu ergänzen:

1. **Im Tab „Vokabeln verwalten"** unten in der Tabelle eine leere Zeile ausfüllen
   und auf *Änderungen speichern* klicken.
2. **CSV anhängen**: eigene Datei mit denselben Spalten hochladen. Sie wird
   *angehängt*, nicht ersetzt; Wörter, die in `russisch` schon existieren, werden übersprungen.
3. **Direkt in `vocab.csv`**: Zeile anhängen und die Datei als UTF-8 speichern.
   Enthält ein Feld ein Komma oder Anführungszeichen, muss es in `"…"` stehen –
   ein Tabellenprogramm macht das automatisch. Danach die App neu laden (Browser-Reload
   genügt, der Cache wird beim Speichern über die App invalidiert; bei manueller
   Bearbeitung der Datei einmal `R` in Streamlit drücken oder die App neu starten).

Neu ergänzte Wörter landen automatisch in Box 1 und sind sofort fällig.
Wird ein Wort in `russisch` umbenannt, gilt es als neue Vokabel – der alte
Fortschrittseintrag bleibt verwaist in `progress.json` liegen und stört nicht.

## Enthaltener Wortschatz

362 Vokabeln des Grundwortschatzes, Niveau A1 (158) und A2 (204), gemischt aus
Substantiven, Verben, Adjektiven, Adverbien, festen Wendungen sowie einigen
Konjunktionen und Präpositionen. Die Liste ist eine eigene Zusammenstellung mit
selbst geschriebenen Beispielsätzen und als Startpunkt gedacht – über die drei
Wege oben lässt sie sich beliebig erweitern.

## Die Karten

Jede Vokabel steht auf einer echten Flashcard, die sich beim Aufdecken um die
senkrechte Achse dreht (CSS-`rotateY`, 0,75 s Animation):

* **Vorderseite** (blau): Abfragerichtung und Box-Nummer, das Fragewort,
  darunter Wortart und Niveau.
* **Rückseite** (grün): Übersetzung, Transkription in eckigen Klammern und der
  Beispielsatz – russischer Satz oben, deutsche Übersetzung darunter abgesetzt.

Gedreht wird mit dem Button **„🔄 Karte umdrehen"** direkt unter der Karte;
danach erscheinen **Nochmal** und **Gewusst**. Die Karte selbst ist bewusst
nicht anklickbar: Ein Klick im eingebetteten iframe kann Streamlit nicht
erreichen, ohne ins DOM der Elternseite zu greifen – dieser Hack bliebe draußen.

Technisch rendert `zeige_flashcard()` die Karte als in sich geschlossenes
HTML-Dokument und bettet es über `st.iframe()` ein (mit Rückfall auf
`st.components.v1.html` für ältere Streamlit-Versionen). Alle Felder aus
`vocab.csv` werden vorher `html.escape()`-behandelt, es landet also kein
ungeprüftes Markup in der Seite. Das Farbschema der Karte ist bewusst
eigenständig und funktioniert im hellen wie im dunklen Streamlit-Theme.

## Die zwei Modi

In der Sidebar unter **Modus**:

| Modus | Ablauf |
|---|---|
| **Karten** | Karte umdrehen, Antwort ansehen, selbst mit *Nochmal* / *Gewusst* bewerten |
| **Tippen** | Antwort eintippen, die App prüft und schlägt die Bewertung vor |
| **gemischt** | pro Karte zufällig das eine oder das andere; über der Karte steht, was gerade dran ist |

### Tippmodus

Antwort eingeben und **Eingabetaste** drücken (oder *Prüfen* klicken). Die Karte
dreht sich auf, darunter steht das Urteil:

* **Richtig** → grün, ein Button *Weiter →*, die Karte steigt eine Box auf.
* **Fast** → gelb bei einem Tippfehler. Beide Buttons erscheinen, du entscheidest,
  ob es zählt.
* **Falsch** → rot mit der richtigen Antwort. *Nochmal* ist vorausgewählt, aber
  *Zählt als gewusst* bleibt daneben – falls die App eine gültige Übersetzung
  nicht erkannt hat, behältst du das letzte Wort.

Beim Vergleich wird großzügig normalisiert: Groß-/Kleinschreibung, Satzzeichen und
überflüssige Leerzeichen sind egal, der Artikel darf weg (`Wasser` statt
`das Wasser`), bei mehreren Bedeutungen genügt eine (`sagen` statt
`sprechen, sagen`), Klammerzusätze dürfen fehlen (`Guten Tag` statt
`Guten Tag! (höflich)`), Umlaute dürfen umschrieben werden (`schoen` für `schön`,
`heisse` für `heiße`) und im Russischen zählt `е` auch für `ё` (`ребенок` für
`ребёнок`). Tippfehler landen über einen Ähnlichkeitsvergleich
(`difflib`, ab 82 %) in der Kategorie *fast*.

**Richtung RU → DE:** du tippst deutsch, ganz normal über die Tastatur.

**Richtung DE → RU:** du tippst kyrillisch. Weil ein deutsches Tastaturlayout das
nicht hergibt, klappt unter dem Eingabefeld ein Tastenfeld im russischen
Standardlayout **ЙЦУКЕН** auf – alle 33 Buchstaben inklusive ё, ъ und ь, dazu
Leerzeichen, Rücktaste und eine Feststelltaste für Großbuchstaben. Es erscheint
nur in dieser Richtung.

**Auf Dauer bequemer:** macOS bringt das russische Layout mit
(*Systemeinstellungen → Tastatur → Eingabequellen → + → Russisch*). Danach
wechselt `Ctrl+Leertaste` die Sprache und du tippst direkt ins Feld – auch in die
Vokabeltabelle. Die Belegung ist dieselbe wie im eingebauten Tastenfeld.

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

Abgefragt wird eine einzelne Verbform: oben steht der Infinitiv, darunter die
gesuchte Person. Du tippst die Form ein, die App prüft sofort.

**Die deutsche Bedeutung steht bewusst nicht in der Aufgabe** – sie wird
mitgelernt und erscheint erst zusammen mit der Auflösung. Wer die Form bildet,
soll auch wissen, was das Verb heißt.

Deshalb gibt es ein zweites Feld: **Bedeutung mit abfragen** (standardmäßig an)
verlangt zusätzlich die deutsche Übersetzung. Beide Teile werden getrennt
zurückgemeldet, die Aufgabe zählt nur dann als richtig, wenn beides stimmt.
Zum reinen Formen-Drillen lässt sich der Schalter ausschalten – dann zählt die
Verbform allein.

Bei der Bedeutung genügt eine von mehreren Übersetzungen: für `sprechen, sagen`
wird `sagen` akzeptiert, für `wollen, möchten` auch `moechten`.

* **Zeitform**: `Präsens`, `Präteritum` oder `gemischt`.
* **Verbgruppen** als Mehrfachauswahl: `regelmäßig (-ать)`,
  `regelmäßig (-ить)`, `Stammwechsel`, `unregelmäßig`, `reflexiv (-ся)`.
  So lassen sich gezielt die unregelmäßigen üben.
* **Prüfen** oder Eingabetaste wertet aus (die Eingabetaste löst in beiden
  Feldern aus), **🔀 Andere Aufgabe** überspringt ohne Wertung.
* Nach der Auswertung erscheinen **Bedeutung und die komplette Formentabelle**
  der Zeitform, die gefragte Zeile hervorgehoben.
* Drei Zähler oben: richtig, falsch, Trefferquote. Sie gelten **nur für die
  laufende Sitzung** und wandern nicht in `progress.json` – dort steckt der
  Vokabel-Fortschritt, den Konjugationsübungen nicht verfälschen sollen.

Die Bewertung nutzt dieselbe Prüfung wie der Tippmodus: Groß-/Kleinschreibung
ist egal, `е` zählt für `ё` (`живешь` für `живёшь`), und ein einzelner
Tippfehler landet in der Kategorie *fast*. Eine falsche Person zählt dagegen
klar als falsch – `читаем` für `читаю` wird nicht durchgewinkt.

Mitgeliefert sind **41 Verben mit 404 Formen**. `быть` hat richtigerweise kein
Präsens und wird deshalb nur im Präteritum abgefragt.

### Eigene Verben ergänzen

`verben.json` ist eine Liste von Objekten:

```json
{
  "infinitiv": "читать",
  "deutsch": "lesen",
  "gruppe": "regelmäßig (-ать)",
  "praesens": {"я": "читаю", "ты": "читаешь", "он/она": "читает",
               "мы": "читаем", "вы": "читаете", "они": "читают"},
  "praeteritum": {"он": "читал", "она": "читала",
                  "оно": "читало", "они": "читали"}
}
```

`gruppe` ist frei wählbar und füllt die Auswahlliste. `praesens` darf `null`
sein oder ganz fehlen, wenn es die Form nicht gibt – das Verb wird dann nur im
Präteritum abgefragt. Einträge mit leeren Formen werden beim Laden still
übersprungen; fehlt oder bricht die Datei, zeigt der Tab eine Meldung und der
Rest der App läuft weiter.

## Bekannte Einschränkung

Eine Tastatursteuerung (Leertaste zum Aufdecken o. Ä.) ist nicht eingebaut:
Streamlit bietet dafür keine native API, und die üblichen Lösungen brauchen
JavaScript-Injection oder Zusatzpakete. Die Bedienung läuft daher über die Buttons.
