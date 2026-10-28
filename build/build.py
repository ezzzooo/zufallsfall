"""Baut die Zufallsfall-Seite nach _site/ aus den aktuellen Daten von dreimetadaten.de.

Aufruf: python3 build/build.py
Nur Standardbibliothek, läuft lokal und in der GitHub Action.
"""
import hashlib
import html
import json
import re
import shutil
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = ROOT / "_site"
DMD = "https://dreimetadaten.de/data/"

# Stichwörter im Klappentext für die Themen-Kategorien
THEMEN = {
    "grusel": r"\b(geist\w*|gespenst\w*|spuk\w*|vampir\w*|fluch\w*|monster\w*|dämon\w*|hexe\w*|mumie\w*|totenkopf|untot\w*|werwolf|teufel\w*|grusel\w*|zombie\w*|phantom\w*|jenseits|unheimlich\w*|übernatürlich\w*|horror\w*|geisterhaft\w*|poltergeist)\b",
    "schatz": r"\b(schatz\w*|schätze|rätsel\w*|geheimschrift|verschlüssel\w*|geheimcode|schatzkarte|code\w*)\b",
    "fussball": r"fußball|fussball|bundesliga|elfmeter|torwart",
    "meer": r"\b(meer\w*|ozean\w*|schiff\w*|insel\w*|riff\w*|tauch\w*|pirat\w*|bucht|küste\w*|segel\w*|segler\w*|hafen|wrack\w*|kapitän\w*)\b",
}
ADVENT = r"Advent|Nacht, düstere|finstere|Bescherung|Glocken|Weihnacht"
# Für „Zum Einschlafen“: Folgen mit diesen Wörtern in Titel oder Klappentext gelten als zu aufregend
UNRUHIG = r"grusel|geist|gespenst|spuk|vampir|fluch|monster|dämon|mumie|totenkopf|untot|werwolf|horror|zombie|phantom|jenseits|unheimlich|mord|leiche|\btot|tödlich|panik|angst|schrecken|grauen|blut|entführ|bombe|explosion|schüsse|waffe|gefangen|gift|teufel|unterwelt|grab\b|wolf"
RB = "https://www.rocky-beach.com"


def hole(url):
    req = urllib.request.Request(url, headers={"User-Agent": "zufallsfall-build (github.com/ezzzooo/zufallsfall)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def dekade(jahr):
    return "dek70" if jahr < "1990" else "dek" + jahr[2] + "0"


def folge(e, n, titel, tags):
    """Ein Eintrag aus dreimetadaten in das kompakte Format der Seite."""
    jahr = (e.get("veröffentlichungsdatum") or "")[:4]
    k = list(tags)
    text = (titel + " " + (e.get("gesamtbeschreibung") or "")).lower()
    for name, muster in THEMEN.items():
        if re.search(muster, text):
            k.append(name)
    rollen = " | ".join(r.get("rolle", "") for r in (e.get("sprechrollen") or []))
    if "Skinny" in rollen:
        k.append("skinny")
    if "Hugenay" in rollen:
        k.append("hugenay")
    if "Hitchcock" in rollen:
        k.append("hitchcock")
    ruhig = not re.search(UNRUHIG, text)
    dauer = e.get("gesamtdauer")
    if dauer and dauer < 50 * 60000:
        k.append("kurz")
    if jahr:
        k.append(dekade(jahr))
    eintrag = {"n": n, "t": titel, "id": str(e["ids"]["appleMusic"]), "j": jahr, "b": e.get("beschreibung") or "", "k": k}
    if dauer:
        eintrag["m"] = round(dauer / 60000)
    if ruhig:
        eintrag["_ruhig"] = True
    datum = (e.get("veröffentlichungsdatum") or "")[:10]
    if len(datum) == 10:
        eintrag["d"] = datum
    if e["ids"].get("spotify"):
        eintrag["sp"] = e["ids"]["spotify"]
    return eintrag


def bewertungen(serie):
    """Hörspiel-Bewertungen von rocky-beach.com: {Nummer: (Note, Rang, Stimmen, Titel)}."""
    req = urllib.request.Request(RB + "/php/project/f_ausgabe.html", data=f"serie={serie}&ansicht=1".encode(),
                                 headers={"User-Agent": "zufallsfall-build (github.com/ezzzooo/zufallsfall)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        seite = r.read().decode("utf-8", "replace")
    ergebnis = {}
    for zeile in re.findall(r'<tr><td height="30">(.*?)</tr>', seite, re.S):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "|", zeile)))
        m = re.search(r"\|([^|]+?) \((\d+)\)\|+([\d.]+)\|+(\d+)\|+(\d+)", text)
        if m:
            ergebnis[int(m.group(2))] = (round(float(m.group(3)), 2), int(m.group(4)), int(m.group(5)), m.group(1).strip())
    return ergebnis


def einfach(text):
    return re.sub(r"[^a-z0-9äöüß]", "", text.lower().replace("und ", "").replace("die drei ???", ""))


def main():
    serie = hole(DMD + "Serie.json")
    spezial = hole(DMD + "Spezial.json")["spezial"]
    kurz = hole(DMD + "Kurzgeschichten.json")["kurzgeschichten"]
    am = lambda e: (e.get("ids") or {}).get("appleMusic")

    eps = [folge(e, e["nummer"], e["titel"], ["haupt"]) for e in serie["serie"] if am(e)]
    for e in spezial:
        if am(e):
            tags = ["special"] + (["advent"] if re.search(ADVENT, e["titel"]) else [])
            eps.append(folge(e, None, e["titel"], tags))
    for e in kurz:
        if am(e):
            eps.append(folge(e, None, e["titel"] + " (Kurzgeschichten)", ["special", "kurz_sammlung"]))
    vorhanden = {e["id"] for e in eps}
    for w in json.loads((BUILD / "weitere.json").read_text()):
        if w["id"] not in vorhanden:
            k = ["weitere"] + ([dekade(w["j"])] if w["j"] else [])
            k += [name for name, muster in THEMEN.items() if re.search(muster, w["t"].lower())]
            eps.append({"n": None, "t": w["t"], "id": w["id"], "j": w["j"], "b": "", "k": k})

    # Bewertungen von rocky-beach.com (Hauptfolgen über die Nummer, Specials über den Titel)
    try:
        noten, noten_dr3i = bewertungen(2), bewertungen(3)
    except Exception as fehler:
        print("rocky-beach.com nicht erreichbar, Bewertungen fehlen:", fehler)
        noten, noten_dr3i = {}, {}
    sondertitel = {einfach(t).replace("live", ""): (note, rang, stimmen) for nr, (note, rang, stimmen, t) in noten.items() if nr >= 900}
    def sonder(titel):
        if "(Kopfhörer" in titel or "Kinofilm" in titel or "Taipan" in titel:
            return None
        eigen = einfach(titel)
        return next((w for k, w in sondertitel.items() if k and k in eigen), None)
    for e in eps:
        if e["n"] is not None and e["n"] in noten:
            e["r"] = list(noten[e["n"]][:3])
            e["rb"] = f"{RB}/hoerspiel/folgen/{e['n']:03d}.html"
        elif e["n"] is None and sonder(e["t"]):
            e["r"] = list(sonder(e["t"]))
            e["rb"] = RB + "/php/project/f_ausgabe.html"
        if e.pop("_ruhig", False) and 40 <= e.get("m", 0) <= 80 and e.get("r") and e["r"][0] <= 2.6:
            e["k"].append("schlaf")
    # Eigene Plätze: Hauptfolgen und Specials getrennt, Reihenfolge wie auf rocky-beach.com (dort ungerundet)
    def plaetze(liste):
        liste = sorted((e for e in liste if e.get("r")), key=lambda e: (e["r"][1], e["r"][0]))
        for i, e in enumerate(liste, 1):
            e["p"] = [i, len(liste)]
    plaetze([e for e in eps if e["n"] is not None])
    plaetze([e for e in eps if e["n"] is None])
    for e in eps:
        if e["n"] is not None and e.get("p") and e["p"][0] <= 50:
            e["k"].append("top50")
    print(f"Bewertungen: {sum(1 for e in eps if e.get('r'))} Alben, {sum('schlaf' in e['k'] for e in eps)} zum Einschlafen")

    dr3i = json.loads((BUILD / "dr3i.json").read_text())
    for f in dr3i:
        treffer = noten_dr3i.get(f["n"] if f["n"] is not None else 999)
        if treffer:
            f["r"] = list(treffer[:3])
    plaetze(dr3i)

    korr = json.loads((BUILD / "korrekturen.json").read_text())
    for e in eps:
        if e["n"] is None:
            continue
        for thema in ("grusel", "fussball", "schlaf"):
            if e["t"] in korr.get(thema + "_plus", []) and thema not in e["k"]:
                e["k"].append(thema)
            if e["t"] in korr.get(thema + "_minus", []) and thema in e["k"]:
                e["k"].remove(thema)

    haupt = sum(1 for e in eps if e["n"] is not None)
    if haupt < 241:
        raise SystemExit(f"Nur {haupt} Hauptfolgen gefunden, Abbruch – die alte Seite bleibt online.")

    # Cover-Adressen über die iTunes-Schnittstelle
    art, ids = {}, [e["id"] for e in eps]
    for i in range(0, len(ids), 100):
        for a in hole("https://itunes.apple.com/lookup?country=de&id=" + ",".join(ids[i:i + 100]))["results"]:
            if "artworkUrl100" in a:
                art[str(a["collectionId"])] = a["artworkUrl100"].replace("100x100bb", "300x300bb")
        time.sleep(3)

    stand = datetime.fromisoformat(serie["dbInfo"]["lastModified"].replace("Z", "+00:00")).strftime("%d.%m.%Y")
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    seite = (BUILD / "template.html").read_text()
    for platzhalter, wert in {
        "__DATEN__": js(eps),
        "__DR3I__": js(dr3i),
        "__ART__": js(art),
        "__STAND__": stand,
        "__ANZAHL__": str(len(eps)),
    }.items():
        assert platzhalter in seite, platzhalter
        seite = seite.replace(platzhalter, wert)

    # Versionskennung: die Seite prüft version.json und lädt neu, wenn sie sich ändert
    version = hashlib.sha256(seite.encode()).hexdigest()[:12]
    seite = seite.replace("__VERSION__", version)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    (OUT / "index.html").write_text(seite)
    (OUT / "version.json").write_text(json.dumps({"v": version}))
    print(f"{len(eps)} Alben ({haupt} Hauptfolgen), {len(art)} Cover, Stand {stand}")


if __name__ == "__main__":
    main()
