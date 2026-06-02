# CLAUDE.md — 编程智能体操作说明

## 项目概述
医学文献智能学习助手，使用 Claude API 实现多模式智能体工作流。

## 运行方式
```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 ANTHROPIC_API_KEY
python src/main.py
```

## 代码结构
- `src/agent.py`：主智能体，包含路由、提示链、反思逻辑
- `src/rag.py`：TF-IDF 本地知识库检索
- `src/tools.py`：Claude tool_use 工具定义与执行
- `src/memory.py`：会话记忆 + 持久化记忆
- `src/main.py`：CLI 入口

## 测试
```bash
python tests/eval.py
```

## 注意事项
- 不得在代码中硬编码 API Key，使用 .env 文件
- 知识库文件位于 `data/knowledge_base/`，可添加 .txt 文件扩展
