"""Lesen und Schreiben einer Datei in einem (privaten) GitHub-Gist.

Dient als dauerhafter Speicher für den Lernfortschritt auf Streamlit Cloud,
wo die lokale Festplatte bei jedem Neustart gelöscht wird. Nur Standardbibliothek.
"""

import json
import urllib.request


API = "https://api.github.com/gists/"


class GistFehler(Exception):
    pass


def _anfrage(gist_id: str, token: str, methode: str = "GET", daten: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + gist_id,
        method=methode,
        data=json.dumps(daten).encode("utf-8") if daten is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except (OSError, ValueError) as exc:  # URLError/HTTPError sind OSError
        raise GistFehler(str(exc)) from exc


def lesen(gist_id: str, token: str, dateiname: str) -> str | None:
    """Inhalt der Datei im Gist, None wenn es sie (noch) nicht gibt."""
    datei = _anfrage(gist_id, token).get("files", {}).get(dateiname)
    if datei is None:
        return None
    if datei.get("truncated"):
        req = urllib.request.Request(datei["raw_url"], headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as antwort:
                return antwort.read().decode("utf-8")
        except OSError as exc:
            raise GistFehler(str(exc)) from exc
    return datei.get("content", "")


def schreiben(gist_id: str, token: str, dateiname: str, inhalt: str) -> None:
    _anfrage(gist_id, token, "PATCH", {"files": {dateiname: {"content": inhalt}}})
