# CopilotKit 前端部署详细步骤

不使用 HTML，用 CopilotKit 完成前端部署的完整步骤。

---

## 一、架构说明

```
┌─────────────────┐     /api/copilotkit     ┌──────────────────────┐     /v1/chat/completions     ┌─────────────────┐
│  Next.js 前端   │ ─────────────────────► │  CopilotKit Runtime   │ ───────────────────────────► │  FastAPI 后端    │
│  (port 3000)   │                         │  (内置在 Next.js)      │                              │  (port 8000)     │
└─────────────────┘                         └──────────────────────┘                              └─────────────────┘
```

- **前端**：Next.js + React + CopilotKit
- **Runtime**：Next.js API 路由 `/api/copilotkit`，使用 `OpenAIAdapter` 转发到 FastAPI
- **后端**：FastAPI 提供 `/v1/chat/completions`（OpenAI 兼容）

---

## 二、前置要求

- Node.js 18+（建议 20+）
- 已安装 uv（Python 依赖管理）
- 已配置好 Qwen 模型路径

---

## 三、步骤 1：安装前端依赖

```powershell
cd F:\projects\qwen-local\frontend
npm install
```

---

## 四、步骤 2：配置环境变量（可选）

如需修改默认地址，在 `frontend/` 下创建 `.env.local`：

```env
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_MODEL=qwen
```

默认即可对接本地 FastAPI，无需修改。

---

## 五、启动方式

### 方式 A：一键启动（推荐）

```powershell
cd F:\projects\qwen-local
uv run python start.py
```

同时启动前后端，按 **Ctrl+C** 可一起关闭。

### 方式 B：分别启动

**终端 1**（后端）：

```powershell
cd F:\projects\qwen-local
uv run python server.py
```

**终端 2**（前端）：

```powershell
cd F:\projects\qwen-local\frontend
npm run dev
```

---

## 六、访问

浏览器打开：**http://localhost:3000**

即可使用 CopilotKit 聊天界面，对话会走本地 Qwen 模型。

（模型加载需几十秒，请等待后端输出「模型加载完成」后再使用）

---

## 七、生产构建

### 8.1 构建前端

```powershell
cd F:\projects\qwen-local\frontend
npm run build
```

### 8.2 启动生产服务

```powershell
# 终端 1：FastAPI
cd F:\projects\qwen-local
uv run python server.py

# 终端 2：Next.js 生产模式
cd F:\projects\qwen-local\frontend
npm run start
```

---

## 八、单端口部署（可选）

若希望前端和后端在同一端口：

1. 构建 Next.js：`npm run build`
2. 将 `frontend/.next` 和 `frontend/public` 用 `next export` 导出静态文件
3. 用 FastAPI 挂载静态资源，或使用 Nginx 反向代理

或使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:3000;  # Next.js
    }
    location /v1/ {
        proxy_pass http://127.0.0.1:8000
    }
}
```

注意：CopilotKit 的 `/api/copilotkit` 在 Next.js 内部，需转发到 3000。

---

## 十、常见问题

### 1. "Failed to fetch" / 连接失败

- 确认 FastAPI 已启动：`http://127.0.0.1:8000/v1/chat/completions` 可访问
- 确认 `frontend/app/api/copilotkit/route.ts` 中 `baseURL` 正确

### 2. 模型返回格式错误

- 确认 `server.py` 中 `/v1/chat/completions` 返回格式与 OpenAI 一致
- 必须包含 `choices[0].message.content`

### 3. 端口冲突

- 修改 Next.js 端口：`npm run dev -- -p 3001`
- 修改 FastAPI 端口：`uvicorn.run(..., port=8001)`，并同步修改 `OPENAI_BASE_URL`

### 4. 跨域问题

开发时 Next.js 和 FastAPI 同源策略不同。Runtime 在服务端运行，直接请求 `127.0.0.1:8000`，无浏览器跨域问题。若仍有问题，可在 FastAPI 添加 CORS：

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

---

## 十一、项目结构

```
qwen-local/
├── server.py              # FastAPI，含 /v1/chat/completions
├── model_loader.py
├── frontend/              # CopilotKit 前端
│   ├── app/
│   │   ├── api/
│   │   │   └── copilotkit/
│   │   │       └── route.ts   # Runtime 配置
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── package.json
│   └── next.config.ts
└── docs/
    └── CopilotKit部署步骤.md
```
