import logging
import asyncio
try:
    import pyautogui
except ImportError:
    pyautogui = None

logger = logging.getLogger("AutomationEngine")

class AutomationEngine:
    def __init__(self):
        if pyautogui:
            pyautogui.FAILSAFE = True # Move mouse to corner to abort
            # Set a default pause
            pyautogui.PAUSE = 0.5 

    async def type_text(self, text: str, interval: float = 0.05):
        if not pyautogui:
            return "PyAutoGUI not installed."
        
        logger.info(f"Typing text: {text}")
        # Run in executor to avoid blocking async loop since pyautogui is blocking
        await asyncio.to_thread(pyautogui.write, text, interval=interval)
        return "Typed text."

    async def press_key(self, key: str):
        if not pyautogui: return "PyAutoGUI not installed."
        
        logger.info(f"Pressing key: {key}")
        await asyncio.to_thread(pyautogui.press, key)
        return f"Pressed {key}"

    async def take_screenshot(self, path: str = "screenshot.png"):
        if not pyautogui: return "PyAutoGUI not installed."
        
        logger.info("Taking screenshot")
        await asyncio.to_thread(pyautogui.screenshot, path)
        return f"Screenshot saved to {path}"
