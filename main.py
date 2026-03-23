"""命令行对话（可选：python main.py 或 python server.py 启动 Web）"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from model_loader import chat, load_model

print("正在加载模型，请稍等...")
load_model()
print("模型加载完成！开始对话（输入quit退出，Ctrl+C 可中断生成）")

messages = []
try:
    while True:
        user_input = input("\n你：")
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response = chat(messages)
        except KeyboardInterrupt:
            print("\n\n[已中断]")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": response})
        print(f"\nAI：{response}")

except KeyboardInterrupt:
    print("\n\n再见！")
