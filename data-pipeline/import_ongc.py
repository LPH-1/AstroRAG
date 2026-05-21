"""
Import OpenNGC catalog from local CSV files into ChromaDB
NGC.csv + addendum.csv => 13,000+ NGC/IC objects
Generates natural Chinese descriptions for better retrieval quality
"""

import csv
import os
import sys
import time
import requests
from sentence_transformers import SentenceTransformer

CHROMA_BASE = os.environ.get("CHROMA_BASE", "http://localhost:8000")
CHROMA_API = f"{CHROMA_BASE}/api/v2/tenants/default_tenant/databases/default_database"
COLLECTION_NAME = "astronomy_knowledge"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
NGC_CSV = os.path.join(SCRIPT_DIR, "database_files", "NGC.csv")
ADDENDUM_CSV = os.path.join(SCRIPT_DIR, "database_files", "addendum.csv")

# OpenNGC type codes -> Chinese
TYPE_MAP = {
    "G": "星系", "Sb": "旋涡星系", "Sc": "旋涡星系", "Sbc": "旋涡星系",
    "E": "椭圆星系", "S0": "透镜星系", "Sa": "旋涡星系", "Sd": "旋涡星系",
    "SBa": "棒旋星系", "SBb": "棒旋星系", "SBc": "棒旋星系", "SBd": "棒旋星系",
    "Irr": "不规则星系", "Amorph": "不规则星系", "Ring": "环状星系",
    "Pec": "特殊星系", "Pair": "星系对", "Triple": "星系三重",
    "OC": "疏散星团", "OCl": "疏散星团", "GlC": "球状星团", "GCl": "球状星团",
    "Cl+N": "星团连带星云",
    "EmN": "发射星云", "RfN": "反射星云", "DrkN": "暗星云",
    "HII": "电离氢区", "PN": "行星状星云", "SNR": "超新星遗迹",
    "Neb": "星云", "Neb?": "疑似星云",
    "Star": "恒星", "**": "恒星", "*": "恒星", "D*": "双星",
    "***": "三星系统", "V*": "变星", "C*": "碳星",
    "Ast": "星群", "*Ass": "星协",
    "NonEx": "历史记录错误", "NF": "未确认天体",
    "Unknown": "深空天体", "": "深空天体",
}

# IAU 3-letter constellation codes to Chinese
CONST_MAP = {
    "And": "仙女座", "Ant": "唧筒座", "Aps": "天燕座", "Aqr": "宝瓶座",
    "Aql": "天鹰座", "Ara": "天坛座", "Ari": "白羊座", "Aur": "御夫座",
    "Boo": "牧夫座", "Cae": "雕具座", "Cam": "鹿豹座", "Cnc": "巨蟹座",
    "CVn": "猎犬座", "CMa": "大犬座", "CMi": "小犬座", "Cap": "摩羯座",
    "Car": "船底座", "Cas": "仙后座", "Cen": "半人马座", "Cep": "仙王座",
    "Cet": "鲸鱼座", "Cha": "蝘蜓座", "Cir": "圆规座", "Col": "天鸽座",
    "Com": "后发座", "CrA": "南冕座", "CrB": "北冕座", "Crv": "乌鸦座",
    "Crt": "巨爵座", "Cru": "南十字座", "Cyg": "天鹅座", "Del": "海豚座",
    "Dor": "剑鱼座", "Dra": "天龙座", "Equ": "小马座", "Eri": "波江座",
    "For": "天炉座", "Gem": "双子座", "Gru": "天鹤座", "Her": "武仙座",
    "Hor": "时钟座", "Hya": "长蛇座", "Hyi": "水蛇座", "Ind": "印第安座",
    "Lac": "蝎虎座", "Leo": "狮子座", "LMi": "小狮座", "Lep": "天兔座",
    "Lib": "天秤座", "Lup": "豺狼座", "Lyn": "天猫座", "Lyr": "天琴座",
    "Men": "山案座", "Mic": "显微镜座", "Mon": "麒麟座", "Mus": "苍蝇座",
    "Nor": "矩尺座", "Oct": "南极座", "Oph": "蛇夫座", "Ori": "猎户座",
    "Pav": "孔雀座", "Peg": "飞马座", "Per": "英仙座", "Phe": "凤凰座",
    "Pic": "绘架座", "Psc": "双鱼座", "PsA": "南鱼座", "Pup": "船尾座",
    "Pyx": "罗盘座", "Ret": "网罟座", "Sge": "天箭座", "Sgr": "人马座",
    "Sco": "天蝎座", "Scl": "玉夫座", "Sct": "盾牌座", "Ser": "巨蛇座",
    "Sex": "六分仪座", "Tau": "金牛座", "Tel": "望远镜座", "Tri": "三角座",
    "TrA": "南三角座", "Tuc": "杜鹃座", "UMa": "大熊座", "UMi": "小熊座",
    "Vel": "船帆座", "Vir": "室女座", "Vol": "飞鱼座", "Vul": "狐狸座",
}

def load_model():
    for root, dirs, files in os.walk(MODELS_DIR):
        if "config.json" in files and "tokenizer.json" in files:
            print(f"Found model at: {root}")
            m = SentenceTransformer(root)
            print(f"Model loaded, dim={m.get_sentence_embedding_dimension()}")
            return m
    print("Model not found locally, downloading from ModelScope...")
    from modelscope import snapshot_download
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = snapshot_download("BAAI/bge-m3", cache_dir=MODELS_DIR)
    return SentenceTransformer(path)

def get_collection_id():
    r = requests.get(f"{CHROMA_API}/collections", timeout=10)
    r.raise_for_status()
    for c in r.json():
        if c["name"] == COLLECTION_NAME:
            return c["id"]
    return None

def build_description(row):
    """Build a natural Chinese description for an NGC/IC object"""
    name = row.get("Name", "").strip()
    obj_type_code = row.get("Type", "").strip()
    type_cn = TYPE_MAP.get(obj_type_code, obj_type_code if obj_type_code else "深空天体")
    const_code = row.get("Const", "").strip()
    const_cn = CONST_MAP.get(const_code, const_code)
    common_names = row.get("Common names", "").strip()
    identifiers = row.get("Identifiers", "").strip()
    ra = row.get("RA", "").strip()
    dec = row.get("Dec", "").strip()
    vmag = row.get("V-Mag", "").strip()
    bmag = row.get("B-Mag", "").strip()
    mag = vmag or bmag
    maj = row.get("MajAx", "").strip()
    min_ax = row.get("MinAx", "").strip()
    hubble = row.get("Hubble", "").strip()
    rv = row.get("RadVel", "").strip()
    redshift = row.get("Redshift", "").strip()

    # Build sentences
    sentences = []

    # Opening: name, common names, type, constellation
    intro = name
    if common_names:
        intro += f"（又名{common_names}）"
    intro += f"是位于{const_cn}的{type_cn}"
    if mag:
        try:
            intro += f"，视星等约{float(mag):.1f}等"
        except ValueError:
            pass
    sentences.append(intro)

    # Size
    if maj:
        size_str = maj
        if min_ax and min_ax != maj:
            size_str += f"乘{min_ax}"
        sentences.append(f"角大小约{size_str}角分")

    # Coordinates
    if ra and dec:
        sentences.append(f"天球坐标为赤经{ra}、赤纬{dec}")

    # Hubble type for galaxies
    if hubble and hubble.strip():
        sentences.append(f"哈勃分类为{hubble}")

    # Redshift / velocity
    if rv:
        try:
            rv_val = int(float(rv))
            sentences.append(f"视向速度约{rv_val}公里每秒")
        except ValueError:
            pass

    if redshift:
        try:
            z_val = float(redshift)
            if z_val > 0:
                sentences.append(f"红移值{z_val:.6f}")
        except ValueError:
            pass

    # Other identifiers
    if identifiers:
        sentences.append(f"其他编号包括{identifiers}")

    return "。".join(s for s in sentences if s) + "。"

def parse_csv(filepath):
    """Parse an OpenNGC CSV file and return list of document dicts"""
    documents = []
    skipped = 0

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            name = row.get("Name", "").strip()
            if not name:
                skipped += 1
                continue

            obj_type_code = row.get("Type", "").strip()
            type_cn = TYPE_MAP.get(obj_type_code, obj_type_code if obj_type_code else "深空天体")
            common_names = row.get("Common names", "").strip()
            const_code = row.get("Const", "").strip()
            const_cn = CONST_MAP.get(const_code, const_code)

            doc_text = build_description(row)

            documents.append({
                "id": name,
                "text": doc_text,
                "metadata": {
                    "category": "ngc_full",
                    "object_id": name,
                    "name": name,
                    "name_en": common_names if common_names else "",
                    "type": type_cn,
                    "constellation": const_cn,
                }
            })

    return documents, skipped

def main():
    print("=" * 60)
    print("OpenNGC Full Catalog Import (v2 - Natural Language)")
    print("=" * 60)

    # Check ChromaDB
    try:
        r = requests.get(f"{CHROMA_BASE}/api/v2/heartbeat", timeout=10)
        print("ChromaDB connected")
    except:
        print("ERROR: ChromaDB not available!")
        sys.exit(1)

    cid = get_collection_id()
    if not cid:
        print("ERROR: Collection not found! Run embed.py first.")
        sys.exit(1)
    print(f"Collection ID: {cid}")

    # Remove old NGC entries first
    print("\nRemoving old ngc_full entries...")
    try:
        requests.post(
            f"{CHROMA_API}/collections/{cid}/delete",
            json={"where": {"category": "ngc_full"}},
            timeout=60,
        )
        print("  Old entries removed")
    except Exception as e:
        print(f"  Warning: {e}")

    # Parse CSV files
    all_docs = []

    for filepath, label in [(NGC_CSV, "NGC.csv"), (ADDENDUM_CSV, "addendum.csv")]:
        if not os.path.exists(filepath):
            print(f"\nWARNING: {label} not found, skipping")
            continue
        print(f"\nParsing {label} ...")
        docs, skipped = parse_csv(filepath)
        print(f"  {len(docs)} objects ({skipped} skipped)")
        all_docs.extend(docs)

    print(f"\nTotal: {len(all_docs)} objects to import")
    print("Sample descriptions:")
    for d in all_docs[:3]:
        print(f"  ---")
        print(f"  {d['text'][:200]}...")

    # Load model
    model = load_model()

    # Embed and import in batches
    batch_size = 50
    total = 0

    print(f"\nImporting {len(all_docs)} objects...")
    for batch_start in range(0, len(all_docs), batch_size):
        batch = all_docs[batch_start:batch_start + batch_size]

        ids = [f"ngc_{d['id']}" for d in batch]
        texts = [d["text"] for d in batch]
        metadatas = [d["metadata"] for d in batch]

        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

        try:
            r = requests.post(
                f"{CHROMA_API}/collections/{cid}/add",
                json={
                    "ids": ids,
                    "documents": texts,
                    "metadatas": metadatas,
                    "embeddings": embeddings,
                },
                timeout=120,
            )
            r.raise_for_status()
            total += len(batch)
            pct = total * 100 // len(all_docs)
            bar = "#" * (pct // 2) + "-" * (50 - pct // 2)
            print(f"  [{bar}] {total}/{len(all_docs)} ({pct}%)", end="\r")
        except Exception as e:
            print(f"\n  Error at batch {batch_start}: {e}")
            continue

        time.sleep(0.05)

    print(f"\n\nDone! Imported {total} NGC/IC objects")
    print("Embedding server needs restart to pick up new data")

if __name__ == "__main__":
    main()
