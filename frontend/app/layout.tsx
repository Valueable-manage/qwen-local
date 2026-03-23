import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Qwen 问答助手",
  description: "基于 Qwen3.5 的本地对话助手，使用 CopilotKit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body style={{ margin: 0, fontFamily: "Microsoft YaHei, PingFang SC, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
