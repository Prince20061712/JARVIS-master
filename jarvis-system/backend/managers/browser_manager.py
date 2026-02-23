"""
Enhanced Browser Manager for macOS
Handles web browsing, tab management, bookmarks, and browser automation with robust error handling
"""

import os
import webbrowser
import urllib.parse
import subprocess
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import sqlite3
import plistlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserType(Enum):
    """Supported browser types"""
    CHROME = "chrome"
    SAFARI = "safari"
    FIREFOX = "firefox"
    BRAVE = "brave"
    EDGE = "edge"
    OPERA = "opera"
    ARC = "arc"
    VIVALDI = "vivaldi"
    CUSTOM = "custom"


class SearchEngine(Enum):
    """Supported search engines"""
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    YAHOO = "yahoo"
    BAIDU = "baidu"
    YANDEX = "yandex"
    ECOSIA = "ecosia"
    BRAVE_SEARCH = "brave"


class PrivacyMode(Enum):
    """Privacy modes for browsing"""
    NORMAL = "normal"
    INCOGNITO = "incognito"
    PRIVATE = "private"
    TOR = "tor"


@dataclass
class BrowserProfile:
    """Browser profile information"""
    name: str
    browser_type: BrowserType
    path: Optional[Path] = None
    data_dir: Optional[Path] = None
    default_search: SearchEngine = SearchEngine.GOOGLE
    incognito_supported: bool = True
    extensions: List[str] = field(default_factory=list)
    bookmarks_file: Optional[Path] = None
    cookies_file: Optional[Path] = None
    history_file: Optional[Path] = None
    last_used: Optional[datetime] = None


@dataclass
class Bookmark:
    """Bookmark data structure"""
    id: str
    title: str
    url: str
    folder: str = "Other"
    tags: List[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    last_visited: Optional[datetime] = None
    visit_count: int = 0
    favicon: Optional[str] = None


@dataclass
class HistoryEntry:
    """Browser history entry"""
    id: str
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    browser: Optional[str] = None


class BrowserError(Exception):
    """Custom exception for browser operations"""
    pass


class BrowserManager:
    """
    Enhanced Browser Manager with comprehensive features:
    - Multi-browser support with profile management
    - Tab management (create, close, list, switch)
    - Bookmark management
    - History tracking
    - Download management
    - Privacy modes
    - Screenshot capture
    - Browser automation
    - Performance monitoring
    - Error recovery
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Browser Manager
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or Path.home() / ".config" / "browser_manager.json"
        self.profiles: Dict[str, BrowserProfile] = {}
        self.default_profile: Optional[str] = None
        self.active_tabs: Dict[str, List[Dict]] = {}  # browser -> list of tabs
        self.downloads: List[Dict] = []
        self.bookmarks: Dict[str, List[Bookmark]] = {}  # browser -> bookmarks
        self.history: Dict[str, List[HistoryEntry]] = {}  # browser -> history
        
        # Known browser paths and data directories
        self.browser_paths = self._initialize_browser_paths()
        
        # Search engine URLs
        self.search_engines = {
            SearchEngine.GOOGLE: "https://www.google.com/search?q={}",
            SearchEngine.BING: "https://www.bing.com/search?q={}",
            SearchEngine.DUCKDUCKGO: "https://duckduckgo.com/?q={}",
            SearchEngine.YAHOO: "https://search.yahoo.com/search?p={}",
            SearchEngine.BAIDU: "https://www.baidu.com/s?wd={}",
            SearchEngine.YANDEX: "https://yandex.com/search/?text={}",
            SearchEngine.ECOSIA: "https://www.ecosia.org/search?q={}",
            SearchEngine.BRAVE_SEARCH: "https://search.brave.com/search?q={}",
        }
        
        # Common website shortcuts
        self.website_shortcuts = {
            "youtube": "https://youtube.com",
            "yt": "https://youtube.com",
            "github": "https://github.com",
            "gh": "https://github.com",
            "gmail": "https://mail.google.com",
            "drive": "https://drive.google.com",
            "docs": "https://docs.google.com",
            "sheets": "https://sheets.google.com",
            "slides": "https://slides.google.com",
            "calendar": "https://calendar.google.com",
            "meet": "https://meet.google.com",
            "maps": "https://maps.google.com",
            "translate": "https://translate.google.com",
            "news": "https://news.google.com",
            "reddit": "https://reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://twitter.com",
            "linkedin": "https://linkedin.com",
            "facebook": "https://facebook.com",
            "instagram": "https://instagram.com",
            "ig": "https://instagram.com",
            "whatsapp": "https://web.whatsapp.com",
            "wa": "https://web.whatsapp.com",
            "telegram": "https://web.telegram.org",
            "tg": "https://web.telegram.org",
            "discord": "https://discord.com/app",
            "dc": "https://discord.com/app",
            "slack": "https://app.slack.com",
            "notion": "https://notion.so",
            "figma": "https://figma.com",
            "canva": "https://canva.com",
            "medium": "https://medium.com",
            "devto": "https://dev.to",
            "stackoverflow": "https://stackoverflow.com",
            "so": "https://stackoverflow.com",
            "wikipedia": "https://wikipedia.org",
            "wiki": "https://wikipedia.org",
            "amazon": "https://amazon.com",
            "flipkart": "https://flipkart.com",
            "netflix": "https://netflix.com",
            "prime": "https://primevideo.com",
            "hotstar": "https://hotstar.com",
            "spotify": "https://open.spotify.com",
            "apple music": "https://music.apple.com",
        }
        
        self._load_config()
        self._discover_browsers()
        self._initialize_default_profile()
    
    def _initialize_browser_paths(self) -> Dict[BrowserType, Dict[str, Path]]:
        """Initialize known browser paths for different platforms"""
        home = Path.home()
        
        return {
            BrowserType.CHROME: {
                "app": Path("/Applications/Google Chrome.app"),
                "data": home / "Library/Application Support/Google/Chrome",
                "bookmarks": home / "Library/Application Support/Google/Chrome/Default/Bookmarks",
                "history": home / "Library/Application Support/Google/Chrome/Default/History",
                "cookies": home / "Library/Application Support/Google/Chrome/Default/Cookies",
            },
            BrowserType.SAFARI: {
                "app": Path("/Applications/Safari.app"),
                "data": home / "Library/Safari",
                "bookmarks": home / "Library/Safari/Bookmarks.plist",
                "history": home / "Library/Safari/History.db",
            },
            BrowserType.FIREFOX: {
                "app": Path("/Applications/Firefox.app"),
                "data": home / "Library/Application Support/Firefox/Profiles",
                "bookmarks": None,  # Dynamic based on profile
                "history": None,  # Dynamic based on profile
            },
            BrowserType.BRAVE: {
                "app": Path("/Applications/Brave Browser.app"),
                "data": home / "Library/Application Support/BraveSoftware/Brave-Browser",
                "bookmarks": home / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks",
                "history": home / "Library/Application Support/BraveSoftware/Brave-Browser/Default/History",
            },
            BrowserType.EDGE: {
                "app": Path("/Applications/Microsoft Edge.app"),
                "data": home / "Library/Application Support/Microsoft Edge",
                "bookmarks": home / "Library/Application Support/Microsoft Edge/Default/Bookmarks",
                "history": home / "Library/Application Support/Microsoft Edge/Default/History",
            },
            BrowserType.OPERA: {
                "app": Path("/Applications/Opera.app"),
                "data": home / "Library/Application Support/com.operasoftware.Opera",
                "bookmarks": home / "Library/Application Support/com.operasoftware.Opera/Bookmarks",
                "history": home / "Library/Application Support/com.operasoftware.Opera/History",
            },
            BrowserType.ARC: {
                "app": Path("/Applications/Arc.app"),
                "data": home / "Library/Application Support/Arc",
                "bookmarks": None,
            },
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.default_profile = config.get('default_profile')
                    logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                'default_profile': self.default_profile,
                'profiles': {
                    name: {
                        'browser_type': profile.browser_type.value,
                        'default_search': profile.default_search.value
                    }
                    for name, profile in self.profiles.items()
                }
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _discover_browsers(self):
        """Discover installed browsers on the system"""
        for browser_type, paths in self.browser_paths.items():
            app_path = paths.get('app')
            if app_path and app_path.exists():
                profile = BrowserProfile(
                    name=browser_type.value,
                    browser_type=browser_type,
                    path=app_path,
                    data_dir=paths.get('data'),
                    bookmarks_file=paths.get('bookmarks'),
                    history_file=paths.get('history'),
                    cookies_file=paths.get('cookies')
                )
                self.profiles[browser_type.value] = profile
                logger.info(f"Discovered browser: {browser_type.value}")
    
    def _initialize_default_profile(self):
        """Initialize default browser profile"""
        if not self.default_profile and self.profiles:
            # Prefer Chrome, then Safari, then first available
            preferred = ['chrome', 'safari', 'firefox']
            for name in preferred:
                if name in self.profiles:
                    self.default_profile = name
                    break
            if not self.default_profile:
                self.default_profile = list(self.profiles.keys())[0]
    
    def _get_browser_app_path(self, browser: str) -> Optional[Path]:
        """Get the application path for a browser"""
        if browser in self.profiles:
            return self.profiles[browser].path
        return None
    
    def _execute_browser_command(self, command: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute a browser command with error handling"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            raise BrowserError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise BrowserError(f"Failed to execute command: {e}")
    
    def _generate_tab_id(self) -> str:
        """Generate a unique tab ID"""
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:12]
    
    def search_web(self, query: str, browser: Optional[str] = None, 
                  search_engine: Union[str, SearchEngine] = SearchEngine.GOOGLE,
                  privacy_mode: PrivacyMode = PrivacyMode.NORMAL,
                  new_tab: bool = True) -> Dict[str, Any]:
        """
        Search the web with advanced options
        
        Args:
            query: Search query
            browser: Browser to use (None for default)
            search_engine: Search engine to use
            privacy_mode: Privacy mode (normal/incognito/private)
            new_tab: Open in new tab vs new window
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "message": "",
            "url": None,
            "browser_used": None,
            "tab_id": None
        }
        
        try:
            # Validate and get browser
            browser = browser or self.default_profile
            if browser not in self.profiles:
                # Try to find by partial match
                matches = [b for b in self.profiles.keys() if browser in b]
                if matches:
                    browser = matches[0]
                else:
                    raise BrowserError(f"Browser '{browser}' not found")
            
            profile = self.profiles[browser]
            
            # Get search engine URL
            if isinstance(search_engine, str):
                search_engine = SearchEngine(search_engine.lower())
            
            search_url_template = self.search_engines.get(search_engine, self.search_engines[SearchEngine.GOOGLE])
            search_url = search_url_template.format(urllib.parse.quote(query))
            result["url"] = search_url
            
            # Build open command based on privacy mode
            cmd = ['open']
            
            if privacy_mode != PrivacyMode.NORMAL:
                # Handle incognito/private modes
                if profile.browser_type == BrowserType.CHROME:
                    if privacy_mode == PrivacyMode.INCOGNITO:
                        cmd.extend(['-n', '-a', profile.path, '--args', '--incognito'])
                elif profile.browser_type == BrowserType.FIREFOX:
                    if privacy_mode == PrivacyMode.PRIVATE:
                        cmd.extend(['-n', '-a', profile.path, '--args', '--private-window'])
                elif profile.browser_type == BrowserType.SAFARI:
                    if privacy_mode == PrivacyMode.PRIVATE:
                        # Safari private mode via AppleScript
                        script = f'''
                            tell application "Safari"
                                make new document with properties {{URL:"{search_url}"}}
                                set private browsing of first document to true
                            end tell
                        '''
                        subprocess.run(['osascript', '-e', script])
                        result["success"] = True
                        result["message"] = f"Searching for '{query}' in {browser} (private mode)"
                        result["browser_used"] = browser
                        return result
            
            # Add URL to command
            if not new_tab:
                cmd.append(search_url)
            else:
                cmd.extend([search_url])
            
            # Execute command
            if profile.path:
                cmd = ['open', '-a', str(profile.path), search_url]
            else:
                # Fallback to webbrowser module
                webbrowser.open(search_url)
                result["success"] = True
                result["message"] = f"Searching for '{query}' in default browser"
                result["browser_used"] = "default"
                return result
            
            process_result = self._execute_browser_command(cmd)
            
            if process_result.returncode == 0:
                result["success"] = True
                result["message"] = f"Searching for '{query}' in {browser}"
                result["browser_used"] = browser
                
                # Track this search in history
                self._add_to_history(browser, search_url, f"Search: {query}")
            else:
                # Fallback to webbrowser
                webbrowser.open(search_url)
                result["success"] = True
                result["message"] = f"Searching for '{query}' in default browser (fallback)"
                result["browser_used"] = "default"
        
        except BrowserError as e:
            result["message"] = str(e)
            logger.error(f"Browser error: {e}")
            
            # Ultimate fallback
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(search_url)
            result["success"] = True
            result["message"] = f"Searching for '{query}' in default browser (emergency fallback)"
            result["browser_used"] = "default"
        
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            logger.exception("Unexpected error in search_web")
        
        return result
    
    def open_website(self, url: str, browser: Optional[str] = None,
                    privacy_mode: PrivacyMode = PrivacyMode.NORMAL,
                    new_tab: bool = True,
                    wait_for_load: bool = False) -> Dict[str, Any]:
        """
        Open a website with advanced options
        
        Args:
            url: Website URL or shortcut
            browser: Browser to use
            privacy_mode: Privacy mode
            new_tab: Open in new tab
            wait_for_load: Wait for page to load
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "message": "",
            "url": None,
            "browser_used": None,
            "title": None
        }
        
        try:
            # Handle shortcuts
            if url.lower() in self.website_shortcuts:
                url = self.website_shortcuts[url.lower()]
                result["message"] = f"Resolved shortcut to {url}"
            
            # Ensure proper URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            result["url"] = url
            
            # Validate browser
            browser = browser or self.default_profile
            if browser not in self.profiles:
                # Try partial match
                matches = [b for b in self.profiles.keys() if browser in b]
                if matches:
                    browser = matches[0]
                else:
                    raise BrowserError(f"Browser '{browser}' not found")
            
            profile = self.profiles[browser]
            
            # Open website
            if profile.path:
                cmd = ['open', '-a', str(profile.path), url]
                
                # Handle privacy modes
                if privacy_mode == PrivacyMode.INCOGNITO and profile.browser_type == BrowserType.CHROME:
                    cmd = ['open', '-n', '-a', str(profile.path), '--args', '--incognito', url]
                elif privacy_mode == PrivacyMode.PRIVATE and profile.browser_type == BrowserType.FIREFOX:
                    cmd = ['open', '-n', '-a', str(profile.path), '--args', '--private-window', url]
                
                process_result = self._execute_browser_command(cmd)
                
                if process_result.returncode == 0:
                    result["success"] = True
                    result["message"] = f"Opening {url} in {browser}"
                    result["browser_used"] = browser
                    
                    # Get page title if requested
                    if wait_for_load:
                        time.sleep(2)  # Wait for page to load
                        title = self._get_page_title(url)
                        result["title"] = title
                    
                    # Add to history
                    self._add_to_history(browser, url)
                else:
                    # Fallback
                    webbrowser.open(url)
                    result["success"] = True
                    result["message"] = f"Opening {url} in default browser (fallback)"
                    result["browser_used"] = "default"
            else:
                webbrowser.open(url)
                result["success"] = True
                result["message"] = f"Opening {url} in default browser"
                result["browser_used"] = "default"
        
        except Exception as e:
            result["message"] = f"Error opening website: {e}"
            logger.exception("Error in open_website")
        
        return result
    
    def _get_page_title(self, url: str) -> Optional[str]:
        """Get page title from URL"""
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.title.string if soup.title else None
        except:
            return None
    
    def _add_to_history(self, browser: str, url: str, title: Optional[str] = None):
        """Add entry to browser history"""
        if browser not in self.history:
            self.history[browser] = []
        
        entry = HistoryEntry(
            id=self._generate_tab_id(),
            url=url,
            title=title or url,
            visit_time=datetime.now(),
            browser=browser
        )
        
        self.history[browser].append(entry)
        
        # Keep only last 1000 entries
        if len(self.history[browser]) > 1000:
            self.history[browser] = self.history[browser][-1000:]
    
    def open_multiple_websites(self, urls: List[str], browser: Optional[str] = None,
                              new_window: bool = False) -> Dict[str, Any]:
        """
        Open multiple websites at once
        
        Args:
            urls: List of URLs or shortcuts
            browser: Browser to use
            new_window: Open in new window vs tabs
            
        Returns:
            Dictionary with operation results
        """
        result = {
            "success": False,
            "message": "",
            "results": []
        }
        
        try:
            browser = browser or self.default_profile
            
            if new_window:
                # Open first URL in new window, rest in tabs
                for i, url in enumerate(urls):
                    tab_result = self.open_website(
                        url, 
                        browser=browser,
                        new_tab=(i > 0)
                    )
                    result["results"].append(tab_result)
            else:
                # Open all in new tabs of existing window
                for url in urls:
                    tab_result = self.open_website(
                        url,
                        browser=browser,
                        new_tab=True
                    )
                    result["results"].append(tab_result)
            
            result["success"] = True
            result["message"] = f"Opened {len(urls)} websites"
        
        except Exception as e:
            result["message"] = f"Error opening multiple websites: {e}"
        
        return result
    
    def close_tab(self, browser: Optional[str] = None, tab_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Close a browser tab
        
        Args:
            browser: Browser to target
            tab_index: Tab index to close (None for current)
            
        Returns:
            Dictionary with operation result
        """
        result = {"success": False, "message": ""}
        
        try:
            browser = browser or self.default_profile
            
            if browser == "safari":
                # Safari tab closing via AppleScript
                if tab_index is not None:
                    script = f'''
                        tell application "Safari"
                            close tab {tab_index} of window 1
                        end tell
                    '''
                else:
                    script = '''
                        tell application "Safari"
                            close current tab of window 1
                        end tell
                    '''
                
                subprocess.run(['osascript', '-e', script])
                result["success"] = True
                result["message"] = "Tab closed"
            
            elif browser in ["chrome", "brave", "edge"]:
                # Chrome-based browsers - use AppleScript
                app_name = self.profiles[browser].path.stem
                if tab_index is not None:
                    script = f'''
                        tell application "{app_name}"
                            close tab {tab_index} of window 1
                        end tell
                    '''
                else:
                    script = f'''
                        tell application "{app_name}"
                            close active tab of window 1
                        end tell
                    '''
                
                subprocess.run(['osascript', '-e', script])
                result["success"] = True
                result["message"] = "Tab closed"
            
            else:
                result["message"] = f"Tab closing not supported for {browser}"
        
        except Exception as e:
            result["message"] = f"Error closing tab: {e}"
        
        return result
    
    def get_open_tabs(self, browser: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of open tabs in browser
        
        Args:
            browser: Browser to query
            
        Returns:
            List of tab information
        """
        tabs = []
        
        try:
            browser = browser or self.default_profile
            
            if browser == "safari":
                script = '''
                    tell application "Safari"
                        set tabList to {}
                        set windowCount to number of windows
                        repeat with w from 1 to windowCount
                            set tabCount to number of tabs in window w
                            repeat with t from 1 to tabCount
                                set tabURL to URL of tab t of window w
                                set tabName to name of tab t of window w
                                set end of tabList to {tabURL, tabName, w, t}
                            end repeat
                        end repeat
                        return tabList
                    end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    # Parse AppleScript list output
                    lines = result.stdout.strip().split(', ')
                    for i in range(0, len(lines), 4):
                        if i + 3 < len(lines):
                            tabs.append({
                                "url": lines[i],
                                "title": lines[i+1],
                                "window": int(lines[i+2]),
                                "index": int(lines[i+3])
                            })
            
            elif browser in ["chrome", "brave", "edge"]:
                app_name = self.profiles[browser].path.stem
                script = f'''
                    tell application "{app_name}"
                        set tabList to {{}}
                        repeat with w in windows
                            repeat with t in tabs of w
                                set end of tabList to {{URL:t, title:title of t}}
                            end repeat
                        end repeat
                        return tabList
                    end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True
                )
                
                # Parse would be more complex for Chrome
                # For now, return empty list
                pass
        
        except Exception as e:
            logger.error(f"Error getting open tabs: {e}")
        
        return tabs
    
    def get_bookmarks(self, browser: Optional[str] = None, folder: Optional[str] = None) -> List[Bookmark]:
        """
        Get bookmarks from browser
        
        Args:
            browser: Browser to query
            folder: Specific folder to get bookmarks from
            
        Returns:
            List of bookmarks
        """
        bookmarks = []
        
        try:
            browser = browser or self.default_profile
            profile = self.profiles.get(browser)
            
            if not profile or not profile.bookmarks_file:
                return bookmarks
            
            if profile.browser_type == BrowserType.CHROME:
                # Chrome bookmarks are JSON
                with open(profile.bookmarks_file, 'r') as f:
                    data = json.load(f)
                
                def extract_bookmarks(node, current_folder="Other"):
                    if node.get('type') == 'folder':
                        folder_name = node.get('name', current_folder)
                        for child in node.get('children', []):
                            extract_bookmarks(child, folder_name)
                    elif node.get('type') == 'url':
                        bookmarks.append(Bookmark(
                            id=node.get('id', self._generate_tab_id()),
                            title=node.get('name', ''),
                            url=node.get('url', ''),
                            folder=current_folder,
                            created=datetime.fromtimestamp(node.get('date_added', 0) / 1000000 - 11644473600)
                        ))
                
                roots = data.get('roots', {})
                for root_name, root_node in roots.items():
                    extract_bookmarks(root_node, root_name)
            
            elif profile.browser_type == BrowserType.SAFARI:
                # Safari bookmarks are plist
                with open(profile.bookmarks_file, 'rb') as f:
                    plist_data = plistlib.load(f)
                
                def extract_safari_bookmarks(node, current_folder="Other"):
                    if node.get('Title') and node.get('URLString'):
                        bookmarks.append(Bookmark(
                            id=self._generate_tab_id(),
                            title=node.get('Title', ''),
                            url=node.get('URLString', ''),
                            folder=current_folder
                        ))
                    elif node.get('Children'):
                        folder_name = node.get('Title', current_folder)
                        for child in node.get('Children', []):
                            extract_safari_bookmarks(child, folder_name)
                
                extract_safari_bookmarks(plist_data)
            
            # Filter by folder if specified
            if folder:
                bookmarks = [b for b in bookmarks if b.folder.lower() == folder.lower()]
        
        except Exception as e:
            logger.error(f"Error getting bookmarks: {e}")
        
        return bookmarks
    
    def add_bookmark(self, url: str, title: str, folder: str = "Other",
                    browser: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a bookmark
        
        Args:
            url: Bookmark URL
            title: Bookmark title
            folder: Folder to save bookmark in
            browser: Target browser
            
        Returns:
            Dictionary with operation result
        """
        result = {"success": False, "message": ""}
        
        try:
            browser = browser or self.default_profile
            
            if browser == "safari":
                script = f'''
                    tell application "Safari"
                        make new bookmark item at end of bookmarks bar with properties {{URL:"{url}", name:"{title}"}}
                    end tell
                '''
                subprocess.run(['osascript', '-e', script])
                result["success"] = True
                result["message"] = f"Bookmark added to Safari"
            
            elif browser in ["chrome", "brave", "edge"]:
                app_name = self.profiles[browser].path.stem
                script = f'''
                    tell application "{app_name}"
                        make new bookmark at end of bookmarks bar with properties {{URL:"{url}", title:"{title}"}}
                    end tell
                '''
                subprocess.run(['osascript', '-e', script])
                result["success"] = True
                result["message"] = f"Bookmark added to {app_name}"
            
            else:
                result["message"] = f"Bookmarking not supported for {browser}"
        
        except Exception as e:
            result["message"] = f"Error adding bookmark: {e}"
        
        return result
    
    def get_browser_info(self, browser: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a browser
        
        Args:
            browser: Browser name (None for default)
            
        Returns:
            Dictionary with browser information
        """
        browser = browser or self.default_profile
        profile = self.profiles.get(browser)
        
        if not profile:
            return {"error": f"Browser '{browser}' not found"}
        
        # Get running status
        is_running = self.is_browser_running(browser)
        
        # Get tab count
        tabs = self.get_open_tabs(browser)
        
        # Get bookmarks count
        bookmarks = self.get_bookmarks(browser)
        
        return {
            "name": profile.name,
            "type": profile.browser_type.value,
            "path": str(profile.path) if profile.path else None,
            "is_installed": profile.path is not None and profile.path.exists(),
            "is_running": is_running,
            "data_directory": str(profile.data_dir) if profile.data_dir else None,
            "tab_count": len(tabs),
            "bookmarks_count": len(bookmarks),
            "default_search": profile.default_search.value,
            "supports_incognito": profile.incognito_supported,
            "extensions_count": len(profile.extensions),
            "last_used": profile.last_used.isoformat() if profile.last_used else None
        }
    
    def is_browser_running(self, browser: Optional[str] = None) -> bool:
        """Check if a browser is currently running"""
        browser = browser or self.default_profile
        profile = self.profiles.get(browser)
        
        if not profile or not profile.path:
            return False
        
        try:
            result = subprocess.run(
                ['pgrep', '-f', profile.path.stem],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def clear_browser_data(self, browser: Optional[str] = None,
                          data_types: List[str] = None) -> Dict[str, Any]:
        """
        Clear browser data (history, cache, cookies, etc.)
        
        Args:
            browser: Target browser
            data_types: List of data types to clear ['history', 'cache', 'cookies', 'passwords']
            
        Returns:
            Dictionary with operation result
        """
        result = {"success": False, "message": ""}
        
        try:
            browser = browser or self.default_profile
            data_types = data_types or ['history', 'cache', 'cookies']
            
            if browser == "safari":
                commands = []
                if 'history' in data_types:
                    commands.append('tell application "Safari" to close every document')
                if 'cache' in data_types:
                    commands.append('do shell script "rm -rf ~/Library/Caches/com.apple.Safari/*"')
                if 'cookies' in data_types:
                    commands.append('do shell script "rm -rf ~/Library/Cookies/Cookies.binarycookies"')
                
                if commands:
                    script = '\n'.join(commands)
                    subprocess.run(['osascript', '-e', script])
                    result["success"] = True
                    result["message"] = f"Cleared {', '.join(data_types)} from Safari"
            
            elif browser in ["chrome", "brave", "edge"]:
                app_name = self.profiles[browser].path.stem
                script = f'''
                    tell application "{app_name}"
                        activate
                    end tell
                    delay 1
                    tell application "System Events"
                        keystroke "," using {{command down}}
                        delay 1
                        -- This would need more complex automation
                    end tell
                '''
                # This is simplified - actual Chrome data clearing requires more complex automation
                result["message"] = "Manual clearing required for Chrome-based browsers"
            
            else:
                result["message"] = f"Data clearing not supported for {browser}"
        
        except Exception as e:
            result["message"] = f"Error clearing browser data: {e}"
        
        return result
    
    def take_screenshot(self, browser: Optional[str] = None,
                       full_page: bool = False) -> Dict[str, Any]:
        """
        Take a screenshot of the current browser tab
        
        Args:
            browser: Target browser
            full_page: Capture full page (scroll) vs visible area
            
        Returns:
            Dictionary with screenshot path
        """
        result = {"success": False, "message": "", "screenshot_path": None}
        
        try:
            browser = browser or self.default_profile
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = Path.home() / "Desktop" / f"screenshot_{timestamp}.png"
            
            if full_page:
                # Use AppleScript to capture full page
                if browser == "safari":
                    script = f'''
                        tell application "Safari"
                            set doc to document 1
                            set bounds of window 1 to {{0, 0, 1280, 800}}
                            delay 1
                        end tell
                        do shell script "screencapture -T0 -x " + quote + "{screenshot_path}" + quote
                    '''
                    subprocess.run(['osascript', '-e', script])
            else:
                # Regular screenshot
                subprocess.run(['screencapture', '-x', str(screenshot_path)])
            
            if screenshot_path.exists():
                result["success"] = True
                result["message"] = f"Screenshot saved to {screenshot_path}"
                result["screenshot_path"] = str(screenshot_path)
            else:
                result["message"] = "Failed to capture screenshot"
        
        except Exception as e:
            result["message"] = f"Error taking screenshot: {e}"
        
        return result
    
    def get_browsing_history(self, browser: Optional[str] = None,
                            days: int = 7, limit: int = 100) -> List[Dict]:
        """
        Get browsing history
        
        Args:
            browser: Target browser
            days: Number of days of history to retrieve
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        history_entries = []
        
        try:
            browser = browser or self.default_profile
            profile = self.profiles.get(browser)
            
            if not profile:
                return history_entries
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Try to get from internal history first
            if browser in self.history:
                entries = self.history[browser]
                for entry in entries:
                    if entry.visit_time >= cutoff_date:
                        history_entries.append({
                            "url": entry.url,
                            "title": entry.title,
                            "visit_time": entry.visit_time.isoformat(),
                            "browser": entry.browser
                        })
            
            # If no internal history, try to read from browser's history file
            if not history_entries and profile.history_file and profile.history_file.exists():
                if profile.browser_type == BrowserType.CHROME:
                    # Chrome uses SQLite
                    conn = sqlite3.connect(f"file:{profile.history_file}?mode=ro", uri=True)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT url, title, last_visit_time 
                        FROM urls 
                        WHERE last_visit_time > ?
                        ORDER BY last_visit_time DESC
                        LIMIT ?
                    ''', (int(cutoff_date.timestamp() * 1000000), limit))
                    
                    for row in cursor.fetchall():
                        history_entries.append({
                            "url": row[0],
                            "title": row[1] or row[0],
                            "visit_time": datetime.fromtimestamp(row[2] / 1000000 - 11644473600).isoformat(),
                            "browser": browser
                        })
                    conn.close()
            
            # Sort by visit time (newest first) and limit
            history_entries.sort(key=lambda x: x['visit_time'], reverse=True)
            history_entries = history_entries[:limit]
        
        except Exception as e:
            logger.error(f"Error getting browsing history: {e}")
        
        return history_entries
    
    def search_history(self, query: str, browser: Optional[str] = None) -> List[Dict]:
        """Search browsing history"""
        all_history = self.get_browsing_history(browser, days=365, limit=1000)
        
        results = []
        query_lower = query.lower()
        
        for entry in all_history:
            if (query_lower in entry['url'].lower() or 
                (entry['title'] and query_lower in entry['title'].lower())):
                results.append(entry)
        
        return results
    
    def download_file(self, url: str, download_dir: Optional[Path] = None,
                     browser: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a file using browser
        
        Args:
            url: File URL
            download_dir: Download directory
            browser: Target browser
            
        Returns:
            Dictionary with download result
        """
        result = {"success": False, "message": "", "file_path": None}
        
        try:
            browser = browser or self.default_profile
            download_dir = download_dir or Path.home() / "Downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Open URL in browser which will trigger download
            self.open_website(url, browser=browser)
            
            # Monitor downloads folder for new file
            max_wait = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Get most recent file in downloads
                files = list(download_dir.glob("*"))
                if files:
                    latest_file = max(files, key=lambda p: p.stat().st_mtime)
                    # Check if file was created in the last few seconds
                    if time.time() - latest_file.stat().st_mtime < 5:
                        result["success"] = True
                        result["message"] = f"Download started: {latest_file.name}"
                        result["file_path"] = str(latest_file)
                        break
                time.sleep(1)
            
            if not result["success"]:
                result["message"] = "Download may have started, but couldn't confirm"
        
        except Exception as e:
            result["message"] = f"Error downloading file: {e}"
        
        return result
    
    def get_downloads(self, browser: Optional[str] = None) -> List[Dict]:
        """Get recent downloads"""
        try:
            browser = browser or self.default_profile
            profile = self.profiles.get(browser)
            
            if not profile:
                return []
            
            # Try to get from browser's history
            if profile.browser_type == BrowserType.CHROME:
                # Chrome stores downloads in History file
                if profile.history_file and profile.history_file.exists():
                    conn = sqlite3.connect(f"file:{profile.history_file}?mode=ro", uri=True)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT target_path, start_time, received_bytes, total_bytes 
                        FROM downloads 
                        ORDER BY start_time DESC 
                        LIMIT 50
                    ''')
                    
                    downloads = []
                    for row in cursor.fetchall():
                        downloads.append({
                            "path": row[0],
                            "start_time": datetime.fromtimestamp(row[1] / 1000000 - 11644473600).isoformat(),
                            "progress": f"{row[2]}/{row[3]}" if row[3] > 0 else "Unknown",
                            "complete": row[2] == row[3] if row[3] > 0 else False
                        })
                    conn.close()
                    return downloads
        
        except Exception as e:
            logger.error(f"Error getting downloads: {e}")
        
        return []
    
    def set_default_browser(self, browser: str) -> Dict[str, Any]:
        """
        Set default browser
        
        Args:
            browser: Browser name
            
        Returns:
            Dictionary with operation result
        """
        result = {"success": False, "message": ""}
        
        try:
            if browser not in self.profiles:
                raise BrowserError(f"Browser '{browser}' not found")
            
            profile = self.profiles[browser]
            
            # On macOS, default browser is set via system preferences
            # This is a simplified version
            script = f'''
                tell application "System Preferences"
                    activate
                    set current pane to pane "com.apple.preference.general"
                end tell
                delay 1
                tell application "System Events"
                    tell process "System Preferences"
                        click pop up button "Default web browser:" of window 1
                        click menu item "{profile.path.stem}" of menu 1 of pop up button 1
                    end tell
                end tell
            '''
            
            subprocess.run(['osascript', '-e', script])
            
            self.default_profile = browser
            self._save_config()
            
            result["success"] = True
            result["message"] = f"Default browser set to {browser}"
        
        except Exception as e:
            result["message"] = f"Error setting default browser: {e}"
        
        return result
    
    def create_profile(self, name: str, browser_type: Union[str, BrowserType],
                      data_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Create a new browser profile
        
        Args:
            name: Profile name
            browser_type: Browser type
            data_dir: Custom data directory
            
        Returns:
            Dictionary with operation result
        """
        result = {"success": False, "message": ""}
        
        try:
            if isinstance(browser_type, str):
                browser_type = BrowserType(browser_type.lower())
            
            # Check if browser is installed
            browser_paths = self.browser_paths.get(browser_type)
            if not browser_paths or not browser_paths.get('app', Path()).exists():
                raise BrowserError(f"{browser_type.value} is not installed")
            
            # Create profile
            profile = BrowserProfile(
                name=name,
                browser_type=browser_type,
                path=browser_paths['app'],
                data_dir=data_dir or browser_paths.get('data')
            )
            
            self.profiles[name] = profile
            
            if not self.default_profile:
                self.default_profile = name
            
            self._save_config()
            
            result["success"] = True
            result["message"] = f"Profile '{name}' created"
        
        except Exception as e:
            result["message"] = f"Error creating profile: {e}"
        
        return result


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import pprint
    
    manager = BrowserManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "search" and len(sys.argv) > 2:
            query = sys.argv[2]
            browser = sys.argv[3] if len(sys.argv) > 3 else None
            result = manager.search_web(query, browser)
            pprint.pprint(result)
        
        elif command == "open" and len(sys.argv) > 2:
            url = sys.argv[2]
            browser = sys.argv[3] if len(sys.argv) > 3 else None
            result = manager.open_website(url, browser)
            pprint.pprint(result)
        
        elif command == "info":
            browser = sys.argv[2] if len(sys.argv) > 2 else None
            info = manager.get_browser_info(browser)
            pprint.pprint(info)
        
        elif command == "bookmarks":
            browser = sys.argv[2] if len(sys.argv) > 2 else None
            bookmarks = manager.get_bookmarks(browser)
            for b in bookmarks[:10]:  # Show first 10
                print(f"{b.title}: {b.url}")
        
        elif command == "history":
            browser = sys.argv[2] if len(sys.argv) > 2 else None
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
            history = manager.get_browsing_history(browser, days=days)
            for h in history[:10]:
                print(f"{h['visit_time']}: {h['title']}")
        
        elif command == "tabs":
            browser = sys.argv[2] if len(sys.argv) > 2 else None
            tabs = manager.get_open_tabs(browser)
            pprint.pprint(tabs)
        
        elif command == "screenshot":
            browser = sys.argv[2] if len(sys.argv) > 2 else None
            result = manager.take_screenshot(browser)
            print(result['message'])
        
        else:
            print("Usage: browser_manager.py [search|open|info|bookmarks|history|tabs|screenshot] [args]")
    else:
        # Demo mode
        print("Browser Manager Demo")
        print("-" * 50)
        
        # List available browsers
        print("\nAvailable browsers:")
        for browser in manager.profiles.keys():
            info = manager.get_browser_info(browser)
            print(f"  - {browser}: {'Running' if info['is_running'] else 'Not running'}")
        
        # Search example
        print("\nSearching...")
        result = manager.search_web("Python programming", browser="chrome")
        print(result['message'])
        
        # Open website
        print("\nOpening website...")
        result = manager.open_website("github.com", browser="safari")
        print(result['message'])
        
        # Get browser info
        print("\nBrowser info:")
        info = manager.get_browser_info("chrome")
        pprint.pprint(info)