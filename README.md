# Qwen 本地问答助手

基于 **Qwen3.5-4B** + **CopilotKit** 构建的本地私有化 AI 对话系统，支持 RAG 知识库检索，全程本地运行，无需联网，数据不出本机。

---

## ✨ 功能特性

- **本地部署**：模型与数据均运行在本机，无任何外网调用
- **Web 对话界面**：基于 CopilotKit + Next.js 的现代化聊天 UI
- **命令行模式**：支持终端直接对话，轻量快速
- **RAG 知识库**：上传 `.docx` 文档即可构建私有知识库，支持智能检索问答
- **GPU 加速**：自动检测 NVIDIA GPU，支持 4-bit 量化加载，显存占用低至 4GB
- **一键部署**：双击 `deploy.bat` 全自动完成环境安装、模型下载、启动

---

## 🛠 技术栈

| 模块 | 技术 |
|------|------|
| 大语言模型 | Qwen3.5-4B（4-bit 量化） |
| 推理框架 | PyTorch + Transformers + BitsAndBytes |
| Web 后端 | FastAPI + Uvicorn |
| 前端界面 | Next.js + CopilotKit |
| RAG 检索 | ChromaDB（向量）+ BM25（关键词）+ 交叉编码器重排序 |
| 包管理 | uv |
| 运行环境 | Python 3.12+，Windows |

---

## 📁 项目结构

```
qwen-local/
├── src/                      # 后端核心代码
│   ├── server.py             # FastAPI Web 服务
│   ├── model_loader.py       # 模型加载与推理
│   ├── rag_pipeline.py       # RAG 知识库检索流程
│   ├── download_model.py     # 模型下载脚本
│   └── download_rag_models.py# RAG 嵌入模型下载
├── frontend/                 # Next.js 前端界面
│   ├── app/
│   │   ├── page.tsx          # 主聊天页面
│   │   └── api/              # 前端 API 路由
│   └── package.json
├── scripts/                  # 部署与运行脚本
│   ├── deploy.bat            # 一键部署（海外网络）
│   ├── deploy_cn.bat         # 一键部署（国内网络）
│   ├── deploy_prepare.bat    # 手动安装 Python/Node
│   ├── run.bat               # 日常启动
│   ├── setup.ps1             # 环境安装脚本
│   ├── pack.ps1              # 打包分发脚本
│   └── create_desktop_shortcut.ps1
├── docs/                     # 项目文档
├── rag_docs/                 # RAG 知识库文档（放置 .docx 文件）
├── main.py                   # 命令行对话入口
├── start.py                  # 一键启动前后端
└── pyproject.toml
```

---

## 🚀 快速开始

### 新电脑一键部署（推荐）

**双击 `scripts/deploy.bat`** 即可全自动完成：

```
自动安装 Python / Node → 安装依赖 → 下载模型（约 8-10GB）→ 创建桌面图标 → 启动
```

> 国内网络请使用 `scripts/deploy_cn.bat`，使用 ModelScope 下载模型、清华镜像安装依赖，速度更快。

### 日常启动（依赖已安装）

```powershell
uv run python start.py
```

或双击桌面快捷方式 **Qwen.lnk**。

### 命令行模式

```powershell
uv run python main.py
```

---

## 🔧 系统要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Windows 10/11 |
| Python | 3.12+ |
| Node.js | 18+ |
| 内存 | 16GB RAM |
| 显卡 | NVIDIA GPU，显存 ≥ 6GB（推荐 8GB+）|
| 磁盘空间 | 15GB+（模型约 8-10GB）|

> 无 GPU 时自动切换 CPU 推理，速度较慢。

---

## 📚 RAG 知识库使用

1. 将 `.docx` 格式文档放入 `rag_docs/` 目录
2. 重启程序，系统自动解析文档并构建向量索引
3. 对话时直接提问，系统自动检索相关内容辅助回答

RAG 检索流程：
```
提问 → 查询改写 → 向量召回 + BM25 关键词召回 → 交叉编码器重排序 → Top-3 上下文注入 → 回答
```

---

## 📦 打包分发

```powershell
.\scripts\pack.ps1
```

生成 zip 压缩包（自动排除 `.venv`、`node_modules`、`.next`、模型文件），发送给客户解压后双击 `deploy.bat` 即可使用。

详见 [docs/打包与验证.md](docs/打包与验证.md)。

---

## 🔒 隐私说明

- 所有对话数据仅在本机处理，不上传任何服务器
- 模型推理完全离线，断网可正常使用
- RAG 文档内容存储于本地 `rag_db/` 目录

---

## 📄 License

MIT License
