import urllib.parse
import webbrowser
import pywhatkit
import pyautogui

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
