"""Rückseite des Werbebriefs: Alles in einem Programm, Handwerk-Funktionen, Tarife."""

def ico(pfad):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{pfad}</svg>')

I = {
    "kamera": ico('<path d="M4 8h3l1.5-2h7L17 8h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>'),
    "chat": ico('<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>'),
    "kalender": ico('<rect x="4" y="5" width="16" height="15" rx="1.5"/><path d="M4 9.5h16M8 3v4M16 3v4"/><path d="M8.5 14l2 2 4-4"/>'),
    "angebot": ico('<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 12h7M9 15.5h7M9 8.5h3"/>'),
    "erechnung": ico('<path d="M6 3h9l4 4v14H6z"/><path d="M9.5 12.5l-2 2 2 2M14.5 12.5l2 2-2 2"/>'),
    "beleg": ico('<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 11.5h6M9 15h3"/>'),
    "uhr": ico('<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>'),
    "auto": ico('<path d="M4 15.5V12l2-5h12l2 5v3.5z"/><circle cx="8" cy="16.5" r="1.6"/><circle cx="16" cy="16.5" r="1.6"/><path d="M4 12h16"/>'),
    "stift": ico('<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M13.5 7.5l3 3"/><path d="M14 20h6"/>'),
    "mail": ico('<rect x="3.5" y="5.5" width="17" height="13" rx="1.5"/><path d="M4 7l8 6 8-6"/>'),
    "team": ico('<circle cx="9" cy="9" r="3"/><path d="M3.5 19c.5-3 2.7-4.5 5.5-4.5s5 1.5 5.5 4.5"/><circle cx="17" cy="8.5" r="2.3"/><path d="M15.5 13.5c2.3 0 4.3 1.3 4.8 4"/>'),
    "hand": ico('<path d="M7 11V6.5a1.5 1.5 0 013 0V11M10 10V5a1.5 1.5 0 013 0v5M13 10V6a1.5 1.5 0 013 0v6"/><path d="M16 9.5a1.5 1.5 0 013 0V14a7 7 0 01-7 7h-.5A6.5 6.5 0 015 15l-1.5-3a1.5 1.5 0 012.6-1.5L7 12"/>'),
    "zettel": ico('<path d="M5 4h10l4 4v12H5z"/><path d="M8 9h5M8 12h8M8 15h6"/>'),
    "tabelle": ico('<rect x="4" y="5" width="16" height="14" rx="1"/><path d="M4 10h16M4 14.5h16M10 5v14"/>'),
    "handy": ico('<rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/>'),
    "ordner": ico('<path d="M3.5 7V18.5h17V8.5H11L9 6H3.5z"/>'),
}

CSS2 = """
.s2 { left: 20mm; top: 16mm; width: 170mm; }
.s2 .eyebrow { font-size: 7.5pt; font-weight: 700; letter-spacing: 2pt; text-transform: uppercase; color: var(--muted); }
.s2 h2 { font-family: Playfair; font-weight: 600; font-size: 20pt; line-height: 1.15; color: var(--forest); margin: 1.5mm 0 5mm; }
.vergleich { display: flex; align-items: center; gap: 4mm; margin-bottom: 7mm; }
.vorher { flex: 1; background: #f3f1ec; padding: 4mm; }
.vorher .k, .nachher .k { font-size: 7.5pt; font-weight: 700; letter-spacing: 1.5pt; text-transform: uppercase; margin-bottom: 2.5mm; }
.vorher .k { color: #8a8f8c; }
.chaos { display: grid; grid-template-columns: 1fr 1fr; gap: 1.8mm 3mm; font-size: 8.3pt; color: #6e7571; }
.chaos div { display: flex; align-items: center; gap: 1.8mm; }
.chaos svg { width: 4.6mm; height: 4.6mm; color: #9aa09d; flex: none; }
.pfeil { color: var(--forest); font-size: 18pt; font-weight: 300; }
.nachher { flex: 1; background: var(--forest); color: var(--cream); padding: 4mm; align-self: stretch; display:flex; flex-direction:column; justify-content:center; }
.nachher .k { color: var(--sage); }
.nachher .gross { font-family: Playfair; font-size: 15pt; font-weight: 600; line-height: 1.2; }
.nachher .klein { font-size: 8.3pt; margin-top: 2mm; color: #dfe6d8; }
.hw-titel { font-family: Playfair; font-weight: 600; font-size: 13.5pt; color: var(--forest); margin-bottom: 3mm; }
.hw { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm; margin-bottom: 7mm; }
.hw > div { background: var(--cream); padding: 4mm 3.6mm; border-top: 1.4mm solid var(--peach); }
.hw .ic { width: 11mm; height: 11mm; border-radius: 50%; background: var(--forest); color: var(--cream); display:flex; align-items:center; justify-content:center; margin-bottom: 2.5mm; }
.hw .ic svg { width: 6.2mm; height: 6.2mm; }
.hw b { display:block; font-size: 10pt; color: var(--forest); margin-bottom: 1.2mm; line-height: 1.25; }
.hw p { font-size: 8.5pt; line-height: 1.4; margin: 0; }
.hw .tarif { display:inline-block; margin-top: 2mm; font-size: 7pt; font-weight: 700; color: var(--muted); letter-spacing: .6pt; text-transform: uppercase; }
.raster-titel { font-family: Playfair; font-weight: 600; font-size: 13.5pt; color: var(--forest); margin-bottom: 3mm; }
.raster { display: grid; grid-template-columns: repeat(4, 1fr); gap: 3mm 3mm; margin-bottom: 7mm; }
.raster div { display: flex; align-items: center; gap: 2.2mm; font-size: 8.5pt; line-height: 1.25; }
.raster .ic { width: 8.5mm; height: 8.5mm; border-radius: 2mm; background: var(--sage-l); color: var(--forest); display:flex; align-items:center; justify-content:center; flex: none; }
.raster .ic svg { width: 5.2mm; height: 5.2mm; }
.raster sup { font-size: 6.5pt; color: var(--muted); }
.tarife { display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; margin-bottom: 4mm; }
.tarife > div { border: 0.6pt solid var(--sage); padding: 3mm 3.5mm; }
.tarife .n { font-size: 7.5pt; font-weight: 700; letter-spacing: 1.5pt; text-transform: uppercase; color: var(--muted); }
.tarife .p { font-family: Playfair; font-size: 15pt; font-weight: 600; color: var(--forest); margin: .5mm 0 1mm; }
.tarife .p small { font-family: DMSans; font-size: 8pt; font-weight: 500; color: var(--muted); }
.tarife .d { font-size: 8pt; line-height: 1.35; }
.tarife .hl { background: var(--cream); border-color: var(--forest); }
.s2 .fussnote { font-size: 7.5pt; color: var(--muted); line-height: 1.45; }
.s2 .cta { margin-top: 5mm; display:flex; justify-content: space-between; align-items:center; background: var(--peach); padding: 3.5mm 5mm; }
.s2 .cta b { font-family: Playfair; font-size: 12.5pt; color: var(--forest); font-weight: 600; }
.s2 .cta span { font-size: 9pt; color: var(--forest); font-weight: 600; text-align: right; line-height: 1.4; }
"""


def seite2():
    chaos = [("zettel", "Textprogramm für Angebote"), ("tabelle", "Tabelle für Stunden"),
             ("handy", "Messenger für Baustellenfotos"), ("kalender", "Wandkalender für Termine"),
             ("beleg", "Schuhkarton für Belege"), ("auto", "Zettel für Fahrten"),
             ("mail", "E-Mails überall verteilt"), ("ordner", "Ordner für Verträge")]
    hw = [
        ("kamera", "Baustellenfotos direkt zum Auftrag",
         "Foto mit dem Handy machen, Notiz dazu – fertig. Alles liegt beim Auftrag und beim Kunden, statt im Fotoalbum zu verschwinden.", "Business und Premium"),
        ("chat", "Eigener Chat für jeden Auftrag",
         "Absprachen, Fragen und Fotos bleiben beim Auftrag. Kein Suchen mehr in privaten Gruppen-Chats.", "Business und Premium"),
        ("kalender", "Aufträge verteilen – direkt im Kalender",
         "Sie ordnen den Auftrag einem Mitarbeiter zu. Er sieht ihn sofort in seinem Planer, mit Adresse, Route, Beschreibung und Fotos.", "Business und Premium"),
    ]
    raster = [("angebot", "Angebote und Rechnungen", "¹"), ("erechnung", "E-Rechnung (XRechnung)", ""),
              ("beleg", "Belege per Handy fotografieren", ""), ("uhr", "Zeiterfassung und Stundenzettel", "²"),
              ("auto", "Fahrten und Verpflegung", ""), ("stift", "Kundenverträge mit Unterschrift am Handy", "²"),
              ("tabelle", "Bankimport und DATEV-Export", "²"), ("hand", "Büroaufgaben an Fokuszeit abgeben", "")]
    return f"""
<section class="seite">
  <div class="abs s2">
    <div class="eyebrow">FokusOffice für Handwerksbetriebe</div>
    <h2>Alles in einem Programm –<br>statt vieler verschiedener</h2>

    <div class="vergleich">
      <div class="vorher"><div class="k">Bisher</div><div class="chaos">
        {''.join(f'<div>{I[i]}{t}</div>' for i, t in chaos)}
      </div></div>
      <div class="pfeil">→</div>
      <div class="nachher"><div class="k">Mit FokusOffice</div>
        <div class="gross">Ein Programm. Ein Login.<br>Alles am Auftrag.</div>
        <div class="klein">Am PC im Büro, auf dem Tablet und auf dem Handy auf der Baustelle.</div>
      </div>
    </div>

    <div class="hw-titel">Gemacht für den Alltag im Handwerk</div>
    <div class="hw">
      {''.join(f'<div><div class="ic">{I[i]}</div><b>{t}</b><p>{d}</p>' + (f'<span class="tarif">{x}</span>' if x else '') + '</div>' for i, t, d, x in hw)}
    </div>

    <div class="raster-titel">Außerdem drin</div>
    <div class="raster">
      {''.join(f'<div><span class="ic">{I[i]}</span><span>{t}<sup>{s}</sup></span></div>' for i, t, s in raster)}
    </div>

    <div class="tarife">
      <div><div class="n">Basis</div><div class="p">9,99 € <small>/ Monat</small></div><div class="d">1 Zugang für den Inhaber</div></div>
      <div class="hl"><div class="n">Business</div><div class="p">16,99 € <small>/ Monat</small></div><div class="d">Bis 3 Benutzer, mit Angeboten und Team-Funktionen</div></div>
      <div><div class="n">Premium</div><div class="p">29,99 € <small>/ Monat</small></div><div class="d">Unbegrenzt viele Benutzer, inkl. 15 Min. Büroassistenz im Monat</div></div>
    </div>
    <div class="fussnote">Alle Preise: keine USt. gem. § 19 UStG. Im Jahresabo 2 Monate geschenkt. 14 Tage kostenlos testen, alle Funktionen inklusive – der Test endet automatisch.<br>
    ¹ Angebote ab Business &nbsp;·&nbsp; ² Business und Premium &nbsp;·&nbsp; Für Handwerksbetriebe mit Team empfehle ich Business.</div>

    <div class="cta"><b>Lassen Sie uns einen Termin ausmachen.</b><span>Lara Kohls · 0176 20558600<br>kontakt@fokuszeit-business.de</span></div>
  </div>
</section>"""
