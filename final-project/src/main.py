import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import StudyAgent

HELP_TEXT = """
医学文献智能学习助手 — 可用命令：
  /help              显示帮助
  /quiz [主题]       生成测验题（默认：心脏病学）
  /summary <主题>    生成主题摘要
  /search <关键词>   检索知识库
  /progress          查看学习进度
  /clear             清空会话记忆
  /quit              退出
或直接输入问题进行问答。
"""


def main():
    print("=" * 50)
    print("  医学文献智能学习助手")
    print("  输入 /help 查看命令")
    print("=" * 50)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("错误：请在 .env 文件中设置 ANTHROPIC_API_KEY")
        sys.exit(1)

    agent = StudyAgent()
    print("知识库加载完成，助手已就绪。\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("再见！")
            break
        elif user_input == "/help":
            print(HELP_TEXT)
            continue
        elif user_input == "/clear":
            agent.memory.session.clear()
            print("会话记忆已清空。\n")
            continue

        try:
            response = agent.run(user_input)
            print(f"\n助手: {response}\n")
        except Exception as e:
            print(f"\n[错误] {e}\n")


if __name__ == "__main__":
    main()
