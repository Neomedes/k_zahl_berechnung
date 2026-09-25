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


def _temperatur_druck_paare(
    temperaturen: list[float], druecke: list[float]
) -> list[tuple[float, float]]:
    if len(temperaturen) != len(druecke):
        raise ValueError(
            "Temperatur und Druck müssen gleich viele Werte enthalten "
            f"(Temperaturen: {len(temperaturen)}, Drücke: {len(druecke)})."
        )
    return list(zip(temperaturen, druecke))


def _lese_umgebungen(daten: dict) -> list[tuple[float, str, float, str]]:
    """Read scalar temperature/pressure values with units for each environment."""
    umgebungen = daten["umgebungen"]
    if not isinstance(umgebungen, list) or not umgebungen:
        raise ValueError("'umgebungen' muss eine nicht-leere Liste sein.")

    paare = []
    for index, umgebung in enumerate(umgebungen, start=1):
        if not isinstance(umgebung, dict):
            raise ValueError(f"Umgebung {index} muss ein Objekt sein.")

        temperatur_keys = [key for key in ("temp_K", "temp_C") if key in umgebung]
        druck_keys = [key for key in ("druck_bar", "druck_kPa") if key in umgebung]
        if len(temperatur_keys) != 1:
            raise ValueError(
                f"Umgebung {index} muss genau einen Temperaturwert (temp_K oder temp_C) enthalten."
            )
        if len(druck_keys) != 1:
            raise ValueError(
                f"Umgebung {index} muss genau einen Druckwert (druck_bar oder druck_kPa) enthalten."
            )
        temperatur_key, druck_key = temperatur_keys[0], druck_keys[0]
        paare.append(
            (
                float(umgebung[temperatur_key]),
                "K" if temperatur_key == "temp_K" else "C",
                float(umgebung[druck_key]),
                "bar" if druck_key == "druck_bar" else "kPa",
            )
        )
    return paare


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
        "anzahl_kombinationen": len(temperaturen),
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
    if "umgebungen" in payload:
        umgebungswerte = _lese_umgebungen(payload)
    else:
        temperaturen, temperatur_einheit = _lese_temperaturen(payload)
        druecke, druck_einheit = _lese_druecke(payload)
        umgebungswerte = [
            (temperatur, temperatur_einheit, druck, druck_einheit)
            for temperatur, druck in _temperatur_druck_paare(temperaturen, druecke)
        ]
    stoffmengenanteile = _lese_stoffmengenanteile(payload)
    startdichte = _lese_startdichte(payload)

    ergebnisse = []
    if "umgebungen" in payload:
        global_eingabedaten = {
            "umgebungen": payload["umgebungen"],
            "intern_verwendete_umgebungen": [
                {
                    "temperatur_K": _temperatur_nach_kelvin(temp, temp_unit),
                    "druck_kPa": _druck_nach_kpa(pressure, pressure_unit),
                }
                for temp, temp_unit, pressure, pressure_unit in umgebungswerte
            ],
            "startwert_molare_dichte_mol_pro_l": startdichte,
            "stoffmengenanteile_vor_normierung": stoffmengenanteile,
            "anzahl_kombinationen": len(umgebungswerte),
        }
    else:
        global_eingabedaten = _globalisierte_eingabedaten(
            payload, temperaturen, temperatur_einheit, druecke, druck_einheit
        )

    for index, (temperatur, temperatur_einheit, druck, druck_einheit) in enumerate(umgebungswerte, start=1):
        temperatur_k = _temperatur_nach_kelvin(temperatur, temperatur_einheit)
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
                "index": index,
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
