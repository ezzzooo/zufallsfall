"""Baut die Zufallsfall-Seite nach _site/ aus den aktuellen Daten von dreimetadaten.de.

Aufruf: python3 build/build.py
Nur Standardbibliothek, läuft lokal und in der GitHub Action.
"""
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
    "meer": r"\b(meer\w*|ozean\w*|schiff\w*|insel\w*|riff\w*|tauch\w*|pirat\w*|bucht|küste\w*|segel\w*|segler\w*|hafen|wrack\w*|kapitän\w*)\b",
}
ADVENT = r"Advent|Nacht, düstere|finstere|Bescherung|Glocken|Weihnacht"


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
    dauer = e.get("gesamtdauer")
    if dauer and dauer < 50 * 60000:
        k.append("kurz")
    if jahr:
        k.append(dekade(jahr))
    eintrag = {"n": n, "t": titel, "id": str(e["ids"]["appleMusic"]), "j": jahr, "b": e.get("beschreibung") or "", "k": k}
    if e["ids"].get("spotify"):
        eintrag["sp"] = e["ids"]["spotify"]
    return eintrag


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

    korr = json.loads((BUILD / "korrekturen.json").read_text())
    for e in eps:
        if e["n"] is not None and e["t"] in korr["grusel_plus"] and "grusel" not in e["k"]:
            e["k"].append("grusel")
        if e["n"] is not None and e["t"] in korr["grusel_minus"] and "grusel" in e["k"]:
            e["k"].remove("grusel")

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
        "__DR3I__": js(json.loads((BUILD / "dr3i.json").read_text())),
        "__ART__": js(art),
        "__STAND__": stand,
        "__ANZAHL__": str(len(eps)),
    }.items():
        assert platzhalter in seite, platzhalter
        seite = seite.replace(platzhalter, wert)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    (OUT / "index.html").write_text(seite)
    print(f"{len(eps)} Alben ({haupt} Hauptfolgen), {len(art)} Cover, Stand {stand}")


if __name__ == "__main__":
    main()
