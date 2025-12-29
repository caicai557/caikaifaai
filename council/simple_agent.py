#!/usr/bin/env python3
"""
Council Simple Agent - 最简智能体产品

特点：
1. 开发简单：单文件即可运行
2. 功能完整：目标 → 规划 → 执行 → 结果
3. 稳定可用：异常处理完善
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from datetime import datetime


@dataclass
class Task:
    """一个可执行的任务"""

    name: str
    description: str
    status: str = "pending"  # pending, running, done, failed
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentState:
    """智能体状态"""

    goal: str
    tasks: List[Task] = field(default_factory=list)
    current_step: int = 0
    completed: bool = False
    final_result: Optional[str] = None


class SimpleAgent:
    """
    最简智能体 - 自动规划并执行任务

    使用方法：
        agent = SimpleAgent()
        result = await agent.run("帮我分析这段代码的问题")
    """

    def __init__(
        self,
        name: str = "SimpleAgent",
        llm_fn: Optional[Callable] = None,
        max_steps: int = 5,
        verbose: bool = True,
    ):
        self.name = name
        self.llm_fn = llm_fn or self._mock_llm
        self.max_steps = max_steps
        self.verbose = verbose
        self.state: Optional[AgentState] = None

    async def run(self, goal: str) -> str:
        """运行智能体完成目标"""
        self._log(f"🎯 目标: {goal}")

        # 1. 初始化状态
        self.state = AgentState(goal=goal)

        # 2. 规划任务
        self._log("📋 规划中...")
        tasks = await self._plan(goal)
        self.state.tasks = tasks
        self._log(f"   生成 {len(tasks)} 个任务")

        # 3. 逐个执行
        for i, task in enumerate(tasks):
            if i >= self.max_steps:
                self._log(f"⚠️ 达到最大步数限制 ({self.max_steps})")
                break

            self.state.current_step = i + 1
            self._log(f"🔄 执行 [{i + 1}/{len(tasks)}]: {task.name}")

            try:
                task.status = "running"
                result = await self._execute(task)
                task.status = "done"
                task.result = result
                self._log("   ✅ 完成")
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                self._log(f"   ❌ 失败: {e}")

        # 4. 总结结果
        self._log("📊 总结中...")
        final = await self._summarize()
        self.state.completed = True
        self.state.final_result = final

        self._log("🏁 完成!")
        return final

    async def _plan(self, goal: str) -> List[Task]:
        """规划任务列表"""
        prompt = (
            f"请将以下目标分解为3-5个简单步骤:\n目标: {goal}\n返回格式: 每行一个步骤"
        )
        response = await self.llm_fn(prompt)

        # 解析响应为任务
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        tasks = []
        for i, line in enumerate(lines[:5]):  # 最多5个
            # 移除序号前缀
            clean = line.lstrip("0123456789.-) ").strip()
            if clean:
                tasks.append(Task(name=f"step_{i + 1}", description=clean))

        return tasks if tasks else [Task(name="step_1", description="执行用户请求")]

    async def _execute(self, task: Task) -> str:
        """执行单个任务"""
        prompt = f"请执行以下任务并返回结果:\n任务: {task.description}"
        return await self.llm_fn(prompt)

    async def _summarize(self) -> str:
        """总结所有结果"""
        if not self.state:
            return "无结果"

        results = []
        for task in self.state.tasks:
            if task.status == "done" and task.result:
                results.append(f"- {task.description}: {task.result[:100]}...")

        if not results:
            return "任务执行完成，但无具体输出"

        summary_prompt = f"""
基于以下任务结果，给出简洁总结：
目标: {self.state.goal}
任务结果:
{chr(10).join(results)}
"""
        return await self.llm_fn(summary_prompt)

    async def _mock_llm(self, prompt: str) -> str:
        """模拟 LLM 响应 (用于测试)"""
        await asyncio.sleep(0.1)  # 模拟延迟

        if "分解" in prompt or "步骤" in prompt:
            return """
1. 分析输入内容
2. 处理核心逻辑
3. 生成输出结果
"""
        elif "执行" in prompt:
            return f"已完成: {prompt[:50]}..."
        else:
            return "任务已完成，结果正常"

    def _log(self, msg: str):
        """输出日志"""
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] {self.name}: {msg}")


# ============================================
# 使用示例
# ============================================


async def main():
    """演示用法"""
    agent = SimpleAgent(name="DemoAgent")

    # 运行智能体
    result = await agent.run("帮我总结Python异步编程的要点")

    print("\n" + "=" * 50)
    print("📝 最终结果:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
