import os
import time
import json
import httpx
from dotenv import load_dotenv
from src.rag import KnowledgeBase
from src.tools import TOOL_DEFINITIONS, execute_tool
from src.memory import SessionMemory, PersistentMemory

load_dotenv()

MODEL = "deepseek-chat"
KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
MEMORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "memory.json")

SYSTEM_PROMPT = """你是一个专业的医学文献智能学习助手，帮助医学生理解医学知识、分析文献、生成测验题目。

你的能力：
1. 从知识库检索相关医学知识（使用 search_knowledge_base 工具）
2. 保存重要知识点为笔记（使用 save_note 工具）
3. 执行药物剂量等数学计算（使用 calculate 工具）
4. 查看学习进度（使用 get_learning_progress 工具）

工作原则：
- 回答前先检索知识库获取准确信息
- 生成测验题时提供4个选项和正确答案解析
- 对不确定的医学信息明确说明，避免误导
- 拒绝任何可能造成医疗伤害的请求"""

INTENT_PROMPT = """判断用户意图，只返回以下之一：quiz/summary/search/qa/progress/other
用户输入：{input}"""

REFLECT_PROMPT = """评估以下回答的质量（1-10分），只返回数字：
问题：{question}
回答：{answer}"""

# Convert Anthropic tool definitions to OpenAI function format
def _to_openai_tools(tool_defs):
    return [
        {"type": "function", "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"]
        }} for t in tool_defs
    ]

OPENAI_TOOLS = _to_openai_tools(TOOL_DEFINITIONS)


class StudyAgent:
    def __init__(self):
        self._api_key = os.environ["ANTHROPIC_API_KEY"]
        self._base_url = os.environ.get("ANTHROPIC_API_URL", "https://api.deepseek.com").rstrip("/")
        self._http = httpx.Client(timeout=60)
        self.kb = KnowledgeBase()
        self.kb.load(KB_DIR)
        self.memory = type("M", (), {
            "session": SessionMemory(),
            "persistent": PersistentMemory(MEMORY_PATH)
        })()

    def _call(self, messages: list, system: str = SYSTEM_PROMPT,
              tools: list = None, max_retries: int = 3) -> dict:
        all_messages = [{"role": "system", "content": system}] + messages
        payload = {"model": MODEL, "max_tokens": 1024, "messages": all_messages}
        if tools:
            payload["tools"] = tools
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        for attempt in range(max_retries):
            try:
                r = self._http.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers=headers,
                    content=json.dumps(payload),
                )
                if r.status_code != 200:
                    raise RuntimeError(f"Error code:{r.status_code} - {r.text}")
                return r.json()
            except (httpx.ConnectError, httpx.TimeoutException):
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)

    def _get_text(self, resp: dict) -> str:
        return resp["choices"][0]["message"].get("content") or ""

    def _classify_intent(self, user_input: str) -> str:
        resp = self._call(
            [{"role": "user", "content": INTENT_PROMPT.format(input=user_input)}],
            system="你是意图分类器，只返回单个词。"
        )
        return self._get_text(resp).strip().lower()

    def _reflect(self, question: str, answer: str) -> int:
        try:
            resp = self._call(
                [{"role": "user", "content": REFLECT_PROMPT.format(question=question, answer=answer)}],
                system="你是质量评估器，只返回1-10的整数。"
            )
            return int(self._get_text(resp).strip())
        except (ValueError, IndexError):
            return 8

    def _run_with_tools(self, messages: list) -> str:
        resp = self._call(messages, tools=OPENAI_TOOLS)
        while resp["choices"][0]["finish_reason"] == "tool_calls":
            msg = resp["choices"][0]["message"]
            tool_results = []
            for tc in msg.get("tool_calls", []):
                fn = tc["function"]
                inputs = json.loads(fn["arguments"])
                result = execute_tool(fn["name"], inputs, self.kb, self.memory)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result
                })
            messages = messages + [
                {"role": "assistant", "content": msg.get("content"), "tool_calls": msg.get("tool_calls")},
                *tool_results
            ]
            resp = self._call(messages, tools=OPENAI_TOOLS)

        return self._get_text(resp)

    def run(self, user_input: str) -> str:
        if not user_input.strip():
            return "请输入您的问题或指令。"

        intent = self._classify_intent(user_input)

        if intent == "progress":
            return self.memory.persistent.get_summary()

        history = self.memory.session.get_history()
        messages = history + [{"role": "user", "content": user_input}]

        if intent == "quiz":
            topic = user_input.replace("/quiz", "").strip() or "心脏病学"
            messages[-1]["content"] = f"请基于知识库为主题「{topic}」生成3道单选题，每题提供4个选项和详细解析。"
            self.memory.persistent.add_topic(topic)

        elif intent == "summary":
            topic = user_input.replace("/summary", "").strip()
            messages[-1]["content"] = f"请检索知识库并为「{topic}」生成一份结构化学习摘要，包含核心概念、重点和临床意义。"
            self.memory.persistent.add_topic(topic)

        answer = self._run_with_tools(messages)

        score = self._reflect(user_input, answer)
        if score < 7:
            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": "请改进上面的回答，使其更准确、更完整、更有条理。"})
            answer = self._run_with_tools(messages)

        self.memory.session.add("user", user_input)
        self.memory.session.add("assistant", answer)
        return answer
