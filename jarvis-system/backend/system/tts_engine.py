
import asyncio
import edge_tts
import pygame
import os
import tempfile
import time
import platform
from threading import Thread

class EdgeTTSEngine:
    """
    High-quality Neural TTS Engine using Microsoft Edge's online voices.
    """
    def __init__(self, voice="en-US-ChristopherNeural", rate="+0%", volume="+0%"):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.temp_dir = tempfile.gettempdir()
        self.pygame_available = False
        self.is_cancelled = False
        
        # Initialize pygame mixer for audio playback
        try:
            # Suppress pygame support prompt and errors
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
            import logging
            logging.getLogger("pygame").setLevel(logging.CRITICAL)
            
            # Check OS - on macOS, prefer afplay over pygame for reliability
            if platform.system() == 'Darwin':
                # Force disable pygame to use afplay
                self.pygame_available = False
                # print("MacOS detected: Using system player (afplay) for reliability")
            else:
                pygame.mixer.init()
                self.pygame_available = True
        except Exception as e:
            # print(f"Warning: Could not initialize pygame mixer: {e}")
            self.pygame_available = False

    async def _generate_audio(self, text, output_file):
        """Generate audio file from text using Edge TTS"""
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)
        await communicate.save(output_file)

    def speak(self, text, on_complete=None, on_start=None):
        """
        Convert text to speech and play it immediately.
        Handles both synchronous and asynchronous contexts.
        """
        self.is_cancelled = False
        
        if not text:
            if on_complete:
                on_complete()
            return

        try:
            # Create a unique temporary file
            output_file = os.path.join(self.temp_dir, f"jarvis_speech_{int(time.time()*1000)}.mp3")
            
            # Generate audio handles loop complexity
            try:
                try:
                    # Check if there is an existing loop
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        # Use a separate thread to run the async generation AND playback 
                        # to avoid blocking/conflict and ensure sequence
                        thread = Thread(target=self._generate_and_play, args=(text, output_file, on_complete, on_start))
                        thread.start()
                    else:
                         loop.run_until_complete(self._generate_audio(text, output_file))
                         if on_start:
                             on_start()
                             
                         if self.is_cancelled:
                             return
                             
                         self._play_audio(output_file)
                         if on_complete:
                             on_complete()
                except RuntimeError:
                    # No running loop, safe to create one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._generate_audio(text, output_file))
                    loop.close()
                    if on_start:
                        on_start()
                        
                    if self.is_cancelled:
                        return
                        
                    self._play_audio(output_file)
                    if on_complete:
                        on_complete()
            except Exception as e:
                print(f"Error generating speech: {e}")
                if on_complete:
                    on_complete()
                return

            # Note: _play_audio is now called inside the blocks above
            
        except Exception as e:
            print(f"Error in TTS: {e}")
            if on_complete:
                on_complete()
            
    def _generate_and_play(self, text, output_file, on_complete=None, on_start=None):
        """Helper to generate and play audio in a thread"""
        try:
             # We need a new loop for async generation in this thread
             new_loop = asyncio.new_event_loop()
             asyncio.set_event_loop(new_loop)
             new_loop.run_until_complete(self._generate_audio(text, output_file))
             new_loop.close()
             
             if on_start:
                 try:
                     on_start()
                 except Exception as e:
                     print(f"Error in start callback: {e}")
             
             if not self.is_cancelled:
                 self._play_audio(output_file)
        except Exception as e:
             print(f"Error in background TTS thread: {e}")
        finally:
             if on_complete:
                 try:
                     on_complete()
                 except Exception as e:
                     print(f"Error in completion callback: {e}")

    def _play_audio(self, file_path):
        """Play audio file using pygame or system player"""
        print(f"Attempting playback for: {file_path}")
        
        # Try pygame first if available
        pygame_success = False
        if self.pygame_available:
            try:
                # Suppress pygame error spam
                import logging
                logging.getLogger("pygame").setLevel(logging.CRITICAL)
                
                if not pygame.mixer.get_init():
                    try:
                        pygame.mixer.init()
                    except:
                        pass
                
                if pygame.mixer.get_init():
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    pygame.mixer.music.unload()
                    pygame_success = True
            except Exception:
                # maintain silence on pygame failure if it's common
                pass

        # Fallback to system player (afplay for macOS)
        if not pygame_success:
            try:
                print("Falling back to system player (afplay)...")
                import subprocess
                subprocess.run(["afplay", file_path], check=False)
                print("afplay playback successful.")
            except Exception as e:
                print(f"System playback error: {e}")

                
        # Cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

    async def speak_async(self, text):
        """Async version of speak"""
        if not text:
            return

        try:
            output_file = os.path.join(self.temp_dir, f"jarvis_speech_{int(time.time()*1000)}.mp3")
            await self._generate_audio(text, output_file)
            self._play_audio(output_file)
        except Exception as e:
            print(f"Error in async TTS: {e}")

    def stop(self):
        """Stop current playback"""
        self.is_cancelled = True
        try:
            if platform.system() == "Darwin":
                import subprocess
                subprocess.run(['pkill', '-f', 'afplay'], capture_output=True)
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
