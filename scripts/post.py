"""Veröffentlicht fällige Instagram-Beiträge aus dem Ordner posts/.

Dateinamen-Schema (deutsche Zeit, Europe/Berlin):
    posts/2026-11-03_18-00.jpg   -> Bild (jpg, png, heic, webp)
    posts/2026-11-03_18-00.mp4   -> oder Video als Reel (mp4, mov)
    posts/2026-11-03_18-00.txt   -> Caption (optional)
    posts/2026-11-03_09-00_story.jpg   -> Story (Bild oder Video, ohne Caption)
    posts/2026-11-03_09-00_story-2.jpg -> weitere Story zur selben Zeit
    posts/2026-11-03_18-00/01.jpg …    -> Karussell: Ordner mit 2 bis 10 Bildern (Reihenfolge nach Dateiname),
                                          Caption daneben als posts/2026-11-03_18-00.txt

Aufruf:
    python scripts/post.py test     -> prüft nur die Verbindung, postet nichts
    python scripts/post.py pruefen  -> lässt Instagram alle geplanten Dateien prüfen, postet nichts
    python scripts/post.py post     -> veröffentlicht alle fälligen Beiträge

Facebook (optional): Sind die Secrets FB_PAGE_ID und FB_PAGE_TOKEN hinterlegt, erscheinen
Feed-Beiträge (Bilder) zusätzlich auf der Facebook-Seite. Storys und Reels nur auf Instagram.
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
FB_API = "https://graph.facebook.com/v26.0"
TZ = ZoneInfo("Europe/Berlin")
ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
BEREIT = ROOT / "posts" / "_bereit"
GEPOSTET = ROOT / "gepostet"
FEHLER = ROOT / "fehler"

BILD = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
VIDEO = {".mp4", ".mov"}
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})(_story(?:-\d+)?)?$")


# ---------------------------------------------------------------- API-Helfer

def token() -> str:
    t = os.environ.get("IG_TOKEN", "").strip()
    if not t:
        sys.exit("FEHLER: Secret IG_TOKEN fehlt (Settings -> Secrets and variables -> Actions).")
    return t


def api(method: str, path: str, basis: str = API, zugang: str = "", **params):
    params["access_token"] = zugang or token()
    data = urllib.parse.urlencode(params).encode()
    url = f"{basis}/{path}"
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
            fehler = json.loads(body)["error"]
            msg = fehler["message"]
            details = " ".join(t for t in (fehler.get("error_user_title"), fehler.get("error_user_msg")) if t)
            if details:
                msg = f"{msg} – {details}"
            if fehler.get("error_subcode"):
                msg += f" (Code {fehler.get('code')}/{fehler['error_subcode']})"
        except Exception:
            msg = body
        dienst = "Facebook" if basis == FB_API else "Instagram"
        raise RuntimeError(f"{dienst}-API meldet: {msg}") from None


def ich() -> dict:
    return api("GET", "me", fields="user_id,username")


_fb = {}


def facebook() -> tuple[str, str] | None:
    """Liefert (Seiten-ID, Seiten-Schlüssel) oder None, wenn Facebook nicht eingerichtet ist.

    FB_PAGE_TOKEN darf ein Seiten- oder ein Systemnutzer-Schlüssel sein. Fehlt FB_PAGE_ID,
    wird die Seite über den Schlüssel gesucht (der Systemnutzer hat genau eine Seite)."""
    if "seite" in _fb:
        return _fb["seite"]
    seite = os.environ.get("FB_PAGE_ID", "").strip()
    zugang = os.environ.get("FB_PAGE_TOKEN", "").strip()
    _fb["seite"] = None
    if not zugang:
        return None
    seiten = api("GET", "me/accounts", basis=FB_API, zugang=zugang, fields="id,name,access_token").get("data", [])
    if seite:
        seiten = [s for s in seiten if s.get("id") == seite] or [{"id": seite, "access_token": zugang}]
    if len(seiten) != 1:
        namen = ", ".join(f"{s.get('name')} ({s.get('id')})" for s in seiten) or "keine"
        raise RuntimeError(f"Facebook-Seite nicht eindeutig gefunden. Gefunden: {namen}. Bitte FB_PAGE_ID setzen.")
    _fb["seite"] = (seiten[0]["id"], seiten[0].get("access_token") or zugang)
    return _fb["seite"]


def fb_api(method: str, path: str, **params):
    seite, zugang = facebook()
    return api(method, path.format(seite=seite), basis=FB_API, zugang=zugang, **params)


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

def karussell_bilder(ordner: Path) -> list[Path]:
    return sorted(f for f in ordner.iterdir() if f.is_file() and f.suffix.lower() in BILD)


def ist_story(datei: Path) -> bool:
    m = NAME.match(datei.stem)
    return bool(m and m[4])


def bild_vorbereiten(quelle: Path, story: bool = False) -> Path:
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
    # Feed: Instagram erlaubt 4:5 (0.8) bis 1.91:1 – sonst mittig zuschneiden wie die App
    # Story: bleibt im Hochformat (ideal 9:16)
    if story:
        pass
    elif ratio < 0.8:
        neu_h = int(w / 0.8)
        oben = (h - neu_h) // 2
        img = img.crop((0, oben, w, oben + neu_h))
    elif ratio > 1.91:
        neu_w = int(h * 1.91)
        links = (w - neu_w) // 2
        img = img.crop((links, 0, links + neu_w, h))
    max_breite = 1080 if story else 1440
    if img.width > max_breite:
        img = img.resize((max_breite, round(img.height * max_breite / img.width)), Image.LANCZOS)

    ist_ok = (
        quelle.suffix.lower() in {".jpg", ".jpeg"}
        and img.size == Image.open(quelle).size
        and quelle.stat().st_size < 8_000_000
    )
    if ist_ok:
        return quelle

    BEREIT.mkdir(parents=True, exist_ok=True)
    name = quelle.stem if quelle.parent == POSTS else f"{quelle.parent.name}_{quelle.stem}"
    ziel = BEREIT / f"{name}.jpg"
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


def faellige_posts(alle: bool = False):
    jetzt = datetime.now(TZ)
    gefunden = []
    for f in sorted(POSTS.glob("*")):
        endung = f.suffix.lower()
        if f.is_dir():
            if f.name.startswith("_") or not karussell_bilder(f):
                continue
        elif endung not in BILD | VIDEO:
            continue
        m = NAME.match(f.stem)
        if not m:
            print(f"Übersprungen (Dateiname passt nicht zum Schema JJJJ-MM-TT_SS-MM): {f.name}")
            continue
        zeit = datetime.strptime(f"{m[1]} {m[2]}:{m[3]}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if alle or zeit <= jetzt:
            gefunden.append(f)
    return gefunden


def bild_url(medien: Path, story: bool = False) -> str:
    datei = bild_vorbereiten(medien, story)
    if datei != medien:
        push(f"Bild für {medien.stem} vorbereitet")
        time.sleep(15)  # GitHub kurz Zeit geben, die Datei auszuliefern
    return raw_url(datei)


def container_erstellen(user_id: str, medien: Path) -> str:
    story = ist_story(medien)
    caption_datei = medien.with_suffix(".txt")
    caption = caption_datei.read_text(encoding="utf-8").strip() if caption_datei.exists() else ""

    if medien.is_dir():
        bilder = karussell_bilder(medien)
        if not 2 <= len(bilder) <= 10:
            raise RuntimeError(f"Ein Karussell braucht 2 bis 10 Bilder, gefunden: {len(bilder)}.")
        print(f"Lade hoch: Karussell {medien.name} ({len(bilder)} Bilder)")
        kinder = []
        for b in bilder:
            kind = api("POST", f"{user_id}/media", image_url=bild_url(b), is_carousel_item="true")["id"]
            warten_bis_fertig(kind)
            kinder.append(kind)
        params = {"media_type": "CAROUSEL", "children": ",".join(kinder)}
        if caption:
            params["caption"] = caption
        container = api("POST", f"{user_id}/media", **params)["id"]
        warten_bis_fertig(container)
        return container

    if medien.suffix.lower() in VIDEO:
        url = raw_url(medien)
        params = {"media_type": "STORIES" if story else "REELS", "video_url": url}
        if not story:
            params["share_to_feed"] = "true"
    else:
        params = {"image_url": bild_url(medien, story)}
        if story:
            params["media_type"] = "STORIES"
    if caption and not story:
        params["caption"] = caption

    print(f"Lade hoch: {medien.name}")
    container = api("POST", f"{user_id}/media", **params)["id"]
    warten_bis_fertig(container)
    return container


def veroeffentlichen(user_id: str, medien: Path):
    container = container_erstellen(user_id, medien)
    ergebnis = api("POST", f"{user_id}/media_publish", creation_id=container)
    print(f"Veröffentlicht: {medien.name} (Instagram-ID {ergebnis.get('id')})")


WEBSITE = "https://www.fokuszeit-business.de"
FOKUSOFFICE = "https://www.fokuszeit-business.de/fokusoffice.html"
BIO = re.compile(r"Link in (?:meiner|der) Bio", re.IGNORECASE)


def facebook_text(caption: str) -> str:
    """Auf Facebook sind Links anklickbar: „Link in der Bio“ wird durch die echten Links ersetzt."""
    zeilen = []
    for zeile in caption.splitlines():
        if BIO.search(zeile):
            links = []
            if "fokusoffice" in zeile.lower() or ("büroassistenz" not in zeile.lower() and "fokusoffice" in caption.lower()):
                links.append(f"FokusOffice 14 Tage kostenlos testen: {FOKUSOFFICE}")
            if "büroassistenz" in zeile.lower() or not links:
                links.insert(0, f"Büroassistenz anfragen: {WEBSITE}")
            if zeile.lstrip().startswith("🔗"):
                zeile = "\n".join(f"🔗 {l}" for l in links)
            else:
                zeile = BIO.sub(" · ".join(links), zeile)
        zeilen.append(zeile)
    return "\n".join(zeilen)


def auf_facebook(medien: Path):
    """Feed-Bild zusätzlich auf der Facebook-Seite veröffentlichen."""
    if ist_story(medien) or medien.suffix.lower() in VIDEO:
        return
    caption_datei = medien.with_suffix(".txt")
    caption = caption_datei.read_text(encoding="utf-8").strip() if caption_datei.exists() else ""
    caption = facebook_text(caption)
    if medien.is_dir():  # Karussell: Bilder unveröffentlicht hochladen, dann als ein Beitrag
        fotos = [fb_api("POST", "{seite}/photos", url=raw_url(bild_vorbereiten(b)), published="false")["id"]
                 for b in karussell_bilder(medien)]
        params = {"attached_media": json.dumps([{"media_fbid": f} for f in fotos])}
        if caption:
            params["message"] = caption
        ergebnis = fb_api("POST", "{seite}/feed", **params)
        print(f"Auf Facebook veröffentlicht: Karussell {medien.name} (Facebook-ID {ergebnis.get('id')})")
        return
    params = {"url": raw_url(bild_vorbereiten(medien))}
    if caption:
        params["caption"] = caption
    ergebnis = fb_api("POST", "{seite}/photos", **params)
    print(f"Auf Facebook veröffentlicht: {medien.name} (Facebook-ID {ergebnis.get('post_id') or ergebnis.get('id')})")


def verschieben(medien: Path, caption: Path, ziel: Path, log: str = ""):
    ziel.mkdir(exist_ok=True)
    shutil.move(str(medien), ziel / medien.name)
    if caption.exists():
        shutil.move(str(caption), ziel / caption.name)
    for vorbereitet in [BEREIT / f"{medien.stem}.jpg", *BEREIT.glob(f"{medien.name}_*.jpg")]:
        if vorbereitet.exists():
            vorbereitet.unlink()
    if log:
        (ziel / f"{medien.stem}_FEHLER.txt").write_text(log, encoding="utf-8")


def main():
    modus = sys.argv[1] if len(sys.argv) > 1 else "post"
    if modus != "fb-loeschen":
        profil = ich()
        user_id = profil["user_id"]

    if modus == "test":
        limit = api("GET", f"{user_id}/content_publishing_limit", fields="quota_usage,config")
        print(f"✅ Verbindung klappt! Verbunden mit @{profil.get('username')}")
        print(f"Posting-Kontingent: {json.dumps(limit.get('data', limit), ensure_ascii=False)}")
        if facebook():
            seite = fb_api("GET", "{seite}", fields="name")
            print(f"✅ Facebook klappt auch! Verbunden mit der Seite „{seite.get('name')}“ (ID {seite.get('id')})")
        else:
            print("Facebook ist nicht eingerichtet (Secret FB_PAGE_TOKEN fehlt).")
        return

    if modus == "fb-loeschen":  # Instagram erlaubt kein Löschen über die Schnittstelle, Facebook schon
        beitrag = os.environ.get("FB_BEITRAG", "").strip()
        if not beitrag:
            sys.exit("Bitte die Facebook-ID des Beitrags angeben.")
        _, zugang = facebook()
        anfrage = urllib.request.Request(f"{FB_API}/{beitrag}?access_token={urllib.parse.quote(zugang)}", method="DELETE")
        try:
            urllib.request.urlopen(anfrage, timeout=60).read()
        except urllib.error.HTTPError as e:
            sys.exit(f"Facebook-API meldet: {e.read().decode(errors='replace')[:300]}")
        print(f"✅ Facebook-Beitrag {beitrag} gelöscht.")
        return

    if modus == "profil":
        info = api("GET", "me", fields="username,media_count,followers_count,biography")
        print(f"@{info.get('username')}: {info.get('media_count')} Beiträge, {info.get('followers_count')} Follower")
        print(f"Bio: {info.get('biography')}")
        medien = api("GET", f"{user_id}/media", fields="timestamp,media_type,caption,permalink", limit=25).get("data", [])
        for m in medien:
            text = (m.get("caption") or "").replace("\n", " ")
            print(f"- {m.get('timestamp', '')[:10]} {m.get('media_type')}: {text[:160]}")
        return

    if modus == "pruefen":
        probleme = []
        for medien in faellige_posts(alle=True):
            try:
                container_erstellen(user_id, medien)
                print(f"✅ {medien.name}: Instagram kann die Datei verarbeiten")
            except Exception as e:
                print(f"❌ {medien.name}: {e}")
                probleme.append(medien.name)
        if probleme:
            sys.exit(f"Probleme bei: {', '.join(probleme)}")
        print("Alles geprüft, nichts wurde gepostet.")
        return

    posts = faellige_posts()
    if not posts:
        print("Keine fälligen Beiträge.")
        return

    fehlgeschlagen = []
    fb_fehler = []
    for medien in posts:
        caption = medien.with_suffix(".txt")
        try:
            veroeffentlichen(user_id, medien)
            if os.environ.get("FB_PAGE_TOKEN", "").strip():
                try:
                    auf_facebook(medien)
                except Exception as e:  # Instagram ist schon online, deshalb nur melden
                    print(f"⚠️ Facebook {medien.name}: {e}")
                    fb_fehler.append(f"{medien.name}: {e}")
            verschieben(medien, caption, GEPOSTET)
            push(f"Gepostet: {medien.stem}")
        except Exception as e:
            print(f"❌ {medien.name}: {e}")
            verschieben(medien, caption, FEHLER, log=str(e))
            push(f"Fehler bei {medien.stem}")
            fehlgeschlagen.append(medien.name)

    if fehlgeschlagen:
        sys.exit(f"Fehlgeschlagen: {', '.join(fehlgeschlagen)} – Details im Ordner 'fehler'.")
    if fb_fehler:
        sys.exit("Auf Instagram gepostet, aber nicht auf Facebook:\n" + "\n".join(fb_fehler))


if __name__ == "__main__":
    main()
