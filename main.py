from __future__ import annotations

import argparse
import json
from pathlib import Path

from aga8_detail import calculate_from_inputs


def _lade_eingabe(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def _als_liste(v: object) -> list[object]:
    if isinstance(v, list):
        return v
    return [v]


def _lese_temperaturen(daten: dict) -> tuple[list[float], str]:
    if "temperatur_C" in daten:
        return [float(wert) for wert in _als_liste(daten["temperatur_C"])], "C"
    if "temperatur_K" in daten:
        return [float(wert) for wert in _als_liste(daten["temperatur_K"])], "K"
    return [float(wert) for wert in _als_liste(daten["temperature_k"])], "K"


def _lese_druecke(daten: dict) -> tuple[list[float], str]:
    if "druck_bar" in daten:
        return [float(wert) for wert in _als_liste(daten["druck_bar"])], "bar"
    if "druck_kPa" in daten:
        return [float(wert) for wert in _als_liste(daten["druck_kPa"])], "kPa"
    return [float(wert) for wert in _als_liste(daten["pressure_kpa"])], "kPa"


def _temperatur_nach_kelvin(wert: float, einheit: str) -> float:
    if einheit == "C":
        return wert + 273.15
    return wert


def _druck_nach_kpa(wert: float, einheit: str) -> float:
    if einheit == "bar":
        return wert * 100.0
    return wert


def _lese_stoffmengenanteile(daten: dict) -> dict:
    if "stoffmengenanteile" in daten:
        return daten["stoffmengenanteile"]
    return daten["composition"]


def _lese_startdichte(daten: dict) -> float | None:
    if "startwert_molare_dichte_mol_pro_l" in daten:
        wert = daten["startwert_molare_dichte_mol_pro_l"]
        return None if wert is None else float(wert)
    wert = daten.get("initial_density_mol_per_l")
    return None if wert is None else float(wert)


def _ausgabepfad_fuer_eingabe(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}-out.json")


def _globalisierte_eingabedaten(
    daten: dict,
    temperaturen: list[float],
    temperatur_einheit: str,
    druecke: list[float],
    druck_einheit: str,
) -> dict:
    eingabedaten = {
        "temperatur_C": temperaturen if temperatur_einheit == "C" else None,
        "druck_bar": druecke if druck_einheit == "bar" else None,
        "intern_verwendete_temperaturen_K": [
            _temperatur_nach_kelvin(wert, temperatur_einheit) for wert in temperaturen
        ],
        "intern_verwendete_druecke_kPa": [
            _druck_nach_kpa(wert, druck_einheit) for wert in druecke
        ],
        "startwert_molare_dichte_mol_pro_l": _lese_startdichte(daten),
        "stoffmengenanteile_vor_normierung": _lese_stoffmengenanteile(daten),
        "anzahl_kombinationen": len(temperaturen) * len(druecke),
    }
    if temperatur_einheit == "K":
        eingabedaten["temperatur_K"] = temperaturen
    if druck_einheit == "kPa":
        eingabedaten["druck_kPa"] = druecke
    return eingabedaten


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_datei", nargs="?", default="input.json")
    args = parser.parse_args()

    input_path = Path(args.input_datei)
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} wurde nicht gefunden.")

    payload = _lade_eingabe(input_path)
    temperaturen, temperatur_einheit = _lese_temperaturen(payload)
    druecke, druck_einheit = _lese_druecke(payload)
    stoffmengenanteile = _lese_stoffmengenanteile(payload)
    startdichte = _lese_startdichte(payload)

    ergebnisse = []
    global_eingabedaten = _globalisierte_eingabedaten(
        payload, temperaturen, temperatur_einheit, druecke, druck_einheit
    )

    for index, temperatur in enumerate(temperaturen, start=1):
        temperatur_k = _temperatur_nach_kelvin(temperatur, temperatur_einheit)
        for druck in druecke:
            druck_kpa = _druck_nach_kpa(druck, druck_einheit)
            result = calculate_from_inputs(
                temperature_k=temperatur_k,
                pressure_kpa=druck_kpa,
                composition=stoffmengenanteile,
                initial_density_mol_per_l=startdichte,
            )

            global_eingabedaten["summe_vor_normierung"] = result["eingabedaten"][
                "summe_vor_normierung"
            ]
            global_eingabedaten["stoffmengenanteile_normiert"] = result["eingabedaten"][
                "stoffmengenanteile_normiert"
            ]

            ergebnisse.append(
                {
                    "index": len(ergebnisse) + 1,
                    "temperatur_C": temperatur_k - 273.15,
                    "druck_bar": druck_kpa / 100.0,
                    "intern_verwendete_temperatur_K": temperatur_k,
                    "intern_verwendeter_druck_kPa": druck_kpa,
                    "ergebnis": result["ergebnis"],
                    "status": result["status"],
                }
            )

    output = {
        "verfahren": "DIN EN ISO 12213-2:2010-01 / AGA8 DETAIL",
        "eingabedaten": global_eingabedaten,
        "ergebnisse": ergebnisse,
    }

    output_path = _ausgabepfad_fuer_eingabe(input_path)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
