# 医学文献智能学习助手

## 项目简介

本项目是一个面向医学生的智能学习助手，基于 Claude API 实现多模式智能体工作流，支持知识问答、文献摘要、自测出题和学习进度追踪。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY

# 3. 运行助手
python src/main.py

# 4. 运行评估
python tests/eval.py
```

## 演示样例

### 样例 1：知识问答
```
你: 心肌梗死的诊断依据是什么？
助手: 根据知识库检索，心肌梗死诊断依据包括：
1. 典型症状：胸骨后压榨性疼痛，可放射至左臂
2. 心电图：ST段抬高（STEMI）
3. 心肌酶：肌钙蛋白升高
治疗首选经皮冠状动脉介入治疗（PCI）。
```

### 样例 2：生成摘要
```
你: /summary 药物代谢动力学
助手: 【药物代谢动力学摘要】
核心概念：ADME（吸收、分布、代谢、排泄）
- 吸收：口服药物受首过效应影响...
- 分布：与血浆蛋白结合，Vd反映分布范围...
```

### 样例 3：自测出题
```
你: /quiz 心脏病学
助手: 【心脏病学测验】
第1题：心房颤动最主要的并发症是？
A. 心力衰竭  B. 脑卒中  C. 心肌梗死  D. 肾衰竭
答案：B。解析：AF导致心房内血栓形成，脱落后引起脑栓塞...
```

## 智能体设计模式

| 模式 | 实现位置 | 说明 |
|------|----------|------|
| 路由 (Routing) | `agent.py:_classify_intent` | 按意图分发到不同处理流程 |
| RAG 检索 | `rag.py:KnowledgeBase` | TF-IDF 本地知识库检索 |
| 提示链 | `agent.py:run` | 意图分类→检索→生成→反思 |
| 反思 (Reflection) | `agent.py:_reflect` | 质量评分<7时自动重试 |
| 工具使用 | `tools.py` + `agent.py:_run_with_tools` | Claude tool_use API |
| 记忆管理 | `memory.py` | 会话记忆 + 持久化 JSON |

## 项目结构

```
final-project/
├── src/
│   ├── agent.py      # 主智能体
│   ├── rag.py        # 知识库检索
│   ├── tools.py      # 工具定义与执行
│   ├── memory.py     # 记忆管理
│   └── main.py       # CLI 入口
├── data/knowledge_base/  # 医学知识库
├── tests/eval.py     # 评估脚本（7个用例）
├── requirements.txt
└── .env.example
```

## 环境要求

- Python 3.9+
- 兼容 OpenAI 格式的 LLM API Key（默认使用 DeepSeek，也可替换为其他兼容服务）
