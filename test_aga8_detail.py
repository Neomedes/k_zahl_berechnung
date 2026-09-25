from __future__ import annotations

from aga8_detail import calculate_from_inputs
from main import _lese_umgebungen, _temperatur_druck_paare


def test_temperatur_und_druck_werden_positionsweise_zugeordnet() -> None:
    assert _temperatur_druck_paare([100.0, 200.0], [10.0, 20.0]) == [
        (100.0, 10.0),
        (200.0, 20.0),
    ]


def test_unterschiedlich_viele_temperaturen_und_druecke_werden_abgelehnt() -> None:
    try:
        _temperatur_druck_paare([100.0, 200.0], [10.0])
    except ValueError as exc:
        assert "gleich viele Werte" in str(exc)
    else:
        raise AssertionError("Unterschiedlich lange Eingaben wurden nicht abgelehnt")


def test_umgebungen_lesen_eigene_einheiten_unabhaengig():
    assert _lese_umgebungen({"umgebungen": [
        {"temp_K": 290, "druck_bar": 41},
        {"temp_C": 15, "druck_kPa": 3900},
    ]}) == [(290.0, "K", 41.0, "bar"), (15.0, "C", 3900.0, "kPa")]


def test_umgebung_mit_fehlenden_oder_mehrdeutigen_einheiten_wird_abgelehnt():
    for environment in (
        {"temp_K": 290, "temp_C": 17, "druck_bar": 41},
        {"temp_K": 290},
        {"druck_bar": 41},
    ):
        try:
            _lese_umgebungen({"umgebungen": [environment]})
        except ValueError:
            pass
        else:
            raise AssertionError(f"Ungültige Umgebung wurde akzeptiert: {environment}")


def test_example_environment_units_preserve_calculation_results():
    from main import _druck_nach_kpa, _temperatur_nach_kelvin

    composition = {"methan": 100}
    parsed = _lese_umgebungen({"umgebungen": [
        {"temp_K": 290, "druck_bar": 41},
        {"temp_C": 15, "druck_kPa": 3900},
    ]})
    results = [
        calculate_from_inputs(
            _temperatur_nach_kelvin(temp, temp_unit),
            _druck_nach_kpa(pressure, pressure_unit),
            composition,
        )["ergebnis"]
        for temp, temp_unit, pressure, pressure_unit in parsed
    ]
    assert abs(results[0]["druck_kPa"] - 4100.0) < 1e-9
    assert abs(results[1]["druck_kPa"] - 3900.0) < 1e-9
    assert abs(results[0]["k_zahl"] - 0.9236893759415037) < 1e-12
    assert abs(results[0]["molare_dichte_mol_pro_l"] - 1.840870551470663) < 1e-12
    assert abs(results[1]["k_zahl"] - 0.925450504439891) < 1e-12
    assert abs(results[1]["molare_dichte_mol_pro_l"] - 1.7589606611449082) < 1e-12


def test_reference_case() -> None:
    result = calculate_from_inputs(
        temperature_k=400.0,
        pressure_kpa=50000.0,
        composition={
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
            "argon": 0.1,
        },
    )

    ergebnis = result["ergebnis"]

    def check(key: str, expected: float, tol: float = 1e-8) -> None:
        actual = ergebnis[key]
        assert abs(actual - expected) <= tol, f"{key}: {actual} != {expected}"

    check("molare_masse_g_pro_mol", 20.54333051)
    check("molare_dichte_mol_pro_l", 12.80792403648801)
    check("druck_kPa", 50000.0, 1e-6)
    check("k_zahl", 1.173801364147326)
    check("dP_dRho_kPa_pro_mol_l", 6971.387690924090)
    check("d2P_dRho2_kPa_pro_mol_l2", 1118.803636639520)
    check("dP_dT_kPa_pro_K", 235.6641493068212)
    check("innere_energie_J_pro_mol", -2739.134175817231)
    check("enthalpie_J_pro_mol", 1164.699096269404)
    check("entropie_J_pro_mol_K", -38.54882684677111)
    check("cv_J_pro_mol_K", 39.12076154430332)
    check("cp_J_pro_mol_K", 58.54617672380667)
    check("schallgeschwindigkeit_m_pro_s", 712.6393684057903)
    check("gibbs_energie_J_pro_mol", 16584.22983497785)
    check("joule_thomson_K_pro_kPa", 7.432969304794577e-05)
    check("isentropenexponent", 2.672509225184606)
