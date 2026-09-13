"""Die Flashcard: ein in sich geschlossenes HTML-Dokument, das sich dreht."""

import html

import streamlit as st
import streamlit.components.v1 as components

from konfig import MAX_BOX


KARTEN_HOEHE = 300


KARTEN_CSS = """
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: transparent;
         font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .buehne { perspective: 1600px; padding: 4px 2px 10px; }
  .karte { position: relative; width: 100%; height: CARDHEIGHTpx;
           transform-style: preserve-3d;
           transition: transform 0.75s cubic-bezier(0.2, 0.75, 0.3, 1); }
  .karte.gedreht { transform: rotateY(180deg); }
  .seite { position: absolute; top: 0; left: 0; right: 0; bottom: 0;
           backface-visibility: hidden; -webkit-backface-visibility: hidden;
           border-radius: 20px; padding: 30px 34px;
           display: flex; flex-direction: column;
           align-items: center; justify-content: center;
           text-align: center; color: #fff;
           box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24); }
  .vorne { background: linear-gradient(150deg, #2a3a8c 0%, #3f53c6 55%, #5a6fe0 100%); }
  .hinten { background: linear-gradient(150deg, #0e6a5f 0%, #148578 55%, #1da08e 100%);
            transform: rotateY(180deg); }
  .marke { position: absolute; top: 15px; left: 22px; font-size: 0.7rem;
           letter-spacing: 0.09em; text-transform: uppercase;
           font-weight: 700; opacity: 0.72; }
  .wort { font-weight: 700; line-height: 1.15; margin: 2px 0; }
  .meta { margin-top: 16px; font-size: 0.82rem; opacity: 0.68; }
  .lautschrift { margin-top: 10px; font-size: 1.05rem; font-style: italic; opacity: 0.9; }
  .beispiel { margin-top: 16px; padding-top: 14px; max-width: 94%;
              font-size: 0.9rem; line-height: 1.5;
              border-top: 1px solid rgba(255, 255, 255, 0.3); }
  .beispiel .de { opacity: 0.76; }
  .fuss { position: absolute; bottom: 13px; font-size: 0.72rem; opacity: 0.55; }
</style>
""".replace("CARDHEIGHT", str(KARTEN_HOEHE))


def _schriftgroesse(text: str) -> str:
    laenge = len(text)
    if laenge <= 12:
        return "3rem"
    if laenge <= 22:
        return "2.3rem"
    if laenge <= 34:
        return "1.7rem"
    return "1.35rem"


def zeige_flashcard(frage: str, antwort: str, karte, richtung: str, box: int, gedreht: bool) -> None:
    """Rendert die Vokabel als 3D-Karte; `gedreht` löst die Drehung animiert aus."""
    esc = html.escape
    beispiel = karte["beispiel"]
    bsp_ru, _, bsp_de = beispiel.partition(" — ")
    beispiel_html = (
        f'<div class="beispiel">{esc(bsp_ru)}'
        + (f'<br><span class="de">{esc(bsp_de)}</span>' if bsp_de else "")
        + "</div>"
        if beispiel
        else ""
    )
    lautschrift = (
        f'<div class="lautschrift">[{esc(karte["transkription"])}]</div>'
        if karte["transkription"]
        else ""
    )
    inhalt = f"""
    <div class="buehne">
      <div class="karte" id="karte">
        <div class="seite vorne">
          <div class="marke">{esc(richtung)} &middot; Box {box}/{MAX_BOX}</div>
          <div class="wort" style="font-size:{_schriftgroesse(frage)}">{esc(frage)}</div>
          <div class="meta">{esc(karte["wortart"])} &middot; {esc(karte["niveau"])}</div>
          <div class="fuss">Umdrehen mit dem Button darunter</div>
        </div>
        <div class="seite hinten">
          <div class="marke">Auflösung</div>
          <div class="wort" style="font-size:{_schriftgroesse(antwort)}">{esc(antwort)}</div>
          {lautschrift}
          {beispiel_html}
        </div>
      </div>
    </div>
    <script>
      if ({str(bool(gedreht)).lower()}) {{
        const k = document.getElementById("karte");
        requestAnimationFrame(() => setTimeout(() => k.classList.add("gedreht"), 80));
      }}
    </script>
    """
    _einbetten(KARTEN_CSS + inhalt, KARTEN_HOEHE + 24)


def _einbetten(html_text: str, hoehe: int) -> None:
    """st.iframe auf neueren Streamlit-Versionen, sonst der klassische HTML-Component.

    Alle Vokabelfelder sind vorher html-escaped, es landet also kein
    ungeprüfter Inhalt aus vocab.csv im iframe.
    """
    if hasattr(st, "iframe"):
        st.iframe(html_text, height=hoehe)
    else:
        components.html(html_text, height=hoehe)
