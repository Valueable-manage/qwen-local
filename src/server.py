"""问答助手 Web 服务"""

import io
import json
import os
import time
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel

from model_loader import chat, chat_stream, load_model

# 中断标志
_stop_flag: list[bool] = [False]

# RAG 状态
_rag_ready: bool = False
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_DOCS_DIR = os.path.join(APP_DIR, "rag_docs")


# ──────────────────────────────────────────
# RAG
# ──────────────────────────────────────────


def _init_rag_file(docx_path: str):
    global _rag_ready
    try:
        from rag_pipeline import init_rag

        init_rag(docx_path)
        _rag_ready = True
        print(f"  RAG 就绪：{os.path.basename(docx_path)}")
    except Exception as e:
        print(f"  RAG 初始化失败：{e}")


def _list_rag_files():
    """返回 (doc_files, json_files)"""
    if not os.path.exists(RAG_DOCS_DIR):
        return [], []
    all_files = os.listdir(RAG_DOCS_DIR)
    doc_files = [f for f in all_files if f.lower().endswith((".docx", ".doc"))]
    json_files = [f for f in all_files if f.endswith("_translated.json")]
    return doc_files, json_files


def _init_all_rag():
    global _rag_ready
    os.makedirs(RAG_DOCS_DIR, exist_ok=True)
    doc_files, json_files = _list_rag_files()

    # 1. 优先从 doc/docx 初始化
    if doc_files:
        # 若有 xxx_中文版.docx，则跳过 xxx.docx，优先用中文版
        base_names = {os.path.splitext(f)[0].replace("_中文版", "") for f in doc_files}
        to_init = []
        for f in doc_files:
            base = os.path.splitext(f)[0]
            if base.endswith("_中文版"):
                to_init.append(f)
            elif f"{base}_中文版.docx" not in doc_files:
                to_init.append(f)
        for f in to_init:
            _init_rag_file(os.path.join(RAG_DOCS_DIR, f))
        return

    # 2. 无 doc 时，尝试从 *_translated.json 初始化
    if json_files:
        for f in json_files:
            try:
                from rag_pipeline import init_rag_from_json

                init_rag_from_json(os.path.join(RAG_DOCS_DIR, f))
                _rag_ready = True
                print(f"  RAG 就绪：{f}")
                return
            except Exception as e:
                print(f"  RAG 初始化失败（{f}）：{e}")
        return

    print("  rag_docs/ 无文档，RAG 未启用")


def _build_rag_messages(messages: list[dict], user_query: str) -> list[dict]:
    """检索 top-3，注入上下文，返回新 messages"""
    from rag_pipeline import search

    hits = search(user_query, top_k=3, rewrite=False)
    if not hits:
        return messages
    # 若最佳匹配相似度偏低，说明文档中无相关内容，不注入避免干扰
    best_score = hits[0].get("相似度", 0)
    if best_score < 0.5:
        return messages
    parts = []
    for i, h in enumerate(hits, 1):
        p = f"【参考{i}】\n问题：{h['问题']}\n答复：{h['答复']}"
        if h.get("图号"):
            p += f"\n图号：{h['图号']}"
        parts.append(p)
    context = "\n\n".join(parts)
    return messages[:-1] + [
        {
            "role": "user",
            "content": f"以下是相关的船舶工程处理意见，请根据这些内容回答问题。\n\n{context}\n\n问题：{user_query}",
        }
    ]


# ──────────────────────────────────────────
# 启动
# ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在加载模型...")
    load_model()
    print("模型加载完成")

    # RAG 后台初始化，不阻塞服务启动（首次请求时可能尚未就绪）
    def _init_rag_background():
        print("正在初始化 RAG（后台）...")
        _init_all_rag()

    threading.Thread(target=_init_rag_background, daemon=True).start()
    yield
    print("服务关闭")


app = FastAPI(title="Qwen 问答助手", lifespan=lifespan)


# ──────────────────────────────────────────
# 控制接口
# ──────────────────────────────────────────


@app.post("/api/cancel")
def api_cancel():
    _stop_flag[0] = True
    return {"ok": True}


@app.post("/api/shutdown")
def api_shutdown():
    os._exit(0)


# ──────────────────────────────────────────
# 文档管理接口
# ──────────────────────────────────────────


@app.post("/api/upload-doc")
async def api_upload_doc(file: UploadFile = File(...)):
    """上传 docx，保存后后台异步建 RAG 索引"""
    if not file.filename or not file.filename.lower().endswith((".docx", ".doc")):
        return {"ok": False, "error": "仅支持 .docx / .doc 文件"}
    try:
        data = await file.read()
        os.makedirs(RAG_DOCS_DIR, exist_ok=True)
        # 统一保存为 .docx 扩展名，避免重复；rag_pipeline 按实际格式读取
        base = os.path.splitext(file.filename)[0]
        ext = os.path.splitext(file.filename)[1].lower()
        save_path = os.path.join(RAG_DOCS_DIR, base + ext)
        with open(save_path, "wb") as f:
            f.write(data)
        threading.Thread(target=_init_rag_file, args=(save_path,), daemon=True).start()
        try:
            from docx import Document

            chars = len(
                "\n".join(
                    p.text
                    for p in Document(io.BytesIO(data)).paragraphs
                    if p.text.strip()
                )
            )
        except Exception:
            chars = 0
        return {"ok": True, "chars": chars, "filename": file.filename}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/doc-status")
def api_doc_status():
    doc_files, _ = _list_rag_files()
    return {"rag_ready": _rag_ready, "docs": doc_files}


@app.post("/api/clear-doc")
def api_clear_doc():
    global _rag_ready
    import shutil

    for d in [RAG_DOCS_DIR, os.path.join(APP_DIR, "rag_db")]:
        if os.path.exists(d):
            shutil.rmtree(d)
    _rag_ready = False
    return {"ok": True}


# ──────────────────────────────────────────
# OpenAI 兼容接口
# ──────────────────────────────────────────


def _normalize_messages(messages: list[dict]) -> list[dict]:
    result = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            content = "".join(parts)
        result.append({"role": m["role"], "content": content or ""})
    return result


def _get_last_user(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


@app.get("/v1/models")
def openai_list_models():
    return {"object": "list", "data": [{"id": "qwen", "object": "model", "created": 0}]}


class OpenAICompletionRequest(BaseModel):
    model: str = "qwen"
    messages: list[dict]
    stream: bool = False
    max_tokens: int = 512


def _sse_chunk(data: dict) -> bytes:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


@app.post("/v1/chat/completions")
def openai_chat_completions(req: OpenAICompletionRequest):
    messages = _normalize_messages(req.messages)
    t0 = time.perf_counter()

    # RAG：有索引时检索 top-3 注入上下文
    if _rag_ready:
        try:
            user_query = _get_last_user(messages)
            messages = _build_rag_messages(messages, user_query)
        except Exception as e:
            print(f"  RAG 检索失败，回退普通对话：{e}")

    if req.stream:

        def generate():
            id_ = "chatcmpl-local"
            _stop_flag[0] = False
            yield _sse_chunk(
                {
                    "id": id_,
                    "object": "chat.completion.chunk",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant"},
                            "finish_reason": None,
                        }
                    ],
                }
            )
            for chunk in chat_stream(
                messages, max_new_tokens=req.max_tokens, stop_flag=_stop_flag
            ):
                yield _sse_chunk(
                    {
                        "id": id_,
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
            yield _sse_chunk(
                {
                    "id": id_,
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
            )
            yield b"data: [DONE]\n\n"
            print(f">>> 流式完成，耗时 {time.perf_counter() - t0:.2f} 秒")

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    content = chat(messages, max_new_tokens=req.max_tokens)
    print(f">>> 完成，耗时 {time.perf_counter() - t0:.2f} 秒")
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


@app.get("/")
def index():
    return RedirectResponse(url="http://localhost:3000", status_code=302)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
