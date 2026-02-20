from typing import Dict, Any, List, Optional
from services.llm.local_llm import LocalLLM
from utils.logger import logger

class DebugAssistant:
    """
    Helps students debug errors using LLM-powered explanations and logic analysis.
    """
    def __init__(self, llm_service: Optional[LocalLLM] = None):
        self.llm = llm_service

    def parse_error(self, stderr: str) -> Dict[str, str]:
        """Extracts the error type and message from a stack trace."""
        lines = stderr.strip().splitlines()
        if not lines:
            return {"type": "Unknown", "message": "No error output found"}
        
        # Last line usually contains the error: "TypeError: ..."
        last_line = lines[-1]
        if ":" in last_line:
            err_type, msg = last_line.split(":", 1)
            return {"type": err_type.strip(), "message": msg.strip()}
        
        return {"type": "RuntimeError", "message": last_line}

    async def explain_error(self, code: str, stderr: str) -> str:
        """Uses LLM to explain why the code failed and how to fix it."""
        if not self.llm:
            return "I can see an error here, but my brain (LLM) isn't connected right now to explain it in depth."

        error_info = self.parse_error(stderr)
        prompt = f"""
I'm a student learning programming. My code failed with the following error:
Error Type: {error_info['type']}
Message: {error_info['message']}

Full Stack Trace:
{stderr}

My Code:
```python
{code}
```

Please:
1. Explain what this error means in simple terms.
2. Identify the specific line where it happened.
3. Suggest a fix with a code snippet.
4. Mention a common pitfall related to this.

Explanation:
"""
        return await self.llm.generate(prompt)

    def suggest_fixes(self, error_type: str) -> List[str]:
        """Provides generic 'quick-fix' tips based on error type."""
        fixes = {
            "IndentationError": ["Check if you mixed tabs and spaces", "Ensure all loops/blocks are indented"],
            "NameError": ["Check for typos in variable names", "Ensure variables are defined before use"],
            "IndexError": ["Check if you are accessing an empty list", "Remember that indices start at 0"],
            "KeyError": ["Use .get() for dictionaries to avoid this error", "Verify the key exists in the dict"]
        }
        return fixes.get(error_type, ["Review the logic near the line indicated in the stack trace."])
