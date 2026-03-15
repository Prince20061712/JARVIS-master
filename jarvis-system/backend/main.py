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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

import uvicorn

# compatibility shim: some older dependencies (e.g. sentence-transformers 2.x)
# expect `cached_download` exported from huggingface_hub.  newer versions removed
# it, breaking imports.  Insert a simple alias so imports succeed even when the
# installed hub is recent.
try:
    import huggingface_hub
    if not hasattr(huggingface_hub, 'cached_download'):
        from huggingface_hub import hf_hub_download
        huggingface_hub.cached_download = hf_hub_download
except ImportError:
    # huggingface_hub may not even be installed yet; it will be brought in by
    # downstream packages if required.
    pass

from brain.ai_brain import EnhancedAIBrain
from flashcard_system.scanner.subject_scanner import SubjectScanner
from flashcard_system.viva.adaptive_questioner import AdaptiveQuestioner

# Initialize colorama
init(autoreset=True)

# ========== CONFIGURATION SECTION ==========
USER_NAME = "Prince"
JARVIS_NAME = "Jarvis"
CONTINUOUS_MODE = True
WAKE_WORD = "jarvis"
ENABLE_LOCAL_AI = True
OLLAMA_MODEL = "llama3.1:latest"
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

# === MOUNT MODULAR API ===
from api.rest.routes import app as api_app
app.mount("/api/v1", api_app)

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
from managers.audio_manager import AudioSystem
from managers.app_manager import ApplicationManager
from managers.browser_manager import BrowserManager
from managers.media_manager import MediaManager
from managers.screen_manager import ScreenCaptureManager
from managers.code_manager import CodeEditorManager
from managers.system_manager import SystemUtilitiesManager
from managers.voice_manager import VoiceTypingManager
from managers.file_manager import FileManager

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
        self.recognizer.pause_threshold = 2.5  # Allow much longer pauses (2.5s) to avoid cutting off
        self.recognizer.non_speaking_duration = 1.5
        self.recognizer.energy_threshold = 300  # distinct speech
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        
        self.command_queue = queue.Queue()
        self.is_listening = CONTINUOUS_MODE
        self.command_queue = queue.Queue()
        self.is_listening = CONTINUOUS_MODE
        self.is_running = True
        self.voice_enabled = False # Start with voice disabled
        self.is_client_speaking = False # Track if client is speaking
        self.is_jarvis_speaking = False # Track if JARVIS is speaking
        self.is_processing_command = False # Track if JARVIS is thinking/speaking
        self.viva_mode = False
        self.viva_question = ""
        self.viva_subject = None
        self.active_subject = None

        print(f"\n{Fore.CYAN}🤖 Loading Enhanced AI Brain (Modular)...")
        # Initialize AI Brain
        try:
            # Use centralized data directory
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            self.ai_brain = EnhancedAIBrain(USER_NAME, data_dir=data_dir, primary_model=OLLAMA_MODEL)
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
        
        audio_vol = int((self.audio.volume_level / 100.0) * 100) if hasattr(self.audio, 'volume_level') else 100
        print(f"{Fore.CYAN}🔊 Audio Status: Volume {audio_vol}%, Rate: {self.audio.speech_rate} wpm")
        print(f"{Fore.YELLOW}💡 Try saying 'test audio' to check your speakers")
        
        time.sleep(0.5)
        
        ai_status = self.ai_brain.get_brain_status()
        if ai_status.get("local_ai", {}).get("available", False):
            welcome = f"Hello {USER_NAME}, I am JARVIS with enhanced AI capabilities. Ollama server started automatically. Local intelligence is online. All systems are ready to assist you."
            self.speak(welcome, play_beep=True)
        else:
            welcome = f"Hello {USER_NAME}, I am JARVIS. Basic AI systems online. For advanced AI, I tried to start Ollama but it's not available. How can I help you?"
            self.speak(welcome, play_beep=True)
    
    def cleanup(self):
        """Cleanup function"""
        print(f"\n{Fore.CYAN}🧹 Cleaning up...")
        if hasattr(self, 'ai_brain') and hasattr(self.ai_brain, 'save_state'):
            self.ai_brain.save_state()
            
    def cancel_current(self):
        """Immediately stop speaking and abort current AI request"""
        print(f"{Fore.RED}🛑 Executing hard cancel on current operations...{Style.RESET_ALL}")
        # Stop speech playback instantly
        if hasattr(self, 'audio'):
            self.audio.stop_speech()
        
        # Abort any ongoing AI generation logic
        if hasattr(self, 'ai_brain'):
            self.ai_brain.cancel_current_request = True
            if hasattr(self.ai_brain, 'ollama'):
                self.ai_brain.ollama.cancel_current_request = True
            
        # Reset state flags
        self.is_processing_command = False
        self.is_jarvis_speaking = False
        
        # Broadcast safe state to frontend
        if hasattr(self, 'audio') and self.audio.websocket_manager and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.audio.websocket_manager.broadcast({
                    "type": "voice_status",
                    "listening": False
                }),
                self.loop
            )
    
    def set_client_speaking(self, speaking):
        """Set client speaking status to prevent feedback loop"""
        self.is_client_speaking = speaking
        if speaking:
            print(f"{Fore.MAGENTA}🔇 Client speaking - Pausing backend listening...")
        else:
            print(f"{Fore.MAGENTA}👂 Client finished speaking - Resuming listening...")

    def speak(self, text, play_beep=False, rate=None):
        """Wrapper for audio system speak"""
        if isinstance(text, dict):
            text = text.get("message", text.get("title", str(text)))
        elif not isinstance(text, str):
            text = str(text)

        if play_beep:
            self.audio.play_beep("response")
        
        if ENABLE_TERMINAL_VOICE:
            self.audio.speak(text, priority=rate if rate is not None else 0)
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
            # Check if AudioSystem.speak supports on_end and on_start
            if hasattr(self.audio, 'speak'):
                # We assume we updated AudioSystem.speak to support both
                self.audio.speak(text, priority=rate if rate is not None else 0, on_end=on_speech_complete, on_start=on_speech_start)
            else:
                 # Fallback
                 self.audio.speak(text, priority=rate if rate is not None else 0)
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
            
            # Calibrate for ambient noise (longer sample for better quality)
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            try:
                # Increased phrase_time_limit to avoid cutting off long commands
                rec_phrase_limit = None if phrase_time_limit is None else 30 
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=rec_phrase_limit)
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
                    
                    # Switch UI to processing mode immediately
                    asyncio.run_coroutine_threadsafe(
                        self.audio.websocket_manager.broadcast({
                            "type": "processing"
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
    
    async def process_command_wrapper(self, command, subject=None):
        """Wrapper to prevent simultaneous listening and processing"""
        self.is_processing_command = True
        
        # Reset cancellation flags before starting new command
        if hasattr(self, 'ai_brain'):
            self.ai_brain.cancel_current_request = False
            if hasattr(self.ai_brain, 'ollama'):
                self.ai_brain.ollama.cancel_current_request = False
                
        try:
            await self.process_command(command, subject=subject)
        finally:
            # Wait a tiny bit to ensure audio has completely finished
            await asyncio.sleep(0.5)
            self.is_processing_command = False

    async def process_command(self, command, subject=None):
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
                
        # ========== VIVA MODE COMMANDS ==========
        if "start viva" in command_lower or "begin viva" in command_lower:
            # Check if a subject is selected
            if subject and subject != "General":
                self.viva_mode = True
                self.viva_subject = subject
                self.speak(f"Starting Viva session for {subject}. I will ask questions based on your uploaded materials.")
                
                if hasattr(self, 'ai_brain') and hasattr(self.ai_brain, 'rag_engine') and self.ai_brain.rag_engine:
                    # Check if materials exist using SubjectScanner
                    scanner = SubjectScanner()
                    content = scanner.get_subject_content(subject)
                    if not content or not content.strip():
                        self.speak(f"I couldn't find any materials for {subject}. Please upload some documents first.")
                        self.viva_mode = False
                        return
                    
                    # Retrieve context from the specific subject using RAG
                    context = self.ai_brain.rag_engine.retrieve_context("key concepts definitions", subject=subject)
                    if not context or not context.strip():
                        # Fallback: use the scanned content directly
                        context = content[:2000]  # Limit context length
                    
                    prompt = f"Based on this academic context from {subject}, ask a single, concise viva question. Do not provide the answer.\nContext: {context}"
                    self.audio.play_beep("ai_processing")
                    response = self.ai_brain.ollama.generate_response(prompt)
                    
                    if getattr(self.ai_brain, 'cancel_current_request', False):
                        return
                        
                    if response:
                        self.viva_question = response
                        self.speak(response)
                    else:
                        # Fallback to hard-coded templates
                        try:
                            questioner = AdaptiveQuestioner()
                            # Map subject names to template topic names
                            topic_mapping = {
                                "operating system": "Operating Systems",
                                "Computer networks": "Computer Networks",
                                "Computer Networks": "Computer Networks",
                                "Operating Systems": "Operating Systems",
                            }
                            template_topic = topic_mapping.get(subject, subject)
                            
                            templates = questioner.get_templates(template_topic)
                            if templates:
                                template = random.choice(templates)
                                self.viva_question = template.template_text
                                self.speak(self.viva_question)
                            else:
                                self.speak("Sorry, I could not generate a question right now.")
                        except Exception as e:
                            print(f"Fallback question generation failed: {e}")
                            self.speak("Sorry, I could not generate a question right now.")
                return
            else:
                self.speak("Please select a flashcard subject first, then say 'start viva'.")
                return
            
        elif "stop viva" in command_lower or "exit viva" in command_lower or "end viva" in command_lower:
            self.viva_mode = False
            self.viva_question = ""
            self.viva_subject = None
            self.speak("Viva session ended.")
            return
            
        elif self.viva_mode:
            # We are evaluating the user's answer
            if hasattr(self, 'ai_brain') and hasattr(self.ai_brain, 'rag_engine') and self.ai_brain.rag_engine:
                context = self.ai_brain.rag_engine.retrieve_context(self.viva_question, subject=self.viva_subject)
                evaluation_prompt = f"""You are an examiner in a viva for {self.viva_subject}. 
The question you asked was: "{self.viva_question}"
The student answered: "{command}"

Here is the textbook context for evaluation: 
{context}

1. Evaluate if the student's answer is correct. Give a score out of 10.
2. If correct, praise the student. If incorrect, correct the user and explain briefly why.
3. Then, ask ONE new, different viva question based on the context. Do not answer it.
Keep your response conversational and concise."""

                self.audio.play_beep("ai_processing")
                response = self.ai_brain.ollama.generate_response(evaluation_prompt)
                
                if getattr(self.ai_brain, 'cancel_current_request', False):
                    return
                    
                if response:
                    self.viva_question = response
                    self.speak(response)
                else:
                    self.speak("I had trouble evaluating that. Let's try another question.")
            return
        
        # ========== AUDIO/SPEECH COMMANDS ==========
        if any(word in command_lower for word in ["volume up", "increase volume", "raise volume"]):
            new_vol = int(min(100, self.audio.get_volume() * 100 + 20))
            new_volume = self.audio.set_volume(new_vol)
            self.audio.adjust_system_volume("up", 20)
            self.speak(f"Volume increased to {int(new_volume)} percent.")
            return
        
        if any(word in command_lower for word in ["volume down", "decrease volume", "low the volume", "lower the volume"]):
            new_vol = int(max(0, self.audio.get_volume() * 100 - 20))
            new_volume = self.audio.set_volume(new_vol)
            self.audio.adjust_system_volume("down", 20)
            self.speak(f"Volume decreased to {int(new_volume)} percent.")
            return
            
        if "volume at " in command_lower or "set volume to " in command_lower:
            import re
            match = re.search(r'(\d+)', command_lower)
            if match:
                vol = int(match.group(1))
                new_volume = self.audio.set_volume(vol)
                self.audio.adjust_system_volume("set", vol)
                self.speak(f"Volume set to {new_volume} percent.")
            return
        
        if "mute" in command_lower and "unmute" not in command_lower:
            self.audio.set_volume(0)
            self.audio.adjust_system_volume("mute")
            self.speak("Audio muted. Say 'unmute' to restore audio.")
            return
        
        if "unmute" in command_lower:
            self.audio.set_volume(80)
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
        
        # ========== BROWSER / MEDIA COMMANDS ==========
        # Specific search commands first
        if "youtube" in command_lower:
            if "search" in command_lower:
                query = command_lower.replace("search youtube for ", "").replace("search youtube ", "").replace("search ", "").replace(" on youtube", "").strip()
                result = self.browser_manager.open_youtube(query)
            elif "play " in command_lower:
                query = command_lower.replace("play ", "").replace("on youtube", "").strip()
                result = self.media_manager.play_youtube_video(query)
                msg = result.get("message", str(result)) if isinstance(result, dict) else str(result)
                self.speak(msg)
                return
            else:
                result = self.browser_manager.open_youtube()
            self.speak(result)
            return
        
        if "spotify" in command_lower:
            if "play " in command_lower:
                query = command_lower.replace("play ", "").replace("on spotify web", "").replace("on spotify", "").strip()
                result = self.media_manager.play_spotify_song(query)
                msg = result.get("message", str(result)) if isinstance(result, dict) else str(result)
                self.speak(msg)
                return
            elif "search" in command_lower:
                query = command_lower.replace("search spotify for ", "").replace("search spotify ", "").replace("search ", "").replace(" on spotify", "").strip()
                result = self.browser_manager.open_spotify(query)
            else:
                result = self.browser_manager.open_spotify()
            self.speak(result)
            return

        # General search fallback
        if "search for " in command_lower or "search " in command_lower:
            if "search for " in command_lower:
                query = command_lower.replace("search for ", "").strip()
            else:
                query = command_lower.replace("search ", "").strip()
            
            result = self.browser_manager.search_web(query)
            self.speak(result)
            return
        
        # ========== SCREENSHOT COMMANDS ==========
        if "screenshot" in command_lower or "capture screen" in command_lower:
            area = "full_screen"
            if "window" in command_lower:
                area = "active_window"
            elif "region" in command_lower:
                area = "selected_region"
            
            result = self.screen_capture.take_screenshot(area)
            self.speak(result)
            return

        if "read screen" in command_lower or "what is on my screen" in command_lower:
            try:
                self.speak("Reading your screen now. Please wait a moment.")
                capture_result = self.screen_capture.take_screenshot("full_screen")
                if capture_result.success:
                    ocr_res = self.screen_capture.extract_text(capture_result.file_path)
                    if ocr_res.get("success") and ocr_res.get("text"):
                        text = ocr_res["text"]
                        # Run async AI response logic
                        import asyncio
                        summary = ""
                        try:
                            # Use ai_brain to summarize the on-screen text
                            future = asyncio.run_coroutine_threadsafe(
                                self.ai_brain.generate_response(
                                    f"Please summarize what is on my screen based on this OCR text:\n\n{text[:2000]}", 
                                    context={}
                                ),
                                self.loop
                            )
                            summary = future.result(timeout=10)
                            self.speak(f"On your screen: {summary}")
                        except Exception as ai_e:
                            logger.error(f"AI summarizing error: {ai_e}")
                            self.speak("I read the screen, but couldn't summarize it properly.")
                    else:
                        self.speak("I couldn't read any text on the screen.")
                else:
                    self.speak("I failed to capture the screen.")
            except Exception as e:
                logger.error(f"Screen reading error: {e}")
                self.speak("I encountered an error while trying to read your screen.")
            return
        
        # ========== CODE COMMANDS ==========
        if "create file" in command_lower or "new file" in command_lower or ("create " in command_lower and " file" in command_lower):
            import re
            
            # Extract language (e.g., "using python")
            language = "text" # default
            lang_match = re.search(r'(?:using|in) ([a-zA-Z]+)', command_lower)
            if lang_match:
                language = lang_match.group(1).lower()
                command_lower = command_lower.replace(lang_match.group(0), "")
            
            # Extract filename (e.g., "create a hello world txt file")
            name_match = re.search(r'(?:create|make)(?: a | an | )?(.*?)(?: file)', command_lower)
            if name_match:
                filename = name_match.group(1).strip()
                if " txt" in filename:
                    filename = filename.replace(" txt", ".txt")
                if " py" in filename:
                    filename = filename.replace(" py", ".py")
                filename = filename.replace(" ", "_")
                if not filename:
                    filename = "new_file"
            else:
                filename = command_lower.replace("create file ", "").replace("new file ", "").strip()
                if not filename:
                    filename = "new_file"
                    
            result = self.code_editor.create_code_file(filename, language=language)
            msg = result.get("message", "File created.") if isinstance(result, dict) else str(result)
            self.speak(msg)
            return
        
        if "open vs code" in command_lower or "open code" in command_lower:
            result = self.code_editor.open_in_vscode()
            self.speak(result)
            return
        
        # ========== SYSTEM COMMANDS ==========
        settings_keywords = ["turn on ", "turn off ", "enable ", "disable ", "toggle "]
        if any(keyword in command_lower for keyword in settings_keywords) and any(s in command_lower for s in ["wifi", "wi-fi", "bluetooth", "dark mode"]):
            setting = None
            if "wifi" in command_lower or "wi-fi" in command_lower:
                setting = "wifi"
            elif "bluetooth" in command_lower:
                setting = "bluetooth"
            elif "dark mode" in command_lower:
                setting = "dark_mode"
            
            state = None
            if "turn on" in command_lower or "enable" in command_lower:
                state = True
            elif "turn off" in command_lower or "disable" in command_lower:
                state = False
                
            if setting:
                result = self.system_utils.toggle_system_setting(setting, state)
                self.speak(result.get("message", "Setting updated."))
                return

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
        
        # =========== AI RESPONSE FOR OTHER QUERIES ===========
        await self.handle_ai_response(command_lower, subject=subject)
    
    async def handle_ai_response(self, query, subject=None):
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
            analysis = self.ai_brain.process_input(query, subject=subject)
            
            # Broadcast emotion state back to frontend via visual updates
            if hasattr(self.audio, 'websocket_manager') and self.audio.websocket_manager and self.loop:
                try:
                    thought = analysis.get("thought_process", {})
                    ei_data = thought.get("intermediate_results", {}).get("layer2", {}).get("emotion_analysis", {})
                    emotion = ei_data.get("primary_emotion", "neutral")
                    wellbeing = ei_data.get("wellbeing_score", 0.5)
                    
                    asyncio.run_coroutine_threadsafe(
                        self.audio.websocket_manager.broadcast({
                            "type": "emotion_state",
                            "emotion": emotion,
                            "wellbeing_score": wellbeing
                        }),
                        self.loop
                    )
                    print(f"{Fore.MAGENTA}😊 Emotion detected: {emotion} | Wellbeing: {wellbeing}")
                except Exception as e:
                    print(f"⚠️ Failed to broadcast emotion: {e}")
                    
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
        
        if getattr(self.ai_brain, 'cancel_current_request', False):
            return

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
                if getattr(self, 'is_processing_command', False):
                    time.sleep(0.1)
                    continue

                if CONTINUOUS_MODE:
                    command = self.listen(timeout=None, phrase_time_limit=10)
                    if command:
                        if "exit" in command or "quit" in command or "goodbye" in command:
                            self.speak("Goodbye! Have a great day.")
                            break
                        asyncio.run_coroutine_threadsafe(self.process_command_wrapper(command, subject=self.active_subject), self.loop)
                else:
                    command = self.listen(timeout=1, phrase_time_limit=5)
                    if command and WAKE_WORD in command:
                        self.speak("Yes, I'm listening.")
                        command = self.listen(timeout=10, phrase_time_limit=15)
                        if command:
                            asyncio.run_coroutine_threadsafe(self.process_command_wrapper(command, subject=self.active_subject), self.loop)
                
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

    async def load_existing_flashcards():
        if not hasattr(jarvis, 'ai_brain') or not getattr(jarvis.ai_brain, 'rag_engine', None):
            return
            
        subjects_dir = Path("data/subjects")
        if not subjects_dir.exists():
            return
            
        print(f"📚 Auto-loading existing flashcard materials from disk into memory...")
        for subject_dir in subjects_dir.iterdir():
            if subject_dir.is_dir():
                subject = subject_dir.name
                for file_path in subject_dir.iterdir():
                    if file_path.is_file() and file_path.name != ".DS_Store":
                        try:
                            print(f"   Ingesting {file_path.name} for subject '{subject}'...")
                            exec_loop = asyncio.get_running_loop()
                            await exec_loop.run_in_executor(
                                None, 
                                jarvis.ai_brain.rag_engine.ingest_document, 
                                str(file_path), 
                                subject
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to auto-ingest {file_path.name}: {e}")
        print(f"✅ Finished auto-loading flashcards.")

    asyncio.create_task(load_existing_flashcards())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Put handler logic here or route to jarvis
            if data.get("type") == "command":
                content = data.get("content")
                subject = data.get("subject")
                if jarvis and content:
                    print(f"Received command from Web UI: {content} (Subject: {subject})")
                    # Process command using threadsafe execution on the main loop
                    asyncio.run_coroutine_threadsafe(jarvis.process_command(content, subject=subject), jarvis.loop)
            
            elif data.get("type") == "set_subject":
                subject = data.get("subject")
                if jarvis:
                    jarvis.active_subject = subject

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
            
            elif data.get("type") == "cancel":
                if jarvis:
                    print(f"{Fore.YELLOW}User sent STOP command. Cancelling current operation...{Style.RESET_ALL}")
                    jarvis.cancel_current()
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/v1/upload-document")
async def upload_document(file: UploadFile = File(...)):
    global jarvis
    if not jarvis or not hasattr(jarvis, 'ai_brain') or not hasattr(jarvis.ai_brain, 'rag_engine'):
        raise HTTPException(status_code=503, detail="JARVIS AI Brain not initialized. Please wait for startup.")
    
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = f"temp_uploads/{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        print(f"📄 Processing uploaded document: {file.filename}")
        
        # Run the CPU-heavy ingestion in a separate thread so we don't block the event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, 
            jarvis.ai_brain.rag_engine.ingest_document, 
            file_path, 
            "viva_doc"
        )
        return {"status": "success", "message": result}
    except Exception as e:
        print(f"❌ Error during document upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ========== FLASHCARD SYSTEM API ==========
FLASHCARDS_FILE = "ai_brain_data/flashcards.json"

def load_flashcards():
    if not os.path.exists(FLASHCARDS_FILE):
        return []
    try:
        with open(FLASHCARDS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_flashcards(flashcards):
    os.makedirs(os.path.dirname(FLASHCARDS_FILE), exist_ok=True)
    with open(FLASHCARDS_FILE, "w") as f:
        json.dump(flashcards, f)

@app.get("/api/local-flashcards")
async def get_flashcards():
    return {"flashcards": load_flashcards()}

@app.post("/api/local-flashcards")
async def create_flashcard(request: Request):
    data = await request.json()
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
        
    flashcards = load_flashcards()
    # Case-insensitive check to prevent duplicates like "Operating System" and "operating system"
    if any(f.lower() == name.lower() for f in flashcards):
        raise HTTPException(status_code=400, detail=f"Flashcard subject '{name}' already exists.")
        
    flashcards.append(name)
    save_flashcards(flashcards)
    
    # Create subject folder for viva materials
    subject_dir = Path("data/subjects") / name
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "status": "success", 
        "message": f"Created subject '{name}'",
        "flashcards": flashcards,
        "count": len(flashcards)
    }

@app.post("/api/local-flashcards/{subject}/upload")
async def upload_flashcard_material(subject: str, file: UploadFile = File(...)):
    global jarvis
    if not jarvis or not hasattr(jarvis, 'ai_brain') or not hasattr(jarvis.ai_brain, 'rag_engine'):
        raise HTTPException(status_code=503, detail="JARVIS AI Brain not initialized.")
        
    flashcards = load_flashcards()
    if subject not in flashcards:
        raise HTTPException(status_code=404, detail="Flashcard subject not found")
        
    # Save to subject folder instead of temp_uploads
    subject_dir = Path("data/subjects") / subject
    subject_dir.mkdir(parents=True, exist_ok=True)
    file_path = subject_dir / file.filename
    
    e = None
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        print(f"📄 Processing flashcard material for {subject}: {file.filename}")
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, 
            jarvis.ai_brain.rag_engine.ingest_document, 
            str(file_path), 
            subject
        )
        return {"status": "success", "message": result}
    except Exception as ex:
        e = ex
        import traceback
        traceback.print_exc()
        print(f"❌ Error during flashcard material upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up if file was created but ingestion failed
        if os.path.exists(file_path) and e is not None and "error" in str(e).lower():
            os.remove(file_path)

@app.get("/api/local-flashcards/{subject}/materials")
async def get_subject_materials(subject: str):
    """Get list of materials uploaded to a flashcard subject."""
    flashcards = load_flashcards()
    if subject not in flashcards:
        raise HTTPException(status_code=404, detail="Flashcard subject not found")
    
    subject_dir = Path("data/subjects") / subject
    if not subject_dir.exists():
        return {"materials": []}
    
    materials = []
    for file_path in subject_dir.rglob("*"):
        if file_path.is_file():
            # Get relative path from subject directory
            relative_path = file_path.relative_to(subject_dir)
            materials.append({
                "name": file_path.name,
                "path": str(relative_path),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
    
    return {"materials": materials}

import shutil

@app.delete("/api/local-flashcards/{subject}")
async def delete_flashcard_subject(subject: str):
    """Deletes an entire flashcard subject and its folder."""
    flashcards = load_flashcards()
    if subject not in flashcards:
        raise HTTPException(status_code=404, detail="Flashcard subject not found")
        
    # 1. Remove from JSON tracker
    flashcards.remove(subject)
    save_flashcards(flashcards)
    
    # 2. Delete the directory and its contents
    subject_dir = Path("data/subjects") / subject
    if subject_dir.exists() and subject_dir.is_dir():
        try:
            shutil.rmtree(subject_dir)
        except Exception as e:
            print(f"⚠️ Failed to delete folder {subject_dir}: {e}")
            
    return {"status": "success", "message": f"Deleted subject '{subject}'"}

@app.delete("/api/local-flashcards/{subject}/materials/{filename}")
async def delete_flashcard_material(subject: str, filename: str):
    """Deletes a specific material file from a flashcard subject."""
    flashcards = load_flashcards()
    if subject not in flashcards:
        raise HTTPException(status_code=404, detail="Flashcard subject not found")
        
    file_path = Path("data/subjects") / subject / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Material file not found")
        
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"❌ Error deleting material {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "success", "message": f"Deleted material '{filename}'"}
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