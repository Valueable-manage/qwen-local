import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import OpenAI from "openai";

/**
 * CopilotKit Runtime：将请求转发到本地 FastAPI（Qwen 模型）
 * 确保 server.py 已启动在 http://127.0.0.1:8000
 *
 * 通过 patch-package 修改 @copilotkit/runtime，强制使用 Chat Completions API
 * 而非 Responses API（本地 FastAPI 只实现了 /v1/chat/completions）
 */
const openai = new OpenAI({
  apiKey: "sk-placeholder",
  baseURL: process.env.OPENAI_BASE_URL || "http://127.0.0.1:8000/v1",
});

const serviceAdapter = new OpenAIAdapter({
  openai,
  model: process.env.OPENAI_MODEL || "qwen",
});

const runtime = new CopilotRuntime();

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
