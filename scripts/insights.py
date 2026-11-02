"""Reichweiten-Bericht für Instagram (postet nichts).

Aufruf: python scripts/insights.py [Tage]   (Standard 30)
"""
import sys, json, datetime as dt
from collections import defaultdict
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import post


def versuch(titel, f):
    try:
        return f()
    except Exception as e:
        print(f"  ({titel} nicht verfügbar: {e})")
        return None


def main():
    tage = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    bis = dt.datetime.now(dt.timezone.utc)
    von = bis - dt.timedelta(days=min(tage, 30))
    p = post.api("GET", "me", fields="user_id,username,followers_count,follows_count,media_count")
    uid = p["user_id"]
    print(f"== Konto @{p.get('username')}: {p.get('followers_count')} Follower, {p.get('media_count')} Beiträge")

    print(f"== Konto-Kennzahlen {von:%d.%m.}–{bis:%d.%m.%Y}")
    for m in ["reach", "views", "accounts_engaged", "total_interactions", "profile_links_taps", "follows_and_unfollows", "saves", "shares", "comments", "likes"]:
        r = versuch(m, lambda: post.api("GET", f"{uid}/insights", metric=m, period="day", metric_type="total_value",
                                         since=int(von.timestamp()), until=int(bis.timestamp())))
        if r:
            for d in r.get("data", []):
                tv = d.get("total_value", {})
                wert = tv.get("value")
                teile = tv.get("breakdowns")
                print(f"- {m}: {wert}" + (f" {json.dumps(teile, ensure_ascii=False)}" if teile else ""))
    r = versuch("follower_count", lambda: post.api("GET", f"{uid}/insights", metric="follower_count", period="day",
                                                   since=int((bis - dt.timedelta(days=29)).timestamp()), until=int(bis.timestamp())))
    if r:
        werte = [(v["end_time"][:10], v["value"]) for d in r.get("data", []) for v in d.get("values", [])]
        print(f"- neue Follower pro Tag: {werte} (Summe {sum(v for _, v in werte)})")

    print("== Wann sind deine Follower online? (Stunde UTC: Anzahl, Durchschnitt letzte Tage)")
    r = versuch("online_followers", lambda: post.api("GET", f"{uid}/insights", metric="online_followers", period="lifetime",
                                                     since=int((bis - dt.timedelta(days=7)).timestamp()), until=int(bis.timestamp())))
    if r:
        summe = defaultdict(list)
        for d in r.get("data", []):
            for v in d.get("values", []):
                for h, n in (v.get("value") or {}).items():
                    summe[int(h)].append(n)
        if summe:
            print("- " + ", ".join(f"{h}h: {round(sum(n)/len(n))}" for h, n in sorted(summe.items())))
    for b in ["city", "age", "gender"]:
        r = versuch(f"Follower nach {b}", lambda: post.api("GET", f"{uid}/insights", metric="follower_demographics", period="lifetime",
                                                           metric_type="total_value", breakdown=b, timeframe="this_month"))
        if r:
            for d in r.get("data", []):
                for br in d.get("total_value", {}).get("breakdowns", []):
                    erg = sorted(br.get("results", []), key=lambda x: -x["value"])[:8]
                    print(f"- Follower nach {b}: " + ", ".join(f"{x['dimension_values'][0]} {x['value']}" for x in erg))

    print("== Beiträge (neueste zuerst)")
    medien = post.api("GET", f"{uid}/media", fields="id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", limit=40).get("data", [])
    zeilen = []
    for m in medien:
        art = "REEL" if m.get("media_product_type") == "REELS" else m.get("media_type")
        werte = {}
        for metr in (["reach", "views", "saved", "shares", "total_interactions", "follows", "profile_visits"],
                     ["reach", "views", "saved", "shares", "total_interactions"],
                     ["reach", "saved", "shares"]):
            try:
                r = post.api("GET", f"{m['id']}/insights", metric=",".join(metr))
                werte = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in r.get("data", [])}
                break
            except Exception as e:
                letzter = e
        titel = (m.get("caption") or "").split("\n")[0][:60]
        zeilen.append((m["timestamp"][:16], art, titel, werte, m.get("like_count"), m.get("comments_count")))
        print(f"- {m['timestamp'][:16]} {art} „{titel}“: " + ", ".join(f"{k} {v}" for k, v in werte.items())
              + f", Likes {m.get('like_count')}, Kommentare {m.get('comments_count')}" + ("" if werte else f" ({letzter})"))


if __name__ == "__main__":
    main()
