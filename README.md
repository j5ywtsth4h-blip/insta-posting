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

## Was dann passiert

- GitHub schaut **jede Stunde** nach (meist kurz nach der vollen Stunde, manchmal etwas später).
- Fällige Beiträge werden gepostet und landen danach im Ordner **`gepostet`**.
- Klappt etwas nicht, landet der Beitrag im Ordner **`fehler`**, zusammen mit einer Datei, die den Grund erklärt. Du bekommst außerdem eine E-Mail von GitHub.

## Gut zu wissen

- **Bilder:** jpg, png, heic oder webp. Zu hohe Bilder (z. B. Handy-Hochformat 9:16) werden automatisch mittig auf 4:5 zugeschnitten, so wie es auch die Instagram-App macht.
- **Reels:** mp4 oder mov.
- **Sofort testen:** Reiter **Actions → „Instagram posten“ → „Run workflow“**.
  - `verbindung-testen` prüft nur, ob alles verbunden ist (postet nichts).
  - `faellige-jetzt-posten` postet alle fälligen Beiträge sofort.
- **Zugriffsschlüssel:** läuft nach ca. 60 Tagen ab. Dann im Meta-Entwicklerportal neu generieren und unter *Settings → Secrets and variables → Actions* bei `IG_TOKEN` ersetzen.
