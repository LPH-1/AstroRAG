"""
从 ModelScope 下载 bge-m3 模型到本地
运行一次即可: python download_model.py
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_ID = "BAAI/bge-m3"
LOCAL_DIR = os.path.join(SCRIPT_DIR, "models")

print(f"正在从 ModelScope 下载 {MODEL_ID} ...")
print(f"存储路径: {LOCAL_DIR}")
print("(约 2GB，请耐心等待)")
print()

try:
    from modelscope import snapshot_download
except ImportError:
    print("请先安装 modelscope: pip install modelscope")
    sys.exit(1)

os.makedirs(LOCAL_DIR, exist_ok=True)

model_dir = snapshot_download(MODEL_ID, cache_dir=LOCAL_DIR)

print()
print(f"下载完成! 模型路径: {model_dir}")
print("现在可以运行 embedding_server.py 或 embed.py 了")
