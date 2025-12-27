import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional

class GeminiClient:
    def __init__(self, api_key: Optional[str], model_name: str = "gemini-2.0-flash"):
        # Configure is handled by Factory, but we can store key if needed
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, prompt: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate content using Gemini.
        Note: True 'function calling' in Gemini requires specific schema config.
        For Phase 8 Step 1, we might implement a text-based tool parser or use the native API if simple.
        For robustness, we'll start with text generation and basic prompt engineering if tools are requested.
        """
        # TODO: Implement proper Function Calling schema mapping
        
        try:
            # Simple text generation with heuristic parsing
            response = self.model.generate_content(prompt)
            text = response.text
            with open("llm_debug.log", "a") as f:
                f.write(f"\n---\nPROMPT: {prompt}\nRESPONSE: {text}\n---\n")
        except Exception as e:
            with open("llm_error.log", "a") as f:
                f.write(f"GENERATE ERROR: {e}\n")
            print(f"GENERATE ERROR: {e}")
            return {"content": f"Error: {e}", "tool_calls": []}

        tool_calls = []
        
        # Heuristic: Look for JSON blocks or lines with "action": "..."
        import re
        import json
        
        # Heuristic: Look for JSON blocks or lines with "action": "..."
        import re
        import json
        
        # Try to find a JSON block: { ... "action": ... }
        # Matches { "action": ... } multiline, non-greedy
        # We look for open brace, followed by anything, then "action", then anything, then close brace
        match = re.search(r'(\{.*?"action"\s*:\s*".*?\".*?\})', text, re.DOTALL | re.IGNORECASE)
        
        # If not found, try finding just the JSON block if it exists
        if not match:
             match = re.search(r'(\{.*\})', text, re.DOTALL)

        if match:
            try:
                # Clean up potential markdown code blocks if matched loosely
                json_str = match.group(1).strip()
                # Remove markdown fences if caught
                if json_str.startswith("```json"): json_str = json_str[7:]
                if json_str.startswith("```"): json_str = json_str[3:]
                if json_str.endswith("```"): json_str = json_str[:-3]
                
                tool_data = json.loads(json_str)
                # Map to Agent's expected structure
                tool_calls.append({
                    "name": "browser", 
                    "args": tool_data
                })
            except Exception as e:
                print(f"Failed to parse tool JSON: {e}")

        return {
            "content": text,
            "tool_calls": tool_calls
        }

class LLMFactory:
    @staticmethod
    def create_client(provider: str, model_name: Optional[str] = None):
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            
            # Support "Automatic Login" (ADC / Environment Defaults)
            if not api_key or "your_" in api_key:
                # Try to use default credentials or rely on library defaults
                # genai.configure() without params checks GOOGLE_API_KEY etc.
                genai.configure() 
            else:
                genai.configure(api_key=api_key)
            
            model = model_name or "gemini-2.0-flash"
            return GeminiClient(api_key if api_key and "your_" not in api_key else None, model)
        
        raise ValueError(f"Unknown provider: {provider}")
