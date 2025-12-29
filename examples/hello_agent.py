from council.agents.base_agent import BaseAgent, ExecuteResult, ThinkResult, Vote


class HelloAgent(BaseAgent):
    def __init__(self):
        super().__init__("HelloAgent", "You are a friendly agent.")

    def think(self, task, context=None):
        return ThinkResult("Thinking about " + task)

    def vote(self, proposal, context=None):
        return Vote("HelloAgent", "approve", 1.0, "Looks good")

    def execute(self, task, plan=None):
        import time

        time.sleep(1)  # Simulate work
        return ExecuteResult(
            True,
            f"# Hello from Council!\n\nI received your task: **{task}**\n\n- Step 1: Processed\n- Step 2: Done",
        )


agent = HelloAgent()
