# Zufallsfall

Zieht eine zufällige Die-drei-???-Folge nach Kategorie und öffnet sie in Apple Music.
Dazu ein Bereich für DiE DR3i, der über den Kurzbefehl „DR3i“ aus der eigenen Mediathek abspielt.

Seite: https://ezzzooo.github.io/zufallsfall/

## Aktualisierung

Die GitHub Action `Seite bauen` läuft jeden Montag früh und bei jedem Push.
Sie holt die Folgendaten von [dreimetadaten.de](https://dreimetadaten.de/), berechnet die Kategorien und veröffentlicht die Seite.
Alben, die bei Apple Music schon erschienen sind, aber bei dreimetadaten.de noch fehlen (neue Folgen, Adventskalender), ergänzt sie direkt aus Apple Music – zunächst ohne Klappentext und Spotify-Link.
Von Hand starten: Actions → Seite bauen → Run workflow.

## Funktionen (Auswahl)

- **Gehört-Sammlung:** Geöffnete Folgen werden automatisch abgehakt, in der Akte von Hand umschaltbar. Fortschritt im Reiter Rangliste, Filter „Nur noch nicht gehörte“ in den Kategorien.
- **Siri-Link:** `?los=<kategorie>` (z. B. `?los=grusel`) zieht sofort einen Fall und öffnet die Musik-App. Den Link gibt es in den Einstellungen unter „Siri & Kurzbefehl“.
- **Countdown:** zeigt die nächste angekündigte Folge (Datum von Apple Music, sonst dreimetadaten.de).

## Dateien

- `build/build.py` baut `_site/` (nur Python-Standardbibliothek): `python3 build/build.py`
- `build/template.html` die Seite mit Platzhaltern
- `build/weitere.json` Film-, Live- und Kopfhörer-Alben, die dreimetadaten.de nicht führt
- `build/korrekturen.json` Handkorrekturen der Kategorie Grusel
- `build/dr3i.json` DiE-DR3i-Folgen mit Suchbegriffen für die Mediathek
- `static/` Icon und DR3i-Cover

## Dokumentation

Ausführliches Handbuch: [docs/dokumentation.html](docs/dokumentation.html), online unter https://ezzzooo.github.io/zufallsfall/dokumentation.html, als PDF unter [docs/Zufallsfall-Dokumentation.pdf](docs/Zufallsfall-Dokumentation.pdf).

PDF neu erzeugen (am Mac, nach Änderungen an `docs/dokumentation.html`):

```
swift docs/html2pdf.swift "$PWD/docs/dokumentation.html" "$PWD/docs/Zufallsfall-Dokumentation.pdf"
```
