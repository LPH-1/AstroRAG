"""
天文知识向量化 & 写入 ChromaDB (本地 embedding)

使用方法:
1. 确保 ChromaDB 已启动: chroma run --path ./chroma_data
2. 首次运行自动从 ModelScope 下载 bge-m3 (~2GB)
3. 运行: python embed.py
"""

import json
import os
import sys
import time

import requests

CHROMA_BASE = os.environ.get("CHROMA_BASE", "http://localhost:8000")
CHROMA_API = f"{CHROMA_BASE}/api/v2/tenants/default_tenant/databases/default_database"
COLLECTION_NAME = "astronomy_knowledge"
MODEL_ID = "BAAI/bge-m3"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
DATA_FILE = os.path.join(SCRIPT_DIR, "astronomy_data.json")


def find_or_download_model():
    """查找或下载 bge-m3 模型"""
    for root, dirs, files in os.walk(MODELS_DIR):
        if "config.json" in files and "tokenizer.json" in files:
            print(f"找到本地模型: {root}")
            return root

    print(f"本地未找到模型 {MODEL_ID}，从 ModelScope 下载...")
    print("(约 2GB，仅首次需要)")
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("错误: 请先安装 modelscope")
        print("  pip install modelscope")
        print("或手动下载: python download_model.py")
        sys.exit(1)

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_dir = snapshot_download(MODEL_ID, cache_dir=MODELS_DIR)
    print(f"下载完成: {model_dir}")
    return model_dir


def load_embedding_model():
    """加载本地 bge-m3 模型"""
    model_path = find_or_download_model()
    print(f"正在加载模型: {model_path} ...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_path)
    dim = model.get_sentence_embedding_dimension()
    print(f"模型加载完成! 向量维度: {dim}")
    return model


def check_chroma():
    """检查 ChromaDB 是否可用"""
    try:
        r = requests.get(f"{CHROMA_BASE}/api/v2/heartbeat", timeout=10)
        r.raise_for_status()
        print(f"ChromaDB 可用 ({CHROMA_BASE})")
        return True
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到 ChromaDB ({CHROMA_BASE})")
        print("请启动 ChromaDB: chroma run --path ./chroma_data")
        return False
    except Exception as e:
        print(f"ChromaDB 检查失败: {e}")
        return False


def get_embedding(model, text: str) -> list[float] | None:
    """使用本地 bge-m3 生成 embedding"""
    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Embedding 失败: {e}")
        return None


def build_document(entry: dict, category: str) -> str:
    """根据条目构建可检索的文本"""
    if category == "messier" or category == "ngc_selected":
        parts = [
            f"天体编号: {entry['id']}",
            f"中文名: {entry['name']}",
            f"英文名: {entry['name_en']}",
            f"类型: {entry['type']}",
            f"所在星座: {entry['constellation']}",
        ]
        if entry.get("ra"):
            parts.append(f"赤经: {entry['ra']}")
        if entry.get("dec"):
            parts.append(f"赤纬: {entry['dec']}")
        parts.append(f"视星等: {entry['magnitude']}")
        parts.append(f"距离: {entry['distance_ly']} 光年")
        if entry.get("season"):
            parts.append(f"最佳观测季节: {entry['season']}")
        parts.append(f"简介: {entry['description']}")
        return "\n".join(parts)

    elif category == "constellations":
        parts = [
            f"星座名: {entry['name']}",
            f"英文名: {entry['name_en']}",
        ]
        if entry.get("area_sq_deg"):
            parts.append(f"面积: {entry['area_sq_deg']} 平方度")
        parts.append(f"最亮恒星: {entry['brightest_star']}")
        parts.append(f"简介: {entry['description']}")
        return "\n".join(parts)

    elif category == "terminology":
        return f"天文术语: {entry['term']}\n英文: {entry['term_en']}\n分类: {entry['category']}\n解释: {entry['description']}"

    return ""


def ensure_collection() -> str | None:
    """确保 ChromaDB collection 存在, 返回 collection ID"""
    try:
        r = requests.get(f"{CHROMA_API}/collections", timeout=10)
        r.raise_for_status()
        collections = r.json()

        for c in collections:
            if c["name"] == COLLECTION_NAME:
                print(f"Collection '{COLLECTION_NAME}' 已存在 (ID: {c['id']}), 将清空后重用")
                # 清空 collection 中的旧数据
                try:
                    requests.post(
                        f"{CHROMA_API}/collections/{c['id']}/delete",
                        json={"where": {}},
                        timeout=30,
                    )
                    print("  已清空旧数据")
                except Exception as e:
                    print(f"  清空数据时出现警告: {e}")
                return c["id"]

        r2 = requests.post(
            f"{CHROMA_API}/collections",
            json={"name": COLLECTION_NAME, "metadata": {"description": "天文知识 RAG 向量库"}},
            timeout=10,
        )
        r2.raise_for_status()
        cid = r2.json()["id"]
        print(f"Collection '{COLLECTION_NAME}' 创建成功 (ID: {cid})")
        return cid
    except Exception as e:
        print(f"Collection 操作失败: {e}")
        return None


def add_documents(collection_id: str, ids: list[str], documents: list[str],
                  metadatas: list[dict], embeddings: list[list[float]]):
    """批量写入 ChromaDB"""
    try:
        r = requests.post(
            f"{CHROMA_API}/collections/{collection_id}/add",
            json={
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "embeddings": embeddings,
            },
            timeout=120,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  写入失败: {e}")
        return False


def main():
    print("=" * 60)
    print("天文知识 RAG — 数据入库脚本")
    print("=" * 60)

    if not check_chroma():
        sys.exit(1)

    model = load_embedding_model()

    if not os.path.exists(DATA_FILE):
        print(f"错误: 数据文件不存在: {DATA_FILE}")
        print("请先运行: python scraper.py")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    collection_id = ensure_collection()
    if not collection_id:
        sys.exit(1)

    total_count = 0
    batch_size = 20

    for category, entries in data.items():
        print(f"\n处理类别: {category} ({len(entries)} 条)")

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for i, entry in enumerate(entries):
            doc_text = build_document(entry, category)
            doc_id = f"{category}_{entry.get('id', entry.get('term', str(i)))}"

            print(f"  [{i+1}/{len(entries)}] Embedding: {entry.get('name', entry.get('term', entry.get('id', '?')))} ...", end=" ", flush=True)

            embedding = get_embedding(model, doc_text)
            if embedding is None:
                print("跳过")
                continue

            ids.append(doc_id)
            documents.append(doc_text)
            metadatas.append({
                "category": category,
                "object_id": entry.get("id", entry.get("term", "")),
                "name": entry.get("name", entry.get("term", "")),
                "name_en": entry.get("name_en", entry.get("term_en", "")),
                "type": entry.get("type", entry.get("category", "")),
            })
            embeddings.append(embedding)
            print("OK")

            if len(ids) >= batch_size:
                print(f"  写入 {len(ids)} 条到 ChromaDB...", end=" ", flush=True)
                if add_documents(collection_id, ids, documents, metadatas, embeddings):
                    print("OK")
                    total_count += len(ids)
                ids, documents, metadatas, embeddings = [], [], [], []

        if ids:
            print(f"  写入剩余 {len(ids)} 条到 ChromaDB...", end=" ", flush=True)
            if add_documents(collection_id, ids, documents, metadatas, embeddings):
                print("OK")
                total_count += len(ids)

    print(f"\n{'=' * 60}")
    print(f"完成! 共写入 {total_count} 条知识记录到 ChromaDB")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
