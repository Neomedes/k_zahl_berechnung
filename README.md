# K-Zahl nach DIN EN ISO 12213-2

Dieses kleine Programm liest eine frei waehlbare JSON-Datei, berechnet den Realgasfaktor beziehungsweise die Kompressibilitaetszahl `Z` nach dem in DIN EN ISO 12213-2:2010-01 beschriebenen AGA8-DETAIL-Verfahren und schreibt das Ergebnis in eine zweite JSON-Datei mit dem Suffix `-out`.

Die Implementierung orientiert sich eng an der offiziellen NIST-Referenz `DETAIL.FOR` beziehungsweise deren direkte C++-Uebersetzung aus `usnistgov/AGA8`.

## Start

```bash
python3 main.py
python3 main.py test.json
```

Aus `input.json` wird `input-out.json`, aus `test.json` wird `test-out.json`.

## Eingabeformat

```json
{
  "temperatur_C": 126.85,
  "druck_bar": 500.0,
  "stoffmengenanteile": {
    "methan": 77.824,
    "stickstoff": 2.0,
    "kohlendioxid": 6.0,
    "ethan": 8.0,
    "propan": 3.0,
    "isobutan": 0.15,
    "n_butan": 0.3,
    "isopentan": 0.05,
    "n_pentan": 0.165,
    "n_hexan": 0.215,
    "n_heptan": 0.088,
    "n_oktan": 0.024,
    "n_nonan": 0.015,
    "n_dekan": 0.009,
    "wasserstoff": 0.4,
    "sauerstoff": 0.5,
    "kohlenmonoxid": 0.2,
    "wasser": 0.01,
    "schwefelwasserstoff": 0.25,
    "helium": 0.7,
    "argon": 0.1
  }
}
```

Die Stoffmengenanteile werden automatisch normiert. Das gilt sowohl fuer Anteile mit Summe `100` als auch fuer beliebige andere Summen ungleich `0`.
Temperatur und Druck koennen jetzt direkt in `Grad Celsius` und `bar` angegeben werden; intern rechnet das Programm normkonform mit `K` und `kPa`.

## Test

```bash
python3 -m pytest -q
```
