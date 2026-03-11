"""
Enhanced Media Manager for macOS
Handles music, video, streaming services, and media playback control
"""

import urllib.parse
import webbrowser
import subprocess
import time
import json
import logging
import re
import os
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import pywhatkit
import pyautogui
import requests
import applescript
import psutil
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yt_dlp
import vlc
import pygame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaService(Enum):
    """Supported media services"""
    YOUTUBE = "youtube"
    YOUTUBE_MUSIC = "youtube_music"
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    SOUNDCLOUD = "soundcloud"
    BANDCAMP = "bandcamp"
    VIMEO = "vimeo"
    NETFLIX = "netflix"
    PRIME_VIDEO = "prime_video"
    HOTSTAR = "hotstar"
    JIO_SAVN = "jio_saavn"
    GAANA = "gaana"
    WYNK = "wynk"
    TIDAL = "tidal"
    DEEZER = "deezer"
    LOCAL = "local"


class MediaType(Enum):
    """Types of media content"""
    MUSIC = "music"
    VIDEO = "video"
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    PLAYLIST = "playlist"
    ALBUM = "album"
    PODCAST = "podcast"
    AUDIOBOOK = "audiobook"


class PlaybackState(Enum):
    """Playback states"""
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    BUFFERING = "buffering"
    LOADING = "loading"
    ERROR = "error"


@dataclass
class MediaItem:
    """Media item data structure"""
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None  # seconds
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    service: MediaService = MediaService.YOUTUBE
    media_type: MediaType = MediaType.MUSIC
    quality: Optional[str] = None
    file_path: Optional[Path] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    lyrics: Optional[str] = None
    rating: Optional[float] = None
    play_count: int = 0
    last_played: Optional[datetime] = None
    added_date: datetime = field(default_factory=datetime.now)


@dataclass
class Playlist:
    """Playlist data structure"""
    id: str
    name: str
    items: List[MediaItem] = field(default_factory=list)
    service: MediaService = MediaService.LOCAL
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    item_count: int = 0
    total_duration: int = 0
    cover_art: Optional[str] = None


class MediaError(Exception):
    """Custom exception for media operations"""
    pass


class MediaManager:
    """
    Enhanced Media Manager with comprehensive features:
    - Multi-service support (YouTube, Spotify, Apple Music, etc.)
    - Smart media recognition and parsing
    - Playback control across services
    - Playlist management
    - Download capabilities
    - Lyrics fetching
    - Queue management
    - History tracking
    - Voice command parsing
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Media Manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".config" / "media_manager.json"
        
        # Service configurations
        self.services = self._initialize_services()
        
        # Media state
        self.current_playback: Dict[str, Any] = {
            "state": PlaybackState.STOPPED,
            "item": None,
            "position": 0,
            "volume": 50,
            "queue": [],
            "history": [],
            "service": None
        }
        
        # Collections
        self.playlists: Dict[str, Playlist] = {}
        self.library: List[MediaItem] = []
        self.recently_played: List[MediaItem] = []
        
        # Media players
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()
        
        # Initialize pygame for audio
        pygame.mixer.init()
        
        self.default_service: MediaService = MediaService.LOCAL
        
        # Audio configuration
        self.sample_rate = 44100
        self.channels = 2
        
        # Spotify client
        self.spotify_client: Optional[spotipy.Spotify] = None
        
        # Load configuration
        self._load_config()
        
        # Initialize service clients
        self._init_service_clients()
    
    def _initialize_services(self) -> Dict[MediaService, Dict[str, Any]]:
        """Initialize service configurations"""
        home = Path.home()
        
        return {
            MediaService.SPOTIFY: {
                "name": "Spotify",
                "app_path": Path("/Applications/Spotify.app"),
                "api_enabled": False,  # Will be enabled if credentials exist
                "web_url": "https://open.spotify.com",
                "search_url": "https://api.spotify.com/v1/search",
                "protocol": "spotify://"
            },
            MediaService.APPLE_MUSIC: {
                "name": "Apple Music",
                "app_path": Path("/Applications/Music.app"),
                "api_enabled": True,
                "web_url": "https://music.apple.com",
                "protocol": "music://"
            },
            MediaService.YOUTUBE: {
                "name": "YouTube",
                "app_path": None,  # Web-based
                "web_url": "https://youtube.com",
                "search_url": "https://www.youtube.com/results?search_query={}",
                "watch_url": "https://www.youtube.com/watch?v={}"
            },
            MediaService.YOUTUBE_MUSIC: {
                "name": "YouTube Music",
                "app_path": None,
                "web_url": "https://music.youtube.com",
                "search_url": "https://music.youtube.com/search?q={}"
            },
            MediaService.NETFLIX: {
                "name": "Netflix",
                "app_path": None,
                "web_url": "https://netflix.com",
                "search_url": "https://www.netflix.com/search?q={}"
            },
            MediaService.PRIME_VIDEO: {
                "name": "Prime Video",
                "app_path": None,
                "web_url": "https://primevideo.com",
                "search_url": "https://www.primevideo.com/search/ref=atv_nb_sr?phrase={}"
            },
            MediaService.LOCAL: {
                "name": "Local Media",
                "music_dir": home / "Music",
                "videos_dir": home / "Movies",
                "download_dir": home / "Downloads"
            }
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                    # Load Spotify credentials
                    if 'spotify' in config:
                        self.services[MediaService.SPOTIFY]['api_enabled'] = True
                        self.services[MediaService.SPOTIFY]['client_id'] = config['spotify'].get('client_id')
                        self.services[MediaService.SPOTIFY]['client_secret'] = config['spotify'].get('client_secret')
                    
                    # Load default service
                    self.default_service = MediaService(config.get('default_service', 'youtube'))
                    
                    logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Set default service if not set
        if not hasattr(self, 'default_service'):
            self.default_service = MediaService.YOUTUBE
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'default_service': self.default_service.value,
                'spotify': {
                    'client_id': self.services[MediaService.SPOTIFY].get('client_id'),
                    'client_secret': self.services[MediaService.SPOTIFY].get('client_secret')
                } if self.services[MediaService.SPOTIFY].get('api_enabled') else {}
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _init_service_clients(self):
        """Initialize API clients for services"""
        # Initialize Spotify client if credentials exist
        if self.services[MediaService.SPOTIFY].get('api_enabled'):
            try:
                self.spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=self.services[MediaService.SPOTIFY]['client_id'],
                    client_secret=self.services[MediaService.SPOTIFY]['client_secret'],
                    redirect_uri="http://localhost:8888/callback",
                    scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
                ))
                logger.info("Spotify client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
                self.services[MediaService.SPOTIFY]['api_enabled'] = False
    
    def _parse_media_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language query for media
        
        Args:
            query: Natural language query like "play O Sathii on Spotify"
            
        Returns:
            Parsed query components
        """
        result: Dict[str, Any] = {
            "action": "play",  # Default action
            "query": query,
            "service": None,
            "media_type": MediaType.MUSIC,
            "artist": None,
            "album": None,
            "song": None,
            "playlist": None,
            "explicit_service": None
        }
        
        query_lower = query.lower()
        
        # Extract action
        action_patterns = {
            "play": r"^(play|start|listen to|watch)\s+",
            "pause": r"^(pause|stop)\s+",
            "resume": r"^(resume|continue)\s+",
            "next": r"^(next|skip)\s+",
            "previous": r"^(previous|back)\s+"
        }
        
        for action, pattern in action_patterns.items():
            if re.match(pattern, query_lower):
                result["action"] = action
                query = re.sub(pattern, "", query, count=1)
                break
        
        # Extract service
        service_patterns = {
            MediaService.SPOTIFY: r"\b(on|from|via)\s+(spotify)\b",
            MediaService.APPLE_MUSIC: r"\b(on|from|via)\s+(apple music|itunes)\b",
            MediaService.YOUTUBE: r"\b(on|from|via)\s+(youtube|yt)\b",
            MediaService.YOUTUBE_MUSIC: r"\b(on|from|via)\s+(youtube music|yt music)\b",
            MediaService.SOUNDCLOUD: r"\b(on|from|via)\s+(soundcloud)\b",
            MediaService.NETFLIX: r"\b(on|from|via)\s+(netflix)\b",
            MediaService.PRIME_VIDEO: r"\b(on|from|via)\s+(prime video|amazon prime)\b"
        }
        
        for service, pattern in service_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                result["service"] = service
                result["explicit_service"] = service
                query = re.sub(pattern, "", query, count=1).strip()
                break
        
        # Extract media type
        if any(word in query_lower for word in ["movie", "film", "cinema"]):
            result["media_type"] = MediaType.MOVIE
        elif any(word in query_lower for word in ["video", "clip", "music video"]):
            result["media_type"] = MediaType.VIDEO
        elif any(word in query_lower for word in ["podcast", "episode"]):
            result["media_type"] = MediaType.PODCAST
        elif any(word in query_lower for word in ["playlist"]):
            result["media_type"] = MediaType.PLAYLIST
            result["playlist"] = query.replace("playlist", "").strip()
        
        # Try to extract artist and song
        # Pattern: "song by artist" or "artist song"
        artist_patterns = [
            r"(.+?)\s+by\s+(.+)",  # "song by artist"
            r"(.+?)\s+from\s+(.+)",  # "song from album"
        ]
        
        for pattern in artist_patterns:
            match = re.match(pattern, query)
            if match:
                result["song"] = match.group(1).strip()
                result["artist"] = match.group(2).strip()
                query = query.replace(match.group(0), "").strip()
                break
        
        # If no artist extracted, the whole query is the search term
        if not result["song"]:
            result["song"] = query
        
        # Clean up the query
        result["clean_query"] = query
        
        return result
    
    def play_media(self, query: str, service: Optional[MediaService] = None,
                  **kwargs) -> Dict[str, Any]:
        """
        Main method to play media based on natural language query
        
        Args:
            query: Natural language query
            service: Preferred service (optional)
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "item": None,
            "service_used": None,
            "action": "play"
        }
        
        try:
            # Parse the query
            parsed = self._parse_media_query(query)
            
            # Override service if provided
            if service:
                parsed["service"] = service
            
            # Determine which service to use
            target_service = parsed.get("service") or self.default_service
            
            # Route to appropriate method based on service and media type
            if target_service in [MediaService.SPOTIFY, MediaService.APPLE_MUSIC]:
                if parsed["media_type"] == MediaType.PLAYLIST:
                    play_result = self.play_spotify_playlist(parsed["playlist"] or parsed["song"])
                else:
                    play_result = self.play_spotify_track(
                        song=parsed["song"],
                        artist=parsed["artist"]
                    )
            
            elif target_service in [MediaService.YOUTUBE, MediaService.YOUTUBE_MUSIC]:
                if parsed["media_type"] == MediaType.VIDEO:
                    play_result = self.play_youtube_video(parsed["song"])
                elif parsed["media_type"] == MediaType.PLAYLIST:
                    play_result = self.play_youtube_playlist(parsed["playlist"] or parsed["song"])
                else:
                    play_result = self.play_youtube_music(parsed["song"], parsed["artist"])
            
            elif target_service == MediaService.NETFLIX:
                play_result = self.play_netflix_content(parsed["song"], parsed["media_type"])
            
            elif target_service == MediaService.PRIME_VIDEO:
                play_result = self.play_prime_video(parsed["song"])
            
            else:
                # Try to find local media
                play_result = self.play_local_media(parsed["song"])
            
            result.update(play_result)
            
        except MediaError as e:
            result["message"] = str(e)
            logger.error(f"Media error: {e}")
            
            # Try fallback to YouTube
            if "fallback" in kwargs.get("options", []):
                logger.info("Falling back to YouTube")
                return self.play_youtube_video(query)
        
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            logger.exception("Unexpected error in play_media")
        
        return result
    
    def play_youtube_video(self, query: str, video_id: Optional[str] = None,
                          quality: str = "high") -> Dict[str, Any]:
        """
        Play a YouTube video with enhanced options
        
        Args:
            query: Search query or video title
            video_id: Specific YouTube video ID
            quality: Video quality preference
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "youtube",
            "media_type": "video",
            "url": None,
            "title": None,
            "duration": None
        }
        
        try:
            if video_id:
                # Direct video ID
                url = f"https://www.youtube.com/watch?v={video_id}"
                result["url"] = url
                
                # Get video info using yt-dlp
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    result["title"] = info.get('title')
                    result["duration"] = info.get('duration')
            else:
                # Search and play
                try:
                    # Try pywhatkit first
                    pywhatkit.playonyt(query)
                    result["success"] = True
                    result["message"] = f"Playing '{query}' on YouTube"
                    result["url"] = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                except:
                    # Fallback to browser
                    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                    webbrowser.open(url)
                    result["success"] = True
                    result["message"] = f"Searching YouTube for '{query}'"
                    result["url"] = url
            
            # Track in history
            if result["success"]:
                self._add_to_history(MediaItem(
                    id=self._generate_id(),
                    title=result.get("title", query),
                    artist="YouTube",
                    url=result["url"],
                    service=MediaService.YOUTUBE,
                    media_type=MediaType.VIDEO
                ))
        
        except Exception as e:
            result["message"] = f"Error playing YouTube video: {e}"
            logger.exception("YouTube playback error")
        
        return result
    
    def play_youtube_music(self, song: str, artist: Optional[str] = None) -> Dict[str, Any]:
        """
        Play music on YouTube Music
        
        Args:
            song: Song title
            artist: Artist name (optional)
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "youtube_music",
            "media_type": "music"
        }
        
        try:
            # Construct search query
            if artist:
                search_query = f"{song} {artist}"
            else:
                search_query = song
            
            # Try YouTube Music specific URL
            url = f"https://music.youtube.com/search?q={urllib.parse.quote(search_query)}"
            
            # Open in browser
            webbrowser.open(url)
            
            result["success"] = True
            result["message"] = f"Searching YouTube Music for '{search_query}'"
            result["url"] = url
            
            # Try to get first result info
            try:
                # Use yt-dlp to search
                ydl_opts = {
                    'quiet': True,
                    'extract_flat': True,
                    'default_search': 'ytsearch1'
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                    if info and 'entries' in info and info['entries']:
                        first_result = info['entries'][0]
                        result["title"] = first_result.get('title')
                        result["duration"] = first_result.get('duration')
            except:
                pass
        
        except Exception as e:
            result["message"] = f"Error playing YouTube Music: {e}"
        
        return result
    
    def play_youtube_playlist(self, playlist_name: str) -> Dict[str, Any]:
        """
        Play a YouTube playlist
        
        Args:
            playlist_name: Playlist name or query
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "youtube",
            "media_type": "playlist"
        }
        
        try:
            # Search for playlist
            search_query = f"{playlist_name} playlist"
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}&sp=EgIQAw%253D%253D"
            
            webbrowser.open(url)
            
            result["success"] = True
            result["message"] = f"Searching YouTube for playlist '{playlist_name}'"
            result["url"] = url
        
        except Exception as e:
            result["message"] = f"Error playing YouTube playlist: {e}"
        
        return result
    
    def play_spotify_track(self, song: str, artist: Optional[str] = None,
                          use_api: bool = True) -> Dict[str, Any]:
        """
        Play a Spotify track
        
        Args:
            song: Song title
            artist: Artist name (optional)
            use_api: Use Spotify API if available
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "spotify",
            "media_type": "track"
        }
        
        try:
            # Check if Spotify app is installed
            spotify_path = self.services[MediaService.SPOTIFY]['app_path']
            
            # Try using API first
            if use_api and self.services[MediaService.SPOTIFY].get('api_enabled'):
                try:
                    # Search for track
                    search_query = song
                    if artist:
                        search_query = f"track:{song} artist:{artist}"
                    
                    results = self.spotify_client.search(q=search_query, type='track', limit=1)  # pyre-ignore[16]
                    
                    if results['tracks']['items']:
                        track = results['tracks']['items'][0]
                        track_uri = track['uri']
                        
                        # Get active devices
                        devices = self.spotify_client.devices()  # pyre-ignore[16]
                        
                        if devices['devices']:
                            # Play on first available device
                            self.spotify_client.start_playback(  # pyre-ignore[16]
                                uris=[track_uri],
                                device_id=devices['devices'][0]['id']
                            )
                            result["success"] = True
                            result["message"] = f"Playing '{song}' on Spotify"
                            result["track_name"] = track['name']
                            result["artist"] = track['artists'][0]['name']
                            result["album"] = track['album']['name']
                            result["duration_ms"] = track['duration_ms']
                            result["url"] = track['external_urls']['spotify']
                            
                            # Track in history
                            self._add_to_history(MediaItem(
                                id=track['id'],
                                title=track['name'],
                                artist=track['artists'][0]['name'],
                                album=track['album']['name'],
                                duration=track['duration_ms'] // 1000,
                                url=track['external_urls']['spotify'],
                                service=MediaService.SPOTIFY,
                                media_type=MediaType.MUSIC
                            ))
                            
                            return result
                except Exception as e:
                    logger.error(f"Spotify API error: {e}")
            
            # Fallback to opening Spotify app or web player
            if spotify_path and spotify_path.exists():
                # Open Spotify app
                search_query = song
                if artist:
                    search_query = f"{song} {artist}"
                
                # Spotify URI scheme
                spotify_uri = f"spotify:search:{urllib.parse.quote(search_query)}"
                
                subprocess.run(['open', '-a', str(spotify_path), spotify_uri])
                result["success"] = True
                result["message"] = f"I've opened Spotify search for {search_query}. Please press play manually, as auto-playback requires API configuration."
                result["method"] = "app"
            else:
                # Open web player
                search_query = song
                if artist:
                    search_query = f"{song} {artist}"
                
                url = f"https://open.spotify.com/search/{urllib.parse.quote(search_query)}"
                webbrowser.open(url)
                result["success"] = True
                result["message"] = f"I've opened Spotify Web search for {search_query}. Please press play manually, as auto-playback requires API configuration."
                result["method"] = "web"
                result["url"] = url
        
        except Exception as e:
            result["message"] = f"Error playing Spotify track: {e}"
        
        return result
    
    def play_spotify_playlist(self, playlist_name: str) -> Dict[str, Any]:
        """
        Play a Spotify playlist
        
        Args:
            playlist_name: Playlist name
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "spotify",
            "media_type": "playlist"
        }
        
        try:
            # Try API first
            if self.services[MediaService.SPOTIFY].get('api_enabled'):
                try:
                    results = self.spotify_client.search(q=playlist_name, type='playlist', limit=1)  # pyre-ignore[16]
                    
                    if results['playlists']['items']:
                        playlist = results['playlists']['items'][0]
                        playlist_uri = playlist['uri']
                        
                        devices = self.spotify_client.devices()  # pyre-ignore[16]
                        if devices['devices']:
                            self.spotify_client.start_playback(  # pyre-ignore[16]
                                context_uri=playlist_uri,
                                device_id=devices['devices'][0]['id']
                            )
                            
                            result["success"] = True
                            result["message"] = f"Playing playlist '{playlist_name}' on Spotify"
                            result["playlist_name"] = playlist['name']
                            result["tracks_total"] = playlist['tracks']['total']
                            result["url"] = playlist['external_urls']['spotify']
                            
                            return result
                except Exception as e:
                    logger.error(f"Spotify API error: {e}")
            
            # Fallback to web player
            url = f"https://open.spotify.com/search/{urllib.parse.quote(playlist_name)}/playlists"
            webbrowser.open(url)
            result["success"] = True
            result["message"] = f"Searching Spotify for playlist '{playlist_name}'"
            result["url"] = url
        
        except Exception as e:
            result["message"] = f"Error playing Spotify playlist: {e}"
        
        return result
    
    def play_apple_music(self, song: str, artist: Optional[str] = None) -> Dict[str, Any]:
        """
        Play Apple Music
        
        Args:
            song: Song title
            artist: Artist name
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "apple_music",
            "media_type": "music"
        }
        
        try:
            # Check if Music app is installed
            music_path = self.services[MediaService.APPLE_MUSIC]['app_path']
            
            if music_path and music_path.exists():
                # Use AppleScript to search in Music app
                search_query = song
                if artist:
                    search_query = f"{song} {artist}"
                
                script = f'''
                    tell application "Music"
                        activate
                        search library for "{search_query}"
                    end tell
                '''
                
                subprocess.run(['osascript', '-e', script])
                result["success"] = True
                result["message"] = f"Searching Apple Music for '{search_query}'"
                result["method"] = "app"
            else:
                # Open web player
                search_query = song
                if artist:
                    search_query = f"{song} {artist}"
                
                url = f"https://music.apple.com/search?term={urllib.parse.quote(search_query)}"
                webbrowser.open(url)
                result["success"] = True
                result["message"] = f"Searching Apple Music Web for '{search_query}'"
                result["method"] = "web"
                result["url"] = url
        
        except Exception as e:
            result["message"] = f"Error playing Apple Music: {e}"
        
        return result
    
    def play_netflix_content(self, title: str, media_type: MediaType = MediaType.MOVIE) -> Dict[str, Any]:
        """
        Play Netflix content
        
        Args:
            title: Movie or show title
            media_type: Type of content
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "netflix",
            "media_type": media_type.value
        }
        
        try:
            # Construct search URL
            search_url = f"https://www.netflix.com/search?q={urllib.parse.quote(title)}"
            
            # Open Netflix in browser
            webbrowser.open(search_url)
            
            result["success"] = True
            result["message"] = f"Searching Netflix for '{title}'"
            result["url"] = search_url
        
        except Exception as e:
            result["message"] = f"Error playing Netflix content: {e}"
        
        return result
    
    def play_prime_video(self, title: str) -> Dict[str, Any]:
        """
        Play Prime Video content
        
        Args:
            title: Movie or show title
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "prime_video"
        }
        
        try:
            # Construct search URL
            search_url = f"https://www.primevideo.com/search/ref=atv_nb_sr?phrase={urllib.parse.quote(title)}"
            
            webbrowser.open(search_url)
            
            result["success"] = True
            result["message"] = f"Searching Prime Video for '{title}'"
            result["url"] = search_url
        
        except Exception as e:
            result["message"] = f"Error playing Prime Video content: {e}"
        
        return result
    
    def play_local_media(self, query: str) -> Dict[str, Any]:
        """
        Play local media files
        
        Args:
            query: File name or search query
            
        Returns:
            Dictionary with playback result
        """
        result = {
            "success": False,
            "message": "",
            "service": "local"
        }
        
        try:
            # Search in common media directories
            media_dirs = [
                self.services[MediaService.LOCAL]['music_dir'],
                self.services[MediaService.LOCAL]['videos_dir'],
                self.services[MediaService.LOCAL]['download_dir']
            ]
            
            matches = []
            query_lower = query.lower()
            
            for directory in media_dirs:
                if directory and directory.exists():
                    for file in directory.rglob("*"):
                        if file.is_file() and query_lower in file.stem.lower():
                            if file.suffix.lower() in ['.mp3', '.wav', '.flac', '.m4a', '.mp4', '.mkv', '.avi']:
                                matches.append(file)
            
            if matches:
                # Play the first match
                file_path = matches[0]
                
                # Determine media type
                if file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.m4a']:
                    # Audio file
                    pygame.mixer.music.load(str(file_path))
                    pygame.mixer.music.play()
                    
                    result["success"] = True
                    result["message"] = f"Playing local file: {file_path.name}"
                    result["file_path"] = str(file_path)
                    result["media_type"] = "audio"
                else:
                    # Video file - open with default player
                    subprocess.run(['open', str(file_path)])
                    
                    result["success"] = True
                    result["message"] = f"Opening video: {file_path.name}"
                    result["file_path"] = str(file_path)
                    result["media_type"] = "video"
            else:
                result["message"] = f"No local media found matching '{query}'"
        
        except Exception as e:
            result["message"] = f"Error playing local media: {e}"
        
        return result
    
    def play_spotify_song(self, query: str) -> Dict[str, Any]:
        """
        Specialized method for playing a Spotify song by query, 
        mapping directly from the main JARVIS command loop.
        """
        return self.play_media(query, service=MediaService.SPOTIFY)

    def control_playback(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Control media playback across services
        
        Args:
            action: Action to perform (play, pause, next, previous, etc.)
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with control result
        """
        result = {
            "success": False,
            "message": "",
            "action": action
        }
        
        try:
            action = action.lower()
            
            # Define action mappings
            action_mappings = {
                "play": ("play", None),
                "pause": ("pause", None),
                "stop": ("stop", None),
                "next": ("next", "right"),
                "previous": ("previous", "left"),
                "skip": ("next", "right"),
                "back": ("previous", "left"),
                "volume_up": ("volume_up", "up"),
                "volume_down": ("volume_down", "down"),
                "mute": ("mute", None),
                "unmute": ("unmute", None),
                "shuffle": ("shuffle", None),
                "repeat": ("repeat", None)
            }
            
            if action not in action_mappings:
                result["message"] = f"Unknown action: {action}"
                return result
            
            # Try service-specific control first
            service_controlled = False
            
            # Check if Spotify is active
            if self._is_service_active(MediaService.SPOTIFY):
                if self.services[MediaService.SPOTIFY].get('api_enabled'):
                    try:
                        if action == "play":
                            self.spotify_client.start_playback()  # pyre-ignore[16]
                        elif action == "pause":
                            self.spotify_client.pause_playback()  # pyre-ignore[16]
                        elif action == "next":
                            self.spotify_client.next_track()  # pyre-ignore[16]
                        elif action == "previous":
                            self.spotify_client.previous_track()  # pyre-ignore[16]
                        elif action == "shuffle":
                            self.spotify_client.shuffle(True)  # pyre-ignore[16]
                        
                        service_controlled = True
                        result["success"] = True
                        result["message"] = f"Spotify: {action}"
                        result["service"] = "spotify"
                    except Exception as e:
                        logger.error(f"Spotify control error: {e}")
            
            # Check if Apple Music is active
            if not service_controlled and self._is_service_active(MediaService.APPLE_MUSIC):
                try:
                    apple_script = {
                        "play": 'tell application "Music" to play',
                        "pause": 'tell application "Music" to pause',
                        "next": 'tell application "Music" to next track',
                        "previous": 'tell application "Music" to previous track',
                        "volume_up": 'tell application "Music" to set sound volume to sound volume + 10',
                        "volume_down": 'tell application "Music" to set sound volume to sound volume - 10'
                    }
                    
                    if action in apple_script:
                        subprocess.run(['osascript', '-e', apple_script[action]])
                        service_controlled = True
                        result["success"] = True
                        result["message"] = f"Apple Music: {action}"
                        result["service"] = "apple_music"
                except Exception as e:
                    logger.error(f"Apple Music control error: {e}")
            
            # Fallback to keyboard shortcuts
            if not service_controlled:
                mapped_action, key = action_mappings.get(action, (action, None))
                
                if key:
                    pyautogui.press(key)
                    result["success"] = True
                    result["message"] = f"Media {action} executed (keyboard)"
                elif action == "play":
                    pyautogui.press("space")
                    result["success"] = True
                    result["message"] = "Play/Pause toggled"
                elif action == "volume_up":
                    pyautogui.press("volumeup")
                    result["success"] = True
                    result["message"] = "Volume increased"
                elif action == "volume_down":
                    pyautogui.press("volumedown")
                    result["success"] = True
                    result["message"] = "Volume decreased"
                elif action == "mute":
                    pyautogui.press("volumemute")
                    result["success"] = True
                    result["message"] = "Volume muted"
        
        except Exception as e:
            result["message"] = f"Error controlling playback: {e}"
            logger.exception("Playback control error")
        
        return result
    
    def _is_service_active(self, service: MediaService) -> bool:
        """Check if a media service is currently active"""
        try:
            if service == MediaService.SPOTIFY:
                # Check if Spotify is running
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and 'spotify' in proc.info['name'].lower():
                        return True
            
            elif service == MediaService.APPLE_MUSIC:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] and 'music' in proc.info['name'].lower():
                        return True
            
            return False
        except:
            return False
    
    def set_volume(self, level: int) -> Dict[str, Any]:
        """
        Set media volume
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            Dictionary with result
        """
        result = {"success": False, "message": "", "volume": level}
        
        try:
            level = max(0, min(100, level))  # Clamp between 0-100
            
            # Try system volume first
            if level < 0 or level > 100:
                result["message"] = "Volume must be between 0 and 100"
                return result
            
            # macOS volume control
            subprocess.run([
                'osascript', '-e',
                f'set volume output volume {level}'
            ])
            
            # Update internal state
            self.current_playback["volume"] = level
            
            result["success"] = True
            result["message"] = f"Volume set to {level}%"
        
        except Exception as e:
            result["message"] = f"Error setting volume: {e}"
        
        return result
    
    def get_current_playback(self) -> Dict[str, Any]:
        """
        Get current playback information
        
        Returns:
            Dictionary with current playback state
        """
        result = {
            "success": False,
            "message": "",
            "state": self.current_playback["state"].value,
            "item": None,
            "position": self.current_playback["position"],
            "volume": self.current_playback["volume"]
        }
        
        try:
            # Try to get info from active services
            if self._is_service_active(MediaService.SPOTIFY) and self.services[MediaService.SPOTIFY].get('api_enabled'):
                try:
                    playback = self.spotify_client.current_playback()  # pyre-ignore[16]
                    if playback:
                        item = playback.get('item', {})
                        result["success"] = True
                        result["state"] = playback.get('is_playing') and "playing" or "paused"
                        result["item"] = {
                            "title": item.get('name'),
                            "artist": item['artists'][0]['name'] if item.get('artists') else None,
                            "album": item.get('album', {}).get('name'),
                            "duration_ms": item.get('duration_ms'),
                            "progress_ms": playback.get('progress_ms'),
                            "url": item.get('external_urls', {}).get('spotify'),
                            "service": "spotify"
                        }
                        result["position"] = playback.get('progress_ms', 0) / 1000
                except:
                    pass
            
            elif self._is_service_active(MediaService.APPLE_MUSIC):
                try:
                    script = '''
                        tell application "Music"
                            if player state is playing then
                                return {name:name of current track, artist:artist of current track, album:album of current track, duration:duration of current track, position:player position}
                            end if
                        end tell
                    '''
                    
                    proc = subprocess.run(
                        ['osascript', '-e', script],
                        capture_output=True,
                        text=True
                    )
                    
                    if proc.stdout:
                        # Parse AppleScript output (simplified)
                        result["success"] = True
                        result["state"] = "playing"
                        result["service"] = "apple_music"
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Error getting current playback: {e}")
        
        return result
    
    def create_playlist(self, name: str, items: Optional[List[MediaItem]] = None) -> Playlist:
        """
        Create a new playlist
        
        Args:
            name: Playlist name
            items: Initial items
            
        Returns:
            Created playlist
        """
        playlist_id = self._generate_id()
        
        playlist = Playlist(
            id=playlist_id,
            name=name,
            items=items or [],
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
        
        self.playlists[playlist_id] = playlist
        
        return playlist
    
    def add_to_playlist(self, playlist_id: str, item: MediaItem) -> bool:
        """
        Add item to playlist
        
        Args:
            playlist_id: Playlist ID
            item: Media item to add
            
        Returns:
            Success status
        """
        if playlist_id in self.playlists:
            self.playlists[playlist_id].items.append(item)
            self.playlists[playlist_id].modified_date = datetime.now()
            self.playlists[playlist_id].item_count = len(self.playlists[playlist_id].items)
            
            # Update total duration
            if item.duration:
                self.playlists[playlist_id].total_duration += item.duration
            
            return True
        
        return False
    
    def get_lyrics(self, song: str, artist: Optional[str] = None) -> Optional[str]:
        """
        Get song lyrics
        
        Args:
            song: Song title
            artist: Artist name
            
        Returns:
            Lyrics if found
        """
        try:
            # Try multiple sources
            sources = [
                self._get_lyrics_genius(song, artist),
                self._get_lyrics_azlyrics(song, artist)
            ]
            
            for lyrics in sources:
                if lyrics:
                    return lyrics
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting lyrics: {e}")
            return None
    
    def _get_lyrics_genius(self, song: str, artist: Optional[str] = None) -> Optional[str]:
        """Get lyrics from Genius"""
        try:
            # Construct search URL
            search_query = song
            if artist:
                search_query = f"{song} {artist}"
            
            url = f"https://genius.com/search?q={urllib.parse.quote(search_query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find first song link
            song_link = soup.find('a', class_='song_link')
            if song_link and song_link.get('href'):
                lyrics_url = song_link['href']
                
                # Get lyrics page
                lyrics_response = requests.get(lyrics_url, headers=headers, timeout=5)
                lyrics_soup = BeautifulSoup(lyrics_response.text, 'html.parser')
                
                # Extract lyrics
                lyrics_div = lyrics_soup.find('div', class_='lyrics')
                if lyrics_div:
                    return lyrics_div.get_text().strip()
        
        except Exception as e:
            logger.error(f"Genius lyrics error: {e}")
        
        return None
    
    def _get_lyrics_azlyrics(self, song: str, artist: Optional[str] = None) -> Optional[str]:
        """Get lyrics from AZLyrics"""
        try:
            # Simplified artist and song for URL
            if artist:
                artist_clean = re.sub(r'[^a-zA-Z0-9]', '', artist.lower())
                song_clean = re.sub(r'[^a-zA-Z0-9]', '', song.lower())
                
                url = f"https://www.azlyrics.com/lyrics/{artist_clean}/{song_clean}.html"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find lyrics div
                    lyrics_div = soup.find('div', class_='lyricsh')
                    if lyrics_div:
                        return lyrics_div.get_text().strip()
        
        except Exception as e:
            logger.error(f"AZLyrics error: {e}")
        
        return None
    
    def download_media(self, url: str, format: str = "best",
                      output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Download media from URL
        
        Args:
            url: Media URL (YouTube, etc.)
            format: Download format
            output_dir: Output directory
            
        Returns:
            Dictionary with download result
        """
        result = {"success": False, "message": "", "file_path": None}
        
        try:
            output_dir = output_dir or Path.home() / "Downloads" / "Media"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': format,
                'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._download_progress_hook]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                result["success"] = True
                result["message"] = f"Downloaded: {info.get('title')}"
                result["file_path"] = filename
                result["title"] = info.get('title')
                result["duration"] = info.get('duration')
        
        except Exception as e:
            result["message"] = f"Error downloading media: {e}"
            logger.exception("Download error")
        
        return result
    
    def _download_progress_hook(self, d):
        """Download progress hook"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            logger.info(f"Download progress: {percent}")
    
    def search_media(self, query: str, service: Optional[MediaService] = None,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for media across services
        
        Args:
            query: Search query
            service: Specific service to search
            limit: Maximum results
            
        Returns:
            List of search results
        """
        results = []
        
        try:
            # Determine services to search
            services_to_search = [service] if service else list(MediaService)
            
            for svc in services_to_search:
                if svc == MediaService.YOUTUBE:
                    # YouTube search
                    ydl_opts = {
                        'quiet': True,
                        'extract_flat': True,
                        'default_search': f'ytsearch{limit}'
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                        
                        if info and 'entries' in info:
                            for entry in info['entries']:
                                results.append({
                                    "title": entry.get('title'),
                                    "url": f"https://youtube.com/watch?v={entry.get('id')}",
                                    "duration": entry.get('duration'),
                                    "service": "youtube",
                                    "thumbnail": entry.get('thumbnail'),
                                    "channel": entry.get('channel')
                                })
                
                elif svc == MediaService.SPOTIFY and self.services[svc].get('api_enabled'):
                    # Spotify search
                    spotify_results = self.spotify_client.search(q=query, limit=limit)  # pyre-ignore[16]
                    
                    for track in spotify_results['tracks']['items']:
                        results.append({
                            "title": track['name'],
                            "artist": track['artists'][0]['name'],
                            "album": track['album']['name'],
                            "url": track['external_urls']['spotify'],
                            "duration_ms": track['duration_ms'],
                            "service": "spotify",
                            "thumbnail": track['album']['images'][0]['url'] if track['album']['images'] else None
                        })
        
        except Exception as e:
            logger.error(f"Error searching media: {e}")
        
        return results
    
    def get_recently_played(self, limit: int = 20) -> List[MediaItem]:
        """Get recently played media"""
        return self.recently_played[:limit]
    
    def _add_to_history(self, item: MediaItem):
        """Add item to history"""
        self.recently_played.insert(0, item)
        
        # Keep only last 100 items
        if len(self.recently_played) > 100:
            self.recently_played = self.recently_played[:100]
        
        # Update current playback
        self.current_playback["item"] = item
        self.current_playback["state"] = PlaybackState.PLAYING
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import hashlib
        import time
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:16]
    
    def configure_spotify(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """
        Configure Spotify API credentials
        
        Args:
            client_id: Spotify client ID
            client_secret: Spotify client secret
            
        Returns:
            Configuration result
        """
        result = {"success": False, "message": ""}
        
        try:
            self.services[MediaService.SPOTIFY]['client_id'] = client_id
            self.services[MediaService.SPOTIFY]['client_secret'] = client_secret
            self.services[MediaService.SPOTIFY]['api_enabled'] = True
            
            # Reinitialize client
            self._init_service_clients()
            
            self._save_config()
            
            result["success"] = True
            result["message"] = "Spotify configured successfully"
        
        except Exception as e:
            result["message"] = f"Error configuring Spotify: {e}"
        
        return result


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import pprint
    
    manager = MediaManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "play" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            result = manager.play_media(query)
            pprint.pprint(result)
        
        elif command == "control" and len(sys.argv) > 2:
            action = sys.argv[2]
            result = manager.control_playback(action)
            pprint.pprint(result)
        
        elif command == "volume" and len(sys.argv) > 2:
            level = int(sys.argv[2])
            result = manager.set_volume(level)
            pprint.pprint(result)
        
        elif command == "current":
            result = manager.get_current_playback()
            pprint.pprint(result)
        
        elif command == "search" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            results = manager.search_media(query)
            pprint.pprint(results)
        
        elif command == "lyrics" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            lyrics = manager.get_lyrics(query)
            print(lyrics)
        
        else:
            print("Usage: media_manager.py [play|control|volume|current|search|lyrics] [args]")
    else:
        # Demo mode
        print("Media Manager Demo")
        print("-" * 50)
        
        # Test natural language parsing
        test_queries = [
            "play O Sathii on Spotify",
            "play Shape of You by Ed Sheeran",
            "play Inception movie on Netflix",
            "play my workout playlist",
            "play Bohemian Rhapsody"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            result = manager.play_media(query)
            print(f"Result: {result.get('message', 'N/A')}")
        
        # Test playback control
        print("\nPlayback Control:")
        control_actions = ["pause", "next", "volume_up"]
        for action in control_actions:
            result = manager.control_playback(action)
            print(f"  {action}: {result.get('message', 'N/A')}")