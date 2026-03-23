"""
预下载 RAG 嵌入模型和重排序模型到本地缓存。
部署时运行可避免首次使用 RAG 时的下载等待。
需先设置 HF_ENDPOINT=https://hf-mirror.com 使用国内镜像（setup.ps1 会设置）
"""

import os

# 国内镜像，需在 import huggingface 之前设置
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
RERANK_MODEL = "BAAI/bge-reranker-base"


def main():
    print(">>> 预下载 RAG 模型（国内镜像）...")
    print(f"    嵌入模型: {EMBED_MODEL}")
    from sentence_transformers import SentenceTransformer

    SentenceTransformer(EMBED_MODEL)
    print("    嵌入模型已缓存")

    print(f"    重排序模型: {RERANK_MODEL}")
    from sentence_transformers import CrossEncoder

    CrossEncoder(RERANK_MODEL, max_length=512)
    print("    重排序模型已缓存")
    print(">>> RAG 模型预下载完成")


if __name__ == "__main__":
    main()
