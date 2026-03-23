/**
 * 转发到 FastAPI 后端的 /api/shutdown，关闭整个程序
 * 断网/后端已关闭时静默返回，避免报错
 */
export async function POST() {
  try {
    await fetch("http://127.0.0.1:8000/api/shutdown", { method: "POST" });
  } catch {
    /* 后端可能已关闭 */
  }
  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
