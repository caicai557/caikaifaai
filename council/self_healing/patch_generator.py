"""
Patch Generator - LLM-powered code repair

Generates patches to fix failing tests based on diagnosis.
Uses Gemini or OpenAI to analyze errors and suggest fixes.
"""

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

    def __init__(self, model: str = None):
        """
        Initialize the patch generator

        Args:
            model: LLM model to use for analysis (auto-detected if None)
        """
        self._has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
        self._has_openai = bool(os.environ.get("OPENAI_API_KEY"))
        self._has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

        # Auto-detect model based on available API keys
        if model:
            self.model = model
        elif self._has_anthropic:
            self.model = "claude-sonnet-4-20250514"
        elif self._has_openai:
            self.model = "gpt-4o"
        elif self._has_gemini:
            self.model = "gemini-2.0-flash"
        else:
            self.model = "claude-sonnet-4-20250514"  # Default

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

        [2025 Best Practice] Now uses real LLM to generate patches.

        Args:
            diagnosis: The diagnosis from analyze step

        Returns:
            Patch with LLM-generated fix
        """
        if not diagnosis.suspected_file:
            return Patch(
                file_path="",
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )

        # Check if file exists
        import os

        if not os.path.exists(diagnosis.suspected_file):
            return Patch(
                file_path=diagnosis.suspected_file,
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )

        # [2025 Activation] Use async LLM call via sync wrapper
        try:
            import asyncio

            # Try to get running loop, create new if needed
            try:
                asyncio.get_running_loop()
                # If we're already in an async context, create a task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.generate_patch_with_llm(diagnosis)
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self.generate_patch_with_llm(diagnosis))
        except Exception:
            # Fallback on any error
            return Patch(
                file_path=diagnosis.suspected_file,
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.1,
            )

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM (Gemini preferred, fallback to OpenAI)

        Args:
            prompt: The prompt to send

        Returns:
            The raw text response
        """
        system_prompt = "You are an expert Python developer tasked with fixing code bugs. Return ONLY the fixed code block."

        # Try Gemini
        if self._has_gemini:
            try:
                import google.generativeai as genai

                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction=system_prompt,
                )
                response = await model.generate_content_async(prompt)
                return response.text
            except Exception:
                # Log error or continue to fallback
                pass

        # Try OpenAI
        if self._has_openai:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                )
                return response.choices[0].message.content
            except Exception:
                pass

        return ""

    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks"""
        # Match ```python ... ``` or just ``` ... ```
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

        # If no blocks, assumes the whole text is code if it looks like code
        # But safer to return original text if no blocks found, or try to be smart
        # For this implementation, we'll assume valid LLM output has blocks or is raw code
        if "def " in text or "import " in text or "class " in text:
            return text.strip()

        return ""

    def _construct_prompt(self, diagnosis: Diagnosis, file_content: str) -> str:
        """Construct the prompt for the LLM"""
        return f"""Fix the following test failure:

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

Provide ONLY the valid Python code for the entire file (with the fix applied).
Do not include any explanations, markers, or text outside the code block.
"""

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
            with open(diagnosis.suspected_file, "r") as f:
                file_content = f.read()
        except Exception:
            return Patch(
                file_path=diagnosis.suspected_file,
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )

        # Build prompt
        prompt = self._construct_prompt(diagnosis, file_content)

        # Call LLM
        raw_response = await self._call_llm(prompt)

        if not raw_response:
            return Patch(
                file_path=diagnosis.suspected_file,
                original_content=file_content,
                patched_content=file_content,
                diagnosis=diagnosis,
                confidence=0.0,
            )

        # Parse response
        patched_content = self._extract_code_block(raw_response)

        # Calculate naive confidence (if content changed)
        confidence = 0.8 if patched_content != file_content else 0.0

        return Patch(
            file_path=diagnosis.suspected_file,
            original_content=file_content,
            patched_content=patched_content,
            diagnosis=diagnosis,
            confidence=confidence,
        )


# Export
__all__ = ["PatchGenerator"]
