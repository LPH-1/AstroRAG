"""
Star Chart Generation Server v2
Beautiful star charts with proper astronomical rendering

GET/POST /v1/starchart?ra=83.82&dec=-5.39&fov=15
Port: 8082
"""

import csv
import io
import math
import os
import sys

import numpy as np
from flask import Flask, request, jsonify, send_file

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STAR_CATALOG = os.path.join(SCRIPT_DIR, "hyg_v38.csv")
DSO_CATALOG = os.path.join(SCRIPT_DIR, "database_files", "NGC.csv")

app = Flask(__name__)

PLANET_MARKERS = [
    {"name": "Mars", "ra": 312.2, "dec": -22.4, "mag": -1.2, "color": "#ff6b58"},
    {"name": "Pluto", "ra": 304.8, "dec": -21.2, "mag": 14.4, "color": "#d8c48a"},
    {"name": "Jupiter", "ra": 44.0, "dec": 15.0, "mag": -2.1, "color": "#f2d59b"},
    {"name": "Saturn", "ra": 358.0, "dec": -3.0, "mag": 0.8, "color": "#d6c58e"},
    {"name": "Venus", "ra": 116.0, "dec": 22.0, "mag": -4.0, "color": "#fff0c8"},
]

# ---------------------------------------------------------------------------
# Full constellation stick figures (HIP IDs)
# Covers all 88 constellations with standard IAU stick figures
# ---------------------------------------------------------------------------
CONSTELLATION_LINES = {
    "And": [(677, 2912), (2912, 3092), (3092, 9640), (9640, 677)],
    "Ant": [(51172, 51579)],
    "Aps": [(72370, 80047), (80047, 81852), (81852, 72370)],
    "Aqr": [(109074, 106278), (106278, 102618), (102618, 110003),
            (110003, 109139), (109139, 109074)],
    "Aql": [(97649, 98036), (98036, 97278), (97278, 97649), (97649, 99473)],
    "Ara": [(85727, 85258), (85258, 88714), (88714, 85727)],
    "Ari": [(8832, 8903), (8903, 9884), (9884, 8832)],
    "Aur": [(24608, 28360), (28360, 23015), (23015, 23767), (23767, 24608),
            (24608, 25428)],
    "Boo": [(69673, 72105), (72105, 71075), (71075, 69427), (69427, 69673),
            (69673, 74666), (74666, 73555)],
    "Cae": [(21770, 21861), (21861, 23595)],
    "Cam": [(17959, 22783), (22783, 23040), (23040, 17959)],
    "Cnc": [(44066, 42911), (42911, 42556), (42556, 43103), (43103, 44066)],
    "CVn": [(63125, 61317), (61317, 63125)],
    "CMa": [(32349, 34444), (34444, 34045), (34045, 32349), (32349, 30324),
            (30324, 31592)],
    "CMi": [(37279, 36188), (36188, 37279)],
    "Cap": [(100064, 102485), (102485, 105881), (105881, 106985),
            (106985, 100064), (100064, 102978)],
    "Car": [(30438, 45238), (45238, 42913), (42913, 41037), (41037, 39953),
            (39953, 30438)],
    "Cas": [(3179, 746), (746, 4427), (4427, 8886), (8886, 3179), (3179, 6686)],
    "Cen": [(71683, 68702), (68702, 68933), (68933, 67457), (67457, 71683),
            (68702, 66657), (66657, 65936), (65936, 61932), (61932, 61084),
            (61084, 59196), (59196, 71683)],
    "Cep": [(105199, 106032), (106032, 107259), (107259, 109492),
            (109492, 105199), (105199, 110538)],
    "Cet": [(14135, 12706), (12706, 10826), (10826, 8645), (8645, 14135),
            (14135, 13954)],
    "Cha": [(40702, 42279)],
    "Cir": [(71908, 74824), (74824, 75323)],
    "Col": [(26634, 28328), (28328, 27628), (27628, 26634)],
    "Com": [(60742, 60525), (60525, 60172), (60172, 60742)],
    "CrA": [(83262, 83574), (83574, 83943), (83943, 83262)],
    "CrB": [(76267, 77512), (77512, 76952), (76952, 76127), (76127, 76267)],
    "Crv": [(60965, 61359), (61359, 59803), (59803, 60189), (60189, 60965)],
    "Crt": [(53740, 54682), (54682, 55282), (55282, 55687), (55687, 53740)],
    "Cru": [(60718, 61084), (61084, 62434), (62434, 60260), (60260, 60718)],
    "Cyg": [(102098, 100453), (100453, 97165), (97165, 102488),
            (102488, 107315), (107315, 102098), (102098, 99848),
            (99848, 95947), (95947, 94779)],
    "Del": [(101769, 101421), (101421, 101958), (101958, 102532),
            (102532, 101769)],
    "Dor": [(21281, 19893), (19893, 23693), (23693, 21281)],
    "Dra": [(56211, 59774), (59774, 61281), (61281, 68756), (68756, 75458),
            (75458, 78527), (78527, 83895), (83895, 89937), (89937, 94376),
            (94376, 97433), (97433, 101076), (101076, 107625),
            (107625, 109387), (109387, 56211)],
    "Equ": [(104987, 104521), (104521, 103569)],
    "Eri": [(7588, 17378), (17378, 19587), (19587, 23875), (23875, 7588),
            (7588, 13701)],
    "For": [(13147, 13686), (13686, 14879)],
    "Gem": [(37826, 36850), (36850, 35550), (35550, 32207), (32207, 37826),
            (36850, 36962)],
    "Gru": [(112122, 113638), (113638, 110997), (110997, 109268),
            (109268, 112122)],
    "Her": [(84345, 83207), (83207, 81693), (81693, 80816), (80816, 84345),
            (84345, 86414), (86414, 87808), (87808, 84345)],
    "Hor": [(12484, 12225), (12225, 13884)],
    "Hya": [(46390, 43813), (43813, 42313), (42313, 64962), (64962, 46390),
            (46390, 47431), (47431, 48356)],
    "Hyi": [(2021, 9236), (9236, 11001), (11001, 2021)],
    "Ind": [(102333, 101772), (101772, 103227), (103227, 102333)],
    "Lac": [(109937, 110538), (110538, 111104), (111104, 109937),
            (109937, 109754)],
    "Leo": [(49669, 49583), (49583, 50583), (50583, 54872), (54872, 57632),
            (57632, 49669), (49669, 46750), (46750, 47908)],
    "LMi": [(51200, 46952), (46952, 45614)],
    "Lep": [(25985, 27072), (27072, 25606), (25606, 24305), (24305, 25985)],
    "Lib": [(72622, 73714), (73714, 74785), (74785, 72622), (72622, 71795)],
    "Lup": [(74395, 75141), (75141, 76297), (76297, 77634), (77634, 74395),
            (74395, 71860)],
    "Lyn": [(45860, 45652), (45652, 41075), (41075, 36145)],
    "Lyr": [(91262, 91973), (91973, 91971), (91971, 92420), (92420, 91262)],
    "Men": [(29271, 25918), (25918, 27199)],
    "Mic": [(102831, 103738), (103738, 104019)],
    "Mon": [(29651, 30867), (30867, 31964), (31964, 32578), (32578, 29651),
            (29651, 31236)],
    "Mus": [(59929, 61199), (61199, 61585), (61585, 62322), (62322, 59929)],
    "Nor": [(78639, 79790), (79790, 80000)],
    "Oct": [(70638, 72308), (72308, 76952)],
    "Oph": [(86032, 87108), (87108, 86742), (86742, 84012), (84012, 86032),
            (86032, 83000), (83000, 81377), (81377, 80883)],
    "Ori": [(24436, 27366), (27366, 26727), (26727, 26311), (26311, 25336),
            (25336, 25930), (24436, 24608), (24608, 25930), (27989, 26727),
            (27989, 25930)],
    "Pav": [(100751, 102395), (102395, 105858), (105858, 102805),
            (102805, 99240), (99240, 100751)],
    "Peg": [(113963, 112440), (112440, 113881), (113881, 112029),
            (112029, 113963), (113963, 107315), (107315, 106278),
            (113963, 109410)],
    "Per": [(13268, 14328), (14328, 14576), (14576, 15863), (15863, 13268),
            (13268, 18532), (18532, 19343)],
    "Phe": [(2081, 5348), (5348, 6869), (6869, 7657), (7657, 2081)],
    "Pic": [(27321, 27504), (27504, 26779)],
    "Psc": [(9487, 8198), (8198, 5742), (5742, 7097), (7097, 9487),
            (9487, 11569), (11569, 118268), (118268, 9487)],
    "PsA": [(113368, 111954), (111954, 112948), (112948, 113368),
            (113368, 109422)],
    "Pup": [(39429, 37229), (37229, 38070), (38070, 38170), (38170, 39953),
            (39953, 39429)],
    "Pyx": [(39429, 42828), (42828, 43409), (43409, 39429)],
    "Ret": [(19780, 18597), (18597, 17440), (17440, 19780)],
    "Sge": [(97365, 96757), (96757, 98337), (98337, 97365)],
    "Sgr": [(90185, 89931), (89931, 88635), (88635, 92041), (92041, 92855),
            (92855, 90185), (90185, 95168), (95168, 98066), (98066, 90185),
            (92855, 94141), (88635, 89642)],
    "Sco": [(80763, 78820), (78820, 78401), (78401, 78265), (78265, 80112),
            (80112, 80763), (80763, 82396), (82396, 84143), (84143, 85670),
            (85670, 86670), (80763, 81266), (78401, 82514)],
    "Scl": [(115102, 116231), (116231, 4577)],
    "Sct": [(90568, 91117), (91117, 91726), (91726, 90568)],
    "Ser": [(77070, 77622), (77622, 77233), (77233, 76276), (76276, 77070),
            (77070, 75177), (86263, 86565), (86565, 85829), (85829, 84039),
            (84039, 86263), (86263, 77622)],
    "Sex": [(49019, 48437), (48437, 48519)],
    "Tau": [(21421, 25428), (25428, 26451), (26451, 21421), (21421, 20205),
            (20205, 20894), (20894, 21421)],
    "Tel": [(89112, 90422), (90422, 90887), (90887, 89112)],
    "Tri": [(10064, 8796), (8796, 10670), (10670, 10064)],
    "TrA": [(77952, 76440), (76440, 82273), (82273, 77952)],
    "Tuc": [(110130, 2484), (2484, 1599), (1599, 118322), (118322, 110130)],
    "UMa": [(54061, 53910), (53910, 58001), (58001, 59774), (59774, 62956),
            (62956, 65378), (65378, 67301), (67301, 62956), (54061, 50801),
            (50801, 46733), (58001, 54539), (67301, 69483)],
    "UMi": [(11767, 82080), (82080, 79822), (79822, 77055), (77055, 75097),
            (75097, 72607), (72607, 70090), (70090, 11767)],
    "Vel": [(42913, 44816), (44816, 45941), (45941, 46651), (46651, 50191),
            (50191, 51362), (51362, 52727), (52727, 39953)],
    "Vir": [(65474, 66249), (66249, 61941), (61941, 63090), (63090, 65474),
            (65474, 57757), (57757, 60129), (60129, 57757)],
    "Vol": [(39794, 41312), (41312, 44382), (44382, 39794)],
    "Vul": [(97805, 98353), (98353, 98920), (98920, 97805)],
}

# Bright star names (HIP -> common name)
STAR_NAMES = {
    32349: "天狼星 Sirius", 30438: "老人星 Canopus", 71683: "南门二 Rigil Kent",
    69673: "大角星 Arcturus", 91262: "织女星 Vega", 24608: "五车二 Capella",
    24436: "参宿七 Rigel", 37279: "南河三 Procyon", 7588: "水委一 Achernar",
    27989: "参宿四 Betelgeuse", 97649: "河鼓二 Altair", 60718: "十字架三 Mimosa",
    21421: "毕宿五 Aldebaran", 65474: "角宿一 Spica", 36850: "北河三 Pollux",
    113368: "北落师门 Fomalhaut", 102098: "天津四 Deneb", 26727: "参宿一 Alnitak",
    26311: "参宿二 Alnilam", 25336: "参宿三 Mintaka", 27366: "参宿五 Bellatrix",
    80763: "心宿二 Antares", 37826: "北河二 Castor", 34045: "弧矢七 Adhara",
    34444: "弧矢一 Wezen", 30324: "军市一 Mirzam", 49669: "轩辕十四 Regulus",
    54061: "天枢 Dubhe", 53910: "天璇 Merak", 58001: "天玑 Phecda",
    62956: "天权 Megrez", 67301: "玉衡 Alioth", 65378: "开阳 Mizar",
    59774: "摇光 Alkaid", 11767: "北极星 Polaris", 3179: "王良一 Schedar",
    746: "策星 Caph", 4427: "阁道三 Cih", 8886: "阁道二 Ruchbah",
    76267: "贯索四 Alphecca", 84345: "天市左垣一 Rasalgethi",
    86032: "天市左垣九 Rasalhague", 90185: "斗宿四 Nunki",
    46390: "星宿一 Alphard", 62434: "十字架一 Acrux", 60260: "十字架二 Gacrux",
    61084: "南十字座δ Decrux", 105199: "天钩五 Alderamin",
    110130: "鸟喙一", 2484: "鸟喙四", 112122: "鹤一 Alnair",
    100453: "天津一 Sadr", 97165: "天津九 Gienah", 102488: "天津增九 Albireo",
    101769: "瓠瓜四 Rotanev", 101421: "败瓜一 Sualocin",
    13268: "天船三 Mirfak", 14576: "大陵五 Algol", 15863: "天大将军一",
    95501: "牛郎星 (Altair)", 84012: "侯 Rasalhague",
}

# ---------------------------------------------------------------------------
# Star catalog
# ---------------------------------------------------------------------------
stars = {}
deep_sky_objects = []

def load_stars():
    global stars
    hyg_csv = os.path.join(SCRIPT_DIR, "hyg_v38.csv")
    if os.path.exists(hyg_csv):
        with open(hyg_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    hip_str = row.get("hip", "").strip()
                    if not hip_str:
                        continue
                    hip = int(hip_str)
                    mag = float(row["mag"])
                    ra = hyg_ra_to_degrees(row["ra"])
                    dec = float(row["dec"])
                    sp = row.get("spect", "").strip()
                    proper = row.get("proper", "").strip()
                    con = row.get("con", "").strip()
                    stars[hip] = {
                        "ra": ra, "dec": dec, "mag": mag,
                        "sp_type": sp, "proper": proper, "con": con,
                    }
                    count += 1
                    if count % 20000 == 0:
                        print(f"  Loaded {count} stars...")
                except (ValueError, KeyError):
                    continue
            print(f"Loaded {count} stars from HYG catalog")
    elif os.path.exists(STAR_CATALOG):
        # Fallback to old Hipparcos CSV
        with open(STAR_CATALOG, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    hip = int(row["HIP"])
                    mag = float(row["Vmag"])
                    stars[hip] = {
                        "ra": float(row["RA"]),
                        "dec": float(row["Dec"]),
                        "mag": mag,
                        "sp_type": row.get("SpType", "").strip(),
                        "proper": "",
                        "con": "",
                    }
                    count += 1
                except (ValueError, KeyError):
                    continue
            print(f"Loaded {count} stars from Hipparcos catalog")
    else:
        print("No star catalog found. Using built-in bright stars.")
        _load_builtin()
    load_deep_sky_objects()


def parse_hms_to_degrees(value):
    parts = [float(part) for part in value.strip().replace(" ", ":").split(":") if part]
    if len(parts) != 3:
        raise ValueError(f"Invalid HMS coordinate: {value}")
    hours, minutes, seconds = parts
    return (hours + minutes / 60.0 + seconds / 3600.0) * 15.0


def hyg_ra_to_degrees(value):
    """HYG stores right ascension in decimal hours, while rendering uses degrees."""
    return (float(value) * 15.0) % 360.0


def parse_dms_to_degrees(value):
    raw = value.strip().replace(" ", ":")
    sign = -1.0 if raw.startswith("-") else 1.0
    raw = raw.lstrip("+-")
    parts = [float(part) for part in raw.split(":") if part]
    if len(parts) != 3:
        raise ValueError(f"Invalid DMS coordinate: {value}")
    degrees, minutes, seconds = parts
    return sign * (degrees + minutes / 60.0 + seconds / 3600.0)


def load_deep_sky_objects():
    global deep_sky_objects
    if deep_sky_objects or not os.path.exists(DSO_CATALOG):
        return

    with open(DSO_CATALOG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                mag_text = row.get("V-Mag") or row.get("B-Mag") or ""
                mag = float(mag_text) if mag_text else 99.0
                if mag > 13.0:
                    continue
                deep_sky_objects.append({
                    "name": row.get("Name", "").strip(),
                    "type": row.get("Type", "").strip(),
                    "ra": parse_hms_to_degrees(row.get("RA", "")),
                    "dec": parse_dms_to_degrees(row.get("Dec", "")),
                    "mag": mag,
                    "major_axis": float(row["MajAx"]) if row.get("MajAx") else 0.0,
                    "minor_axis": float(row["MinAx"]) if row.get("MinAx") else 0.0,
                })
            except (ValueError, KeyError):
                continue
    print(f"Loaded {len(deep_sky_objects)} deep-sky objects from OpenNGC")

def _load_builtin():
    """Built-in 100 brightest stars as fallback"""
    global stars
    bright = [
        (32349, 101.287155, -16.716116, -1.44, "A1V"),
        (30438, 95.987958, -52.695661, -0.62, "F0Ib"),
        (71683, 219.920406, -60.838623, -0.27, "G2Ib"),
        (69673, 213.915495, 19.178753, -0.05, "K1.5III"),
        (91262, 279.234735, 38.783689, 0.03, "A0Va"),
        (24608, 79.172146, 45.997987, 0.08, "G8III"),
        (24436, 78.634468, -8.201640, 0.18, "B8Ia"),
        (37279, 114.825508, 5.224993, 0.40, "F5IV-V"),
        (7588, 24.428494, -57.236753, 0.45, "B3V"),
        (27989, 88.792939, 7.407064, 0.45, "M1.5Iab"),
        (97649, 297.695827, 8.867319, 0.76, "A7IV-V"),
        (60718, 186.649563, -63.099093, 0.77, "B0.5III"),
        (21421, 69.079668, -29.068166, 0.87, "K5III"),
        (65474, 201.298249, -11.161305, 0.98, "B1V"),
        (36850, 113.649981, 31.888284, 1.16, "K0III"),
        (113368, 344.412714, -29.622224, 1.17, "A3V"),
        (102098, 310.357980, 45.280342, 1.25, "A2Ia"),
        (25336, 81.282840, 6.349766, 1.69, "B0.5Iae"),
        (26727, 85.189687, -1.942574, 1.64, "B0III"),
        (26311, 83.858467, -5.909929, 2.75, "O9.5V"),
        (25930, 83.001667, -0.299103, 3.33, "O9.7Ib"),
        (27366, 86.939121, -9.669649, 2.06, "B1V"),
        (80763, 247.351908, -26.432004, 1.06, "M1.5Iab"),
        (37826, 116.328957, 28.026339, 1.58, "A1V"),
        (34444, 107.097849, -26.393200, 1.50, "B1II-III"),
        (34045, 105.939617, -16.107952, 1.98, "B2II"),
        (30324, 95.674943, -17.955917, 1.83, "B0.5III"),
        (49669, 152.093230, 11.967210, 1.36, "B7V"),
        (62434, 186.861211, -63.099437, 0.76, "B0.5IV"),
        (60260, 186.039928, -62.969640, 1.59, "M3.5III"),
        (61084, 187.466063, -62.993639, 2.79, "B2IV"),
        (54061, 165.460317, 49.313433, 1.81, "K0III"),
        (53910, 165.031969, 47.186894, 2.34, "A1V"),
        (100453, 305.557099, 40.256680, 2.87, "F8Ib"),
        (97165, 296.243906, 45.130778, 3.21, "A0III"),
        (90185, 276.042895, -34.384556, 2.70, "B9.5III"),
        (3179, 10.126789, 56.537335, 2.27, "B0.5IV"),
        (746, 2.294520, 59.149780, 2.24, "B2IV"),
        (4427, 14.177215, 60.716675, 2.46, "K0IIIa"),
        (8886, 28.598802, 63.670098, 2.64, "A3V"),
        (78820, 241.359306, -21.172578, 2.56, "B1V"),
        (78401, 240.030361, -22.371895, 2.29, "B1III"),
        (82396, 252.540903, -34.293065, 2.29, "B0.5Ia"),
        (84143, 257.196597, -33.549389, 1.86, "F1II"),
        (85670, 262.608397, -37.296435, 1.62, "B1.5III"),
        (11767, 37.946281, 89.264109, 1.97, "F7Ib-II"),
        (76267, 233.672200, 26.714569, 2.22, "A0V"),
        (84345, 258.758170, 14.390423, 3.35, "M5III"),
        (86032, 263.733344, 12.560223, 2.08, "A5III"),
        (35550, 109.668316, 16.505674, 3.50, "M3III"),
        (50583, 154.992731, 19.841490, 2.14, "A0V"),
        (54872, 168.559739, 15.429641, 2.56, "A2V"),
        (57632, 177.265640, 14.572062, 2.14, "B3V"),
        (46390, 141.896847, -8.658601, 1.99, "K3II-III"),
        (86263, 264.412720, 12.951530, 3.65, "B9V"),
        (110130, 311.553179, -57.033749, 2.87, "K3III"),
        (112122, 330.947425, -46.962020, 1.73, "B6V"),
        (113963, 346.189943, 15.205471, 2.48, "B9.5III"),
        (112440, 340.164558, 10.831792, 3.41, "K2III"),
        (113881, 345.479888, 9.034637, 3.52, "A2V"),
        (112029, 339.104660, 7.115722, 4.12, "A0V"),
        (14135, 45.569804, -0.486296, 3.47, "K0III"),
        (12706, 40.828654, 3.355823, 2.53, "K2III"),
        (10826, 34.836546, -8.371797, 2.04, "B9.5III"),
        (8645, 27.860311, -10.334975, 3.45, "F5V"),
        (109074, 328.481905, -9.893750, 3.77, "K1III"),
        (106278, 323.495520, -0.821117, 3.27, "G2Ib"),
        (102618, 316.486756, -4.233944, 3.73, "A0V"),
        (109139, 328.671635, -7.583746, 2.95, "A2V"),
        (110003, 331.531448, -0.319498, 3.85, "A2V"),
    ]
    for hip, ra, dec, mag, sp in bright:
        stars[hip] = {"ra": ra, "dec": dec, "mag": mag, "sp_type": sp}
    print(f"Built-in catalog: {len(stars)} stars")

# ---------------------------------------------------------------------------
# Projection math
# ---------------------------------------------------------------------------
def radec_to_xy(ra, dec, ra0, dec0):
    """Gnomonic projection centered at (ra0, dec0)"""
    ra_r = math.radians(ra)
    dec_r = math.radians(dec)
    ra0_r = math.radians(ra0)
    dec0_r = math.radians(dec0)

    cos_d = math.cos(dec_r)
    sin_d = math.sin(dec_r)
    cos_d0 = math.cos(dec0_r)
    sin_d0 = math.sin(dec0_r)
    cos_dra = math.cos(ra_r - ra0_r)
    sin_dra = math.sin(ra_r - ra0_r)

    denom = sin_d0 * sin_d + cos_d0 * cos_d * cos_dra
    if denom <= 0.05:
        return None, None

    x = cos_d * sin_dra / denom
    y = (cos_d0 * sin_d - sin_d0 * cos_d * cos_dra) / denom
    return x, y

# ---------------------------------------------------------------------------
# Star color from spectral type (approximate B-V to RGB)
# ---------------------------------------------------------------------------
def star_color(sp_type):
    sp = sp_type.strip() if sp_type else ""
    if not sp:
        return (1.0, 1.0, 1.0)
    t = sp[0]
    sub = sp[1:2]
    if t == 'O' or t == 'W':
        return (0.6, 0.7, 1.0)
    elif t == 'B':
        return (0.75, 0.82, 1.0)
    elif t == 'A':
        return (0.92, 0.95, 1.0)
    elif t == 'F':
        return (1.0, 0.97, 0.88)
    elif t == 'G':
        return (1.0, 0.94, 0.72)
    elif t == 'K':
        return (1.0, 0.82, 0.58)
    elif t == 'M':
        if sub in ('5','6','7','8','9'):
            return (1.0, 0.5, 0.35)
        return (1.0, 0.65, 0.45)
    elif t == 'C' or t == 'R' or t == 'N':
        return (1.0, 0.4, 0.3)
    return (0.9, 0.9, 1.0)

# ---------------------------------------------------------------------------
# Professional chart styling helpers
# ---------------------------------------------------------------------------
def magnitude_to_marker(mag):
    """Map visual magnitude to matplotlib scatter area in points^2."""
    return max(3.0, min(72.0, 60.0 * (10 ** (-0.22 * (mag + 1.0)))))


def magnitude_to_alpha(mag, mag_limit):
    if mag <= 1.5:
        return 1.0
    span = max(1.0, mag_limit - 1.5)
    return max(0.28, 1.0 - ((mag - 1.5) / span) * 0.55)


def chart_scale(fov):
    half_fov = fov / 2.0
    return math.tan(math.radians(half_fov)) if fov < 80 else 1.5


def format_ra_label(ra_degrees):
    total_minutes = int(round(((ra_degrees % 360.0) / 15.0) * 60.0)) % (24 * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}h{minutes:02d}m"


def format_dec_label(dec_degrees):
    sign = "+" if dec_degrees >= 0 else "-"
    total_minutes = int(round(abs(dec_degrees) * 60.0))
    degrees = total_minutes // 60
    minutes = total_minutes % 60
    return f"{sign}{degrees:02d}\N{DEGREE SIGN}{minutes:02d}'"


def angular_distance(ra1, dec1, ra2, dec2):
    ra1_r = math.radians(ra1)
    ra2_r = math.radians(ra2)
    dec1_r = math.radians(dec1)
    dec2_r = math.radians(dec2)
    cos_sep = (
        math.sin(dec1_r) * math.sin(dec2_r)
        + math.cos(dec1_r) * math.cos(dec2_r) * math.cos(ra1_r - ra2_r)
    )
    cos_sep = max(-1.0, min(1.0, cos_sep))
    return math.degrees(math.acos(cos_sep))


def star_label(hip, star):
    return STAR_NAMES.get(hip) or star.get("proper") or f"HIP{hip}"


def choose_label_stars(star_map, ra0, dec0, fov, max_labels=24):
    candidates = []
    for hip, star in star_map.items():
        mag = star.get("mag", 99.0)
        if mag > 3.2 and hip not in STAR_NAMES and not star.get("proper"):
            continue
        if angular_distance(star["ra"], star["dec"], ra0, dec0) > fov * 0.62:
            continue
        score = mag
        if hip in STAR_NAMES or star.get("proper"):
            score -= 1.8
        candidates.append((score, hip, star))

    labels = []
    occupied = []
    min_sep = max(0.45, fov / 28.0)
    for _score, hip, star in sorted(candidates, key=lambda item: item[0]):
        too_close = any(
            angular_distance(star["ra"], star["dec"], other["ra"], other["dec"]) < min_sep
            for other in occupied
        )
        if too_close:
            continue
        labels.append({"hip": hip, "name": star_label(hip, star), "star": star})
        occupied.append(star)
        if len(labels) >= max_labels:
            break
    return labels


def iter_grid_values(center, fov, step):
    start = math.floor((center - fov * 0.6) / step) * step
    stop = math.ceil((center + fov * 0.6) / step) * step
    value = start
    while value <= stop + step * 0.5:
        yield value
        value += step


def grid_step(fov):
    if fov <= 8:
        return 1.0
    if fov <= 18:
        return 2.0
    if fov <= 35:
        return 5.0
    return 10.0


def dso_marker(dso_type):
    if dso_type in ("G", "GPair", "GGroup"):
        return "ellipse"
    if dso_type in ("OC", "OCl"):
        return "open_cluster"
    if dso_type in ("Gb", "GCl"):
        return "globular"
    if dso_type in ("Neb", "HII", "PN", "SNR"):
        return "nebula"
    return "box"


def resolve_chart_style(style_name):
    atlas = {
        "background_top": "#0d1525",
        "background_bottom": "#060912",
        "vignette_alpha": 0.30,
        "grid_alpha": 0.50,
        "show_grid": True,
        "star_alpha_floor": 0.32,
        "bright_star_glow": 4.5,
        "constellation_line": "#7d9bc0",
        "constellation_line_alpha": 0.42,
        "constellation_fill": "#557fd4",
        "constellation_fill_alpha": 0.0,
        "label_color": "#dce6f5",
        "show_mobile_chrome": False,
        "show_planets": False,
        "texture_stars": 0,
    }
    if style_name != "mobile":
        return atlas

    mobile = atlas.copy()
    mobile.update({
        "background_top": "#1a2a44",
        "background_bottom": "#0a0f1a",
        "vignette_alpha": 0.52,
        "grid_alpha": 0.0,
        "show_grid": False,
        "star_alpha_floor": 0.42,
        "bright_star_glow": 7.0,
        "constellation_line": "#b8d0ff",
        "constellation_line_alpha": 0.78,
        "constellation_fill": "#5885ff",
        "constellation_fill_alpha": 0.28,
        "label_color": "#e8efff",
        "show_mobile_chrome": True,
        "show_planets": True,
        "texture_stars": 800,
    })
    return mobile


def hex_to_rgb(hex_color):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def convex_hull(points):
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(origin, a, b):
        return ((a[0] - origin[0]) * (b[1] - origin[1])
                - (a[1] - origin[1]) * (b[0] - origin[0]))

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def visible_planet_markers(ra0, dec0, fov):
    visible = []
    for planet in PLANET_MARKERS:
        if angular_distance(planet["ra"], planet["dec"], ra0, dec0) <= fov * 0.72:
            visible.append(planet)
    return visible


def draw_sky_background(ax, x_limit, y_min, y_max, style):
    top = np.array(hex_to_rgb(style["background_top"]))
    bottom = np.array(hex_to_rgb(style["background_bottom"]))
    height = 540
    width = 360
    vertical = np.linspace(0.0, 1.0, height)[:, None]
    gradient = bottom * (1.0 - vertical) + top * vertical
    image = np.repeat(gradient[:, None, :], width, axis=1)

    yy, xx = np.mgrid[-1:1:complex(height), -1:1:complex(width)]
    diagonal = np.exp(-((xx * 0.7 + yy * 0.35 - 0.62) ** 2) / 0.035)
    image[:, :, 2] = np.clip(image[:, :, 2] + diagonal * 0.14, 0, 1)
    image[:, :, 1] = np.clip(image[:, :, 1] + diagonal * 0.08, 0, 1)

    vignette = np.clip((xx ** 2 + yy ** 2) ** 0.72, 0, 1)
    image *= 1.0 - vignette[:, :, None] * style["vignette_alpha"]

    ax.imshow(image, extent=(-x_limit, x_limit, y_min, y_max),
              origin="lower", zorder=-20, aspect="auto")


def draw_texture_stars(ax, x_limit, y_min, y_max, count):
    if count <= 0:
        return
    rng = np.random.default_rng(42)
    xs = rng.uniform(-x_limit, x_limit, count)
    ys = rng.uniform(y_min, y_max, count)
    sizes = rng.uniform(0.6, 3.2, count)
    alphas = rng.uniform(0.12, 0.46, count)
    colors = np.column_stack([
        np.full(count, 0.82),
        np.full(count, 0.9),
        np.ones(count),
        alphas,
    ])
    ax.scatter(xs, ys, s=sizes, c=colors, linewidths=0, zorder=-2)


def draw_mobile_chrome(ax):
    ax.text(0.88, 0.985, "STAR ATLAS", transform=ax.transAxes, color="#c8d8f0",
            fontsize=7, ha="center", va="top", zorder=80, fontweight="bold",
            fontfamily="monospace")
    controls = [("H", 0.70), ("Z", 0.80), ("M", 0.90)]
    for label, x in controls:
        ax.text(x, 0.048, label, transform=ax.transAxes, color="#e8f0ff",
                fontsize=9, ha="center", va="center", zorder=82,
                bbox=dict(boxstyle="circle,pad=0.22", fc="#142238",
                          ec="#5a7aaa", lw=1.0, alpha=0.92))


# ---------------------------------------------------------------------------
# Chart rendering
# ---------------------------------------------------------------------------
def render_chart(ra0, dec0, fov, width, height, mag_limit, show_dso=True, style_name="mobile"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Ellipse

    dpi = 150
    fig_w = width / dpi
    fig_h = height / dpi
    style = resolve_chart_style(style_name)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi, facecolor=style["background_bottom"])
    ax.set_facecolor(style["background_bottom"])
    if style["show_mobile_chrome"]:
        fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
    else:
        fig.subplots_adjust(left=0.055, right=0.945, top=0.92, bottom=0.12)

    scale = chart_scale(fov)
    if style["show_mobile_chrome"]:
        y_min = -scale * (height / width)
        y_max = scale * (height / width)
    else:
        y_min = -scale * 1.12
        y_max = scale
    sorted_stars = sorted(stars.items(), key=lambda item: item[1]["mag"], reverse=True)
    draw_sky_background(ax, scale, y_min, y_max, style)
    draw_texture_stars(ax, scale, y_min, y_max, style["texture_stars"])

    # Coordinate grid, with RA/Dec labels around the plotting frame.
    step = grid_step(fov)
    grid_color = "#2a3f5a"
    label_color = "#99b0cc"
    if style["show_grid"]:
        for dec_line in iter_grid_values(dec0, fov, step):
            if dec_line < -89 or dec_line > 89:
                continue
            pts = []
            for ra in np.linspace(ra0 - fov * 1.35, ra0 + fov * 1.35, 160):
                x, y = radec_to_xy(ra % 360, dec_line, ra0, dec0)
                if x is not None and abs(x) < scale * 1.02 and abs(y) < scale * 1.02:
                    pts.append((x, y))
            if len(pts) > 1:
                xs, ys = zip(*pts)
                ax.plot(xs, ys, color=grid_color, linewidth=0.45,
                        alpha=style["grid_alpha"], zorder=0)
                ax.text(-scale * 0.985, ys[0], format_dec_label(dec_line),
                        color=label_color, fontsize=6, alpha=0.8,
                        ha="left", va="bottom", zorder=30)

        for ra_line in iter_grid_values(ra0, fov, step):
            pts = []
            for dec in np.linspace(dec0 - fov * 1.35, dec0 + fov * 1.35, 160):
                if dec < -89 or dec > 89:
                    continue
                x, y = radec_to_xy(ra_line % 360, dec, ra0, dec0)
                if x is not None and abs(x) < scale * 1.02 and abs(y) < scale * 1.02:
                    pts.append((x, y))
            if len(pts) > 1:
                xs, ys = zip(*pts)
                ax.plot(xs, ys, color=grid_color, linewidth=0.45,
                        alpha=style["grid_alpha"], zorder=0)
                ax.text(xs[-1], -scale * 0.985, format_ra_label(ra_line),
                        color=label_color, fontsize=6, alpha=0.8,
                        ha="right", va="bottom", zorder=30)

    # Constellation stick figures sit beneath the stars, like atlas overlays.
    for const, lines in CONSTELLATION_LINES.items():
        visible_points = []
        for hip1, hip2 in lines:
            if hip1 not in stars or hip2 not in stars:
                continue
            s1, s2 = stars[hip1], stars[hip2]
            x1, y1 = radec_to_xy(s1["ra"], s1["dec"], ra0, dec0)
            x2, y2 = radec_to_xy(s2["ra"], s2["dec"], ra0, dec0)
            if x1 is None or x2 is None:
                continue
            x_out = abs(x1) > scale * 1.08 and abs(x2) > scale * 1.08
            y_out = ((y1 < y_min * 1.08 and y2 < y_min * 1.08)
                     or (y1 > y_max * 1.08 and y2 > y_max * 1.08))
            if x_out or y_out:
                continue
            if style["show_mobile_chrome"]:
                ax.plot([x1, x2], [y1, y2], color="#274573", linewidth=3.0,
                        alpha=0.45, zorder=2)
            ax.plot([x1, x2], [y1, y2], color=style["constellation_line"],
                    linewidth=1.05 if style["show_mobile_chrome"] else 0.65,
                    alpha=style["constellation_line_alpha"], zorder=3)
            if abs(x1) < scale and y_min < y1 < y_max:
                visible_points.append((x1, y1))
            if abs(x2) < scale and y_min < y2 < y_max:
                visible_points.append((x2, y2))
        if visible_points:
            hull = convex_hull(visible_points)
            if len(hull) >= 3 and style["constellation_fill_alpha"] > 0:
                hx, hy = zip(*hull)
                ax.fill(hx, hy, color=style["constellation_fill"],
                        alpha=style["constellation_fill_alpha"], zorder=1)
                ax.plot(list(hx) + [hx[0]], list(hy) + [hy[0]],
                        color="#7fa7ff", linewidth=0.8, alpha=0.34, zorder=2)
            cx = sum(p[0] for p in visible_points) / len(visible_points)
            cy = sum(p[1] for p in visible_points) / len(visible_points)
            if abs(cx) < scale * 0.88 and y_min * 0.88 < cy < y_max * 0.88:
                ax.text(cx, cy, const, color="#7185a1", fontsize=6,
                        alpha=0.34, ha="center", va="center", zorder=3)

    plotted = 0
    # Rough bounding-box pre-filter avoids expensive projection for distant stars
    cos_ref = math.cos(math.radians(max(abs(dec0), 1e-6)))
    dra_limit = fov * 0.78 / cos_ref
    ddec_limit = fov * 0.78

    for hip, star in sorted_stars:
        if star["mag"] > mag_limit:
            continue

        # Fast bounding-box skip
        dra = abs(star["ra"] - ra0)
        if dra > 180.0:
            dra = 360.0 - dra
        if dra * cos_ref > dra_limit or abs(star["dec"] - dec0) > ddec_limit:
            continue

        x, y = radec_to_xy(star["ra"], star["dec"], ra0, dec0)
        if x is None:
            continue
        if abs(x) > scale * 1.05 or y < y_min * 1.05 or y > y_max * 1.05:
            continue

        mag = star["mag"]
        marker_size = magnitude_to_marker(mag)
        alpha = max(style["star_alpha_floor"], magnitude_to_alpha(mag, mag_limit))
        color = star_color(star.get("sp_type", ""))

        if mag < 2.2:
            ax.scatter([x], [y], s=marker_size * style["bright_star_glow"],
                       color=[color], alpha=0.16, linewidths=0, zorder=4)
        ax.scatter([x], [y], s=marker_size, color=[color], alpha=alpha,
                   edgecolors="#f8fbff" if mag < 1.5 else "none",
                   linewidths=0.18 if mag < 1.5 else 0, zorder=10)

        plotted += 1

    if show_dso:
        load_deep_sky_objects()
        dso_plotted = 0
        for dso in sorted(deep_sky_objects, key=lambda item: item["mag"]):
            if dso["mag"] > 12.5 or angular_distance(dso["ra"], dso["dec"], ra0, dec0) > fov * 0.62:
                continue
            x, y = radec_to_xy(dso["ra"], dso["dec"], ra0, dec0)
            if x is None or abs(x) > scale * 0.98 or y < y_min * 0.98 or y > y_max * 0.98:
                continue
            symbol = dso_marker(dso["type"])
            color = "#78d5c6"
            if symbol == "ellipse":
                size = max(0.018 * scale, min(0.06 * scale, dso.get("major_axis", 0.0) * scale / (fov * 18.0)))
                ax.add_patch(Ellipse((x, y), width=size * 1.7, height=size,
                                     edgecolor=color, facecolor="none",
                                     linewidth=0.55, alpha=0.72, zorder=16))
            elif symbol == "open_cluster":
                ax.scatter([x], [y], s=24, marker="o", facecolors="none",
                           edgecolors=color, linewidths=0.65, alpha=0.72, zorder=16)
            elif symbol == "globular":
                ax.scatter([x], [y], s=22, marker="o", facecolors="none",
                           edgecolors=color, linewidths=0.75, alpha=0.8, zorder=16)
                ax.scatter([x], [y], s=8, marker="+", color=color,
                           linewidths=0.65, alpha=0.8, zorder=17)
            elif symbol == "nebula":
                ax.scatter([x], [y], s=26, marker="s", facecolors="none",
                           edgecolors=color, linewidths=0.6, alpha=0.62, zorder=16)
            else:
                ax.scatter([x], [y], s=18, marker="D", facecolors="none",
                           edgecolors=color, linewidths=0.55, alpha=0.62, zorder=16)
            if dso_plotted < 18 and dso["mag"] <= 10.5:
                ax.annotate(dso["name"], (x, y), color=color, fontsize=5.5,
                            alpha=0.76, xytext=(3, -5), textcoords="offset points",
                            zorder=24)
            dso_plotted += 1

    if style["show_planets"]:
        for planet in visible_planet_markers(ra0, dec0, fov):
            x, y = radec_to_xy(planet["ra"], planet["dec"], ra0, dec0)
            if x is None or abs(x) > scale * 0.96 or y < y_min * 0.96 or y > y_max * 0.96:
                continue
            ax.scatter([x], [y], s=72, color=planet["color"], alpha=0.16,
                       linewidths=0, zorder=28)
            ax.scatter([x], [y], s=22, color=planet["color"], alpha=0.96,
                       edgecolors="#ffffff", linewidths=0.35, zorder=29)
            ax.annotate(planet["name"], (x, y), color=planet["color"], fontsize=6.5,
                        alpha=0.96, xytext=(5, 3), textcoords="offset points",
                        zorder=30)

    # Sparse labels keep the chart readable.
    for item in choose_label_stars(stars, ra0, dec0, fov):
        star = item["star"]
        x, y = radec_to_xy(star["ra"], star["dec"], ra0, dec0)
        if x is None or abs(x) > scale * 0.88 or y < y_min * 0.88 or y > y_max * 0.88:
            continue
        ax.annotate(item["name"], (x, y), color=style["label_color"], fontsize=6.2,
                    alpha=0.86, xytext=(4, 3), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.12", fc=style["background_bottom"],
                              ec="none", alpha=0.32 if style["show_mobile_chrome"] else 0.55),
                    zorder=25)

    if not style["show_mobile_chrome"]:
        title = f"RA {format_ra_label(ra0)}  Dec {format_dec_label(dec0)}"
        subtitle = f"FOV {fov:.1f}\N{DEGREE SIGN}  limit mag {mag_limit:.1f}  stars {plotted}"
        ax.text(0.0, 1.035, title, transform=ax.transAxes, color="#f2f6ff",
                fontsize=11, fontweight="bold", ha="center", va="bottom")
        ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, color="#95a7bf",
                fontsize=7, ha="center", va="bottom")

    if not style["show_mobile_chrome"]:
        # North/east marker. In sky charts, east appears left when viewed from Earth.
        ax.annotate("", xy=(0.92, 0.18), xytext=(0.92, 0.08), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="-|>", color="#a9bad1", lw=0.8))
        ax.text(0.92, 0.195, "N", transform=ax.transAxes, color="#a9bad1",
                fontsize=7, ha="center", va="bottom")
        ax.annotate("", xy=(0.80, 0.08), xytext=(0.92, 0.08), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="-|>", color="#a9bad1", lw=0.8))
        ax.text(0.785, 0.08, "E", transform=ax.transAxes, color="#a9bad1",
                fontsize=7, ha="right", va="center")

    if not style["show_mobile_chrome"]:
        legend_mags = [0, 2, 4, 6]
        legend_x = -scale * 0.94
        legend_y = -scale * 1.105
        for idx, mag in enumerate(legend_mags):
            lx = legend_x + idx * scale * 0.12
            ax.scatter([lx], [legend_y], s=magnitude_to_marker(mag),
                       color="#f3f6ff", alpha=magnitude_to_alpha(mag, mag_limit),
                       linewidths=0, clip_on=False, zorder=40)
            ax.text(lx, legend_y - scale * 0.045, f"{mag}", color="#8fa3bc",
                    fontsize=6, ha="center", va="top", clip_on=False)
        ax.text(legend_x - scale * 0.03, legend_y, "mag", color="#8fa3bc",
                fontsize=6, ha="right", va="center", clip_on=False)
    else:
        draw_mobile_chrome(ax)

    ax.set_xlim(-scale, scale)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(not style["show_mobile_chrome"])
        spine.set_edgecolor("#32435c")
        spine.set_linewidth(0.8)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor(),
                edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf, plotted

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok", "stars": len(stars), "constellations": len(CONSTELLATION_LINES)})

@app.route("/v1/starchart", methods=["GET", "POST"])
def starchart():
    if request.method == "POST":
        data = request.get_json(force=True)
    else:
        data = request.args

    ra = float(data.get("ra", 83.82)) % 360
    dec = max(-89, min(89, float(data.get("dec", -5.39))))
    fov = max(2, min(90, float(data.get("fov", 15))))
    width = max(200, min(2000, int(data.get("width", 800))))
    height = max(200, min(2000, int(data.get("height", 600))))
    mag_limit = float(data.get("mag_limit", 7.5))
    show_dso = str(data.get("show_dso", "true")).lower() not in ("0", "false", "no")
    style = str(data.get("style", "mobile")).lower()

    try:
        buf, plotted = render_chart(ra, dec, fov, width, height, mag_limit,
                                    show_dso=show_dso, style_name=style)
        resp = send_file(buf, mimetype="image/png")
        resp.headers["X-Star-Count"] = str(plotted)
        resp.headers["X-Cache-Control"] = "public, max-age=3600"
        return resp
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  Star Chart Server v2")
    print("=" * 50)
    load_stars()
    print(f"  Stars: {len(stars)}")
    print(f"  Constellations: {len(CONSTELLATION_LINES)}")
    print(f"  Port: 8082")
    print("=" * 50)
    app.run(host="127.0.0.1", port=8082)
