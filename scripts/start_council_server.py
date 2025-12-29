#!/usr/bin/env python3
"""
Council MCP Server - Standard Entry Point for Claude Code
Exposes Project Council capabilities (Simulation, Governance, Memory) as MCP Tools.
"""
import sys
import os
from typing import List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' package not found. Install it via provided pip command.", file=sys.stderr)
    sys.exit(1)

from scripts.simulate import simulate_plan
from council.memory.knowledge_graph import KnowledgeGraph
from council.mcp.ai_council_server import AICouncilServer

# Initialize FastMCP
mcp = FastMCP("CesiCouncil")

# Initialize Singletons
kg = KnowledgeGraph()
council_server = AICouncilServer()

@mcp.tool()
async def simulate_plan_step(plan: List[str], dry_run: bool = True) -> List[str]:
    """
    Simulate a list of modifications against the project Knowledge Graph to detect risks.
    Use this BEFORE making destructive changes (delete, invasive refactor).
    """
    print(f"🔍 Simulating plan with dry_run={dry_run}: {plan}", file=sys.stderr)
    return simulate_plan(plan, kg, dry_run=dry_run)

@mcp.tool()
async def council_query(question: str) -> str:
    """
    Ask the AI Council (Gemini + OpenAI + Claude) for consensus advice.
    Use this for architectural decisions or when stuck.
    """
    print(f"⚖️ Council Query: {question}", file=sys.stderr)
    response = await council_server.query(question)
    return response.synthesis

@mcp.tool()
def council_search(query: str) -> str:
    """Search the Knowledge Graph using semantic hybrid search."""
    print(f"🔎 Semantic Search: {query}", file=sys.stderr)
    results = kg.search_hybrid(query)
    return str([{"name": e.name, "type": e.entity_type.value} for e in results])

@mcp.resource("council://graph/summary")
def get_graph_summary() -> str:
    """Get a textual summary of the project dependency graph."""
    return f"Knowledge Graph contains {len(kg.entities)} entities and {len(kg.relations)} relations."

if __name__ == "__main__":
    print("Starting Council MCP Server...", file=sys.stderr)
    mcp.run()
