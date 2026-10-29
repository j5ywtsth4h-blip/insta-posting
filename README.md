# Insta-Posting

Plant Instagram-Beiträge und veröffentlicht sie automatisch zur richtigen Zeit.

## So planst du einen Beitrag

1. Öffne den Ordner **`posts`** und tippe auf **„Add file → Upload files“**.
2. Lade ein Bild (oder ein Video für ein Reel) hoch. Der **Dateiname ist die Posting-Zeit** (deutsche Zeit):

   `2026-11-03_18-00.jpg` → wird am 3. November 2026 um 18:00 Uhr gepostet

3. Optional die Caption als Textdatei mit demselben Namen:

   `2026-11-03_18-00.txt`

   Tipp: Statt eine Datei hochzuladen, kannst du auch **„Add file → Create new file“** wählen, den Namen eintippen und die Caption direkt hineinschreiben.

4. Auf **„Commit changes“** tippen. Fertig.

## Storys und Reels

- **Reel:** einfach ein Video (mp4 oder mov) statt eines Bildes hochladen, z. B. `2026-11-03_19-00.mp4`. Die Caption kommt wie gewohnt in `2026-11-03_19-00.txt`. Das Reel erscheint auch im Feed.
- **Story:** `_story` an den Namen hängen, z. B. `2026-11-05_08-00_story.jpg` (Bild oder Video, am besten im Hochformat 9:16). Storys haben keine Caption.
- **Mehrere Storys zur selben Zeit:** `..._story.jpg`, `..._story-2.jpg`, `..._story-3.jpg`
- Musik, Umfragen und Link-Sticker kann Instagram über diesen Weg leider nicht hinzufügen.
- **Selbst posten:** Alles, was Musik oder Sticker bekommen soll, liegt im Ordner **`manuell`**. Dieser Ordner wird nicht automatisch gepostet. Was wann dazukommt, steht in `manuell/ANLEITUNG.md`.

## Was dann passiert

- GitHub schaut **jede Stunde** nach (meist kurz nach der vollen Stunde, manchmal etwas später).
- Fällige Beiträge werden gepostet und landen danach im Ordner **`gepostet`**.
- Klappt etwas nicht, landet der Beitrag im Ordner **`fehler`**, zusammen mit einer Datei, die den Grund erklärt. Du bekommst außerdem eine E-Mail von GitHub.

## Facebook

Ist unter *Settings → Secrets and variables → Actions* das Secret **`FB_PAGE_TOKEN`** hinterlegt (Schlüssel des Systemnutzers „Fokuszeit Bot“; `FB_PAGE_ID` ist optional), erscheinen alle Feed-Beiträge (Bilder) mit derselben Caption zusätzlich auf der Facebook-Seite. Storys und Reels bleiben nur auf Instagram. Ob es klappt, zeigt `verbindung-testen`.

## LinkedIn

Beiträge für Laras persönliches LinkedIn-Profil liegen in **`linkedin/geplant`**, gleiches Namensschema wie bei Instagram:

- `2026-11-03_08-00.md`: der Beitragstext. Optional ganz oben `TITEL: …` (Titel eines PDF-Dokuments) und unten nach einer Zeile `---KOMMENTAR---` der erste Kommentar, z. B. mit Link.
- `2026-11-03_08-00.jpg` (oder `.png`): Bild, **oder** `2026-11-03_08-00.pdf`: Dokument/Karussell.

Nach dem Posten landen die Dateien in `linkedin/gepostet`, bei Problemen in `linkedin/fehler`. Dafür muss das Secret **`LINKEDIN_TOKEN`** hinterlegt sein. Der LinkedIn-Schlüssel läuft nach 60 Tagen ab und muss dann neu erzeugt werden.

## Gut zu wissen

- **Bilder:** jpg, png, heic oder webp. Zu hohe Bilder (z. B. Handy-Hochformat 9:16) werden automatisch mittig auf 4:5 zugeschnitten, so wie es auch die Instagram-App macht.
- **Reels:** mp4 oder mov.
- **Sofort testen:** Reiter **Actions → „Instagram posten“ → „Run workflow“**.
  - `verbindung-testen` prüft nur, ob alles verbunden ist (postet nichts).
  - `geplante-pruefen` lässt Instagram alle geplanten Dateien vorab prüfen (postet nichts).
  - `faellige-jetzt-posten` postet alle fälligen Beiträge sofort.
- **Zugriffsschlüssel:** läuft nach ca. 60 Tagen ab. Dann im Meta-Entwicklerportal neu generieren und unter *Settings → Secrets and variables → Actions* bei `IG_TOKEN` ersetzen.
