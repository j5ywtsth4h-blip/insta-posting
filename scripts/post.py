"""Veröffentlicht fällige Instagram-Beiträge aus dem Ordner posts/.

Dateinamen-Schema (deutsche Zeit, Europe/Berlin):
    posts/2026-11-03_18-00.jpg   -> Bild (jpg, png, heic, webp)
    posts/2026-11-03_18-00.mp4   -> oder Video als Reel (mp4, mov)
    posts/2026-11-03_18-00.txt   -> Caption (optional)

Aufruf:
    python scripts/post.py test     -> prüft nur die Verbindung, postet nichts
    python scripts/post.py post     -> veröffentlicht alle fälligen Beiträge
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://graph.instagram.com/v26.0"
TZ = ZoneInfo("Europe/Berlin")
ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
BEREIT = ROOT / "posts" / "_bereit"
GEPOSTET = ROOT / "gepostet"
FEHLER = ROOT / "fehler"

BILD = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
VIDEO = {".mp4", ".mov"}
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})$")


# ---------------------------------------------------------------- API-Helfer

def token() -> str:
    t = os.environ.get("IG_TOKEN", "").strip()
    if not t:
        sys.exit("FEHLER: Secret IG_TOKEN fehlt (Settings -> Secrets and variables -> Actions).")
    return t


def api(method: str, path: str, **params):
    params["access_token"] = token()
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body
        raise RuntimeError(f"Instagram-API meldet: {msg}") from None


def ich() -> dict:
    return api("GET", "me", fields="user_id,username")


# ---------------------------------------------------------------- Git-Helfer

def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def push(nachricht: str):
    git("add", "-A")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    git("commit", "-m", nachricht)
    for _ in range(3):
        try:
            git("pull", "--rebase", "origin", "main")
            git("push", "origin", "HEAD:main")
            return
        except subprocess.CalledProcessError:
            time.sleep(5)
    raise RuntimeError("Konnte Änderungen nicht zu GitHub hochladen.")


def raw_url(datei: Path) -> str:
    repo = os.environ["GITHUB_REPOSITORY"]
    rel = urllib.parse.quote(datei.relative_to(ROOT).as_posix())
    return f"https://raw.githubusercontent.com/{repo}/main/{rel}"


# ---------------------------------------------------------------- Bilder

def bild_vorbereiten(quelle: Path) -> Path:
    """Liefert ein Instagram-taugliches JPEG (Format, Größe, Seitenverhältnis)."""
    from PIL import Image, ImageOps
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    img = Image.open(quelle)
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    ratio = w / h
    # Instagram erlaubt 4:5 (0.8) bis 1.91:1 – sonst mittig zuschneiden wie die App
    if ratio < 0.8:
        neu_h = int(w / 0.8)
        oben = (h - neu_h) // 2
        img = img.crop((0, oben, w, oben + neu_h))
    elif ratio > 1.91:
        neu_w = int(h * 1.91)
        links = (w - neu_w) // 2
        img = img.crop((links, 0, links + neu_w, h))
    if img.width > 1440:
        img = img.resize((1440, round(img.height * 1440 / img.width)), Image.LANCZOS)

    ist_ok = (
        quelle.suffix.lower() in {".jpg", ".jpeg"}
        and img.size == Image.open(quelle).size
        and quelle.stat().st_size < 8_000_000
    )
    if ist_ok:
        return quelle

    BEREIT.mkdir(parents=True, exist_ok=True)
    ziel = BEREIT / f"{quelle.stem}.jpg"
    img.save(ziel, "JPEG", quality=90)
    return ziel


# ---------------------------------------------------------------- Posten

def warten_bis_fertig(container: str, max_sekunden: int = 600):
    ende = time.time() + max_sekunden
    while time.time() < ende:
        status = api("GET", container, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram konnte die Datei nicht verarbeiten (Status {status}).")
        time.sleep(10)
    raise RuntimeError("Instagram hat zu lange für die Verarbeitung gebraucht.")


def faellige_posts():
    jetzt = datetime.now(TZ)
    gefunden = []
    for f in sorted(POSTS.glob("*")):
        endung = f.suffix.lower()
        if not f.is_file() or endung not in BILD | VIDEO:
            continue
        m = NAME.match(f.stem)
        if not m:
            print(f"Übersprungen (Dateiname passt nicht zum Schema JJJJ-MM-TT_SS-MM): {f.name}")
            continue
        zeit = datetime.strptime(f"{m[1]} {m[2]}:{m[3]}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if zeit <= jetzt:
            gefunden.append(f)
    return gefunden


def veroeffentlichen(user_id: str, medien: Path):
    caption_datei = medien.with_suffix(".txt")
    caption = caption_datei.read_text(encoding="utf-8").strip() if caption_datei.exists() else ""

    if medien.suffix.lower() in VIDEO:
        url = raw_url(medien)
        params = {"media_type": "REELS", "video_url": url}
    else:
        datei = bild_vorbereiten(medien)
        if datei != medien:
            push(f"Bild für {medien.stem} vorbereitet")
            time.sleep(15)  # GitHub kurz Zeit geben, die Datei auszuliefern
        url = raw_url(datei)
        params = {"image_url": url}
    if caption:
        params["caption"] = caption

    print(f"Lade hoch: {medien.name}")
    container = api("POST", f"{user_id}/media", **params)["id"]
    warten_bis_fertig(container)
    ergebnis = api("POST", f"{user_id}/media_publish", creation_id=container)
    print(f"Veröffentlicht: {medien.name} (Instagram-ID {ergebnis.get('id')})")
    return caption_datei


def verschieben(medien: Path, caption: Path, ziel: Path, log: str = ""):
    ziel.mkdir(exist_ok=True)
    shutil.move(str(medien), ziel / medien.name)
    if caption.exists():
        shutil.move(str(caption), ziel / caption.name)
    vorbereitet = BEREIT / f"{medien.stem}.jpg"
    if vorbereitet.exists():
        vorbereitet.unlink()
    if log:
        (ziel / f"{medien.stem}_FEHLER.txt").write_text(log, encoding="utf-8")


def main():
    modus = sys.argv[1] if len(sys.argv) > 1 else "post"
    profil = ich()
    user_id = profil["user_id"]

    if modus == "test":
        limit = api("GET", f"{user_id}/content_publishing_limit", fields="quota_usage,config")
        print(f"✅ Verbindung klappt! Verbunden mit @{profil.get('username')}")
        print(f"Posting-Kontingent: {json.dumps(limit.get('data', limit), ensure_ascii=False)}")
        return

    posts = faellige_posts()
    if not posts:
        print("Keine fälligen Beiträge.")
        return

    fehlgeschlagen = []
    for medien in posts:
        caption = medien.with_suffix(".txt")
        try:
            veroeffentlichen(user_id, medien)
            verschieben(medien, caption, GEPOSTET)
            push(f"Gepostet: {medien.stem}")
        except Exception as e:
            print(f"❌ {medien.name}: {e}")
            verschieben(medien, caption, FEHLER, log=str(e))
            push(f"Fehler bei {medien.stem}")
            fehlgeschlagen.append(medien.name)

    if fehlgeschlagen:
        sys.exit(f"Fehlgeschlagen: {', '.join(fehlgeschlagen)} – Details im Ordner 'fehler'.")


if __name__ == "__main__":
    main()
