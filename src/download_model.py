"""
从 ModelScope 或 HuggingFace 下载 Qwen3.5-4B 模型到项目内 qwen/Qwen3___5-4B
需联网，首次运行会下载约 8-10GB
默认使用 ModelScope（国内直连，无需VPN）
环境变量 USE_HF=1 时切换为 HuggingFace
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(PROJECT_DIR, "qwen", "Qwen3___5-4B")
HF_MODEL_ID = "Qwen/Qwen3.5-4B"
MS_MODEL_ID = "Qwen/Qwen3.5-4B"


def main():
    if os.path.exists(MODEL_DIR):
        files = os.listdir(MODEL_DIR)
        if any(
            f.endswith(".safetensors") or f.endswith(".bin")
            for f in files
            if os.path.isfile(os.path.join(MODEL_DIR, f))
        ):
            print(f">>> 模型已存在: {MODEL_DIR}")
            return 0

    # 默认 ModelScope（国内直连），USE_HF=1 时切换 HuggingFace
    use_hf = os.environ.get("USE_HF", "").lower() in ("1", "true", "yes")
    src = "HuggingFace" if use_hf else "ModelScope"
    print(f">>> 从 {src} 下载模型到 {MODEL_DIR}")
    print(">>> 约 8-10GB，请耐心等待...")

    os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)

    if use_hf:
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print(">>> 请先运行: uv sync")
            return 1
        snapshot_download(
            repo_id=HF_MODEL_ID,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False,
        )
    else:
        try:
            from modelscope import snapshot_download
        except ImportError:
            print(">>> 请先运行: uv sync")
            return 1
        # 指定 ModelScope 国内镜像
        os.environ.setdefault("MODELSCOPE_CACHE", MODEL_DIR)
        snapshot_download(MS_MODEL_ID, local_dir=MODEL_DIR)

    print(">>> 下载完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
