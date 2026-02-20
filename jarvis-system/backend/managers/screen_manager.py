import datetime
import time
import pyautogui
import pygetwindow as gw
import mss
import mss.tools
from PIL import Image

class ScreenCaptureManager:
    """Manages screenshots and screen recording"""
    
    def take_screenshot(self, area="full"):
        """Take a screenshot"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if area == "full":
            filename = f"screenshot_full_{timestamp}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return f"Full screenshot saved as {filename}"
        
        elif area == "window":
            filename = f"screenshot_window_{timestamp}.png"
            active_window = gw.getActiveWindow()
            if active_window:
                screenshot = pyautogui.screenshot(region=(
                    active_window.left,
                    active_window.top,
                    active_window.width,
                    active_window.height
                ))
                screenshot.save(filename)
                return f"Window screenshot saved as {filename}"
            else:
                return "No active window found"
        
        else:
            try:
                coords = [int(x.strip()) for x in area.split(",")]
                if len(coords) == 4:
                    filename = f"screenshot_region_{timestamp}.png"
                    screenshot = pyautogui.screenshot(region=coords)
                    screenshot.save(filename)
                    return f"Region screenshot saved as {filename}"
                else:
                    return "Invalid region format. Use: x,y,width,height"
            except:
                return "Could not capture screenshot"
    
    def record_screen(self, duration=10):
        """Record screen (limited functionality)"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.gif"
        
        frames = []
        start_time = time.time()
        
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                
                while time.time() - start_time < duration:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                    frames.append(img)
                    time.sleep(0.1)
                
                if frames:
                    frames[0].save(
                        filename,
                        save_all=True,
                        append_images=frames[1:],
                        duration=100,
                        loop=0
                    )
                    return f"Screen recording saved as {filename}"
                else:
                    return "No frames captured"
        except:
            return "Screen recording failed. Try using QuickTime Player instead."
