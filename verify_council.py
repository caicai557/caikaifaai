"""
Verification Script
Tests imports and instantiation of core Council components.
"""
import sys
import os

# Add project root (parent of 'council' dir) to path
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

def verify():
    print("🔍 Verifying Council Components...")

    try:
        print("1. Checking Configuration...")
        from council.config import config
        print(f"   ✅ Config loaded. Model: {config.DEFAULT_MODEL}")

        print("2. Checking Agents...")
        from council.agents.architect import Architect
        from council.agents.coder import Coder
        from council.agents.reviewer import Reviewer
        
        arch = Architect()
        coder = Coder()
        reviewer = Reviewer()
        print(f"   ✅ Agents instantiated: {arch.name}, {coder.name}, {reviewer.name}")

        print("3. Checking Orchestrator & 2025 Features...")
        from council.dev_orchestrator import DevOrchestrator
        from council.protocol.schema import CouncilState, DevStatus
        from council.context.rolling_context import RollingContext
        from council.sandbox.runner import SandboxRunner
        from council.mcp import ToolSearchTool
        
        orch = DevOrchestrator(verbose=False)
        print("   ✅ DevOrchestrator instantiated.")
        
        # Verify RollingContext
        if isinstance(orch.context, RollingContext):
            print(f"   ✅ RollingContext injected (max_tokens={orch.context.max_tokens}).")
        else:
            raise TypeError(f"Expected RollingContext, got {type(orch.context)}")

        # Verify Coder components
        if isinstance(orch.coder.sandbox, SandboxRunner):
            print(f"   ✅ Coder has SandboxRunner ({type(orch.coder.sandbox).__name__}).")
        else:
            raise TypeError(f"Expected SandboxRunner, got {type(orch.coder.sandbox)}")
            
        if hasattr(orch.coder, 'tool_search') and isinstance(orch.coder.tool_search, ToolSearchTool):
            print("   ✅ Coder has ToolSearchTool.")
        else:
            raise TypeError("Coder missing ToolSearchTool")
        
        # Verify State Machine components
        state = CouncilState(task="Test Task")
        assert state.status == DevStatus.ANALYZING
        print("   ✅ CouncilState initialized correctly.")

        print("\n🎉 Verification Successful! The system architecture is sound.")
        return 0

    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(verify())
