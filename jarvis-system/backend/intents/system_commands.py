import os
import subprocess
import sys
import platform
import webbrowser
import logging
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("SystemCommands")

class SystemCommandExecutor:
    def __init__(self):
        self.os_type = platform.system() # Windows, Darwin, Linux

    async def execute(self, intent) -> str:
        command = intent.name
        entities = intent.entities
        
        try:
            if command == "open_app" or command == "launch_app":
                return await self.open_app(entities.get("target"))
            elif command == "web_search":
                return await self.web_search(entities.get("target"))
            elif command == "system_info":
                return await self.get_system_info()
            elif command == "shutdown_system":
                return "Shutdown command simulation (safety mode)."
            else:
                return f"Command {command} not implemented yet."
        except Exception as e:
            logger.error(f"Error executing system command: {e}")
            return f"Error executing command: {str(e)}"

    async def open_app(self, app_name: str):
        if not app_name: return "No app name specified."
        
        logger.info(f"Opening app: {app_name}")
        
        if self.os_type == "Darwin": # macOS
            # Use 'open -a'
            subprocess.Popen(["open", "-a", app_name])
            return f"Opening {app_name}..."
        elif self.os_type == "Windows":
            # Very basic usage, might need specific paths
            os.system(f"start {app_name}")
            return f"Opening {app_name}..."
        else:
            return "OS not supported for detailed app launch yet."

    async def web_search(self, query: str):
        if not query: return "No query specified."
        url = f"https://duckduckgo.com/?q={query}"
        webbrowser.open(url)
        return f"Searching for {query}..."

    async def get_system_info(self):
        if not psutil:
            return "psutil not installed, cannot fetch system info."
        
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        return f"CPU Usage: {cpu_usage}%. RAM Usage: {memory.percent}%."
