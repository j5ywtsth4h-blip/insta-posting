"""Druckfertiger FokusOffice-Werbebrief (DIN A4, DIN 5008 Form B, für DL-Fensterumschlag).

Aufruf:  python3 akquise/brief/brief.py
Ergebnis: akquise/brief/FokusOffice_Brief_alle.pdf (ein Brief je Betrieb aus betriebe.py)
          akquise/brief/FokusOffice_Brief_leer.pdf  (ohne Anschrift, zum Kopieren)
"""
import base64
import html
import io
from pathlib import Path

import qrcode
import qrcode.image.svg
from playwright.sync_api import sync_playwright

from betriebe import BETRIEBE
from seite2 import CSS2, seite2

HIER = Path(__file__).resolve().parent
CHROME = "/opt/pw-browsers/chromium"

# Ziel des QR-Codes. Sobald die Video-Seite steht, hier die genaue Adresse eintragen und neu erzeugen.
VIDEO_URL = "https://fokuszeit-business.de/fokusoffice.html?utm_source=brief"

DATUM = "November 2026"
ANGEBOT_TITEL = "Ihr Vorteil bis 31.12.2026"
ANGEBOT_TEXT = (
    "Ich richte FokusOffice persönlich mit Ihnen ein – bei Ihnen im Betrieb oder online: "
    "Firmendaten, Ihre Preisliste als Leistungskatalog und die erste E-Rechnung gemeinsam."
)
ANGEBOT_PREIS = "60 Minuten für 29 € statt 59 €"
ANGEBOT_ZUSATZ = "Mit Jahresabo Business oder Premium kostenlos."


def qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=0,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    buf = io.BytesIO()
    img.save(buf)
    return "data:image/svg+xml;base64," + base64.b64encode(buf.getvalue()).decode()


CSS = """
@font-face { font-family: Playfair; src: url('fonts/PlayfairDisplay.ttf'); font-weight: 400 900; }
@font-face { font-family: DMSans; src: url('fonts/DMSans.ttf'); font-weight: 100 1000; }
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --forest:#183f35; --sage:#cbd5be; --sage-l:#e9eee2; --cream:#faf7f0; --peach:#f6dfcd; --text:#1f2a26; --muted:#5d6b64; }
body { font-family: DMSans, sans-serif; color: var(--text); font-size: 10pt; line-height: 1.42; }
.seite { width: 210mm; height: 297mm; position: relative; page-break-after: always; overflow: hidden; background: #fff; }
.seite:last-child { page-break-after: auto; }
.abs { position: absolute; }
.marke { left: 4mm; width: 5mm; border-top: 0.3pt solid #9aa59f; }
.kopf { left: 25mm; top: 14mm; right: 20mm; display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 0.6pt solid var(--sage); padding-bottom: 4mm; }
.wort { font-family: Playfair; font-size: 21pt; font-weight: 600; color: var(--forest); letter-spacing: 0.2pt; line-height: 1; }
.wort small { display:block; font-family: DMSans; font-size: 7.5pt; font-weight: 600; letter-spacing: 2.2pt;
              text-transform: uppercase; color: var(--muted); margin-top: 2mm; }
.produkt { text-align: right; font-size: 8pt; color: var(--muted); line-height: 1.35; }
.produkt b { color: var(--forest); font-size: 10pt; font-weight: 700; display:block; }
.ruecksende { left: 25mm; top: 47mm; width: 80mm; font-size: 6.5pt; color: var(--muted);
              border-bottom: 0.3pt solid #b7c0bb; padding-bottom: 0.6mm; }
.anschrift { left: 25mm; top: 62.7mm; width: 80mm; height: 27.3mm; font-size: 10.5pt; line-height: 1.3; }
.info { left: 125mm; top: 50mm; width: 65mm; font-size: 8.3pt; line-height: 1.5; color: var(--muted); }
.info b { color: var(--text); font-weight: 600; }
.inhalt { left: 25mm; top: 99mm; width: 165mm; }
h1 { font-family: Playfair; font-weight: 600; font-size: 15.5pt; color: var(--forest); line-height: 1.2; margin-bottom: 1.2mm; }
.unter { font-weight: 600; font-size: 10pt; color: var(--muted); margin-bottom: 5mm; }
p { margin-bottom: 2.6mm; }
ul { list-style: none; margin: 1mm 0 4mm; }
li { position: relative; padding-left: 6mm; margin-bottom: 1.4mm; }
li::before { content:""; position:absolute; left: 0.8mm; top: 0.35mm; width: 1.9mm; height: 3.3mm;
             border-right: 1.6pt solid var(--forest); border-bottom: 1.6pt solid var(--forest); transform: rotate(40deg); }
.reihe { display: flex; gap: 5mm; margin: 1mm 0 4mm; align-items: stretch; }
.angebot { flex: 1; background: var(--cream); border-left: 2.2mm solid var(--forest); padding: 3.6mm 4.5mm; }
.angebot .t { font-size: 7.5pt; font-weight: 700; letter-spacing: 1.6pt; text-transform: uppercase; color: var(--muted); }
.angebot .p { font-family: Playfair; font-size: 13.5pt; font-weight: 600; color: var(--forest); margin: 1mm 0 1.2mm; }
.angebot .x { font-size: 9pt; }
.angebot .z { font-size: 9pt; font-weight: 600; margin-top: 1mm; }
.qr { width: 41mm; background: var(--sage-l); padding: 3mm; text-align: center; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.qr img { width: 27mm; height: 27mm; background:#fff; padding: 1.6mm; }
.qr span { font-size: 8pt; font-weight: 600; color: var(--forest); margin-top: 1.8mm; line-height: 1.25; }
.sicher { display: flex; gap: 3.5mm; font-size: 8pt; color: var(--muted); border-top: 0.6pt solid var(--sage);
          border-bottom: 0.6pt solid var(--sage); padding: 2.2mm 0; margin-bottom: 4mm; }
.sicher div { flex: 1; }
.sicher b { display:block; color: var(--forest); font-size: 8.3pt; font-weight: 700; }
.gruss { margin-top: 1mm; }
.unterschrift { height: 13mm; }
.fuss { left: 25mm; right: 20mm; top: 280mm; font-size: 7pt; color: var(--muted); display:flex; justify-content: space-between;
        border-top: 0.6pt solid var(--sage); padding-top: 2mm; line-height: 1.45; }
.fuss .note { margin-top: 0; }
"""


def brief(b):
    zeilen = "<br>".join(html.escape(z) for z in b["zeilen"]) if b else ""
    anrede = html.escape((b or {}).get("anrede") or "Guten Tag,")
    return f"""
<section class="seite">
  <div class="abs marke" style="top:105mm"></div>
  <div class="abs marke" style="top:148.5mm; width:7mm"></div>
  <div class="abs marke" style="top:210mm"></div>

  <div class="abs kopf">
    <div class="wort">Fokuszeit<small>Business Support</small></div>
    <div class="produkt"><b>FokusOffice</b>Das Büroprogramm für Handwerk<br>und kleine Betriebe</div>
  </div>

  <div class="abs ruecksende">Fokuszeit Business Support · Zum Lindenrondell 4 · 34379 Calden</div>
  <div class="abs anschrift">{zeilen}</div>

  <div class="abs info">
    <b>Ihre Ansprechpartnerin</b><br>Lara Kohls<br>
    Telefon 0176 20558600<br>kontakt@fokuszeit-business.de<br>fokuszeit-business.de<br><br>
    Calden, im {DATUM}
  </div>

  <div class="abs inhalt">
    <h1>Sind Sie schon digital?</h1>
    <div class="unter">Die E-Rechnung kommt – mit FokusOffice sind Sie vorbereitet.</div>

    <p>{anrede}</p>
    <p>ich bin Lara Kohls aus Calden und unterstütze Betriebe hier in der Region bei der Büroarbeit.
    Seit 2025 müssen Betriebe E-Rechnungen empfangen können, je nach Umsatz ab 2027 oder 2028 auch
    selbst verschicken.¹ Genau dafür habe ich FokusOffice entwickelt – damit Büroarbeit nicht den Feierabend kostet.</p>

    <ul>
      <li>Angebot, Auftrag und Rechnung in wenigen Schritten – auch als E-Rechnung (XRechnung),
          mit dem offiziellen Prüfwerkzeug (KoSIT) geprüft</li>
      <li>Baustellenfotos, Fahrten und Arbeitszeiten direkt beim Auftrag – am PC, Tablet und Handy</li>
      <li>Keine Zeit fürs Büro? Aufgaben direkt im Programm an mich übergeben</li>
    </ul>

    <div class="reihe">
      <div class="angebot">
        <div class="t">{ANGEBOT_TITEL}</div>
        <div class="p">{ANGEBOT_PREIS}</div>
        <div class="x">{ANGEBOT_TEXT}</div>
        <div class="z">{ANGEBOT_ZUSATZ}</div>
      </div>
      <div class="qr">
        <img src="{QR}" alt="">
        <span>Video ansehen:<br>FokusOffice in Aktion</span>
      </div>
    </div>

    <div class="sicher">
      <div><b>Server in Deutschland</b>Ihre Daten liegen bei einem deutschen Anbieter.</div>
      <div><b>Tägliche Sicherung</b>Ihre Daten werden jeden Tag gesichert.</div>
      <div><b>Ihre Daten gehören Ihnen</b>Export jederzeit möglich.</div>
      <div><b>Ohne Abo-Falle</b>14 Tage kostenlos testen, endet automatisch.</div>
    </div>

    <p>Ab 9,99 € im Monat, Angebote ab Tarif Business für 16,99 € (keine USt. gem. § 19 UStG). Rufen Sie mich gern an – ich zeige Ihnen FokusOffice in Ruhe.</p>

    <p class="gruss">Mit freundlichen Grüßen</p>
    <div class="unterschrift"></div>
    <p>Lara Kohls</p>
  </div>

  <div class="abs fuss">
    <div>Fokuszeit Business Support · Lara Kohls · Zum Lindenrondell 4 · 34379 Calden<br>
    Telefon 0176 20558600 · kontakt@fokuszeit-business.de · fokuszeit-business.de</div>
    <div style="text-align:right">¹ Allgemeiner Überblick, ersetzt keine Steuerberatung.<br>
    Alle Preise: keine USt. gem. § 19 UStG.</div>
  </div>
</section>"""


def pdf(seiten, ziel):
    global QR
    doc = f"<!doctype html><html lang='de'><head><meta charset='utf-8'><style>{CSS}{CSS2}</style></head><body>{''.join(seiten)}</body></html>"
    quelle = HIER / "_brief.html"
    quelle.write_text(doc, encoding="utf-8")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=CHROME) if Path(CHROME).exists() else p.chromium.launch()
        pg = br.new_page()
        pg.goto(quelle.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=str(ziel), format="A4", print_background=True, prefer_css_page_size=True)
        br.close()
    quelle.unlink()
    print("ok", ziel)


QR = qr_svg(VIDEO_URL)

if __name__ == "__main__":
    # Je Betrieb Vorder- und Rückseite (beidseitig drucken)
    pdf([s for b in BETRIEBE for s in (brief(b), seite2())], HIER / "FokusOffice_Brief_alle.pdf")
    pdf([brief(None), seite2()], HIER / "FokusOffice_Brief_leer.pdf")
