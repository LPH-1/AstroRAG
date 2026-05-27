"""
共享模型工具 — find_or_download_model()

供 embedding_server.py 和 embed.py 共用，避免重复代码。
"""

import os
import sys

MODEL_ID = "BAAI/bge-m3"


def find_or_download_model(models_dir):
    """
    在 models_dir 下查找 bge-m3 模型；找不到则从 ModelScope 下载。
    返回模型所在目录路径。
    """
    for root, dirs, files in os.walk(models_dir):
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

    os.makedirs(models_dir, exist_ok=True)
    model_dir = snapshot_download(MODEL_ID, cache_dir=models_dir)
    print(f"下载完成: {model_dir}")
    return model_dir
