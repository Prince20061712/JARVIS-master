import subprocess
import os
import tempfile
import time
from typing import Dict, Any, Optional
from utils.logger import logger

class SafeExecutor:
    """
    Safely executes student code snippets (Python, C++, Java) in a sandboxed environment.
    Note: For production, this should use Docker. This implementation uses subprocess with limits.
    """
    def __init__(self, timeout: int = 5, memory_limit_mb: int = 128):
        self.timeout = timeout
        self.memory_limit = memory_limit_mb

    def execute_python(self, code: str) -> Dict[str, Any]:
        """Executes Python code and captures output."""
        return self._run_in_subprocess(["python3", "-c", code])

    def execute_cpp(self, code: str) -> Dict[str, Any]:
        """Compiles and executes C++ code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "main.cpp")
            exec_path = os.path.join(tmpdir, "main")
            
            with open(source_path, "w") as f:
                f.write(code)
            
            # Compile
            compile_res = subprocess.run(["g++", source_path, "-o", exec_path], capture_output=True, text=True)
            if compile_res.returncode != 0:
                return {"stdout": "", "stderr": compile_res.stderr, "exit_code": compile_res.returncode, "status": "compile_error"}
                
            return self._run_in_subprocess([exec_path])

    def execute_java(self, code: str) -> Dict[str, Any]:
        """Compiles and executes Java code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Java files must match class name; assuming 'Main' for snippets
            source_path = os.path.join(tmpdir, "Main.java")
            with open(source_path, "w") as f:
                f.write(code)
            
            # Compile
            compile_res = subprocess.run(["javac", source_path], capture_output=True, text=True)
            if compile_res.returncode != 0:
                return {"stdout": "", "stderr": compile_res.stderr, "exit_code": compile_res.returncode, "status": "compile_error"}
                
            return self._run_in_subprocess(["java", "-cp", tmpdir, "Main"])

    def _run_in_subprocess(self, cmd: list) -> Dict[str, Any]:
        """Helper to run a command with timeout and output capture."""
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            duration = time.time() - start_time
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "duration": round(duration, 3),
                "status": "success" if result.returncode == 0 else "runtime_error"
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": -1,
                "status": "timeout"
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "status": "error"
            }
