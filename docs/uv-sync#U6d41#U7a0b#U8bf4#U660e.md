# uv sync 流程说明

## 一、设计原则

- **torch 单独处理**：GPU 版需从 PyTorch 官方下载，国内易失败；CPU 版从清华镜像。
- **避免覆盖**：部署后不再执行 `uv sync`，防止把 GPU 版 torch 覆盖成 lock 中的版本。
- **单一来源**：每个包只在一个步骤安装，不重复、不来回覆盖。

---

## 二、依赖来源一览

| 包 | 来源 | 安装时机 |
|----|------|----------|
| torch | PyTorch 官方 (cu121/cu118/cu124) 或清华 (CPU) | setup Step 4.5 |
| 其他 Python 包 | 清华镜像 | setup Step 4 |

---

## 三、完整流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  pyproject.toml                                                             │
│  - torch: index = "pytorch-cu124"（供 uv lock 解析，不参与实际安装）        │
│  - 其他: 默认（uv sync 时由 UV_INDEX_URL 指定）                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  uv lock                                                                    │
│  - 解析依赖，生成 uv.lock                                                   │
│  - torch 解析为 cu124（来自 pyproject）                                      │
│  - 其他包解析为清华镜像                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  setup.ps1 Step 4: uv sync --no-install-package torch                       │
│  - UV_INDEX_URL = 清华镜像                                                  │
│  - 安装除 torch 外的所有依赖                                                 │
│  - 不安装 torch（避免 download.pytorch.org 失败）                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  setup.ps1 Step 4.5: uv pip install torch                                   │
│  - 检测 nvidia-smi → 选 cu124 / cu121 / cu118                               │
│  - uv pip install torch --index-url https://download.pytorch.org/whl/cuXXX  │
│  - 失败则保持无 torch（需手动装 CPU 版兜底）                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  日常运行: run.bat                                                          │
│  - venv 存在 → .venv\Scripts\python.exe start.py（不触发 sync）              │
│  - venv 不存在 → uv run --no-sync python start.py                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、关键点

### 4.1 为何 `uv sync --no-install-package torch`？

- `torch` 在 pyproject 中来自 `pytorch-cu124`，uv lock 会解析该源。
- 国内访问 `download.pytorch.org` 常失败，直接 `uv sync` 易报错。
- 用 `--no-install-package torch` 跳过 torch，其余包从清华镜像安装。
- torch 由 Step 4.5 单独安装，可按 nvidia-smi 选择 cu121/cu118/cu124。

### 4.2 为何 run.bat 优先用 venv 直接启动？

- `uv run` 默认会先执行 `uv sync`。
- sync 会按 uv.lock 安装 torch（cu124），可能覆盖 Step 4.5 安装的 cu121/cu118。
- 因此 run.bat 优先用 `.venv\Scripts\python.exe start.py`，不再触发 sync。
- setup.ps1 最后启动时也用 venv 直接启动，避免 uv run 覆盖。

### 4.3 兜底逻辑

- 若 `.venv` 不存在：run.bat 使用 `uv run --no-sync python start.py`。
- 若 Step 4.5 GPU 安装失败：自动回退安装 CPU 版（清华镜像）。
- 若无 nvidia-smi：自动安装 CPU 版（清华镜像）。

---

## 五、谁在何时执行 uv sync？

| 场景 | 是否 sync | 说明 |
|------|-----------|------|
| 首次部署 (setup.ps1) | 是（带 --no-install-package torch） | 只装非 torch 依赖 |
| run.bat 日常启动 | 否 | 直接用 venv |
| 手动 `uv sync` | 是 | 会按 lock 重装 torch，可能覆盖 GPU 版 |
| 手动 `uv run xxx` | 默认是 | 同上，慎用 |

---

## 六、修改依赖时

1. 改 `pyproject.toml`
2. 执行 `uv lock`
3. 执行 `deploy.bat` 或 `setup.ps1` 重新部署
4. 不要在日常使用中执行 `uv sync` 或 `uv run`（除非确认不会覆盖 torch）
