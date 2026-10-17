#!/bin/bash
# Startet den Vokabeltrainer lokal - per Doppelklick im Finder oder ./start.command.
# Holt vorher die neuesten Notion-Wörter (git pull). Der Lernfortschritt liegt in
# progress.json / notion_progress.json in diesem Ordner und wird von git nie angefasst.

cd "$(dirname "$0")" || exit 1

if ! git pull --ff-only -q; then
    echo "Hinweis: git pull hat nicht geklappt - starte mit dem lokalen Stand."
fi

if [ ! -x .venv/bin/streamlit ]; then
    echo "Richte die virtuelle Umgebung ein ..."
    python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || exit 1
fi

echo "Vokabeltrainer läuft auf http://localhost:8501 - beenden mit Ctrl+C oder Fenster schließen."
exec .venv/bin/streamlit run app.py --server.headless false
