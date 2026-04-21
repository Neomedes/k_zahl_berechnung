from __future__ import annotations

import argparse
import json
from pathlib import Path

from aga8_detail import calculate_from_inputs


def _lade_eingabe(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def _lese_temperatur_k(daten: dict) -> float:
    if "temperatur_C" in daten:
        return float(daten["temperatur_C"]) + 273.15
    if "temperatur_K" in daten:
        return float(daten["temperatur_K"])
    return float(daten["temperature_k"])


def _lese_druck_kpa(daten: dict) -> float:
    if "druck_bar" in daten:
        return float(daten["druck_bar"]) * 100.0
    if "druck_kPa" in daten:
        return float(daten["druck_kPa"])
    return float(daten["pressure_kpa"])


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_datei", nargs="?", default="input.json")
    args = parser.parse_args()

    input_path = Path(args.input_datei)
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} wurde nicht gefunden.")

    payload = _lade_eingabe(input_path)
    result = calculate_from_inputs(
        temperature_k=_lese_temperatur_k(payload),
        pressure_kpa=_lese_druck_kpa(payload),
        composition=_lese_stoffmengenanteile(payload),
        initial_density_mol_per_l=_lese_startdichte(payload),
    )

    output = {
        "verfahren": "DIN EN ISO 12213-2:2010-01 / AGA8 DETAIL",
        **result,
    }

    output_path = _ausgabepfad_fuer_eingabe(input_path)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
