/**
 * 转发到 FastAPI 后端的 /api/cancel，用于中断生成
 * 断网/后端未就绪时静默失败，避免报错
 */
export async function POST() {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/cancel", {
      method: "POST",
    });
    const data = await res.json();
    return new Response(JSON.stringify(data), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return new Response(JSON.stringify({ ok: false }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}
