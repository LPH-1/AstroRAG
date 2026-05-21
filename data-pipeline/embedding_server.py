"""
BGE-M3 本地 Embedding + 检索服务器
提供两个核心接口:
  POST /v1/embeddings   - 文本向量化 (OpenAI兼容)
  POST /v1/search       - 文本检索 (embed + ChromaDB search)

启动: python embedding_server.py
端口: 8081
"""

import os
import sys

import requests
from flask import Flask, request, jsonify

MODEL_ID = "BAAI/bge-m3"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
CHROMA_BASE = os.environ.get("CHROMA_BASE", "http://localhost:8000")
CHROMA_API = f"{CHROMA_BASE}/api/v2/tenants/default_tenant/databases/default_database"
COLLECTION_NAME = "astronomy_knowledge"

app = Flask(__name__)
model = None
collection_id = None


def find_or_download_model():
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


def ensure_chroma_collection():
    """确保 ChromaDB collection 存在，返回 collection ID"""
    try:
        r = requests.get(f"{CHROMA_API}/collections", timeout=10)
        r.raise_for_status()
        collections = r.json()

        for c in collections:
            if c["name"] == COLLECTION_NAME:
                print(f"ChromaDB collection 已就绪 (ID: {c['id']})")
                return c["id"]

        r2 = requests.post(
            f"{CHROMA_API}/collections",
            json={"name": COLLECTION_NAME},
            timeout=10,
        )
        r2.raise_for_status()
        cid = r2.json()["id"]
        print(f"ChromaDB collection 创建成功 (ID: {cid})")
        return cid
    except Exception as e:
        print(f"警告: ChromaDB 连接失败 - {e}")
        print(f"请确保 ChromaDB 已启动: chroma run --path chroma_data")
        return None


# === 启动初始化 ===
print("=" * 50)
print("AstroRAG Embedding + 检索服务器")
print("=" * 50)

model_path = find_or_download_model()
print(f"正在加载 embedding 模型...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(model_path)
print(f"模型加载完成! 向量维度: {model.get_sentence_embedding_dimension()}")

collection_id = ensure_chroma_collection()
if collection_id:
    print(f"ChromaDB 连接成功")
else:
    print("ChromaDB 未就绪, 检索功能暂时不可用")
print("=" * 50)


# === API 端点 ===

@app.route("/v1/embeddings", methods=["POST"])
def embeddings():
    """OpenAI 兼容 embedding 接口"""
    data = request.get_json(force=True)
    input_text = data.get("input", "")

    if isinstance(input_text, str):
        texts = [input_text]
    elif isinstance(input_text, list):
        texts = input_text
    else:
        return jsonify({"error": "input must be string or list of strings"}), 400

    if not texts:
        return jsonify({"error": "empty input"}), 400

    embs = model.encode(texts, normalize_embeddings=True)

    return jsonify({
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": emb.tolist()}
            for i, emb in enumerate(embs)
        ],
        "model": MODEL_ID,
    })


@app.route("/v1/search", methods=["POST"])
def search():
    """检索接口: 接收文本查询，返回 ChromaDB 中最匹配的文档"""
    if not collection_id:
        return jsonify({"error": "ChromaDB 未就绪"}), 503

    data = request.get_json(force=True)
    query = data.get("query", "")
    top_k = data.get("top_k", 5)

    if not query:
        return jsonify({"error": "empty query"}), 400

    # 向量化查询
    query_emb = model.encode(query, normalize_embeddings=True).tolist()

    # 在 ChromaDB 中检索
    try:
        r = requests.post(
            f"{CHROMA_API}/collections/{collection_id}/query",
            json={
                "query_embeddings": [query_emb],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            },
            timeout=30,
        )
        r.raise_for_status()
        result = r.json()
    except Exception as e:
        return jsonify({"error": f"ChromaDB 查询失败: {e}"}), 500

    # 格式化结果
    results = []
    if result.get("ids") and result["ids"][0]:
        for i in range(len(result["ids"][0])):
            dist = result["distances"][0][i]
            # ChromaDB uses L2 distance. With normalized vectors:
            # L2^2 = 2 - 2*cosine, so cosine = 1 - L2^2/2
            cosine_sim = 1.0 - (dist * dist) / 2.0
            results.append({
                "id": result["ids"][0][i],
                "document": result["documents"][0][i],
                "metadata": result["metadatas"][0][i],
                "score": round(cosine_sim, 4),
            })

    return jsonify({"results": results})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL_ID,
        "chromadb": collection_id is not None,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081)
