"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    const onUnload = () => {
      navigator.sendBeacon("/api/shutdown");
    };
    window.addEventListener("pagehide", onUnload);
    window.addEventListener("beforeunload", onUnload);
    return () => {
      window.removeEventListener("pagehide", onUnload);
      window.removeEventListener("beforeunload", onUnload);
    };
  }, []);

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="default">
      <div
        style={{
          maxWidth: 720,
          margin: "0 auto",
          minHeight: "100vh",
          padding: 24,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <header style={{ textAlign: "center", padding: "32px 0 24px", borderBottom: "1px solid #e5e5e5" }}>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Qwen 问答助手</h1>
          <p style={{ marginTop: 6, fontSize: "0.875rem", color: "#666" }}>
            基于 Qwen3.5 + CopilotKit
          </p>
        </header>
        <main style={{ flex: 1, padding: "24px 0" }}>
          <CopilotChat
            instructions="你是一个简洁的中文助手。只输出最终答案，不重复用户的问题，不输出分析过程，始终用简体中文回答。"
            className="min-h-[400px]"
            onStopGeneration={() => {
              fetch("/api/cancel", { method: "POST" }).catch(() => {});
            }}
          />
        </main>
      </div>
    </CopilotKit>
  );
}
