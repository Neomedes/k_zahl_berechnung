from __future__ import annotations

from aga8_detail import calculate_from_inputs


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
