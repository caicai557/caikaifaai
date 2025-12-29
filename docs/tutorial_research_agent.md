# 教程：构建研究型 Agent

在本教程中，我们将构建一个 **研究型 Agent (Research Agent)**，它使用 `VectorMemory` 存储知识，并使用 `StreamingLLM` 生成报告。

## 前置条件

- 已安装 Council 框架
- Python 3.10+

## 第一步：定义 Agent

创建一个名为 `research_agent.py` 的文件：

```python
from council.agents.base_agent import BaseAgent, ExecuteResult
from council.memory.vector_memory import VectorMemory
from council.streaming import StreamingLLM
import asyncio

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            system_prompt="你是一个严谨的研究员。",
            model="claude-3-opus"
        )
        # 初始化记忆 (Initialize Memory)
        self.memory = VectorMemory(collection_name="research_data")
        # 初始化 LLM (Initialize LLM)
        self.llm = StreamingLLM()

        # 预置记忆数据 (用于演示)
        self.memory.add("Council v0.2 新增了 CLI run 命令。", doc_id="update1")

    def execute(self, task: str, plan=None) -> ExecuteResult:
        # 1. 检索 (Retrieve)
        results = self.memory.search(task, k=1)
        context = results[0]["document"] if results else "无数据。"

        # 2. 生成 (Generate)
        prompt = f"背景信息: {context}\n任务: {task}"
        response = asyncio.run(self.llm.stream_to_string(prompt, self.model))

        return ExecuteResult(True, response)

agent = ResearchAgent()
```

## 第二步：使用 CLI 运行

使用新的 `council run` 命令来执行你的 Agent：

```bash
council run research_agent.py "v0.2 有什么新功能？"
```

## 预期输出

CLI 将加载你的 Agent，在"思考"时显示加载动画，然后显示 Markdown 格式的报告。

```
Running agent: ResearchAgent...
Result:
根据背景信息，Council v0.2 新增了 CLI run 命令。
```

## 下一步

下面是两个可选的扩展步骤：分层记忆与可观测性追踪。可以先完成其中一个，再逐步完善。

### 1) 添加 `TieredMemory`：分层长短期记忆

将 `VectorMemory` 替换为 `TieredMemory`，并为不同层级写入与检索数据：

```python
from council.memory.vector_memory import TieredMemory

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            system_prompt="你是一个严谨的研究员。",
            model="claude-3-opus"
        )
        self.memory = TieredMemory(persist_dir=".chromadb")
        self.llm = StreamingLLM()

        # Working/Short-term/Long-term 示例数据
        self.memory.working.add("当前会话中的临时信息。", doc_id="w1")
        self.memory.short_term.add("最近的研究结论。", doc_id="s1")
        self.memory.long_term.add("长期保留的知识。", doc_id="l1")

    def execute(self, task: str, plan=None) -> ExecuteResult:
        # 从多层记忆里分别检索，再合并上下文
        results = (
            self.memory.working.search(task, k=1)
            + self.memory.short_term.search(task, k=1)
            + self.memory.long_term.search(task, k=1)
        )
        context = "\n".join([r["document"] for r in results]) or "无数据。"

        prompt = f"背景信息: {context}\n任务: {task}"
        response = asyncio.run(self.llm.stream_to_string(prompt, self.model))
        return ExecuteResult(True, response)
```

如果某条信息从短期变为长期，可用 `promote` 提升：

```python
doc_id = self.memory.short_term.add("可长期保留的结论")
self.memory.promote("short_term", "long_term", doc_id)
```

### 2) 使用 `AgentTracer`：追踪性能与步骤

在 Agent 中接入 `AgentTracer`，为关键步骤加上追踪 span：

```python
from council.observability import AgentTracer

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            system_prompt="你是一个严谨的研究员。",
            model="claude-3-opus"
        )
        self.memory = VectorMemory(collection_name="research_data")
        self.llm = StreamingLLM()
        self.tracer = AgentTracer(service_name="research-agent")

    def execute(self, task: str, plan=None) -> ExecuteResult:
        with self.tracer.trace_agent_step(self.name, "execute"):
            with self.tracer.trace_tool_call("memory.search", {"query": task}):
                results = self.memory.search(task, k=1)
            context = results[0]["document"] if results else "无数据。"
            prompt = f"背景信息: {context}\n任务: {task}"
            with self.tracer.trace_llm_call(model=self.model, prompt=prompt):
                response = asyncio.run(self.llm.stream_to_string(prompt, self.model))

        return ExecuteResult(True, response)
```

如果安装了 OpenTelemetry，会输出 span；未安装则自动退化为 Mock tracer。
