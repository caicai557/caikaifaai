import asyncio
import logging
from typing import Dict, Any

from src.telegram_multi.config import TelegramConfig
from src.telegram_multi.cortex.db import CortexDB
from src.telegram_multi.cortex.logger import LogActor
from src.telegram_multi.cortex.actors.agent import AgentActor
from src.telegram_multi.cortex.actors.council import CouncilActor
from src.telegram_multi.cortex.tools.browser_tool import BrowserTool
from src.telegram_multi.browser_context import BrowserContext

async def bootstrap_system(config: TelegramConfig) -> Dict[str, Any]:
    """
    Initialize all actors and wiring.
    Returns a dictionary of ready-to-start components.
    """
    # 1. Infrastructure
    db = CortexDB("cortex.db") # TODO: Configurable path
    await db.initialize()
    
    logger = LogActor(db)
    
    # 2. Body (Browser)
    # Using the first instance or a specific one? For Council, maybe we launch instance_0
    # For now, let's assume we launch a generic context or specific one from config.
    # Just creating the object here.
    browser_ctx = BrowserContext(config.instances[0], config.global_settings) if config.instances else None
    
    # 3. Brain (Agents)
    # Create a primary agent
    agent = AgentActor("PrimaryAgent", logger)
    
    # 4. Wiring Body to Brain
    if browser_ctx:
        browser_tool = BrowserTool(browser_ctx)
        agent.register_tool("browser", browser_tool)
        
    # 5. Connect Real LLM (TODO: Configuration from secrets)
    # agent.set_llm_client(RealGeminiClient(api_key=...))
    
    # 6. Council Orchestrator
    council = CouncilActor(logger)
    # council.register_agent(agent) # Logic to be added to CouncilActor
    
    return {
        "db": db,
        "logger": logger,
        "browser": browser_ctx,
        "agent": agent,
        "council": council
    }

async def start_council(config: TelegramConfig):
    """
    Main Entry Point for the Council Mode.
    Launches everything and waits.
    """
    system = await bootstrap_system(config)
    
    actors = [
        system["logger"],
        system["agent"],
        system["council"]
    ]
    
    if system["browser"]:
        # Browser start is usually async but not an infinite loop actor style?
        # It's start() method in BrowserContext.
        # We wrap it or just await it.
        # Check BrowserContext.start()
        pass

    # Start Actors
    tasks = [asyncio.create_task(a.start()) for a in actors]
    
    # Start Browser if needed
    if system["browser"]:
         # Assuming browser.start() launches it. 
         # We might need to keep it alive? BrowserContext usually keeps alive until stopped.
         await system["browser"].start()

    print(">> Council System Started. Press Ctrl+C to stop.")
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Stopping...")
    finally:
        await system["db"].close()
