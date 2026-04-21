from __future__ import annotations

import math
from dataclasses import dataclass


COMPONENTS = [
    "methane",
    "nitrogen",
    "carbon_dioxide",
    "ethane",
    "propane",
    "isobutane",
    "n_butane",
    "isopentane",
    "n_pentane",
    "n_hexane",
    "n_heptane",
    "n_octane",
    "n_nonane",
    "n_decane",
    "hydrogen",
    "oxygen",
    "carbon_monoxide",
    "water",
    "hydrogen_sulfide",
    "helium",
    "argon",
]

DEUTSCHE_KOMPONENTEN = [
    "methan",
    "stickstoff",
    "kohlendioxid",
    "ethan",
    "propan",
    "isobutan",
    "n_butan",
    "isopentan",
    "n_pentan",
    "n_hexan",
    "n_heptan",
    "n_oktan",
    "n_nonan",
    "n_dekan",
    "wasserstoff",
    "sauerstoff",
    "kohlenmonoxid",
    "wasser",
    "schwefelwasserstoff",
    "helium",
    "argon",
]

DEUTSCH_ZU_INTERN = dict(zip(DEUTSCHE_KOMPONENTEN, COMPONENTS))
ENGLISCH_ZU_INTERN = {name: name for name in COMPONENTS}
KOMPONENTEN_ALIASE = {
    **DEUTSCH_ZU_INTERN,
    **ENGLISCH_ZU_INTERN,
    "co2": "carbon_dioxide",
    "n2": "nitrogen",
    "o2": "oxygen",
    "co": "carbon_monoxide",
    "h2": "hydrogen",
    "h2o": "water",
    "h2s": "hydrogen_sulfide",
}

NC_DETAIL = 21
MAX_FLDS = 21
N_TERMS = 58
EPSILON = 1e-15
R_DETAIL = 8.31451


def _zeros(size: int) -> list[float]:
    return [0.0] * size


def _ints(size: int) -> list[int]:
    return [0] * size


def _matrix(default: float = 0.0) -> list[list[float]]:
    return [[default for _ in range(MAX_FLDS + 1)] for _ in range(MAX_FLDS + 1)]


def _cube(default: float = 0.0) -> list[list[list[float]]]:
    return [
        [[default for _ in range(19)] for _ in range(MAX_FLDS + 1)]
        for _ in range(MAX_FLDS + 1)
    ]


@dataclass
class DetailState:
    an: list[float]
    un: list[float]
    fn: list[int]
    gn: list[int]
    qn: list[int]
    bn: list[int]
    kn: list[int]
    bsnij2: list[list[list[float]]]
    bs: list[float]
    csn: list[float]
    fi: list[float]
    gi: list[float]
    qi: list[float]
    ki25: list[float]
    ei25: list[float]
    kij5: list[list[float]]
    uij5: list[list[float]]
    gij5: list[list[float]]
    tun: list[float]
    n0i: list[list[float]]
    th0i: list[list[float]]
    mmi: list[float]
    xold: list[float]
    dpdd_save: float
    told: float
    k3: float


def _build_state() -> DetailState:
    an = _zeros(N_TERMS + 1)
    un = _zeros(N_TERMS + 1)
    fn = _ints(N_TERMS + 1)
    gn = _ints(N_TERMS + 1)
    qn = _ints(N_TERMS + 1)
    bn = _ints(N_TERMS + 1)
    kn = _ints(N_TERMS + 1)
    bsnij2 = _cube(0.0)
    bs = _zeros(19)
    csn = _zeros(N_TERMS + 1)
    fi = _zeros(MAX_FLDS + 1)
    gi = _zeros(MAX_FLDS + 1)
    qi = _zeros(MAX_FLDS + 1)
    ki25 = _zeros(MAX_FLDS + 1)
    ei25 = _zeros(MAX_FLDS + 1)
    kij5 = _matrix(1.0)
    uij5 = _matrix(1.0)
    gij5 = _matrix(1.0)
    tun = _zeros(N_TERMS + 1)
    n0i = [[0.0 for _ in range(8)] for _ in range(MAX_FLDS + 1)]
    th0i = [[0.0 for _ in range(8)] for _ in range(MAX_FLDS + 1)]
    mmi = _zeros(MAX_FLDS + 1)
    xold = _zeros(MAX_FLDS + 1)

    mmi_values = [
        16.043,
        28.0135,
        44.01,
        30.07,
        44.097,
        58.123,
        58.123,
        72.15,
        72.15,
        86.177,
        100.204,
        114.231,
        128.258,
        142.285,
        2.0159,
        31.9988,
        28.01,
        18.0153,
        34.082,
        4.0026,
        39.948,
    ]
    for i, value in enumerate(mmi_values, start=1):
        mmi[i] = value

    an_values = [
        0.1538326, 1.341953, -2.998583, -0.04831228, 0.3757965, -1.589575,
        -0.05358847, 0.88659463, -0.71023704, -1.471722, 1.32185035,
        -0.78665925, 0.00000000229129, 0.1576724, -0.4363864, -0.04408159,
        -0.003433888, 0.03205905, 0.02487355, 0.07332279, -0.001600573,
        0.6424706, -0.4162601, -0.06689957, 0.2791795, -0.6966051,
        -0.002860589, -0.008098836, 3.150547, 0.007224479, -0.7057529,
        0.5349792, -0.07931491, -1.418465, -5.99905e-17, 0.1058402,
        0.03431729, -0.007022847, 0.02495587, 0.04296818, 0.7465453,
        -0.2919613, 7.294616, -9.936757, -0.005399808, -0.2432567,
        0.04987016, 0.003733797, 1.874951, 0.002168144, -0.6587164,
        0.000205518, 0.009776195, -0.02048708, 0.01557322, 0.006862415,
        -0.001226752, 0.002850908,
    ]
    for i, value in enumerate(an_values, start=1):
        an[i] = value

    bn_values = [
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        2, 2, 2, 2, 2, 2, 2, 2, 2,
        3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
        4, 4, 4, 4, 4, 4, 4,
        5, 5, 5, 5, 5,
        6, 6,
        7, 7,
        8, 8, 8,
        9, 9,
    ]
    for i, value in enumerate(bn_values, start=1):
        bn[i] = value

    for idx, value in {
        13: 3, 14: 2, 15: 2, 16: 2, 17: 4, 18: 4, 21: 2, 22: 2, 23: 2,
        24: 4, 25: 4, 26: 4, 27: 4, 29: 1, 30: 1, 31: 2, 32: 2, 33: 3,
        34: 3, 35: 4, 36: 4, 37: 4, 40: 2, 41: 2, 42: 2, 43: 4, 44: 4,
        46: 2, 47: 2, 48: 4, 49: 4, 51: 2, 53: 2, 54: 1, 55: 2, 56: 2,
        57: 2, 58: 2,
    }.items():
        kn[idx] = value

    un_values = [
        0, 0.5, 1, 3.5, -0.5, 4.5, 0.5, 7.5, 9.5, 6, 12, 12.5, -6, 2, 3,
        2, 2, 11, -0.5, 0.5, 0, 4, 6, 21, 23, 22, -1, -0.5, 7, -1, 6, 4,
        1, 9, -13, 21, 8, -0.5, 0, 2, 7, 9, 22, 23, 1, 9, 3, 8, 23, 1.5,
        5, -0.5, 4, 7, 3, 0, 1, 0,
    ]
    for i, value in enumerate(un_values, start=1):
        un[i] = value

    for idx in (13, 27, 30, 35):
        fn[idx] = 1
    for idx in (5, 6, 25, 29, 32, 33, 34, 51, 54, 56):
        gn[idx] = 1
    for idx in (7, 16, 26, 28, 37, 42, 47, 49, 52, 58):
        qn[idx] = 1
    sn = _ints(N_TERMS + 1)
    wn = _ints(N_TERMS + 1)
    for idx in (8, 9):
        sn[idx] = 1
    for idx in (10, 11, 12):
        wn[idx] = 1

    ei_values = [
        151.3183, 99.73778, 241.9606, 244.1667, 298.1183, 324.0689,
        337.6389, 365.5999, 370.6823, 402.636293, 427.72263, 450.325022,
        470.840891, 489.558373, 26.95794, 122.7667, 105.5348, 514.0156,
        296.355, 2.610111, 119.6299,
    ]
    ki_values = [
        0.4619255, 0.4479153, 0.4557489, 0.5279209, 0.583749, 0.6406937,
        0.6341423, 0.6738577, 0.6798307, 0.7175118, 0.7525189, 0.784955,
        0.8152731, 0.8437826, 0.3514916, 0.4186954, 0.4533894, 0.3825868,
        0.4618263, 0.3589888, 0.4216551,
    ]
    ei = _zeros(MAX_FLDS + 1)
    ki = _zeros(MAX_FLDS + 1)
    si = _zeros(MAX_FLDS + 1)
    wi = _zeros(MAX_FLDS + 1)
    for i, value in enumerate(ei_values, start=1):
        ei[i] = value
    for i, value in enumerate(ki_values, start=1):
        ki[i] = value

    gi_updates = {
        2: 0.027815, 3: 0.189065, 4: 0.0793, 5: 0.141239, 6: 0.256692,
        7: 0.281835, 8: 0.332267, 9: 0.366911, 10: 0.289731, 11: 0.337542,
        12: 0.383381, 13: 0.427354, 14: 0.469659, 15: 0.034369, 16: 0.021,
        17: 0.038953, 18: 0.3325, 19: 0.0885,
    }
    for i, value in gi_updates.items():
        gi[i] = value

    qi[3] = 0.69
    qi[18] = 1.06775
    qi[19] = 0.633276
    fi[15] = 1.0
    si[18] = 1.5822
    si[19] = 0.39
    wi[18] = 1.0

    eij = _matrix(1.0)
    uij = _matrix(1.0)
    kij = _matrix(1.0)
    gij = _matrix(1.0)

    for (i, j), value in {
        (1, 2): 0.97164, (1, 3): 0.960644, (1, 5): 0.994635,
        (1, 6): 1.01953, (1, 7): 0.989844, (1, 8): 1.00235,
        (1, 9): 0.999268, (1, 10): 1.107274, (1, 11): 0.88088,
        (1, 12): 0.880973, (1, 13): 0.881067, (1, 14): 0.881161,
        (1, 15): 1.17052, (1, 17): 0.990126, (1, 18): 0.708218,
        (1, 19): 0.931484, (2, 3): 1.02274, (2, 4): 0.97012,
        (2, 5): 0.945939, (2, 6): 0.946914, (2, 7): 0.973384,
        (2, 8): 0.95934, (2, 9): 0.94552, (2, 15): 1.08632,
        (2, 16): 1.021, (2, 17): 1.00571, (2, 18): 0.746954,
        (2, 19): 0.902271, (3, 4): 0.925053, (3, 5): 0.960237,
        (3, 6): 0.906849, (3, 7): 0.897362, (3, 8): 0.726255,
        (3, 9): 0.859764, (3, 10): 0.855134, (3, 11): 0.831229,
        (3, 12): 0.80831, (3, 13): 0.786323, (3, 14): 0.765171,
        (3, 15): 1.28179, (3, 17): 1.5, (3, 18): 0.849408,
        (3, 19): 0.955052, (4, 5): 1.02256, (4, 7): 1.01306,
        (4, 9): 1.00532, (4, 15): 1.16446, (4, 18): 0.693168,
        (4, 19): 0.946871, (5, 7): 1.0049, (5, 15): 1.034787,
        (6, 15): 1.3, (7, 15): 1.3, (10, 19): 1.008692,
        (11, 19): 1.010126, (12, 19): 1.011501, (13, 19): 1.012821,
        (14, 19): 1.014089, (15, 17): 1.1,
    }.items():
        eij[i][j] = value

    for (i, j), value in {
        (1, 2): 0.886106, (1, 3): 0.963827, (1, 5): 0.990877,
        (1, 7): 0.992291, (1, 9): 1.00367, (1, 10): 1.302576,
        (1, 11): 1.191904, (1, 12): 1.205769, (1, 13): 1.219634,
        (1, 14): 1.233498, (1, 15): 1.15639, (1, 19): 0.736833,
        (2, 3): 0.835058, (2, 4): 0.816431, (2, 5): 0.915502,
        (2, 7): 0.993556, (2, 15): 0.408838, (2, 19): 0.993476,
        (3, 4): 0.96987, (3, 10): 1.066638, (3, 11): 1.077634,
        (3, 12): 1.088178, (3, 13): 1.098291, (3, 14): 1.108021,
        (3, 17): 0.9, (3, 19): 1.04529, (4, 5): 1.065173,
        (4, 6): 1.25, (4, 7): 1.25, (4, 8): 1.25, (4, 9): 1.25,
        (4, 15): 1.61666, (4, 19): 0.971926, (10, 19): 1.028973,
        (11, 19): 1.033754, (12, 19): 1.038338, (13, 19): 1.042735,
        (14, 19): 1.046966,
    }.items():
        uij[i][j] = value

    for (i, j), value in {
        (1, 2): 1.00363, (1, 3): 0.995933, (1, 5): 1.007619,
        (1, 7): 0.997596, (1, 9): 1.002529, (1, 10): 0.982962,
        (1, 11): 0.983565, (1, 12): 0.982707, (1, 13): 0.981849,
        (1, 14): 0.980991, (1, 15): 1.02326, (1, 19): 1.00008,
        (2, 3): 0.982361, (2, 4): 1.00796, (2, 15): 1.03227,
        (2, 19): 0.942596, (3, 4): 1.00851, (3, 10): 0.910183,
        (3, 11): 0.895362, (3, 12): 0.881152, (3, 13): 0.86752,
        (3, 14): 0.854406, (3, 19): 1.00779, (4, 5): 0.986893,
        (4, 15): 1.02034, (4, 19): 0.999969, (10, 19): 0.96813,
        (11, 19): 0.96287, (12, 19): 0.957828, (13, 19): 0.952441,
        (14, 19): 0.948338,
    }.items():
        kij[i][j] = value

    for (i, j), value in {
        (1, 3): 0.807653, (1, 15): 1.95731, (2, 3): 0.982746,
        (3, 4): 0.370296, (3, 18): 1.67309,
    }.items():
        gij[i][j] = value

    ideal_rows = {
        1: (29.83843397, -15999.69151, 4.00088, 0.76315, 0.0046, 8.74432, -4.46921),
        2: (17.56770785, -2801.729072, 3.50031, 0.13732, -0.1466, 0.90066, 0.0),
        3: (20.65844696, -4902.171516, 3.50002, 2.04452, -1.06044, 2.03366, 0.01393),
        4: (36.73005938, -23639.65301, 4.00263, 4.33939, 1.23722, 13.1974, -6.01989),
        5: (44.70909619, -31236.63551, 4.02939, 6.60569, 3.197, 19.1921, -8.37267),
        6: (34.30180349, -38525.50276, 4.06714, 8.97575, 5.25156, 25.1423, 16.1388),
        7: (36.53237783, -38957.80933, 4.33944, 9.44893, 6.89406, 24.4618, 14.7824),
        8: (43.17218626, -51198.30946, 4.0, 11.7618, 20.1101, 33.1688, 0.0),
        9: (42.67837089, -45215.83, 4.0, 8.95043, 21.836, 33.4032, 0.0),
        10: (46.99717188, -52746.83318, 4.0, 11.6977, 26.8142, 38.6164, 0.0),
        11: (52.07631631, -57104.81056, 4.0, 13.7266, 30.4707, 43.5561, 0.0),
        12: (57.25830934, -60546.76385, 4.0, 15.6865, 33.8029, 48.1731, 0.0),
        13: (62.09646901, -66600.12837, 4.0, 18.0241, 38.1235, 53.3415, 0.0),
        14: (65.93909154, -74131.45483, 4.0, 21.0069, 43.4931, 58.3657, 0.0),
        15: (13.07520288, -5836.943696, 2.47906, 0.95806, 0.45444, 1.56039, -1.3756),
        16: (16.8017173, -2318.32269, 3.50146, 1.07558, 1.01334, 0.0, 0.0),
        17: (17.45786899, -2635.244116, 3.50055, 1.02865, 0.00493, 0.0, 0.0),
        18: (21.57882705, -7766.733078, 4.00392, 0.01059, 0.98763, 3.06904, 0.0),
        19: (21.5830944, -6069.035869, 4.0, 3.11942, 1.00243, 0.0, 0.0),
        20: (10.04639507, -745.375, 2.5, 0.0, 0.0, 0.0, 0.0),
        21: (10.04639507, -745.375, 2.5, 0.0, 0.0, 0.0, 0.0),
    }
    for i, values in ideal_rows.items():
        for j, value in enumerate(values, start=1):
            n0i[i][j] = value

    th0_rows = {
        1: (820.659, 178.41, 1062.82, 1090.53),
        2: (662.738, 680.562, 1740.06, 0.0),
        3: (919.306, 865.07, 483.553, 341.109),
        4: (559.314, 223.284, 1031.38, 1071.29),
        5: (479.856, 200.893, 955.312, 1027.29),
        6: (438.27, 198.018, 1905.02, 893.765),
        7: (468.27, 183.636, 1914.1, 903.185),
        8: (292.503, 910.237, 1919.37, 0.0),
        9: (178.67, 840.538, 1774.25, 0.0),
        10: (182.326, 859.207, 1826.59, 0.0),
        11: (169.789, 836.195, 1760.46, 0.0),
        12: (158.922, 815.064, 1693.07, 0.0),
        13: (156.854, 814.882, 1693.79, 0.0),
        14: (164.947, 836.264, 1750.24, 0.0),
        15: (228.734, 326.843, 1651.71, 1671.69),
        16: (2235.71, 1116.69, 0.0, 0.0),
        17: (1550.45, 704.525, 0.0, 0.0),
        18: (268.795, 1141.41, 2507.37, 0.0),
        19: (1833.63, 847.181, 0.0, 0.0),
        20: (0.0, 0.0, 0.0, 0.0),
        21: (0.0, 0.0, 0.0, 0.0),
    }
    for i, values in th0_rows.items():
        for j, value in zip(range(4, 8), values):
            th0i[i][j] = value

    for i in range(1, MAX_FLDS + 1):
        ki25[i] = ki[i] ** 2.5
        ei25[i] = ei[i] ** 2.5

    for i in range(1, MAX_FLDS + 1):
        for j in range(i, MAX_FLDS + 1):
            for n in range(1, 19):
                bsnij = 1.0
                if gn[n] == 1:
                    bsnij = gij[i][j] * (gi[i] + gi[j]) / 2.0
                if qn[n] == 1:
                    bsnij *= qi[i] * qi[j]
                if fn[n] == 1:
                    bsnij *= fi[i] * fi[j]
                if sn[n] == 1:
                    bsnij *= si[i] * si[j]
                if wn[n] == 1:
                    bsnij *= wi[i] * wi[j]
                bsnij2[i][j][n] = (
                    an[n]
                    * (eij[i][j] * math.sqrt(ei[i] * ei[j])) ** un[n]
                    * (ki[i] * ki[j]) ** 1.5
                    * bsnij
                )
            kij5[i][j] = (kij[i][j] ** 5 - 1.0) * ki25[i] * ki25[j]
            uij5[i][j] = (uij[i][j] ** 5 - 1.0) * ei25[i] * ei25[j]
            gij5[i][j] = (gij[i][j] - 1.0) * (gi[i] + gi[j]) / 2.0

    d0 = 101.325 / R_DETAIL / 298.15
    for i in range(1, MAX_FLDS + 1):
        n0i[i][3] -= 1.0
        n0i[i][1] -= math.log(d0)

    return DetailState(
        an=an,
        un=un,
        fn=fn,
        gn=gn,
        qn=qn,
        bn=bn,
        kn=kn,
        bsnij2=bsnij2,
        bs=bs,
        csn=csn,
        fi=fi,
        gi=gi,
        qi=qi,
        ki25=ki25,
        ei25=ei25,
        kij5=kij5,
        uij5=uij5,
        gij5=gij5,
        tun=tun,
        n0i=n0i,
        th0i=th0i,
        mmi=mmi,
        xold=xold,
        dpdd_save=0.0,
        told=0.0,
        k3=0.0,
    )


STATE = _build_state()


def composition_vector_from_mapping(composition: dict[str, float]) -> list[float]:
    vector = [0.0] * (NC_DETAIL + 1)
    interne_werte = {name: 0.0 for name in COMPONENTS}
    for key, value in composition.items():
        if key not in KOMPONENTEN_ALIASE:
            raise ValueError(f"Unbekannte Komponente im JSON: {key}")
        interne_werte[KOMPONENTEN_ALIASE[key]] += float(value)
    for idx, name in enumerate(COMPONENTS, start=1):
        vector[idx] = interne_werte[name]
    return vector


def normalisiere_stoffmengenanteile(x: list[float]) -> tuple[list[float], float]:
    total = sum(x[1 : NC_DETAIL + 1])
    if total <= 0.0:
        raise ValueError("Die Summe der Stoffmengenanteile muss groesser als 0 sein.")
    normiert = x[:]
    for i in range(1, NC_DETAIL + 1):
        normiert[i] = x[i] / total
    return normiert, total


def stoffmengenanteile_als_deutsches_mapping(x: list[float]) -> dict[str, float]:
    return {
        deutscher_name: x[idx]
        for idx, deutscher_name in enumerate(DEUTSCHE_KOMPONENTEN, start=1)
        if abs(x[idx]) > 0.0
    }


def molar_mass_detail(x: list[float]) -> float:
    return sum(x[i] * STATE.mmi[i] for i in range(1, NC_DETAIL + 1))


def x_terms_detail(x: list[float]) -> None:
    changed = any(abs(x[i] - STATE.xold[i]) > 1e-11 for i in range(1, NC_DETAIL + 1))
    if not changed:
        return

    for i in range(1, NC_DETAIL + 1):
        STATE.xold[i] = x[i]

    k3 = 0.0
    u = 0.0
    g = 0.0
    q = 0.0
    f = 0.0
    STATE.bs = [0.0] * 19

    for i in range(1, NC_DETAIL + 1):
        if x[i] > 0.0:
            xi2 = x[i] ** 2
            k3 += x[i] * STATE.ki25[i]
            u += x[i] * STATE.ei25[i]
            g += x[i] * STATE.gi[i]
            q += x[i] * STATE.qi[i]
            f += xi2 * STATE.fi[i]
            for n in range(1, 19):
                STATE.bs[n] += xi2 * STATE.bsnij2[i][i][n]

    k3 = k3 ** 2
    u = u ** 2

    for i in range(1, NC_DETAIL):
        if x[i] > 0.0:
            for j in range(i + 1, NC_DETAIL + 1):
                if x[j] > 0.0:
                    xij = 2.0 * x[i] * x[j]
                    k3 += xij * STATE.kij5[i][j]
                    u += xij * STATE.uij5[i][j]
                    g += xij * STATE.gij5[i][j]
                    for n in range(1, 19):
                        STATE.bs[n] += xij * STATE.bsnij2[i][j][n]

    STATE.k3 = k3 ** 0.6
    u = u ** 0.2
    q2 = q ** 2

    for n in range(13, 59):
        value = STATE.an[n] * (u ** STATE.un[n])
        if STATE.gn[n] == 1:
            value *= g
        if STATE.qn[n] == 1:
            value *= q2
        if STATE.fn[n] == 1:
            value *= f
        STATE.csn[n] = value


def alpha0_detail(t: float, d: float, x: list[float]) -> list[float]:
    a0 = [0.0, 0.0, 0.0]
    log_d = math.log(d if d > EPSILON else EPSILON)
    log_t = math.log(t)

    for i in range(1, NC_DETAIL + 1):
        if x[i] <= 0.0:
            continue
        log_xd = log_d + math.log(x[i])
        sum_hyp0 = 0.0
        sum_hyp1 = 0.0
        sum_hyp2 = 0.0

        for j in range(4, 8):
            th = STATE.th0i[i][j]
            if th <= 0.0:
                continue
            th0t = th / t
            ep = math.exp(th0t)
            em = 1.0 / ep
            hsn = (ep - em) / 2.0
            hcn = (ep + em) / 2.0
            n0 = STATE.n0i[i][j]
            if j in (4, 6):
                log_hyp = math.log(abs(hsn))
                sum_hyp0 += n0 * log_hyp
                sum_hyp1 += n0 * (log_hyp - th0t * hcn / hsn)
                sum_hyp2 += n0 * (th0t / hsn) ** 2
            else:
                log_hyp = math.log(abs(hcn))
                sum_hyp0 -= n0 * log_hyp
                sum_hyp1 -= n0 * (log_hyp - th0t * hsn / hcn)
                sum_hyp2 += n0 * (th0t / hcn) ** 2

        a0[0] += x[i] * (
            log_xd
            + STATE.n0i[i][1]
            + STATE.n0i[i][2] / t
            - STATE.n0i[i][3] * log_t
            + sum_hyp0
        )
        a0[1] += x[i] * (
            log_xd
            + STATE.n0i[i][1]
            - STATE.n0i[i][3] * (1.0 + log_t)
            + sum_hyp1
        )
        a0[2] -= x[i] * (STATE.n0i[i][3] + sum_hyp2)

    a0[0] *= R_DETAIL * t
    a0[1] *= R_DETAIL
    a0[2] *= R_DETAIL
    return a0


def alphar_detail(itau: int, idel: int, t: float, d: float) -> list[list[float]]:
    del idel
    ar = [[0.0 for _ in range(4)] for _ in range(4)]
    if abs(t - STATE.told) > 1e-11:
        for n in range(1, 59):
            STATE.tun[n] = t ** (-STATE.un[n])
    STATE.told = t

    dred = STATE.k3 * d
    dknn = [0.0] * 10
    dknn[0] = 1.0
    for n in range(1, 10):
        dknn[n] = dred * dknn[n - 1]

    expn = [1.0] * 5
    for n in range(1, 5):
        expn[n] = math.exp(-dknn[n])

    rt = R_DETAIL * t

    coef_d1 = [0.0] * (N_TERMS + 1)
    coef_d2 = [0.0] * (N_TERMS + 1)
    coef_d3 = [0.0] * (N_TERMS + 1)
    coef_t1 = [0.0] * (N_TERMS + 1)
    coef_t2 = [0.0] * (N_TERMS + 1)
    sum_b = [0.0] * (N_TERMS + 1)
    sum_0 = [0.0] * (N_TERMS + 1)

    for n in range(1, 59):
        coef_t1[n] = R_DETAIL * (STATE.un[n] - 1.0)
        coef_t2[n] = coef_t1[n] * STATE.un[n]

        if n <= 18:
            value = STATE.bs[n] * d
            if n >= 13:
                value -= STATE.csn[n] * dred
            sum_b[n] = value * STATE.tun[n]

        if n >= 13:
            sum_0[n] = (
                STATE.csn[n]
                * dknn[STATE.bn[n]]
                * STATE.tun[n]
                * expn[STATE.kn[n]]
            )
            bkd = float(STATE.bn[n]) - float(STATE.kn[n]) * dknn[STATE.kn[n]]
            ckd = float(STATE.kn[n] ** 2) * dknn[STATE.kn[n]]
            coef_d1[n] = bkd
            coef_d2[n] = bkd * (bkd - 1.0) - ckd
            coef_d3[n] = (bkd - 2.0) * coef_d2[n] + ckd * (
                1.0 - float(STATE.kn[n]) - 2.0 * bkd
            )

    for n in range(1, 59):
        s0 = sum_0[n] + sum_b[n]
        s1 = sum_0[n] * coef_d1[n] + sum_b[n]
        s2 = sum_0[n] * coef_d2[n]
        s3 = sum_0[n] * coef_d3[n]
        ar[0][0] += rt * s0
        ar[0][1] += rt * s1
        ar[0][2] += rt * s2
        ar[0][3] += rt * s3
        if itau > 0:
            ar[1][0] -= coef_t1[n] * s0
            ar[1][1] -= coef_t1[n] * s1
            ar[2][0] += coef_t2[n] * s0

    return ar


def pressure_detail(t: float, d: float, x: list[float]) -> tuple[float, float]:
    x_terms_detail(x)
    ar = alphar_detail(0, 2, t, d)
    z = 1.0 + ar[0][1] / R_DETAIL / t
    p = d * R_DETAIL * t * z
    STATE.dpdd_save = R_DETAIL * t + 2.0 * ar[0][1] + ar[0][2]
    return p, z


def density_detail(
    t: float, p: float, x: list[float], initial_density: float | None = None
) -> tuple[float, int, str]:
    if abs(p) < EPSILON:
        return 0.0, 0, ""

    d = initial_density if initial_density is not None else p / R_DETAIL / t
    if d <= -EPSILON:
        d = abs(d)
    elif d <= 0.0:
        d = p / R_DETAIL / t

    plog = math.log(p)
    vlog = -math.log(d)
    tolerance = 1e-7

    for _ in range(20):
        if vlog < -7.0 or vlog > 100.0:
            break
        d = math.exp(-vlog)
        p2, _ = pressure_detail(t, d, x)
        if STATE.dpdd_save < EPSILON or p2 < EPSILON:
            vlog += 0.1
            continue
        dpdlv = -d * STATE.dpdd_save
        vdiff = (math.log(p2) - plog) * p2 / dpdlv
        vlog -= vdiff
        if abs(vdiff) < tolerance:
            return math.exp(-vlog), 0, ""

    return (
        p / R_DETAIL / t,
        1,
        "Calculation failed to converge in DETAIL method, ideal gas density returned.",
    )


def properties_detail(t: float, d: float, x: list[float]) -> dict[str, float]:
    mm = molar_mass_detail(x)
    x_terms_detail(x)
    a0 = alpha0_detail(t, d, x)
    ar = alphar_detail(2, 3, t, d)

    rt = R_DETAIL * t
    z = 1.0 + ar[0][1] / rt
    p = d * rt * z
    dpdd = rt + 2.0 * ar[0][1] + ar[0][2]
    dpdt = d * R_DETAIL + d * ar[1][1]
    a = a0[0] + ar[0][0]
    s = -a0[1] - ar[1][0]
    u = a + t * s
    cv = -(a0[2] + ar[2][0])

    if d > EPSILON:
        h = u + p / d
        g = a + p / d
        cp = cv + t * (dpdt / d) ** 2 / dpdd
        d2pdd2 = (2.0 * ar[0][1] + 4.0 * ar[0][2] + ar[0][3]) / d
        jt = (t / d * dpdt / dpdd - 1.0) / cp / d
    else:
        h = u + rt
        g = a + rt
        cp = cv + R_DETAIL
        d2pdd2 = 0.0
        jt = 1e20

    w2 = 1000.0 * cp / cv * dpdd / mm
    w = 0.0 if w2 < 0.0 else math.sqrt(w2)
    kappa = w * w * mm / (rt * 1000.0 * z)

    return {
        "molar_mass_g_per_mol": mm,
        "molar_density_mol_per_l": d,
        "pressure_kpa": p,
        "compressibility_factor_z": z,
        "dP_dRho_kpa_per_mol_l": dpdd,
        "d2P_dRho2_kpa_per_mol_l2": d2pdd2,
        "d2P_dT_dRho_kpa_per_mol_l_k": 0.0,
        "dP_dT_kpa_per_k": dpdt,
        "internal_energy_j_per_mol": u,
        "enthalpy_j_per_mol": h,
        "entropy_j_per_mol_k": s,
        "cv_j_per_mol_k": cv,
        "cp_j_per_mol_k": cp,
        "speed_of_sound_m_per_s": w,
        "gibbs_energy_j_per_mol": g,
        "joule_thomson_k_per_kpa": jt,
        "isentropic_exponent": kappa,
    }


def calculate_from_inputs(
    temperature_k: float,
    pressure_kpa: float,
    composition: dict[str, float],
    initial_density_mol_per_l: float | None = None,
) -> dict[str, float | int | str | dict[str, float]]:
    x_roh = composition_vector_from_mapping(composition)
    x, summe_vor_normierung = normalisiere_stoffmengenanteile(x_roh)
    density, ierr, herr = density_detail(
        temperature_k, pressure_kpa, x, initial_density_mol_per_l
    )
    result = properties_detail(temperature_k, density, x)
    result = {
        "eingabedaten": {
            "temperatur_C": temperature_k - 273.15,
            "druck_bar": pressure_kpa / 100.0,
            "intern_verwendete_temperatur_K": temperature_k,
            "intern_verwendeter_druck_kPa": pressure_kpa,
            "startwert_molare_dichte_mol_pro_l": initial_density_mol_per_l,
            "stoffmengenanteile_vor_normierung": composition,
            "summe_vor_normierung": summe_vor_normierung,
            "stoffmengenanteile_normiert": stoffmengenanteile_als_deutsches_mapping(x),
        },
        "ergebnis": {
            "molare_masse_g_pro_mol": result["molar_mass_g_per_mol"],
            "molare_dichte_mol_pro_l": result["molar_density_mol_per_l"],
            "druck_kPa": result["pressure_kpa"],
            "k_zahl": result["compressibility_factor_z"],
            "dP_dRho_kPa_pro_mol_l": result["dP_dRho_kpa_per_mol_l"],
            "d2P_dRho2_kPa_pro_mol_l2": result["d2P_dRho2_kpa_per_mol_l2"],
            "d2P_dT_dRho_kPa_pro_mol_l_K": result["d2P_dT_dRho_kpa_per_mol_l_k"],
            "dP_dT_kPa_pro_K": result["dP_dT_kpa_per_k"],
            "innere_energie_J_pro_mol": result["internal_energy_j_per_mol"],
            "enthalpie_J_pro_mol": result["enthalpy_j_per_mol"],
            "entropie_J_pro_mol_K": result["entropy_j_per_mol_k"],
            "cv_J_pro_mol_K": result["cv_j_per_mol_k"],
            "cp_J_pro_mol_K": result["cp_j_per_mol_k"],
            "schallgeschwindigkeit_m_pro_s": result["speed_of_sound_m_per_s"],
            "gibbs_energie_J_pro_mol": result["gibbs_energy_j_per_mol"],
            "joule_thomson_K_pro_kPa": result["joule_thomson_k_per_kpa"],
            "isentropenexponent": result["isentropic_exponent"],
        },
        "status": {
            "fehlercode": ierr,
            "meldung": herr,
        },
    }
    return result
