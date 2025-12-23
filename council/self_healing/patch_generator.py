"""
Patch Generator - LLM-powered code repair

Generates patches to fix failing tests based on diagnosis.
Uses Gemini or OpenAI to analyze errors and suggest fixes.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os
import re


from council.self_healing.loop import Diagnosis, Patch


class PatchGenerator:
    """
    LLM-powered patch generator
    
    Analyzes test failures and generates code patches.
    
    Usage:
        generator = PatchGenerator()
        diagnosis = generator.diagnose(error_output)
        patch = generator.generate_patch(diagnosis)
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initialize the patch generator
        
        Args:
            model: LLM model to use for analysis
        """
        self.model = model
        self._has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
        self._has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    
    def diagnose(self, error_output: str) -> Diagnosis:
        """
        Diagnose a test failure from error output
        
        Args:
            error_output: The stderr/stdout from test run
            
        Returns:
            Diagnosis with root cause analysis
        """
        # Extract failed test name
        failed_test = self._extract_failed_test(error_output)
        
        # Detect error type
        error_type = self._detect_error_type(error_output)
        
        # Extract error message
        error_message = self._extract_error_message(error_output)
        
        # Detect suspected file and line
        file_path, line_num = self._extract_location(error_output)
        
        # Determine root cause
        root_cause = self._analyze_root_cause(error_type, error_message)
        
        # Suggest fix
        suggested_fix = self._suggest_fix(error_type, error_message)
        
        return Diagnosis(
            failed_test=failed_test,
            error_type=error_type,
            error_message=error_message,
            suspected_file=file_path,
            suspected_line=line_num,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
        )
    
    def _extract_failed_test(self, output: str) -> str:
        """Extract the name of the failed test"""
        # Look for pytest FAILED pattern
        match = re.search(r"FAILED\s+([\w/\.:]+)", output)
        if match:
            return match.group(1)
        
        # Look for test:: pattern
        match = re.search(r"(test_\w+)", output)
        if match:
            return match.group(1)
        
        return "unknown_test"
    
    def _detect_error_type(self, output: str) -> str:
        """Detect the type of error"""
        error_types = [
            ("AssertionError", "assertion"),
            ("ImportError", "import"),
            ("ModuleNotFoundError", "import"),
            ("TypeError", "type"),
            ("AttributeError", "attribute"),
            ("NameError", "name"),
            ("ValueError", "value"),
            ("KeyError", "key"),
            ("IndexError", "index"),
            ("SyntaxError", "syntax"),
            ("IndentationError", "indentation"),
        ]
        
        for error, error_type in error_types:
            if error in output:
                return error_type
        
        return "unknown"
    
    def _extract_error_message(self, output: str) -> str:
        """Extract the core error message"""
        # Look for common patterns
        patterns = [
            r"AssertionError:\s*(.+)",
            r"Error:\s*(.+)",
            r"Exception:\s*(.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)[:500]
        
        # Return last 500 chars as fallback
        return output[-500:] if len(output) > 500 else output
    
    def _extract_location(self, output: str) -> tuple:
        """Extract file path and line number from error"""
        # Look for "File xxx, line N" pattern
        match = re.search(r'File "([^"]+)", line (\d+)', output)
        if match:
            return match.group(1), int(match.group(2))
        
        # Look for path:line pattern
        match = re.search(r"([\w/]+\.py):(\d+)", output)
        if match:
            return match.group(1), int(match.group(2))
        
        return None, None
    
    def _analyze_root_cause(self, error_type: str, error_message: str) -> str:
        """Analyze the root cause of the error"""
        causes = {
            "assertion": "Test assertion failed - expected value doesn't match actual",
            "import": "Module import failed - missing dependency or wrong path",
            "type": "Type mismatch - wrong argument type or return type",
            "attribute": "Missing attribute - object doesn't have expected property",
            "name": "Undefined name - variable or function not defined",
            "value": "Invalid value - argument has wrong value",
            "key": "Missing key - dictionary key not found",
            "index": "Index out of range - list access beyond bounds",
            "syntax": "Syntax error - invalid Python syntax",
            "indentation": "Indentation error - wrong whitespace",
        }
        
        return causes.get(error_type, f"Unknown error: {error_message[:100]}")
    
    def _suggest_fix(self, error_type: str, error_message: str) -> str:
        """Suggest a fix based on error type"""
        suggestions = {
            "assertion": "Check expected vs actual values and update test or implementation",
            "import": "Check module path and ensure dependency is installed",
            "type": "Verify argument types match function signature",
            "attribute": "Check object has the expected attribute or use getattr",
            "name": "Define the variable or import the required name",
            "value": "Validate input values before use",
            "key": "Check key exists or use .get() with default",
            "index": "Check list length before accessing by index",
            "syntax": "Fix syntax according to Python grammar",
            "indentation": "Fix indentation to match surrounding code",
        }
        
        return suggestions.get(error_type, "Review error message and stack trace")
    
    def generate_patch(self, diagnosis: Diagnosis) -> Patch:
        """
        Generate a patch to fix the diagnosed issue
        
        Args:
            diagnosis: The diagnosis from analyze step
            
        Returns:
            Patch with suggested fix
        """
        if not diagnosis.suspected_file:
            return Patch(
                file_path="",
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )
        
        # In production, this would call an LLM to generate the patch
        # For now, return a placeholder
        return Patch(
            file_path=diagnosis.suspected_file,
            original_content="",
            patched_content="",
            diagnosis=diagnosis,
            confidence=0.3,  # Low confidence without LLM
        )
    
    async def generate_patch_with_llm(self, diagnosis: Diagnosis) -> Patch:
        """
        Generate a patch using LLM
        
        Args:
            diagnosis: The diagnosis from analyze step
            
        Returns:
            Patch with LLM-generated fix
        """
        if not diagnosis.suspected_file or not os.path.exists(diagnosis.suspected_file):
            return Patch(
                file_path="",
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )
        
        # Read the file
        try:
            with open(diagnosis.suspected_file, 'r') as f:
                file_content = f.read()
        except Exception:
            return Patch(
                file_path=diagnosis.suspected_file,
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )
        
        # Build prompt for LLM
        prompt = f"""Fix the following test failure:

Error Type: {diagnosis.error_type}
Failed Test: {diagnosis.failed_test}
Error Message: {diagnosis.error_message}
File: {diagnosis.suspected_file}
Line: {diagnosis.suspected_line}
Root Cause: {diagnosis.root_cause}

Current file content:
```python
{file_content}
```

Provide only the fixed code, no explanations.
"""
        
        # Call LLM (placeholder - would use actual API)
        # patched_content = await self._call_llm(prompt)
        
        return Patch(
            file_path=diagnosis.suspected_file,
            original_content=file_content,
            patched_content=file_content,  # No change without LLM
            diagnosis=diagnosis,
            confidence=0.3,
        )


# Export
__all__ = ["PatchGenerator"]
