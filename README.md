# Qwen 本地问答助手

基于 Qwen3.5 + CopilotKit 的本地对话应用，支持命令行与 Web 界面。

## 项目结构

```
qwen-local/
├── src/              # 后端核心代码
│   ├── server.py         # Web API 服务
│   ├── model_loader.py   # 模型加载与推理
│   ├── rag_pipeline.py   # RAG 知识库检索
│   └── download_*.py     # 模型下载脚本
├── frontend/         # Next.js 前端界面
├── scripts/          # 部署与运行脚本
│   ├── deploy.bat        # 一键部署（海外网络）
│   ├── deploy_cn.bat     # 一键部署（国内网络）
│   ├── run.bat           # 日常启动
│   └── setup.ps1         # 环境安装脚本
├── docs/             # 项目文档
├── rag_docs/         # RAG 知识库文档
├── main.py           # 命令行对话入口
├── start.py          # 一键启动前后端
└── pyproject.toml
```

## 新电脑一键部署（联网）

**双击 `scripts/deploy.bat`** 即可完成：自动安装 Python/Node（如未安装）→ 安装依赖 → 自动下载模型（约 8–10GB）→ 创建桌面图标 → 启动。

- 国内网络可双击 `scripts/deploy_cn.bat`：使用 ModelScope 下载模型、清华镜像安装 Python 包，整体更快
- 模型已存在时跳过下载，直接创建快捷方式并启动
- 若系统无 Python/Node，会通过 winget 自动安装（国内可能较慢，可先运行 `scripts/deploy_prepare.bat` 手动安装）

## 打包给客户

运行 `scripts\pack.ps1` 生成 zip，排除 .venv、node_modules、.next、qwen。客户解压后双击 deploy.bat 即可。详见 [docs/打包与验证.md](docs/打包与验证.md)。

## 日常运行（依赖已安装）

```powershell
uv run python start.py
```

## 桌面快捷方式

```powershell
.\scripts\create_desktop_shortcut.ps1
```

在桌面创建快捷方式，双击启动前后端。图标使用根目录 `icon.ico`。

## 断网运行

模型、依赖安装完成后可全程断网运行。所有请求均为 localhost，无外网调用。
