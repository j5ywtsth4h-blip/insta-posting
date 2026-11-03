# Empfänger für den FokusOffice-Werbebrief.
# Stand 3.11.2026: Laras Liste (von ChatGPT) online gegengeprüft + neue Betriebe aus Branchenverzeichnissen
# (Gelbe Seiten, Das Örtliche, Elektro-Innung Kassel, sellwerk, trustlocal).
# status: "ok" = Adresse in Verzeichnissen gefunden -> FokusOffice_Brief_alle.pdf
#         "pruefen" = Firma existiert, Adresse unsicher -> FokusOffice_Brief_pruefen.pdf (erst nach Laras Prüfung)
# Nicht gefunden und entfernt: Eichert Elektrotechnik, Messdienst René Kasprowicz, R. Meier Heizung-Sanitär.
# anrede: leer = "Guten Tag,"
BETRIEBE = [
    # --- Laras Liste, bestätigt
    {"zeilen": ["JK Elektrotechnik", "Holländische Str. 35", "34379 Calden"], "anrede": "", "status": "ok"},
    {"zeilen": ["W. Pötter Heizung Sanitär", "Inh. Hendrik Pötter", "An der Kirche 4", "34369 Hofgeismar"], "anrede": "Guten Tag Hendrik Pötter,", "status": "ok"},
    {"zeilen": ["Elektro Ewers GmbH & Co. KG", "Neue Str. 6-8", "34369 Hofgeismar"], "anrede": "", "status": "ok"},
    {"zeilen": ["LeNeu Elektrotechnik", "Am Schindeberge 8", "34393 Grebenstein-Schachten"], "anrede": "", "status": "ok"},
    {"zeilen": ["Thomas Ewers Maler- und Lackierer", "Meißner Str. 12", "34393 Grebenstein-Burguffeln"], "anrede": "Guten Tag Thomas Ewers,", "status": "ok"},
    {"zeilen": ["Malerbetrieb Groppe", "Harleshäuser Str. 8", "34130 Kassel"], "anrede": "", "status": "ok"},
    {"zeilen": ["Heizung & Bäder Loth", "Erhard Loth & Sohn GmbH", "Heckenweg 2a", "34246 Vellmar"], "anrede": "", "status": "ok"},
    # --- neu recherchiert (3.11.)
    {"zeilen": ["Elektro Franke", "Inh. Peter Franke", "Leibnizweg 9", "34379 Calden"], "anrede": "Guten Tag Peter Franke,", "status": "ok"},
    {"zeilen": ["Burmann Haustechnik", "Flugplatzstraße 39", "34379 Calden"], "anrede": "", "status": "ok"},
    {"zeilen": ["Elektro-Wegner UG (haftungsbeschränkt)", "Gustav-Heinemann-Str. 3", "34369 Hofgeismar"], "anrede": "", "status": "ok"},
    {"zeilen": ["Klenke Haustechnik GmbH", "Am Hopfenberg 18 A", "34246 Vellmar"], "anrede": "", "status": "ok"},
    {"zeilen": ["Tim Wagner SHK", "Holländische Str. 177", "34246 Vellmar"], "anrede": "Guten Tag Tim Wagner,", "status": "ok"},
    {"zeilen": ["Bänfer Heizung & Sanitär", "An der Steinbreite 9", "34233 Fuldatal"], "anrede": "", "status": "ok"},
    {"zeilen": ["Lohn Haustechnik", "Hinter der Brandstätte 10", "34233 Fuldatal"], "anrede": "", "status": "ok"},
    {"zeilen": ["Dachdeckerei Kersting", "Inh. Erdal Sen e.K.", "Hofgeismarer Str. 19", "34393 Grebenstein"], "anrede": "Guten Tag Erdal Sen,", "status": "ok"},
    {"zeilen": ["Bönning Dachdeckerei", "Carl-Friedrich-Benz-Str. 1", "34369 Hofgeismar"], "anrede": "", "status": "ok"},
    {"zeilen": ["Becker Holz- und Dachbau GmbH", "Hinter der Eisenbahn 1a", "34376 Immenhausen"], "anrede": "", "status": "ok"},
    {"zeilen": ["Tischlerei Frank Baumann", "Carl-Friedrich-Benz-Str. 4", "34369 Hofgeismar"], "anrede": "Guten Tag Frank Baumann,", "status": "ok"},
    # --- Firma existiert, Adresse bitte prüfen
    {"zeilen": ["AR Haustechnik GmbH", "Über dem Maibach 7", "34393 Grebenstein"], "anrede": "", "status": "pruefen"},
    {"zeilen": ["M. Lang – Montage & Service", "Hegelweg 31", "34379 Calden"], "anrede": "", "status": "pruefen"},
    {"zeilen": ["Haustechnik Radke GmbH", "Bremer Str. 6", "34393 Grebenstein"], "anrede": "", "status": "pruefen"},
    {"zeilen": ["CT-Electronic GmbH & Co. KG", "Frommershäuser Str. 91", "34246 Vellmar"], "anrede": "", "status": "pruefen"},
    {"zeilen": ["Elektrotechnik Dornemann", "Buchenstraße 6", "34314 Espenau"], "anrede": "", "status": "pruefen"},
]
