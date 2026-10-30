"""Verwaltet Werbekampagnen auf Facebook und Instagram über die Meta Marketing API.

Jede Kampagne liegt als Ordner unter werbung/<name>/ mit einer kampagne.json und den
Anzeigen-Dateien. Angelegt wird immer pausiert. Gestartet wird nur mit ausdrücklicher Freigabe.

Aufruf:
    python scripts/werbung.py konten               -> zeigt Werbekonten und Seite
    python scripts/werbung.py vorbereiten <name>   -> legt die Kampagne pausiert an
    python scripts/werbung.py erneuern <name>      -> löscht die Anzeigen und legt sie laut kampagne.json neu an
    python scripts/werbung.py bericht <name>       -> Kennzahlen der Kampagne
    python scripts/werbung.py starten <name>       -> startet die Kampagne (Laufzeit ab jetzt)
    python scripts/werbung.py pausieren <name>     -> pausiert die Kampagne
"""

import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import post  # noqa: E402  (API-Helfer, Git-Helfer, raw_url)

ROOT = post.ROOT
WERBUNG = ROOT / "werbung"


# ---------------------------------------------------------------- Helfer

def zugang() -> str:
    t = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not t:
        sys.exit("FEHLER: Secret FB_PAGE_TOKEN fehlt (Schlüssel des Systemnutzers „Fokuszeit Bot“).")
    return t


def meta(method: str, path: str, **params):
    for k, v in params.items():
        if isinstance(v, (dict, list)):
            params[k] = json.dumps(v, ensure_ascii=False)
    return post.api(method, path, basis=post.FB_API, zugang=zugang(), **params)


def werbekonto() -> dict:
    konten = meta("GET", "me/adaccounts", fields="id,name,account_status,currency,timezone_name,"
                                                 "amount_spent,spend_cap,funding_source_details").get("data", [])
    gewuenscht = os.environ.get("AD_ACCOUNT_ID", "").strip()
    if gewuenscht:
        gewuenscht = gewuenscht if gewuenscht.startswith("act_") else f"act_{gewuenscht}"
        konten = [k for k in konten if k["id"] == gewuenscht]
    if len(konten) != 1:
        namen = ", ".join(f"{k.get('name')} ({k['id']})" for k in konten) or "keins"
        sys.exit("FEHLER: Werbekonto nicht eindeutig. Gefunden: " + namen + ".\n"
                 "Das Werbekonto muss dem Systemnutzer „Fokuszeit Bot“ zugewiesen sein "
                 "(Business Suite → Einstellungen → Systemnutzer → Assets zuweisen → Werbekonten).")
    return konten[0]


def seite() -> dict:
    seiten = meta("GET", "me/accounts", fields="id,name,instagram_business_account,connected_instagram_account").get("data", [])
    if len(seiten) != 1:
        sys.exit("FEHLER: Dem Systemnutzer muss genau eine Facebook-Seite zugewiesen sein.")
    return seiten[0]


def instagram(konto: str, s: dict, laut: bool = False) -> str:
    """ID des Instagram-Kontos für Anzeigen. Meta liefert sie je nach Verknüpfung an
    unterschiedlichen Stellen, deshalb werden alle Wege nacheinander probiert."""
    for feld in ("instagram_business_account", "connected_instagram_account"):
        if (s.get(feld) or {}).get("id"):
            return s[feld]["id"]
    for pfad in (f"{konto}/instagram_accounts", f"{konto}/connected_instagram_accounts",
                 f"{s['id']}/instagram_accounts", "me/instagram_accounts"):
        try:
            daten = meta("GET", pfad, fields="id,username").get("data", [])
        except RuntimeError as e:
            if laut:
                print(f"   ({pfad}: {str(e)[:160]})")
            continue
        if laut:
            print(f"   ({pfad}: {', '.join(d.get('username') or d['id'] for d in daten) or 'leer'})")
        if daten:
            return daten[0]["id"]
    return ""


def laden(name: str) -> tuple[Path, dict, dict]:
    ordner = WERBUNG / name
    plan = json.loads((ordner / "kampagne.json").read_text(encoding="utf-8"))
    status_datei = ordner / "status.json"
    status = json.loads(status_datei.read_text(encoding="utf-8")) if status_datei.exists() else {}
    return ordner, plan, status


def speichern(ordner: Path, status: dict, nachricht: str):
    (ordner / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    post.push(nachricht)


def euro(cent) -> str:
    return f"{int(cent) / 100:.2f} €".replace(".", ",")


# ---------------------------------------------------------------- Aktionen

def konten():
    k = werbekonto()
    s = seite()
    zustand = {1: "aktiv", 2: "deaktiviert", 3: "unbezahlte Rechnung", 7: "in Prüfung", 9: "Kulanzzeit"}
    print(f"✅ Werbekonto: {k.get('name')} ({k['id']}), Status: {zustand.get(k.get('account_status'), k.get('account_status'))}")
    print(f"   Währung {k.get('currency')}, Zeitzone {k.get('timezone_name')}, bisher ausgegeben {euro(k.get('amount_spent', 0))}")
    print(f"   Ausgabenlimit: {euro(k['spend_cap']) if k.get('spend_cap') not in (None, '0') else 'keins gesetzt'}")
    zahlung = (k.get("funding_source_details") or {}).get("display_string")
    print(f"   Zahlungsmethode: {zahlung or 'keine hinterlegt'}")
    print(f"✅ Seite: {s.get('name')} ({s['id']})")
    ig = instagram(k["id"], s, laut=True)
    print(f"   Instagram-Konto für Anzeigen: {ig or 'nicht verknüpft (Anzeigen erscheinen dann unter dem Seitennamen)'}")


def bild_hochladen(konto: str, datei: Path) -> str:
    daten = base64.b64encode(datei.read_bytes()).decode()
    antwort = meta("POST", f"{konto}/adimages", bytes=daten)
    return next(iter(antwort["images"].values()))["hash"]


def video_hochladen(konto: str, datei: Path) -> str:
    video_id = meta("POST", f"{konto}/advideos", file_url=post.raw_url(datei), name=datei.name)["id"]
    ende = time.time() + 900
    while time.time() < ende:
        status = meta("GET", video_id, fields="status").get("status", {})
        if status.get("video_status") == "ready":
            return video_id
        if status.get("video_status") == "error":
            raise RuntimeError(f"Meta konnte das Video {datei.name} nicht verarbeiten.")
        time.sleep(15)
    raise RuntimeError(f"Video {datei.name} wurde nicht rechtzeitig verarbeitet.")


def vorbereiten(name: str):
    ordner, plan, status = laden(name)
    k = werbekonto()
    konto = k["id"]
    s = seite()
    ig = instagram(konto, s)
    print(f"Instagram-Konto für Anzeigen: {ig or 'nicht verknüpft, Anzeigen laufen unter dem Seitennamen'}")
    status.setdefault("anzeigen", [])
    status.update({"werbekonto": konto, "seite": s["id"]})

    # Bereits Angelegtes wird übersprungen, so kann ein abgebrochener Lauf einfach wiederholt werden
    if not status.get("kampagne_id"):
        kampagne = meta("POST", f"{konto}/campaigns", name=plan["name"], objective=plan["ziel"],
                        status="PAUSED", special_ad_categories=[], is_adset_budget_sharing_enabled="false")
        status["kampagne_id"] = kampagne["id"]
        print(f"Kampagne angelegt (pausiert): {kampagne['id']}")
        speichern(ordner, status, f"Werbung {name}: Kampagne angelegt (pausiert)")

    g = plan["anzeigengruppe"]
    if not status.get("anzeigengruppe_id"):
        gruppe = meta("POST", f"{konto}/adsets", name=g["name"], campaign_id=status["kampagne_id"],
                      daily_budget=g["tagesbudget_cent"], billing_event="IMPRESSIONS",
                      optimization_goal=g["optimierung"], bid_strategy="LOWEST_COST_WITHOUT_CAP",
                      destination_type="WEBSITE", targeting=g["zielgruppe"], status="ACTIVE",
                      dsa_beneficiary=plan["dsa_beguenstigter"], dsa_payor=plan["dsa_zahler"])
        status["anzeigengruppe_id"] = gruppe["id"]
        print(f"Anzeigengruppe angelegt: {gruppe['id']} ({euro(g['tagesbudget_cent'])} pro Tag)")
        speichern(ordner, status, f"Werbung {name}: Anzeigengruppe angelegt")

    fertig = {a["name"] for a in status["anzeigen"]}
    for a in plan["anzeigen"]:
        if a["name"] in fertig:
            continue
        datei = ordner / a["datei"]
        cta = {"type": a.get("button", "LEARN_MORE"), "value": {"link": plan["link"]}}
        if datei.suffix.lower() == ".mp4":
            video_id = video_hochladen(konto, datei)
            vorschau = bild_hochladen(konto, ordner / a["vorschaubild"])
            spec = {"page_id": s["id"], "video_data": {
                "video_id": video_id, "image_hash": vorschau, "message": a["text"],
                "title": a["ueberschrift"], "call_to_action": cta}}
        else:
            spec = {"page_id": s["id"], "link_data": {
                "image_hash": bild_hochladen(konto, datei), "link": plan["link"], "message": a["text"],
                "name": a["ueberschrift"], "description": a.get("beschreibung", ""), "call_to_action": cta}}
        if ig:
            spec["instagram_user_id"] = ig
        try:
            creative = meta("POST", f"{konto}/adcreatives", name=a["name"], object_story_spec=spec)
        except RuntimeError:
            if not ig:
                raise
            spec.pop("instagram_user_id")  # Instagram-Konto nicht freigegeben: unter Seitennamen schalten
            creative = meta("POST", f"{konto}/adcreatives", name=a["name"], object_story_spec=spec)
        anzeige = meta("POST", f"{konto}/ads", name=a["name"], adset_id=status["anzeigengruppe_id"],
                       creative={"creative_id": creative["id"]}, status="ACTIVE")
        status["anzeigen"].append({"name": a["name"], "id": anzeige["id"]})
        print(f"Anzeige angelegt: {a['name']} ({anzeige['id']})")
        speichern(ordner, status, f"Werbung {name}: Anzeige {a['name']} angelegt")

    print(f"\n✅ Fertig. Die Kampagne „{plan['name']}“ ist komplett angelegt und PAUSIERT. Es entstehen keine Kosten.")


def erneuern(name: str):
    ordner, plan, status = laden(name)
    for a in status.get("anzeigen", []):
        try:
            meta("POST", a["id"], status="DELETED")
            print(f"Alte Anzeige gelöscht: {a['name']}")
        except RuntimeError as e:
            print(f"⚠️ {a['name']} ließ sich nicht löschen: {e}")
    status["anzeigen"] = []
    speichern(ordner, status, f"Werbung {name}: alte Anzeigen entfernt")
    vorbereiten(name)


def starten(name: str):
    ordner, plan, status = laden(name)
    if os.environ.get("BESTAETIGUNG", "").strip().lower() != "starten":
        sys.exit("Nicht gestartet: Zum Starten muss im Feld „bestaetigung“ das Wort starten stehen.")
    if not status.get("kampagne_id"):
        sys.exit("Die Kampagne ist noch nicht angelegt. Erst „vorbereiten“ ausführen.")
    tage = plan["anzeigengruppe"]["laufzeit_tage"]
    ende = datetime.now(timezone.utc) + timedelta(days=tage)
    meta("POST", status["anzeigengruppe_id"], end_time=ende.strftime("%Y-%m-%dT%H:%M:%S+0000"))
    meta("POST", status["kampagne_id"], status="ACTIVE")
    status["gestartet"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    status["endet"] = ende.isoformat(timespec="minutes")
    speichern(ordner, status, f"Werbung {name}: gestartet")
    budget = plan["anzeigengruppe"]["tagesbudget_cent"]
    print(f"✅ Gestartet. Läuft {tage} Tage bis {ende:%d.%m.%Y}, höchstens {euro(budget * tage)} plus Umsatzsteuer.")


def pausieren(name: str):
    ordner, plan, status = laden(name)
    meta("POST", status["kampagne_id"], status="PAUSED")
    status["pausiert"] = datetime.now(timezone.utc).isoformat(timespec="minutes")
    speichern(ordner, status, f"Werbung {name}: pausiert")
    print("⏸️ Kampagne pausiert. Es entstehen keine weiteren Kosten.")


def bericht(name: str):
    ordner, plan, status = laden(name)
    felder = "ad_name,impressions,reach,frequency,inline_link_clicks,ctr,cpc,spend,actions"
    for ebene, objekt in [("Gesamt", status["kampagne_id"])]:
        k = meta("GET", f"{objekt}/insights", fields=felder, date_preset="maximum").get("data", [])
        print(f"== {plan['name']}: {ebene}")
        print(json.dumps(k[0] if k else {"hinweis": "noch keine Daten"}, indent=2, ensure_ascii=False))
    zeilen = meta("GET", f"{status['kampagne_id']}/insights", fields=felder, level="ad",
                  date_preset="maximum").get("data", [])
    print("== Je Anzeige")
    for z in zeilen:
        print(f"- {z.get('ad_name')}: {z.get('impressions')} Einblendungen, {z.get('inline_link_clicks', 0)} Link-Klicks, "
              f"CTR {z.get('ctr')} %, {z.get('spend')} € ausgegeben")
    info = meta("GET", status["kampagne_id"], fields="effective_status")
    print(f"Status: {info.get('effective_status')}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    aktion, name = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    if aktion == "konten":
        return konten()
    if not name:
        sys.exit("Bitte den Namen der Kampagne angeben (Ordner unter werbung/).")
    {"vorbereiten": vorbereiten, "erneuern": erneuern, "starten": starten, "pausieren": pausieren, "bericht": bericht}[aktion](name)


if __name__ == "__main__":
    main()
