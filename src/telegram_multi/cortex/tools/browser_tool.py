import logging
from typing import Dict, Any
from src.telegram_multi.browser_context import BrowserContext

class BrowserTool:
    """
    Adapter to expose BrowserContext safely to Agents.
    Executes actions like 'click', 'type', 'read' asynchronously.
    """
    def __init__(self, context: BrowserContext):
        self.context = context

    async def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a browser command.
        
        Args:
            command: Dict containing 'action' and parameters.
                     e.g. {"action": "click", "selector": "#btn"}
        
        Returns:
            Dict with "status" ("success"|"error") and "result" or "error".
        """
        action = command.get("action")
        selector = command.get("selector")
        
        try:
            page = self.context.page
            if not page:
                raise RuntimeError("Browser Page not initialized")

            if action == "click":
                # Default timeout 5s for agent interactions
                await page.click(selector, timeout=5000)
                return {"status": "success", "result": f"Clicked {selector}"}
            
            elif action == "type":
                text = command.get("text", "")
                await page.fill(selector, text, timeout=5000)
                return {"status": "success", "result": f"Typed '{text}' into {selector}"}
            
            # TODO: Add 'read', 'screenshot' etc.
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logging.error(f"BrowserTool Action Failed: {e}")
            return {
                "status": "error", 
                "error": str(e),
                # Optimization: In real world, dump HTML or screenshot here
            }
