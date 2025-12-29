#!/usr/bin/env python3
"""
Verification Script for MCP Upgrades (2025 Best Practices)
"""
import asyncio
from council.memory.knowledge_graph import KnowledgeGraph, EntityType
from scripts.simulate import check_syntax
from council.mcp.ai_council_server import AICouncilServer

def test_memory_bridge():
    print("\n[Testing Memory Bridge (Hybrid Search)]")
    kg = KnowledgeGraph(storage_path=".council/test_kg.gml", auto_load=False)

    # Add entities
    kg.add_entity("auth.py", EntityType.FILE, "auth_module", {"path": "src/auth.py"})
    kg.add_entity("auth_test.py", EntityType.FILE, "auth_test", {"path": "tests/auth_test.py"})

    # Test Hybrid Search (Fallback based)
    results = kg.search_hybrid("auth")
    print(f"Entities found for 'auth': {[e.name for e in results]}")

    assert len(results) >= 2, "Should find at least 2 auth related entities"
    print("✅ Memory Bridge Verified")

def test_cognitive_devtool():
    print("\n[Testing Cognitive DevTool (Simulation)]")
    kg = KnowledgeGraph(storage_path=".council/test_kg.gml", auto_load=False)

    # 1. Dependency Check
    kg.add_entity("core.py", EntityType.FILE, "core.py")
    kg.add_entity("plugin.py", EntityType.FILE, "plugin.py")
    # Add dependency: plugin depends on core
    # (Note: simulating KG structure)

    # 2. Syntax Check (Dry Run)
    valid_code = "print('Hello')"
    invalid_code = "print('Hello'"

    errors = check_syntax(valid_code)
    assert len(errors) == 0, "Valid code should have no errors"

    errors = check_syntax(invalid_code)
    assert len(errors) > 0, "Invalid code should have errors"
    print(f"Syntax Check Errors detected as expected: {errors[0]}")

    print("✅ Cognitive DevTool Verified")

async def test_swarm_orchestrator():
    print("\n[Testing Swarm Orchestrator (Semantic Router)]")
    server = AICouncilServer(models=[]) # Empty models to avoid API calls, just testing classification

    role = server._classify_request("How do I fix this security vulnerability in auth.py?")
    print(f"Query: 'How do I fix this security vulnerability...' -> Role: {role}")
    assert role == "security_auditor", "Should classify as security"

    role = server._classify_request("Refactor the class hierarchy for better scalability.")
    print(f"Query: 'Refactor the class hierarchy...' -> Role: {role}")
    assert role == "architect", "Should classify as architect"

    print("✅ Swarm Orchestrator Verified")

async def main():
    test_memory_bridge()
    test_cognitive_devtool()
    await test_swarm_orchestrator()
    print("\n🎉 ALL SYSTEMS GO! MCP Upgrades Verified.")

if __name__ == "__main__":
    asyncio.run(main())
