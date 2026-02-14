#!/usr/bin/env python3
"""
JARVIS - SUPER ENHANCED COMPLETE VERSION
Complete AI Assistant with ALL macOS Applications & Features
Just A Rather Very Intelligent System
Enhanced with Local Ollama AI - ALL RESPONSES SPOKEN VIA SPEAKERS.

FEATURES:
✅ Auto-starts Ollama server
✅ Opens ALL macOS apps (Notes, Camera, Photo Booth, Safari, etc.)
✅ Web browsing & search
✅ YouTube & Spotify music
✅ Screenshots & screen recording
✅ Code editing in VS Code/TextEdit
✅ System utilities
✅ File management
✅ Voice typing
✅ And much more...
"""

import os
import sys
import json
import time
import datetime
import random
import webbrowser
import subprocess
import threading
import queue
import speech_recognition as sr
import pyttsx3
import pywhatkit
import wikipedia
import requests
import pyautogui
import psutil
import platform
import pyjokes
import smtplib
from email.message import EmailMessage
import pyperclip
import screen_brightness_control as sbc
from plyer import notification
import select
import cv2
from bs4 import BeautifulSoup
import re
import atexit
import shutil
import hashlib
import urllib.parse
from PIL import Image
import pygetwindow as gw
import mss
import mss.tools
import pyfiglet
from colorama import init, Fore, Back, Style
import getpass
import socket
import uuid
import pickle
from pathlib import Path
import zipfile
import tarfile
import base64
import sqlite3
import csv
import xml.etree.ElementTree as ET
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

import uvicorn
from core.ai_brain import EnhancedAIBrain

# Initialize colorama
init(autoreset=True)

# ========== CONFIGURATION SECTION ==========
USER_NAME = "Prince"
JARVIS_NAME = "Jarvis"
CONTINUOUS_MODE = True
WAKE_WORD = "jarvis"
ENABLE_LOCAL_AI = True
OLLAMA_MODEL = "llama3.2:1b"
ENABLE_TERMINAL_VOICE = False # Set to False to prevent backend from speaking (prevents feedback loop)

# ========== FASTAPI & WEBSOCKET SETUP ==========
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

# ========== ENHANCED AUDIO SYSTEM ==========
class AudioSystem:
    """Enhanced audio system for better speech control"""
    
    def __init__(self, websocket_manager=None, loop=None):
        self.websocket_manager = websocket_manager
        self.loop = loop
        self.engine = None
        try:
            # Use Edge TTS for high quality voice
            from core.system.tts_engine import EdgeTTSEngine
            self.engine = EdgeTTSEngine(voice="en-US-ChristopherNeural")
            print(f"{Fore.GREEN}🔊 Initialized Edge TTS (Voice: Christopher)")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Could not initialize Edge TTS engine: {e}")
            print(f"{Fore.YELLOW}⚠️  Running in text-only mode (backend voice disabled)")
        
        self.volume_level = 80
        self.speech_rate = 175
        self.volume_level = 80
        self.speech_rate = 175
        self._ensure_audio_output()
        
    def _ensure_audio_output(self):
        """Ensure audio output is properly configured"""
        print(f"\n{Fore.CYAN}🔊 Configuring Audio System...")
        if self.engine:
            try:
                # Simple test
                pass
            except Exception:
                pass
                # self.engine.runAndWait()
                print(f"{Fore.GREEN}✅ Audio output configured")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Audio test warning: {e}")
            
            try:
                self.engine.setProperty('volume', 0.9)
                self.engine.setProperty('rate', 175)
                print(f"{Fore.CYAN}🔊 Volume: 90% | Rate: 175 wpm")
            except:
                pass
        else:
            print(f"{Fore.YELLOW}🔊 Audio System: WebSocket-only mode")
    
    def configure_jarvis_voice(self):
        """Configure pyttsx3 to sound more like JARVIS"""
        if not self.engine: return
        
        try:
            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 0.9)
            
            voices = self.engine.getProperty('voices')
            preferred_voices = ['daniel', 'alex', 'fred', 'samantha']
            for voice in voices:
                voice_name = voice.name.lower()
                for pref in preferred_voices:
                    if pref in voice_name:
                        self.engine.setProperty('voice', voice.id)
                        print(f"{Fore.CYAN}🔊 Selected voice: {voice.name}")
                        return
            
            if len(voices) > 0:
                self.engine.setProperty('voice', voices[0].id)
                print(f"{Fore.CYAN}🔊 Using voice: {voices[0].name}")
        except:
            pass
    
    def set_volume(self, level):
        """Set speech volume (0.0 to 1.0)"""
        if not self.engine: return 0
        
        try:
            level = max(0.0, min(1.0, level))
            self.engine.setProperty('volume', level)
            self.volume_level = level * 100
            print(f"{Fore.CYAN}🔊 Volume set to: {self.volume_level:.0f}%")
            return self.volume_level
        except:
            return 0
    
    def get_volume(self):
        """Get current volume level"""
        if not self.engine: return 0
        try:
            return self.engine.getProperty('volume')
        except:
            return 0
    
    def set_rate(self, rate):
        """Set speech rate (words per minute)"""
        if not self.engine: return
        try:
            self.engine.setProperty('rate', rate)
            self.speech_rate = rate
            print(f"{Fore.CYAN}🔊 Speech rate set to: {rate} wpm")
        except:
            pass
    
    def speak(self, text, play_beep=False, rate=None, on_complete=None, on_start=None):
        """Speak text using Edge TTS (High Quality)"""
        if not text:
            if on_complete: on_complete()
            return

        print(f"{Fore.GREEN}{JARVIS_NAME}: {text}")
        
        # 1. Send text to frontend immediately (no animation)
        if self.websocket_manager and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.websocket_manager.broadcast({
                        "type": "text",
                        "text": text
                    }),
                    self.loop
                )
            except Exception as e:
                print(f"{Fore.RED}Error broadcasting to WebSocket: {e}")

        # 2. Speak audio locally
        if self.engine:
            try:
                # Pass on_start to trigger animation exactly when audio starts
                # Check signature compatibility
                if 'on_start' in self.engine.speak.__code__.co_varnames:
                    self.engine.speak(text, on_complete=on_complete, on_start=on_start)
                else:
                    # Fallback for older engine versions
                    if on_start: on_start()
                    self.engine.speak(text, on_complete=on_complete)
            except Exception as e:
                print(f"{Fore.RED}Error in speech synthesis: {e}")
                if on_complete: on_complete()
        else:
             if on_complete: on_complete()
    
    def play_beep(self, type="response"):
        """Play different beep sounds"""
        try:
            if type == "response":
                print('\a', end='', flush=True)
                # time.sleep(0.1)
                # print('\a', end='', flush=True)
            elif type == "listening":
                print('\a', end='', flush=True)
            elif type == "error":
                print('\a', end='', flush=True)
            elif type == "ai_processing":
                print('\a', end='', flush=True)
        except:
            pass
    
    def test_speakers(self):
        """Test audio output on all speakers"""
        print(f"\n{Fore.CYAN}🔊 Testing audio system...")
        test_messages = [
            "Audio system test one.",
            "Audio system test two.",
            "Audio system test three.",
            "Audio system verification complete."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"{Fore.CYAN}🔊 Test {i}: {message}")
            self.speak(message)
            time.sleep(0.8)
        
        self.speak("Audio system test complete. All speakers are functional.")
        print(f"{Fore.GREEN}✅ Audio system test complete")
        return True
    
    def adjust_system_volume(self, direction="up"):
        """Adjust macOS system volume"""
        try:
            if direction == "up":
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
                self.speak("System volume increased.")
            elif direction == "down":
                os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
                self.speak("System volume decreased.")
            elif direction == "mute":
                os.system("osascript -e 'set volume output muted true'")
                self.speak("System audio muted.")
            elif direction == "unmute":
                os.system("osascript -e 'set volume output muted false'")
                self.speak("System audio unmuted.")
            elif direction == "max":
                os.system("osascript -e 'set volume output volume 100'")
                self.speak("System volume set to maximum.")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  System volume adjustment failed: {e}")


# ========== APPLICATION MANAGER ==========
class ApplicationManager:
    """Manages all macOS applications"""
    
    def __init__(self):
        self.applications = {
            # Productivity
            "notes": "Notes",
            "notepad": "TextEdit",
            "textedit": "TextEdit",
            "calculator": "Calculator",
            "calendar": "Calendar",
            "reminders": "Reminders",
            "stickies": "Stickies",
            
            # Development
            "vscode": "Visual Studio Code",
            "code": "Visual Studio Code",
            "terminal": "Terminal",
            "iterm": "iTerm",
            "xcode": "Xcode",
            "pycharm": "PyCharm",
            "sublime": "Sublime Text",
            
            # Browsers
            "safari": "Safari",
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "edge": "Microsoft Edge",
            
            # Media & Camera
            "camera": "Photo Booth",
            "photo booth": "Photo Booth",
            "photos": "Photos",
            "quicktime": "QuickTime Player",
            "facetime": "FaceTime",
            
            # Music & Video
            "spotify": "Spotify",
            "music": "Music",
            "apple music": "Music",
            "itunes": "Music",
            "videos": "TV",
            "tv": "TV",
            
            # Communication
            "messages": "Messages",
            "whatsapp": "WhatsApp",
            "discord": "Discord",
            "slack": "Slack",
            "mail": "Mail",
            "outlook": "Microsoft Outlook",
            
            # Utilities
            "finder": "Finder",
            "activity monitor": "Activity Monitor",
            "disk utility": "Disk Utility",
            "system preferences": "System Preferences",
            "settings": "System Preferences",
            
            # Creative
            "preview": "Preview",
            "garageband": "GarageBand",
            "imovie": "iMovie",
            "keynote": "Keynote",
            "pages": "Pages",
            "numbers": "Numbers",
            
            # Other
            "app store": "App Store",
            "books": "Books",
            "podcasts": "Podcasts",
            "maps": "Maps",
            "contacts": "Contacts",
            "weather": "Weather"
        }
    
    def open_application(self, app_name):
        """Open a macOS application"""
        app_name_lower = app_name.lower()
        
        if app_name_lower in self.applications:
            app_command = self.applications[app_name_lower]
            
            try:
                os.system(f'open -a "{app_command}"')
                return f"{app_command} opened successfully"
            except:
                return f"Could not open {app_command}"
        
        for key, app_command in self.applications.items():
            if key in app_name_lower:
                try:
                    os.system(f'open -a "{app_command}"')
                    return f"{app_command} opened successfully"
                except:
                    return f"Could not open {app_command}"
        
        return "Application not found"
    
    def close_application(self, app_name):
        """Close a macOS application"""
        try:
            os.system(f'pkill -f "{app_name}"')
            return f"{app_name} closed"
        except:
            return f"Could not close {app_name}"
    
    def list_applications(self):
        """List all available applications"""
        return list(self.applications.keys())

# ========== BROWSER MANAGER ==========
class BrowserManager:
    """Manages web browsing and search"""
    
    def __init__(self):
        self.browsers = {
            "chrome": "Google Chrome",
            "safari": "Safari",
            "firefox": "Firefox",
            "brave": "Brave Browser",
            "edge": "Microsoft Edge"
        }
        self.default_browser = "chrome"
    
    def search_web(self, query, browser=None):
        """Search the web"""
        if not browser:
            browser = self.default_browser
        
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        if browser in self.browsers:
            try:
                os.system(f'open -a "{self.browsers[browser]}" "{search_url}"')
                return f"Searching for '{query}' in {self.browsers[browser]}"
            except:
                webbrowser.open(search_url)
                return f"Searching for '{query}' in default browser"
        else:
            webbrowser.open(search_url)
            return f"Searching for '{query}' in default browser"
    
    def open_website(self, url, browser=None):
        """Open a specific website"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        if browser and browser in self.browsers:
            try:
                os.system(f'open -a "{self.browsers[browser]}" "{url}"')
                return f"Opening {url} in {self.browsers[browser]}"
            except:
                webbrowser.open(url)
                return f"Opening {url} in default browser"
        else:
            webbrowser.open(url)
            return f"Opening {url} in default browser"
    
    def open_youtube(self, query=None):
        """Open YouTube"""
        if query:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            message = f"Searching YouTube for '{query}'"
        else:
            url = "https://www.youtube.com"
            message = "Opening YouTube"
        
        webbrowser.open(url)
        return message
    
    def open_spotify(self, query=None):
        """Open Spotify"""
        if query:
            url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
            message = f"Searching Spotify for '{query}'"
        else:
            try:
                os.system('open -a "Spotify"')
                return "Opening Spotify app"
            except:
                url = "https://open.spotify.com"
                message = "Opening Spotify web player"
        
        webbrowser.open(url)
        return message

# ========== MEDIA MANAGER ==========
class MediaManager:
    """Manages media playback and control"""
    
    def play_youtube_video(self, query):
        """Play YouTube video using pywhatkit"""
        try:
            pywhatkit.playonyt(query)
            return f"Playing '{query}' on YouTube"
        except Exception as e:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching YouTube for '{query}'"
    
    def play_spotify_song(self, query):
        """Play Spotify song (opens in web player)"""
        url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching Spotify for '{query}'"
    
    def play_music(self, query, service="youtube"):
        """Play music on specified service"""
        if service.lower() == "spotify":
            return self.play_spotify_song(query)
        else:
            return self.play_youtube_video(query)
    
    def control_media(self, action):
        """Control media playback"""
        actions = {
            "play": "space",
            "pause": "space",
            "stop": "space",
            "next": "right",
            "previous": "left",
            "volume up": "up",
            "volume down": "down"
        }
        
        if action in actions:
            try:
                pyautogui.press(actions[action])
                return f"Media { action} executed"
            except:
                return f"Could not {action} media"
        else:
            return f"Unknown media action: {action}"

# ========== SCREEN CAPTURE MANAGER ==========
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

# ========== CODE EDITOR MANAGER ==========
class CodeEditorManager:
    """Manages code editing and file creation"""
    
    def create_code_file(self, filename, language="python", content=""):
        """Create a code file"""
        if not '.' in filename:
            if language == "python":
                filename += ".py"
            elif language == "javascript":
                filename += ".js"
            elif language == "html":
                filename += ".html"
            elif language == "css":
                filename += ".css"
            elif language == "java":
                filename += ".java"
            else:
                filename += ".txt"
        
        try:
            with open(filename, "w") as f:
                if content:
                    f.write(content)
                else:
                    if language == "python":
                        f.write(f'#!/usr/bin/env python3\n"""\n{filename}\n"""\n\n')
                    elif language == "html":
                        f.write(f'<!DOCTYPE html>\n<html>\n<head>\n<title>{filename}</title>\n</head>\n<body>\n\n</body>\n</html>')
            
            return f"Created {filename} with {language} content"
        except Exception as e:
            return f"Could not create file: {e}"
    
    def open_in_vscode(self, filename=None):
        """Open file or folder in VS Code"""
        try:
            if filename:
                os.system(f'code "{filename}"')
                return f"Opening {filename} in VS Code"
            else:
                os.system("code .")
                return "Opening current directory in VS Code"
        except:
            return "VS Code not found. Install it from https://code.visualstudio.com/"
    
    def write_code(self, code, filename="code.py"):
        """Write code to a file"""
        try:
            with open(filename, "a") as f:
                f.write(code + "\n")
            return f"Code written to {filename}"
        except:
            return "Could not write code"

# ========== SYSTEM UTILITIES MANAGER ==========
class SystemUtilitiesManager:
    """Manages system utilities"""
    
    def get_system_info(self):
        """Get detailed system information"""
        info = {
            "OS": platform.platform(),
            "Processor": platform.processor(),
            "CPU Cores": psutil.cpu_count(logical=False),
            "CPU Threads": psutil.cpu_count(logical=True),
            "CPU Usage": f"{psutil.cpu_percent()}%",
            "Memory Total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
            "Memory Used": f"{psutil.virtual_memory().used / (1024**3):.2f} GB",
            "Memory Free": f"{psutil.virtual_memory().free / (1024**3):.2f} GB",
            "Memory Percent": f"{psutil.virtual_memory().percent}%",
            "Disk Total": f"{psutil.disk_usage('/').total / (1024**3):.2f} GB",
            "Disk Used": f"{psutil.disk_usage('/').used / (1024**3):.2f} GB",
            "Disk Free": f"{psutil.disk_usage('/').free / (1024**3):.2f} GB",
            "Disk Percent": f"{psutil.disk_usage('/').percent}%",
            "Boot Time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return info
    
    def get_network_info(self):
        """Get network information"""
        try:
            interfaces = psutil.net_if_addrs()
            io_counters = psutil.net_io_counters()
            
            info = {
                "Bytes Sent": f"{io_counters.bytes_sent / (1024**2):.2f} MB",
                "Bytes Received": f"{io_counters.bytes_recv / (1024**2):.2f} MB",
                "Packets Sent": io_counters.packets_sent,
                "Packets Received": io_counters.packets_recv,
                "Network Interfaces": list(interfaces.keys())
            }
            
            return info
        except:
            return {"error": "Could not get network info"}
    
    def get_battery_info(self):
        """Get battery information"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                info = {
                    "Percent": f"{battery.percent}%",
                    "Plugged In": battery.power_plugged,
                    "Time Left": f"{battery.secsleft // 3600}:{(battery.secsleft % 3600) // 60:02d}" if battery.secsleft != -1 else "Unknown"
                }
                return info
            else:
                return {"info": "No battery detected (desktop)"}
        except:
            return {"error": "Could not get battery info"}
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            temp_dir = "/tmp"
            count = 0
            
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        count += 1
                except:
                    pass
            
            return f"Cleaned up {count} temporary files"
        except:
            return "Could not clean temporary files"

    def get_weather(self, city):
        """Get weather for a specific city"""
        try:
            # Use wttr.in service
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t"
            response = requests.get(url)
            if response.status_code == 200:
                weather_info = response.text.strip()
                return f"The weather in {city} is {weather_info}."
            else:
                return f"Could not get weather for {city}."
        except Exception as e:
            return f"Error getting weather: {str(e)}"

# ========== VOICE TYPING MANAGER ==========
class VoiceTypingManager:
    """Manages voice typing and text input"""
    
    def type_text(self, text):
        """Type text using keyboard"""
        try:
            pyautogui.write(text, interval=0.05)
            return f"Typed: {text[:50]}..." if len(text) > 50 else f"Typed: {text}"
        except:
            return "Could not type text"
    
    def type_from_clipboard(self):
        """Type text from clipboard"""
        try:
            text = pyperclip.paste()
            if text:
                pyautogui.write(text, interval=0.05)
                return f"Typed from clipboard: {text[:50]}..."
            else:
                return "Clipboard is empty"
        except:
            return "Could not type from clipboard"
    
    def voice_to_text(self, audio_system, recognizer):
        """Convert voice to text and type it"""
        try:
            with sr.Microphone() as source:
                audio_system.speak("Speak now, I'm listening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
                text = recognizer.recognize_google(audio)
                
                pyautogui.write(text, interval=0.05)
                return f"Voice typed: {text[:100]}..."
        except Exception as e:
            return f"Voice typing failed: {str(e)}"

# ========== FILE MANAGER ==========
class FileManager:
    """Manages file operations"""
    
    def list_files(self, directory="."):
        """List files in directory"""
        try:
            files = os.listdir(directory)
            return f"Files in {directory}: {', '.join(files[:10])}" + ("..." if len(files) > 10 else "")
        except:
            return f"Could not list files in {directory}"
    
    def create_file(self, filename):
        """Create a new file"""
        try:
            with open(filename, 'w') as f:
                pass
            return f"Created file: {filename}"
        except:
            return f"Could not create file: {filename}"
    
    def delete_file(self, filename):
        """Delete a file"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return f"Deleted file: {filename}"
            else:
                return f"File not found: {filename}"
        except:
            return f"Could not delete file: {filename}"
    
    def copy_file(self, source, destination):
        """Copy a file"""
        try:
            shutil.copy2(source, destination)
            return f"Copied {source} to {destination}"
        except:
            return f"Could not copy {source} to {destination}"
    
    def move_file(self, source, destination):
        """Move a file"""
        try:
            shutil.move(source, destination)
            return f"Moved {source} to {destination}"
        except:
            return f"Could not move {source} to {destination}"

# ========== MAIN JARVIS CLASS ==========
class JarvisAI:
    def __init__(self, websocket_manager=None, loop=None):
        # Display banner
        print(f"{Fore.CYAN}{'='*70}")
        ascii_art = pyfiglet.figlet_format("J.A.R.V.I.S", font="slant")
        print(f"{Fore.CYAN}{ascii_art}")
        print(f"{Fore.CYAN}Enhanced Protocol Activated")
        print(f"{Fore.CYAN}AUTO-STARTING OLLAMA FOR LOCAL AI")
        print(f"{Fore.CYAN}{'='*70}")
        
        self.loop = loop
        
        # Initialize managers
        print(f"\n{Fore.CYAN}🚀 INITIALIZING SYSTEMS...")
        
        atexit.register(self.cleanup)
        
        # Initialize all managers
        print(f"\n{Fore.CYAN}🔊 Initializing Audio System...")
        self.audio = AudioSystem(websocket_manager, loop)
        self.audio.play_beep("response")
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.command_queue = queue.Queue()
        self.is_listening = CONTINUOUS_MODE
        self.command_queue = queue.Queue()
        self.is_listening = CONTINUOUS_MODE
        self.is_running = True
        self.voice_enabled = False # Start with voice disabled
        self.is_client_speaking = False # Track if client is speaking
        self.is_jarvis_speaking = False # Track if JARVIS is speaking
        
        print(f"\n{Fore.CYAN}🤖 Loading Enhanced AI Brain (Modular)...")
        # Initialize AI Brain
        try:
            # Use centralized data directory
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            self.ai_brain = EnhancedAIBrain(USER_NAME, data_dir=data_dir)
            print(f"{Fore.GREEN}✅ AI Brain loaded successfully")
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading AI Brain: {e}")
            # Fallback mock object
            class DummyBrain:
                def process_input(self, x): return {"user_input": x}
                async def generate_response(self, x): return "AI Brain offline. Using basic responses."
                def get_brain_status(self): return {"local_ai": {"available": False}}
                def save_state(self): pass
            
            self.ai_brain = DummyBrain()
        
        ai_status = self.ai_brain.get_brain_status()
        if ai_status.get("local_ai", {}).get("available", False):
            print(f"{Fore.GREEN}🤖 Local AI: ONLINE ({ai_status['local_ai'].get('model', 'Unknown')})")
        else:
            print(f"{Fore.YELLOW}🤖 Local AI: OFFLINE")
        
        # Initialize all feature managers
        self.app_manager = ApplicationManager()
        self.browser_manager = BrowserManager()
        self.media_manager = MediaManager()
        self.screen_capture = ScreenCaptureManager()
        self.code_editor = CodeEditorManager()
        self.system_utils = SystemUtilitiesManager()
        self.voice_typing = VoiceTypingManager()
        self.file_manager = FileManager()
        
        # Skills registry
        self.skills = self.register_skills()
        
        self.jarvis_responses = {
            "startup": [
                "Hello, I am JARVIS. Online and ready.",
                "System activated. JARVIS at your service.",
                "Initialization complete. All systems operational.",
                "JARVIS protocol engaged. How may I assist you?"
            ],
            "greeting": [
                f"Hello {USER_NAME}. How may I help you today?",
                f"Good day, {USER_NAME}. What can I do for you?",
                f"Online and operational, {USER_NAME}. Your command?",
                f"Systems nominal, {USER_NAME}. Ready for instructions."
            ],
            "affirmative": [
                "Affirmative.",
                "Understood.",
                "Processing.",
                "Executing.",
                "Confirmed.",
                "Right away.",
                "Working on it."
            ]
        }
        
        print(f"\n{Fore.GREEN}{JARVIS_NAME} Initialization Complete!")
        print(f"{Fore.CYAN}AI Brain: Active")
        print(f"{Fore.CYAN}Mode: {'Continuous Conversation' if CONTINUOUS_MODE else 'Wake Word Activated'}")
        print(f"{Fore.CYAN}User: {USER_NAME}")
        print(f"{Fore.CYAN}Ollama Auto-Start: {'Enabled' if ENABLE_LOCAL_AI else 'Disabled'}")
        
        audio_vol = int(self.audio.get_volume() * 100)
        print(f"{Fore.CYAN}🔊 Audio Status: Volume {audio_vol}%, Rate: {self.audio.speech_rate} wpm")
        print(f"{Fore.YELLOW}💡 Try saying 'test audio' to check your speakers")
        
        time.sleep(0.5)
        
        ai_status = self.ai_brain.get_brain_status()
        if ai_status.get("local_ai", {}).get("available", False):
            welcome = f"Hello {USER_NAME}, I am JARVIS with enhanced AI capabilities. Ollama server started automatically. Local intelligence is online. All systems are ready to assist you."
            self.audio.speak(welcome, play_beep=True)
        else:
            welcome = f"Hello {USER_NAME}, I am JARVIS. Basic AI systems online. For advanced AI, I tried to start Ollama but it's not available. How can I help you?"
            self.audio.speak(welcome, play_beep=True)
    
    def cleanup(self):
        """Cleanup function"""
        print(f"\n{Fore.CYAN}🧹 Cleaning up...")
        if hasattr(self, 'ai_brain') and hasattr(self.ai_brain, 'save_state'):
            self.ai_brain.save_state()
    
    def set_client_speaking(self, speaking):
        """Set client speaking status to prevent feedback loop"""
        self.is_client_speaking = speaking
        if speaking:
            print(f"{Fore.MAGENTA}🔇 Client speaking - Pausing backend listening...")
        else:
            print(f"{Fore.MAGENTA}👂 Client finished speaking - Resuming listening...")

    def speak(self, text, play_beep=False, rate=None):
        """Wrapper for audio system speak"""
        if ENABLE_TERMINAL_VOICE:
            self.audio.speak(text, play_beep, rate)
        elif self.audio.websocket_manager and self.loop:
            # If terminal voice disabled, still send to frontend
            print(f"{Fore.GREEN}{JARVIS_NAME} (Silent): {text}")
            try:
                # Basic check to avoid double sending if AudioSystem also sends it
                # But AudioSystem.speak handles the broadcast. 
                # We need to bypass the local engine.say but keep the broadcast.
                # It's cleaner to let AudioSystem handle the logic if we modify it, 
                # but essentially we want the 'text' to go to the frontend.
                
                # Let's use the existing audio.speak but force it to skip local TTS if config is set
                # Actually, easier to modify AudioSystem.speak or just manually broadcast here if needed.
                # Analyzing AudioSystem.speak: it broadcasts first, then speaks.
                # So we can just call audio.speak but we need to prevent it from using pyttsx3.
                # Let's modify AudioSystem.speak instead of this wrapper to be cleaner.
                pass
            except:
                pass
        
        # We will modify AudioSystem.speak to respect ENABLE_TERMINAL_VOICE global 
        # or pass it as an arg. For now, let's just call it, and we'll patch AudioSystem.
        self.is_jarvis_speaking = True
        
        def on_speech_start():
            # Trigger text display AND lip sync on frontend simultaneously
            if self.audio.websocket_manager and self.loop:
                # 1. Show text
                print(f"[Backend] Broadcasting text: {text[:50]}...")
                asyncio.run_coroutine_threadsafe(
                    self.audio.websocket_manager.broadcast({
                        "type": "text",
                        "text": text
                    }),
                    self.loop
                )
                # 2. Start animation
                print("[Backend] Broadcasting lipsync_start")
                asyncio.run_coroutine_threadsafe(
                    self.audio.websocket_manager.broadcast({
                        "type": "lipsync_start"
                    }),
                    self.loop
                )

        def on_speech_complete():
            self.is_jarvis_speaking = False
            # Stop lip sync on frontend
            if self.audio.websocket_manager and self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.audio.websocket_manager.broadcast({
                        "type": "lipsync_stop"
                    }),
                    self.loop
                )
            
        try:
            # Check if AudioSystem.speak supports on_complete and on_start
            if hasattr(self.audio, 'speak'):
                # We assume we updated AudioSystem.speak to support both
                self.audio.speak(text, play_beep, rate, on_complete=on_speech_complete, on_start=on_speech_start)
            else:
                 # Fallback
                 self.audio.speak(text, play_beep, rate)
        except Exception as e:
            print(f"Error in speech: {e}")
            self.is_jarvis_speaking = False # Reset on error
        except Exception as e:
            print(f"Error in speech: {e}")
            self.is_jarvis_speaking = False # Reset on error
    
    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        self.voice_enabled = not self.voice_enabled
        status = "enabled" if self.voice_enabled else "disabled"
        print(f"{Fore.CYAN}🎤 Voice input {status}")
        
        # Notify via WebSocket
        if self.audio.websocket_manager and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.audio.websocket_manager.broadcast({
                    "type": "voice_status",
                    "listening": self.voice_enabled
                }),
                self.loop
            )
            
        if self.voice_enabled:
            self.audio.play_beep("listening")
        else:
            self.audio.play_beep("response")

    def listen(self, timeout=None, phrase_time_limit=8):
        """Listen for audio input and convert to text"""
        if not self.voice_enabled:
            time.sleep(0.5)
            return ""

        # Check if JARVIS is speaking to prevent feedback loop
        if self.is_jarvis_speaking:
            time.sleep(0.1)
            return ""

        with self.microphone as source:
            # Wait if client is speaking to avoid feedback loop
            while self.is_client_speaking or self.is_jarvis_speaking:
                time.sleep(0.1)
                
            if timeout is None:
                print(f"{Fore.CYAN}🎤 Listening continuously...")
            else:
                print(f"{Fore.CYAN}🎤 Listening...")
            
            # Send status to frontend
            if self.audio.websocket_manager and self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.audio.websocket_manager.broadcast({
                        "type": "voice_status",
                        "listening": True
                    }),
                    self.loop
                )

            self.audio.play_beep("listening")
            
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                text = self.recognizer.recognize_google(audio).lower()
                print(f"{Fore.YELLOW}You: {text}")
                
                 # Send user text to frontend
                if self.audio.websocket_manager and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.audio.websocket_manager.broadcast({
                            "type": "response",
                            "content": text,
                            "sender": "user"
                        }),
                        self.loop
                    )

                return text
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                self.speak("Network connectivity issue detected.")
                return ""
            except Exception as e:
                print(f"{Fore.RED}Audio processing error: {e}")
                return ""
            finally:
                # Send status to frontend
                if self.audio.websocket_manager and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.audio.websocket_manager.broadcast({
                            "type": "voice_status",
                            "listening": False
                        }),
                        self.loop
                    )
    
    async def process_command(self, command):
        """Process and execute commands"""
        if not command or not command.strip():
            self.speak("I didn't catch that. Could you please repeat?")
            return
        
        command_lower = command.lower().strip()
        
        # Remove wake word if present
        if command_lower.startswith(WAKE_WORD):
            command_lower = command_lower[len(WAKE_WORD):].strip()
            if command_lower:
                import random
                self.speak(random.choice(self.jarvis_responses["affirmative"]))
        
        # ========== AUDIO/SPEECH COMMANDS ==========
        if "volume up" in command_lower or "increase volume" in command_lower:
            new_volume = self.audio.set_volume(min(1.0, self.audio.get_volume() + 0.2))
            self.audio.adjust_system_volume("up")
            self.speak(f"Volume increased to {int(new_volume)} percent.")
            return
        
        if "volume down" in command_lower or "decrease volume" in command_lower:
            new_volume = self.audio.set_volume(max(0.0, self.audio.get_volume() - 0.2))
            self.audio.adjust_system_volume("down")
            self.speak(f"Volume decreased to {int(new_volume)} percent.")
            return
        
        if "mute" in command_lower:
            self.audio.set_volume(0.0)
            self.audio.adjust_system_volume("mute")
            self.speak("Audio muted. Say 'unmute' to restore audio.")
            return
        
        if "unmute" in command_lower:
            self.audio.set_volume(0.8)
            self.audio.adjust_system_volume("unmute")
            self.speak("Audio unmuted. Volume restored to 80 percent.")
            return
        
        if "test audio" in command_lower or "test speakers" in command_lower:
            self.speak("Testing audio system. You should hear four test messages.")
            self.audio.test_speakers()
            return
        
        # ========== AI COMMANDS ==========
        if "local ai" in command_lower or "ollama" in command_lower:
            ai_status = self.ai_brain.get_brain_status()
            if ai_status.get("local_ai", {}).get("available", False):
                model = ai_status['local_ai'].get('model', 'Unknown')
                self.speak(f"Local AI is online using {model} model. Advanced capabilities enabled.")
            else:
                self.speak("Local AI is offline. Please check if Ollama is installed.")
            return
        
        # ========== APPLICATION COMMANDS ==========
        if "open " in command_lower or "start " in command_lower or "launch " in command_lower:
            # Extract app name
            app_keywords = ["open ", "start ", "launch "]
            app_name = command_lower
            for keyword in app_keywords:
                if keyword in app_name:
                    app_name = app_name.replace(keyword, "").strip()
                    break
            
            result = self.app_manager.open_application(app_name)
            self.speak(result)
            return
        
        if "close " in command_lower or "quit " in command_lower:
            app_name = command_lower.replace("close ", "").replace("quit ", "").strip()
            result = self.app_manager.close_application(app_name)
            self.speak(result)
            return
        
        # ========== BROWSER COMMANDS ==========
        if "search for " in command_lower or "search " in command_lower:
            if "search for " in command_lower:
                query = command_lower.replace("search for ", "").strip()
            else:
                query = command_lower.replace("search ", "").strip()
            
            result = self.browser_manager.search_web(query)
            self.speak(result)
            return
        
        if "youtube" in command_lower:
            if "search" in command_lower:
                query = command_lower.replace("search youtube for ", "").replace("search youtube ", "").strip()
                result = self.browser_manager.open_youtube(query)
            else:
                result = self.browser_manager.open_youtube()
            self.speak(result)
            return
        
        if "spotify" in command_lower:
            if "search" in command_lower:
                query = command_lower.replace("search spotify for ", "").replace("search spotify ", "").strip()
                result = self.browser_manager.open_spotify(query)
            else:
                result = self.browser_manager.open_spotify()
            self.speak(result)
            return
        
        # ========== MEDIA COMMANDS ==========
        if "play " in command_lower and ("youtube" in command_lower or "on youtube" in command_lower):
            query = command_lower.replace("play ", "").replace("on youtube", "").strip()
            result = self.media_manager.play_youtube_video(query)
            self.speak(result)
            return
        
        if "play " in command_lower and "spotify" in command_lower:
            query = command_lower.replace("play ", "").replace("on spotify", "").strip()
            result = self.media_manager.play_spotify_song(query)
            self.speak(result)
            return
        
        # ========== SCREENSHOT COMMANDS ==========
        if "screenshot" in command_lower or "capture screen" in command_lower:
            area = "full"
            if "window" in command_lower:
                area = "window"
            elif "region" in command_lower:
                area = "region"
            
            result = self.screen_capture.take_screenshot(area)
            self.speak(result)
            return
        
        # ========== CODE COMMANDS ==========
        if "create file" in command_lower or "new file" in command_lower:
            filename = command_lower.replace("create file ", "").replace("new file ", "").strip()
            result = self.code_editor.create_code_file(filename)
            self.speak(result)
            return
        
        if "open vs code" in command_lower or "open code" in command_lower:
            result = self.code_editor.open_in_vscode()
            self.speak(result)
            return
        
        # ========== SYSTEM COMMANDS ==========
        if "system info" in command_lower or "system information" in command_lower:
            info = self.system_utils.get_system_info()
            response = f"System information: OS: {info.get('OS')}, CPU: {info.get('CPU Usage')}, Memory: {info.get('Memory Percent')}"
            self.speak(response)
            return
        
        if "battery" in command_lower:
            info = self.system_utils.get_battery_info()
            if "Percent" in info:
                response = f"Battery at {info['Percent']}, {'plugged in' if info.get('Plugged In') else 'on battery'}"
            else:
                response = info.get('info', 'Could not get battery info')
            self.speak(response)
            return
        
        # ========== VOICE TYPING COMMANDS ==========
        if "type " in command_lower and not "prototype" in command_lower:
            text = command_lower.replace("type ", "").strip()
            result = self.voice_typing.type_text(text)
            self.speak(result)
            return
        
        if "voice type" in command_lower or "dictate" in command_lower:
            result = self.voice_typing.voice_to_text(self.audio, self.recognizer)
            self.speak(result)
            return
        
        # ========== FILE COMMANDS ==========
        if "list files" in command_lower:
            result = self.file_manager.list_files()
            self.speak(result)
            return
        
        if "create new file" in command_lower:
            filename = command_lower.replace("create new file ", "").strip()
            result = self.file_manager.create_file(filename)
            self.speak(result)
            return
        
        # ========== BASIC COMMANDS ==========
        # ========== BASIC COMMANDS ==========
        words = set(command_lower.split())
        if "hello" in words or "hi" in words:
            self.speak(f"Hello {USER_NAME}! How can I assist you?")
            return
        
        if "time" in words:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            return
        
        if "date" in words:
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.speak(f"Today is {current_date}")
            return
        
        if "weather" in command_lower:
            city = command_lower.replace("weather in ", "").replace("weather for ", "").replace("weather ", "").strip()
            if city and city != "weather":
                weather_info = self.system_utils.get_weather(city)
                self.speak(weather_info)
            else:
                self.speak("I can check the weather. Please specify a city, for example: 'weather in London'")
            return
        
        if "joke" in command_lower:
            joke = pyjokes.get_joke()
            self.speak(f"Here's a joke: {joke}")
            return
        
        if "help" in command_lower or "what can you do" in command_lower:
            self.show_help()
            return
        
        if "bye" in command_lower or "goodbye" in command_lower or "exit" in command_lower:
            self.speak("Goodbye! Have a great day.")
            self.is_running = False
            return
        
        # ========== AI RESPONSE FOR OTHER QUERIES ==========
        await self.handle_ai_response(command_lower)
    
    async def handle_ai_response(self, query):
        """Handle queries with AI Brain intelligence"""
        if any(op in query for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided', 'multiplied', 'multiply']):
            try:
                expression = query.lower()
                replacements = {
                    'multiplied by': '*', 'multiply by': '*', 'multiply': '*',
                    'plus': '+', 'minus': '-', 'times': '*', 'x': '*',
                    'divided by': '/', 'over': '/',
                    ' and ': ' '
                }
                
                for word, symbol in replacements.items():
                    expression = expression.replace(word, symbol)
                
                for phrase in ['what is', 'calculate', 'compute', 'solve']:
                    expression = expression.replace(phrase, '')
                
                expression = expression.strip()
                
                if any(char.isdigit() for char in expression):
                    result = eval(expression)
                    print(f"Calculation: {expression} = {result}")
                    self.speak(f"The result is {result}")
                    return
            except:
                pass
        
        try:
            analysis = self.ai_brain.process_input(query)
        except Exception as e:
            print(f"⚠️ AI Brain process_input error: {e}")
            import traceback
            traceback.print_exc()
            self.speak("I encountered an issue processing that. Could you try rephrasing?")
            return
        
        if analysis.get("ai_available", False):
            print(f"{Fore.CYAN}🤖 Processing with local AI...")
            self.audio.play_beep("ai_processing")
        
        try:
            response = await self.ai_brain.generate_response(analysis)
        except Exception as e:
            print(f"⚠️ AI Brain generate_response error: {e}")
            import traceback
            traceback.print_exc()
            response = None
        
        if response:
            self.speak(response)
        else:
            self.speak("I'm having trouble generating a response right now. Please try again.")
    
    def show_help(self):
        """Show help menu"""
        help_text = f"""
{Fore.CYAN}=== JARVIS COMMANDS ==={Fore.WHITE}

{Fore.YELLOW}🎯 BASIC COMMANDS:{Fore.WHITE}
- Hello / Hi / Hey
- What time is it?
- What's the date?
- Tell me a joke
- Help / What can you do
- Goodbye / Exit

{Fore.YELLOW}🎯 AUDIO CONTROLS:{Fore.WHITE}
- Volume up / Volume down
- Mute / Unmute
- Test audio / Test speakers

{Fore.YELLOW}🎯 APPLICATIONS:{Fore.WHITE}
- Open [app name] (e.g., open chrome, open notes)
- Open camera / photo booth
- Open safari / chrome / firefox
- Open vs code / terminal
- Open spotify / music
- Open calculator / calendar

{Fore.YELLOW}🎯 WEB & SEARCH:{Fore.WHITE}
- Search for [query]
- Search YouTube for [query]
- Search Spotify for [query]
- Open YouTube / Open Spotify
- Open website [url]

{Fore.YELLOW}🎯 MEDIA:{Fore.WHITE}
- Play [song] on YouTube
- Play [song] on Spotify
- Play / Pause / Next / Previous (media controls)

{Fore.YELLOW}🎯 SCREEN CAPTURE:{Fore.WHITE}
- Take screenshot
- Screenshot window
- Screenshot region

{Fore.YELLOW}🎯 CODING:{Fore.WHITE}
- Create file [filename]
- Open VS Code
- Write code [code]

{Fore.YELLOW}🎯 SYSTEM:{Fore.WHITE}
- System info
- Battery status
- Clean up files

{Fore.YELLOW}🎯 VOICE TYPING:{Fore.WHITE}
- Type [text]
- Voice type / Dictate

{Fore.YELLOW}🎯 FILE MANAGEMENT:{Fore.WHITE}
- List files
- Create new file [name]
- Delete file [name]
- Copy file [source] [destination]

{Fore.YELLOW}🎯 AI FEATURES:{Fore.WHITE}
- Local AI status
- Enable AI
- [Any question or conversation]
        """
        print(help_text)
        self.speak("I've displayed all available commands in the terminal. You can ask me to do any of these things.")
    
    def register_skills(self):
        """Register all available skills"""
        return {
            "time": lambda cmd: self.speak(f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"),
            "date": lambda cmd: self.speak(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}"),
            "joke": lambda cmd: self.speak(pyjokes.get_joke()),
            "weather": lambda cmd: self.speak("I can check weather. Say 'weather in [city]'"),
            "system": lambda cmd: self.speak("Getting system information..."),
            "help": lambda cmd: self.show_help()
        }
    
    def run(self):
        """Main execution loop"""
        print(f"\n{Fore.GREEN}{USER_NAME}, JARVIS AI is online.")
        print(f"{Fore.CYAN}Say 'help' for command list or 'exit' to quit\n")
        
        if not CONTINUOUS_MODE:
            print(f"{Fore.CYAN}Wake word: '{WAKE_WORD}'")
        
        audio_vol = int(self.audio.get_volume() * 100)
        print(f"{Fore.CYAN}🔊 Audio Status: Volume {audio_vol}%")
        print(f"{Fore.YELLOW}💡 Try saying 'test audio' to check your speakers")
        
        while self.is_running:
            try:
                if CONTINUOUS_MODE:
                    command = self.listen(timeout=None, phrase_time_limit=10)
                    if command:
                        if "exit" in command or "quit" in command or "goodbye" in command:
                            self.speak("Goodbye! Have a great day.")
                            break
                        asyncio.run_coroutine_threadsafe(self.process_command(command), self.loop)
                else:
                    command = self.listen(timeout=1, phrase_time_limit=5)
                    if command and WAKE_WORD in command:
                        self.speak("Yes, I'm listening.")
                        command = self.listen(timeout=10, phrase_time_limit=15)
                        if command:
                            asyncio.run_coroutine_threadsafe(self.process_command(command), self.loop)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                self.speak("Shutting down.")
                break
            except Exception as e:
                print(f"{Fore.RED}System error: {e}")
                time.sleep(1)

from fastapi.staticfiles import StaticFiles

# Global Jarvis instance
jarvis = None

@app.on_event("startup")
async def startup_event():
    global jarvis
    # Get the running event loop
    loop = asyncio.get_running_loop()
    
    # Initialize Jarvis with the websocket manager and loop
    jarvis = JarvisAI(websocket_manager=manager, loop=loop)
    
    # Run Jarvis in a separate thread so it doesn't block FastAPI
    thread = threading.Thread(target=jarvis.run)
    thread.daemon = True
    thread.start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Put handler logic here or route to jarvis
            if data.get("type") == "command":
                content = data.get("content")
                if jarvis and content:
                    print(f"Received command from Web UI: {content}")
                    # Process command using threadsafe execution on the main loop
                    asyncio.run_coroutine_threadsafe(jarvis.process_command(content), jarvis.loop)
            
            elif data.get("type") == "toggle_voice":
                # Handle voice toggle preference if needed
                if jarvis:
                    jarvis.toggle_voice_input()
            
            elif data.get("type") == "speech_state":
                status = data.get("status")
                if jarvis:
                    if status == "started":
                        jarvis.set_client_speaking(True)
                    elif status == "finished":
                        jarvis.set_client_speaking(False)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount static files (React build output)
# Resolve absolute path to frontend dist
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BACKEND_DIR, "../frontend/dist")
FRONTEND_ASSETS = os.path.join(FRONTEND_DIST, "assets")

# Ensure directories exist before mounting
if not os.path.exists(FRONTEND_ASSETS):
    print(f"⚠️ Warning: Frontend assets not found at {FRONTEND_ASSETS}")
    # Create dummy if missing to prevent crash, user needs to build frontend
    os.makedirs(FRONTEND_ASSETS, exist_ok=True)

# Mount static files (React build output)
app.mount("/static", StaticFiles(directory=FRONTEND_ASSETS), name="static")

# Serve React App
@app.get("/")
async def read_root():
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend not built</h1><p>Please run 'npm run build' in frontend directory</p>")

# Serve other static assets if needed (e.g. manifest, etc)
@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    file_path = os.path.join(FRONTEND_DIST, full_path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("Not Found")


# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    try:
        # Run uvicorn server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        print(f"{Fore.YELLOW}Please make sure you have all required packages installed:")
        print(f"{Fore.YELLOW}pip install -r requirements.txt")