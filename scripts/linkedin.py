"""Veröffentlicht fällige LinkedIn-Beiträge aus linkedin/geplant/ auf Laras persönlichem Profil.

Dateinamen-Schema (deutsche Zeit, Europe/Berlin):
    linkedin/geplant/2026-11-03_08-00.md    -> Beitragstext (Pflicht)
    linkedin/geplant/2026-11-03_08-00.jpg   -> Bild (jpg/png, optional)
    linkedin/geplant/2026-11-03_08-00.pdf   -> oder Dokument/Karussell (optional)

Aufbau der .md-Datei:
    TITEL: Titel des Dokuments        (nur bei PDF, erste Zeile, optional)
    Beitragstext …
    ---KOMMENTAR---
    Erster Kommentar, z. B. mit Link   (optional)

Aufruf:
    python scripts/linkedin.py test   -> prüft nur die Verbindung, postet nichts
    python scripts/linkedin.py post   -> veröffentlicht alle fälligen Beiträge
"""

import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import post  # noqa: E402  (Git-Helfer, Zeitzone)

ROOT = post.ROOT
LI = ROOT / "linkedin"
GEPLANT = LI / "geplant"
GEPOSTET = LI / "gepostet"
FEHLER = LI / "fehler"
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})$")
MEDIEN = {".jpg": "images", ".jpeg": "images", ".png": "images", ".pdf": "documents"}

_version = {}


def token() -> str:
    t = os.environ.get("LINKEDIN_TOKEN", "").strip()
    if not t:
        sys.exit("FEHLER: Secret LINKEDIN_TOKEN fehlt.")
    return t


def anfrage(method: str, url: str, daten=None, roh: bytes | None = None, rest: bool = True):
    kopf = {"Authorization": f"Bearer {token()}"}
    if rest:
        kopf["X-Restli-Protocol-Version"] = "2.0.0"
        kopf["LinkedIn-Version"] = _version.get("v", "")
    if daten is not None:
        roh = json.dumps(daten, ensure_ascii=False).encode()
        kopf["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=roh, method=method, headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            inhalt = r.read()
            return (json.loads(inhalt) if inhalt else {}), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"LinkedIn meldet ({e.code}): {body[:500]}") from None


def rest(method: str, pfad: str, daten=None):
    """Aufruf der versionierten REST-API. Sucht beim ersten Mal eine gültige API-Version."""
    if "v" not in _version:
        jetzt = datetime.now(post.TZ)
        kandidaten = []
        j, m = jetzt.year, jetzt.month
        for _ in range(14):
            kandidaten.append(f"{j}{m:02d}")
            j, m = (j, m - 1) if m > 1 else (j - 1, 12)
        letzter = None
        for v in kandidaten:
            _version["v"] = v
            try:
                return anfrage(method, f"https://api.linkedin.com{pfad}", daten)
            except RuntimeError as e:
                if "VERSION" in str(e).upper() and ("426" in str(e) or "400" in str(e)):
                    letzter = e
                    continue
                raise
        del _version["v"]
        raise letzter or RuntimeError("Keine gültige LinkedIn-API-Version gefunden.")
    return anfrage(method, f"https://api.linkedin.com{pfad}", daten)


def ich() -> dict:
    daten, _ = anfrage("GET", "https://api.linkedin.com/v2/userinfo", rest=False)
    return daten


# ---------------------------------------------------------------- Text

RESERVIERT = re.compile(r"([\\|{}@\[\]()<>#*_~])")
HASHTAG = re.compile(r"#([\wÄÖÜäöüß]+)")


def little_text(text: str) -> str:
    """LinkedIn erwartet „little text“: Sonderzeichen escapen, Hashtags als Vorlage."""
    teile, pos = [], 0
    for m in HASHTAG.finditer(text):
        teile.append(RESERVIERT.sub(r"\\\1", text[pos:m.start()]))
        teile.append("{hashtag|\\#|" + m.group(1) + "}")
        pos = m.end()
    teile.append(RESERVIERT.sub(r"\\\1", text[pos:]))
    return "".join(teile)


def lesen(md: Path) -> tuple[str, str, str]:
    inhalt = md.read_text(encoding="utf-8").strip()
    titel = ""
    if inhalt.startswith("TITEL:"):
        erste, _, inhalt = inhalt.partition("\n")
        titel = erste[len("TITEL:"):].strip()
    text, _, kommentar = inhalt.partition("---KOMMENTAR---")
    return titel, text.strip(), kommentar.strip()


# ---------------------------------------------------------------- Posten

def hochladen(person: str, datei: Path) -> str:
    art = MEDIEN[datei.suffix.lower()]
    antwort, _ = rest("POST", f"/rest/{art}?action=initializeUpload",
                      {"initializeUploadRequest": {"owner": person}})
    wert = antwort["value"]
    anfrage("PUT", wert["uploadUrl"], roh=datei.read_bytes(), rest=False)
    return wert["image"] if art == "images" else wert["document"]


def veroeffentlichen(person: str, md: Path) -> str:
    titel, text, kommentar = lesen(md)
    beitrag = {
        "author": person,
        "commentary": little_text(text),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    medien = next((md.with_suffix(e) for e in MEDIEN if md.with_suffix(e).exists()), None)
    if medien:
        print(f"Lade hoch: {medien.name}")
        media = {"id": hochladen(person, medien)}
        if medien.suffix.lower() == ".pdf":
            media["title"] = titel or text.splitlines()[0][:100]
        beitrag["content"] = {"media": media}
    _, kopf = rest("POST", "/rest/posts", beitrag)
    urn = kopf.get("x-restli-id") or kopf.get("X-RestLi-Id") or kopf.get("x-linkedin-id", "")
    print(f"Auf LinkedIn veröffentlicht: {md.stem} ({urn})")
    if kommentar and urn:
        try:
            rest("POST", f"/rest/socialActions/{urllib.parse.quote(urn, safe='')}/comments",
                 {"actor": person, "object": urn, "message": {"text": kommentar}})
            print("Erster Kommentar gesetzt.")
        except RuntimeError as e:  # Beitrag ist online, deshalb nur melden
            print(f"⚠️ Kommentar konnte nicht gesetzt werden: {e}")
    return urn


def faellige():
    jetzt = datetime.now(post.TZ)
    for md in sorted(GEPLANT.glob("*.md")):
        m = NAME.match(md.stem)
        if not m:
            print(f"Übersprungen (Dateiname passt nicht): {md.name}")
            continue
        zeit = datetime.strptime(f"{m[1]} {m[2]}:{m[3]}", "%Y-%m-%d %H:%M").replace(tzinfo=post.TZ)
        if zeit <= jetzt:
            yield md


def verschieben(md: Path, ziel: Path, log: str = ""):
    ziel.mkdir(parents=True, exist_ok=True)
    for f in GEPLANT.glob(md.stem + ".*"):
        shutil.move(str(f), ziel / f.name)
    if log:
        (ziel / f"{md.stem}_FEHLER.txt").write_text(log, encoding="utf-8")


def main():
    modus = sys.argv[1] if len(sys.argv) > 1 else "post"
    if not os.environ.get("LINKEDIN_TOKEN", "").strip():
        print("LinkedIn ist nicht eingerichtet (Secret LINKEDIN_TOKEN fehlt).")
        return
    profil = ich()
    person = f"urn:li:person:{profil['sub']}"

    if modus == "test":
        print(f"✅ LinkedIn klappt! Verbunden mit {profil.get('name')}")
        return

    posts = list(faellige()) if GEPLANT.exists() else []
    if not posts:
        print("Keine fälligen LinkedIn-Beiträge.")
        return
    fehlgeschlagen = []
    for md in posts:
        try:
            veroeffentlichen(person, md)
            verschieben(md, GEPOSTET)
            post.push(f"LinkedIn gepostet: {md.stem}")
        except Exception as e:
            print(f"❌ {md.name}: {e}")
            verschieben(md, FEHLER, log=str(e))
            post.push(f"LinkedIn-Fehler bei {md.stem}")
            fehlgeschlagen.append(md.name)
    if fehlgeschlagen:
        sys.exit(f"LinkedIn fehlgeschlagen: {', '.join(fehlgeschlagen)} – Details in linkedin/fehler.")


if __name__ == "__main__":
    main()
