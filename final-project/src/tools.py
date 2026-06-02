import ast
import operator


TOOL_DEFINITIONS = [
    {
        "name": "search_knowledge_base",
        "description": "在本地医学知识库中检索相关内容，返回最相关的段落。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索查询词"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_note",
        "description": "将重要知识点保存为学习笔记。",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "笔记内容"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "calculate",
        "description": "执行安全的数学计算，例如药物剂量换算。",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式，如 '70 * 0.5'"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_learning_progress",
        "description": "获取用户的学习进度和历史记录。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}


def _safe_eval(expr: str) -> float:
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"不支持的操作: {type(node)}")
    return _eval(ast.parse(expr, mode="eval").body)


def execute_tool(name: str, inputs: dict, kb, memory) -> str:
    try:
        if name == "search_knowledge_base":
            results = kb.search(inputs["query"], top_k=3)
            if not results:
                return "知识库中未找到相关内容。"
            return "\n\n".join(
                f"[来源: {r['source']}]\n{r['content']}" for r in results
            )

        elif name == "save_note":
            memory.persistent.add_note(inputs["content"])
            return f"笔记已保存：{inputs['content'][:50]}..."

        elif name == "calculate":
            result = _safe_eval(inputs["expression"])
            return f"计算结果：{inputs['expression']} = {result}"

        elif name == "get_learning_progress":
            return memory.persistent.get_summary()

        else:
            return f"未知工具：{name}"

    except ZeroDivisionError:
        return "计算错误：除数不能为零。"
    except ValueError as e:
        return f"计算错误：{e}"
    except Exception as e:
        return f"工具执行失败：{e}"
