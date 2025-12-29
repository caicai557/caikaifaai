#!/usr/bin/env python3
"""
Basic Agent Example

演示如何使用 Council 框架创建和运行基本 Agent
"""

from council.agents import BaseAgent


# 创建自定义 Agent
class HelloAgent(BaseAgent):
    """简单的问候 Agent"""

    def __init__(self):
        super().__init__(
            name="HelloAgent",
            system_prompt="You are a friendly greeting agent.",
        )

    def greet(self, name: str) -> str:
        """发送问候"""
        return f"Hello, {name}! Welcome to Council."


def main():
    # 创建 Agent
    agent = HelloAgent()
    print(f"Created agent: {agent.name}")

    # 发送问候
    greeting = agent.greet("Developer")
    print(greeting)

    # 显示 Agent 信息
    print(f"Model: {agent.model}")
    print(f"Allow delegation: {agent.allow_delegation}")


if __name__ == "__main__":
    main()
