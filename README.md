# Zufallsfall

Zieht eine zufällige Die-drei-???-Folge nach Kategorie und öffnet sie in Apple Music.
Dazu ein Bereich für DiE DR3i, der über den Kurzbefehl „DR3i“ aus der eigenen Mediathek abspielt.

Seite: https://ezzzooo.github.io/zufallsfall/

## Aktualisierung

Die GitHub Action `Seite bauen` läuft jeden Montag früh und bei jedem Push.
Sie holt die Folgendaten von [dreimetadaten.de](https://dreimetadaten.de/), berechnet die Kategorien und veröffentlicht die Seite.
Von Hand starten: Actions → Seite bauen → Run workflow.

## Dateien

- `build/build.py` baut `_site/` (nur Python-Standardbibliothek): `python3 build/build.py`
- `build/template.html` die Seite mit Platzhaltern
- `build/weitere.json` Film-, Live- und Kopfhörer-Alben, die dreimetadaten.de nicht führt
- `build/korrekturen.json` Handkorrekturen der Kategorie Grusel
- `build/dr3i.json` DiE-DR3i-Folgen mit Suchbegriffen für die Mediathek
- `static/` Icon und DR3i-Cover
