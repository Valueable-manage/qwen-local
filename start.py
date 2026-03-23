"""
一键启动前后端：同时启动 FastAPI 后端和 CopilotKit 前端。
- 启动后自动打开浏览器
- 关闭浏览器页签会退出整个程序
- 按 Ctrl+C 也可关闭
"""

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
FRONTEND_URL = "http://localhost:3000"

# 直接用 venv 的 python，避免 uv run 每次自动 sync 覆盖 GPU 版 torch
if sys.platform == "win32":
    VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "bin", "python")

# 如果 venv 不存在则回退 uv run（兜底）
USE_UV_RUN = not os.path.exists(VENV_PYTHON)


def _kill_process_tree(pid: int):
    """Windows: 终止进程树"""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
    else:
        try:
            os.kill(pid, 9)
        except Exception:
            pass


def main():
    processes = []

    def cleanup():
        print("\n正在关闭前后端...")
        for p in processes:
            try:
                _kill_process_tree(p.pid)
            except Exception:
                pass
        processes.clear()

    # 启动 FastAPI 后端
    print(">>> 启动 FastAPI 后端 (port 8000)...")
    if USE_UV_RUN:
        backend_cmd = ["uv", "run", "--no-sync", "python", "src/server.py"]
    else:
        backend_cmd = [VENV_PYTHON, "src/server.py"]

    backend = subprocess.Popen(
        backend_cmd,
        cwd=PROJECT_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    processes.append(backend)

    time.sleep(2)

    # 启动 Next.js 前端（关闭 CopilotKit 遥测，支持断网运行）
    print(">>> 启动 CopilotKit 前端 (port 3000)...")
    frontend_env = os.environ.copy()
    frontend_env["COPILOTKIT_TELEMETRY_DISABLED"] = "true"
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=frontend_env,
    )
    processes.append(frontend)

    # 等待前端就绪后打开浏览器
    print(">>> 等待前端就绪...")
    for _ in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen(FRONTEND_URL, timeout=2)
            break
        except Exception:
            pass
    else:
        print(">>> 前端启动超时，请手动打开", FRONTEND_URL)
    webbrowser.open(FRONTEND_URL)

    print("\n" + "=" * 50)
    print("  已启动并打开浏览器")
    print("  关闭浏览器页签将退出程序，或按 Ctrl+C")
    print("=" * 50 + "\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
