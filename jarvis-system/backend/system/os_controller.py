import platform
import subprocess
import os
import shutil
import logging
from typing import List, Dict, Union

logger = logging.getLogger("OSController")

class OSController:
    def __init__(self):
        self.os_type = platform.system()
        self.blocked_commands = ["rm -rf", "format", "mkfs"]

    def is_safe(self, command: str) -> bool:
        """
        Basic safety check.
        """
        for blocked in self.blocked_commands:
            if blocked in command:
                logger.warning(f"Blocked unsafe command: {command}")
                return False
        return True

    def open_file(self, path: str):
        if not os.path.exists(path):
            return f"File not found: {path}"
        
        try:
            if self.os_type == "Darwin":
                subprocess.run(["open", path], check=True)
            elif self.os_type == "Windows":
                 os.startfile(path)
            elif self.os_type == "Linux":
                subprocess.run(["xdg-open", path], check=True)
            return f"Opened {path}"
        except Exception as e:
            logger.error(f"Error opening file: {e}")
            return f"Error: {e}"

    def get_system_detail(self) -> Dict[str, str]:
        return {
            "os": self.os_type,
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor()
        }
