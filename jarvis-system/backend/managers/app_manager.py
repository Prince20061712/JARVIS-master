"""
Enhanced Application Manager for macOS
Handles application operations with robust error handling, caching, and advanced features
"""

import os
import subprocess
import webbrowser
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
from datetime import datetime, timedelta
import plistlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppCategory(Enum):
    """Application categories for better organization"""
    PRODUCTIVITY = "productivity"
    DEVELOPMENT = "development"
    BROWSER = "browser"
    MEDIA = "media"
    COMMUNICATION = "communication"
    UTILITY = "utility"
    CREATIVE = "creative"
    GAMES = "games"
    OTHER = "other"


class AppStatus(Enum):
    """Application status states"""
    RUNNING = "running"
    NOT_RUNNING = "not_running"
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    ERROR = "error"


@dataclass
class ApplicationInfo:
    """Data class for application information"""
    name: str
    display_name: str
    bundle_id: Optional[str] = None
    path: Optional[Path] = None
    category: AppCategory = AppCategory.OTHER
    web_fallback: Optional[str] = None
    keywords: List[str] = None
    icon: Optional[str] = None
    version: Optional[str] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class AppLaunchError(Exception):
    """Custom exception for application launch errors"""
    pass


class ApplicationManager:
    """
    Enhanced Application Manager for macOS with advanced features:
    - Application caching and auto-discovery
    - Usage tracking and analytics
    - Batch operations
    - Process management
    - Installation handling
    - Fallback strategies
    """
    
    def __init__(self, cache_enabled: bool = True, cache_duration: int = 3600):
        """
        Initialize the Application Manager
        
        Args:
            cache_enabled: Whether to cache application info
            cache_duration: Cache duration in seconds
        """
        self.cache_enabled = cache_enabled
        self.cache_duration = cache_duration
        self._app_cache: Dict[str, ApplicationInfo] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._running_processes: Dict[str, List[psutil.Process]] = {}
        
        # Common macOS application paths
        self.app_paths = [
            Path("/Applications"),
            Path("/System/Applications"),
            Path("/System/Applications/Utilities"),
            Path.home() / "Applications",
        ]
        
        # Initialize with predefined applications
        self._initialize_predefined_apps()
        
        # Auto-discover installed applications
        if cache_enabled:
            self.refresh_cache()
    
    def _initialize_predefined_apps(self):
        """Initialize predefined application database"""
        predefined_apps = [
            # Productivity
            ApplicationInfo("notes", "Notes", category=AppCategory.PRODUCTIVITY, keywords=["note", "writing"]),
            ApplicationInfo("textedit", "TextEdit", category=AppCategory.PRODUCTIVITY, keywords=["editor", "text"]),
            ApplicationInfo("calculator", "Calculator", category=AppCategory.PRODUCTIVITY),
            ApplicationInfo("calendar", "Calendar", category=AppCategory.PRODUCTIVITY),
            ApplicationInfo("reminders", "Reminders", category=AppCategory.PRODUCTIVITY),
            ApplicationInfo("stickies", "Stickies", category=AppCategory.PRODUCTIVITY),
            
            # Development
            ApplicationInfo("vscode", "Visual Studio Code", category=AppCategory.DEVELOPMENT, 
                          keywords=["code", "editor", "vs"], bundle_id="com.microsoft.VSCode"),
            ApplicationInfo("code", "Visual Studio Code", category=AppCategory.DEVELOPMENT),
            ApplicationInfo("terminal", "Terminal", category=AppCategory.DEVELOPMENT, 
                          bundle_id="com.apple.Terminal"),
            ApplicationInfo("iterm", "iTerm", category=AppCategory.DEVELOPMENT, 
                          bundle_id="com.googlecode.iterm2"),
            ApplicationInfo("xcode", "Xcode", category=AppCategory.DEVELOPMENT,
                          bundle_id="com.apple.dt.Xcode"),
            ApplicationInfo("pycharm", "PyCharm", category=AppCategory.DEVELOPMENT),
            
            # Browsers
            ApplicationInfo("safari", "Safari", category=AppCategory.BROWSER,
                          bundle_id="com.apple.Safari"),
            ApplicationInfo("chrome", "Google Chrome", category=AppCategory.BROWSER,
                          bundle_id="com.google.Chrome", web_fallback="https://www.google.com"),
            ApplicationInfo("firefox", "Firefox", category=AppCategory.BROWSER,
                          bundle_id="org.mozilla.firefox"),
            
            # Media & Camera
            ApplicationInfo("camera", "Photo Booth", category=AppCategory.MEDIA,
                          bundle_id="com.apple.PhotoBooth"),
            ApplicationInfo("photos", "Photos", category=AppCategory.MEDIA,
                          bundle_id="com.apple.Photos"),
            ApplicationInfo("quicktime", "QuickTime Player", category=AppCategory.MEDIA),
            
            # Communication
            ApplicationInfo("messages", "Messages", category=AppCategory.COMMUNICATION,
                          bundle_id="com.apple.iChat"),
            ApplicationInfo("whatsapp", "WhatsApp", category=AppCategory.COMMUNICATION,
                          web_fallback="https://web.whatsapp.com"),
            ApplicationInfo("slack", "Slack", category=AppCategory.COMMUNICATION,
                          web_fallback="https://app.slack.com"),
            ApplicationInfo("mail", "Mail", category=AppCategory.COMMUNICATION,
                          bundle_id="com.apple.mail"),
            
            # Utilities
            ApplicationInfo("finder", "Finder", category=AppCategory.UTILITY,
                          bundle_id="com.apple.Finder"),
            ApplicationInfo("activity monitor", "Activity Monitor", category=AppCategory.UTILITY),
            ApplicationInfo("system preferences", "System Preferences", category=AppCategory.UTILITY,
                          bundle_id="com.apple.systempreferences"),
        ]
        
        for app in predefined_apps:
            self._app_cache[app.name] = app
    
    def refresh_cache(self) -> None:
        """Refresh the application cache by scanning system"""
        if not self.cache_enabled:
            return
        
        logger.info("Refreshing application cache...")
        
        # Scan all application paths
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for path in self.app_paths:
                if path.exists():
                    futures.append(executor.submit(self._scan_app_directory, path))
            
            for future in as_completed(futures):
                discovered_apps = future.result()
                for app in discovered_apps:
                    # Update cache, preserving predefined data
                    if app.name in self._app_cache:
                        existing = self._app_cache[app.name]
                        existing.path = app.path or existing.path
                        existing.bundle_id = app.bundle_id or existing.bundle_id
                        existing.version = app.version or existing.version
                    else:
                        self._app_cache[app.name] = app
        
        self._cache_timestamp = datetime.now()
        logger.info(f"Cache refreshed with {len(self._app_cache)} applications")
    
    def _scan_app_directory(self, directory: Path) -> List[ApplicationInfo]:
        """Scan a directory for .app bundles"""
        apps = []
        try:
            for item in directory.glob("*.app"):
                app_info = self._extract_app_info(item)
                if app_info:
                    apps.append(app_info)
        except PermissionError:
            logger.warning(f"Permission denied scanning {directory}")
        except Exception as e:
            logger.error(f"Error scanning {directory}: {e}")
        
        return apps
    
    def _extract_app_info(self, app_path: Path) -> Optional[ApplicationInfo]:
        """Extract information from an .app bundle"""
        try:
            # Get app name
            name = app_path.stem.lower()
            display_name = app_path.stem
            
            # Try to read Info.plist for more details
            info_plist_path = app_path / "Contents" / "Info.plist"
            bundle_id = None
            version = None
            
            if info_plist_path.exists():
                with open(info_plist_path, 'rb') as f:
                    plist_data = plistlib.load(f)
                    bundle_id = plist_data.get('CFBundleIdentifier')
                    version = plist_data.get('CFBundleShortVersionString')
                    display_name = plist_data.get('CFBundleDisplayName', display_name)
            
            return ApplicationInfo(
                name=name,
                display_name=display_name,
                bundle_id=bundle_id,
                path=app_path,
                version=version
            )
        except Exception as e:
            logger.error(f"Error extracting app info from {app_path}: {e}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self._cache_timestamp:
            return False
        return datetime.now() - self._cache_timestamp < timedelta(seconds=self.cache_duration)
    
    def find_application(self, query: str) -> Optional[ApplicationInfo]:
        """
        Find an application by name, keyword, bundle ID, or fuzzy match
        
        Args:
            query: Search query (name, keyword, bundle ID)
            
        Returns:
            ApplicationInfo if found, None otherwise
        """
        import difflib
        query_lower = query.lower()
        
        # Refresh cache if needed
        if not self._is_cache_valid():
            self.refresh_cache()
        
        # Direct match
        if query_lower in self._app_cache:
            return self._app_cache[query_lower]
        
        # Search by display name, keywords, or bundle ID
        for app in self._app_cache.values():
            if (query_lower in app.display_name.lower() or
                any(query_lower in kw.lower() for kw in (app.keywords or [])) or
                (app.bundle_id and query_lower in app.bundle_id.lower())):
                return app
                
        # Fuzzy match
        app_names = list(self._app_cache.keys())
        matches = difflib.get_close_matches(query_lower, app_names, n=1, cutoff=0.6)
        if matches:
            logger.info(f"Fuzzy matched '{query}' to '{matches[0]}'")
            return self._app_cache[matches[0]]
            
        # Fuzzy match display names
        display_names = {app.display_name.lower(): app for app in self._app_cache.values()}
        matches = difflib.get_close_matches(query_lower, list(display_names.keys()), n=1, cutoff=0.6)
        if matches:
            logger.info(f"Fuzzy matched '{query}' to display name '{matches[0]}'")
            return display_names[matches[0]]
        
        return None
    
    def open_application(self, query: str, force_web: bool = False, 
                        wait: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Open an application with multiple fallback strategies
        
        Args:
            query: Application name or query
            force_web: Force using web version
            wait: Wait for app to launch before returning
            
        Returns:
            Dictionary with status and message
        """
        result = {
            "success": False,
            "message": "",
            "app_info": None,
            "method_used": ""
        }
        
        try:
            # Find the application
            app = self.find_application(query)
            
            if not app:
                # Try web fallback for unknown app
                if not force_web:
                    return self._try_web_fallback(query, result)
                else:
                    raise AppLaunchError(f"Application '{query}' not found")
            
            result["app_info"] = app
            
            # Try native app first (unless force_web)
            if not force_web and app.path:
                success, message = self._launch_native_app(app, wait)
                if success:
                    result["success"] = True
                    result["message"] = message
                    result["method_used"] = "native"
                    self._track_usage(app)
                    return result
            
            # Try by bundle ID
            if not force_web and app.bundle_id:
                success, message = self._launch_by_bundle_id(app.bundle_id, wait)
                if success:
                    result["success"] = True
                    result["message"] = message
                    result["method_used"] = "bundle_id"
                    self._track_usage(app)
                    return result
            
            # Try web fallback
            if app.web_fallback or not force_web:
                return self._try_web_fallback(app.web_fallback or query, result, app)
            
            raise AppLaunchError(f"Could not launch {app.display_name}")
            
        except AppLaunchError as e:
            result["message"] = str(e)
            logger.error(f"App launch error: {e}")
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            logger.exception("Unexpected error in open_application")
        
        return result
    
    def _launch_native_app(self, app: ApplicationInfo, wait: bool) -> Tuple[bool, str]:
        """Launch a native macOS application"""
        try:
            cmd = ['open']
            if wait:
                cmd.append('-W')
            cmd.extend(['-a', app.display_name])
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if process.returncode == 0:
                return True, f"{app.display_name} opened successfully"
            else:
                return False, f"Failed to open {app.display_name}: {process.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Launch timeout"
        except Exception as e:
            return False, str(e)
    
    def _launch_by_bundle_id(self, bundle_id: str, wait: bool) -> Tuple[bool, str]:
        """Launch an application by its bundle ID"""
        try:
            cmd = ['open', '-b', bundle_id]
            if wait:
                cmd.append('-W')
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                return True, f"Application with bundle ID {bundle_id} opened"
            return False, f"Failed to open by bundle ID: {process.stderr}"
            
        except Exception as e:
            return False, str(e)
    
    def _try_web_fallback(self, query: str, result: Dict, app: Optional[ApplicationInfo] = None) -> Dict:
        """Try to open web fallback version"""
        import urllib.parse
        
        web_urls = {
            "spotify": "https://open.spotify.com",
            "whatsapp": "https://web.whatsapp.com",
            "discord": "https://discord.com/app",
            "slack": "https://app.slack.com",
            "telegram": "https://web.telegram.org",
            "gmail": "https://mail.google.com",
            "outlook": "https://outlook.office.com",
            "google drive": "https://drive.google.com",
            "docs": "https://docs.google.com",
            "sheets": "https://sheets.google.com",
            "linkedin": "https://www.linkedin.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://twitter.com",
            "x": "https://twitter.com",
            "github": "https://github.com",
            "netflix": "https://www.netflix.com",
            "amazon": "https://www.amazon.com",
            "chatgpt": "https://chat.openai.com",
            "claude": "https://claude.ai",
        }
        
        clean_query = query.lower().strip()
        url = web_urls.get(clean_query)
        
        if not url and app and app.web_fallback:
            url = app.web_fallback
            
        if not url and " " not in clean_query and "." not in clean_query:
            # Guessing for common direct URLs
            url = f"https://www.{clean_query}.com"
        
        if url:
            webbrowser.open(url)
            result["success"] = True
            result["message"] = f"Opened {app.display_name if app else query} in browser"
            result["method_used"] = "web_fallback"
        else:
            # Try generic search
            encoded_query = urllib.parse.quote(query)
            # Use DuckDuckGo 'I'm Feeling Lucky' equivalent (!ducky) to go straight to the site if possible
            search_url = f"https://duckduckgo.com/?q=!ducky+{encoded_query}"
            webbrowser.open(search_url)
            result["success"] = True
            result["message"] = f"Opened {query} via web search"
            result["method_used"] = "web_search"
        
        return result
    
    def _track_usage(self, app: ApplicationInfo):
        """Track application usage"""
        app.last_used = datetime.now()
        app.usage_count += 1
        
        # In a real implementation, you might want to persist this to a database
    
    def close_application(self, query: str, force: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Close an application
        
        Args:
            query: Application name or query
            force: Force quit if normal quit fails
            
        Returns:
            Dictionary with status and message
        """
        result = {"success": False, "message": ""}
        
        try:
            # Find the application
            app = self.find_application(query)
            
            if not app:
                # Try by process name
                return self._close_by_process_name(query, force)
            
            # Try graceful quit first
            if not force:
                success, msg = self._graceful_quit(app)
                if success:
                    result["success"] = True
                    result["message"] = msg
                    return result
            
            # Force quit if needed or requested
            success, msg = self._force_quit(app)
            result["success"] = success
            result["message"] = msg
            
        except Exception as e:
            result["message"] = f"Error closing application: {e}"
            logger.exception("Error in close_application")
        
        return result
    
    def _graceful_quit(self, app: ApplicationInfo) -> Tuple[bool, str]:
        """Gracefully quit an application using AppleScript"""
        try:
            script = f'tell application "{app.display_name}" to quit'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"{app.display_name} quit successfully"
            return False, f"Could not quit {app.display_name} gracefully"
            
        except Exception as e:
            return False, str(e)
    
    def _force_quit(self, app: ApplicationInfo) -> Tuple[bool, str]:
        """Force quit an application"""
        try:
            # Try by bundle ID first
            if app.bundle_id:
                subprocess.run(['pkill', '-f', app.bundle_id], check=False)
            
            # Try by process name
            subprocess.run(['pkill', '-f', app.display_name], check=False)
            
            return True, f"{app.display_name} force quit"
            
        except Exception as e:
            return False, f"Could not force quit: {e}"
    
    def _close_by_process_name(self, process_name: str, force: bool) -> Dict:
        """Close application by process name"""
        try:
            signal = 'SIGTERM' if not force else 'SIGKILL'
            subprocess.run(['pkill', '-f', process_name], check=False)
            return {
                "success": True,
                "message": f"Process '{process_name}' terminated"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not terminate process: {e}"
            }
    
    def get_running_applications(self) -> List[Dict]:
        """Get list of running applications"""
        running_apps = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pinfo = proc.info
                running_apps.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_percent": proc.memory_percent()
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(running_apps, key=lambda x: x['cpu_percent'], reverse=True)
    
    def is_running(self, query: str) -> bool:
        """Check if an application is running"""
        app = self.find_application(query)
        if not app:
            return False
        
        # Check by process name
        for proc in psutil.process_iter(['name']):
            try:
                if app.display_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return False
    
    def get_application_info(self, query: str) -> Optional[Dict]:
        """Get detailed information about an application"""
        app = self.find_application(query)
        if not app:
            return None
        
        return {
            "name": app.name,
            "display_name": app.display_name,
            "bundle_id": app.bundle_id,
            "path": str(app.path) if app.path else None,
            "category": app.category.value,
            "is_installed": app.path is not None,
            "is_running": self.is_running(query),
            "version": app.version,
            "last_used": app.last_used.isoformat() if app.last_used else None,
            "usage_count": app.usage_count,
            "keywords": app.keywords,
            "has_web_fallback": app.web_fallback is not None
        }
    
    def list_applications(self, category: Optional[AppCategory] = None) -> List[str]:
        """
        List all available applications, optionally filtered by category
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of application names
        """
        if category:
            return [app.name for app in self._app_cache.values() 
                   if app.category == category]
        
        return list(self._app_cache.keys())
    
    def search_applications(self, query: str) -> List[Dict]:
        """Search applications by name, keyword, or category"""
        results = []
        query_lower = query.lower()
        
        for app in self._app_cache.values():
            score = 0
            
            # Exact name match
            if query_lower == app.name:
                score += 100
            # Name contains query
            elif query_lower in app.name:
                score += 50
            # Display name contains query
            elif query_lower in app.display_name.lower():
                score += 30
            # Keyword match
            elif any(query_lower in kw.lower() for kw in (app.keywords or [])):
                score += 20
            # Category match
            elif query_lower == app.category.value:
                score += 10
            
            if score > 0:
                results.append({
                    **self.get_application_info(app.name),
                    "relevance_score": score
                })
        
        # Sort by relevance score
        return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
    
    def batch_operation(self, app_names: List[str], operation: str, **kwargs) -> Dict[str, Dict]:
        """
        Perform an operation on multiple applications
        
        Args:
            app_names: List of application names
            operation: Operation to perform ('open', 'close', 'info')
            **kwargs: Additional arguments for the operation
            
        Returns:
            Dictionary mapping app names to operation results
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_app = {}
            
            for app_name in app_names:
                if operation == 'open':
                    future = executor.submit(self.open_application, app_name, **kwargs)
                elif operation == 'close':
                    future = executor.submit(self.close_application, app_name, **kwargs)
                elif operation == 'info':
                    future = executor.submit(self.get_application_info, app_name)
                else:
                    results[app_name] = {"error": f"Unknown operation: {operation}"}
                    continue
                
                future_to_app[future] = app_name
            
            for future in as_completed(future_to_app):
                app_name = future_to_app[future]
                try:
                    results[app_name] = future.result(timeout=30)
                except Exception as e:
                    results[app_name] = {"error": str(e)}
        
        return results
    
    def get_most_used_apps(self, limit: int = 10) -> List[Dict]:
        """Get most frequently used applications"""
        apps_with_usage = [
            self.get_application_info(app.name)
            for app in self._app_cache.values()
            if app.usage_count > 0
        ]
        
        return sorted(
            apps_with_usage,
            key=lambda x: x['usage_count'],
            reverse=True
        )[:limit]
    
    def get_recent_apps(self, limit: int = 10) -> List[Dict]:
        """Get recently used applications"""
        apps_with_date = [
            self.get_application_info(app.name)
            for app in self._app_cache.values()
            if app.last_used
        ]
        
        return sorted(
            apps_with_date,
            key=lambda x: x['last_used'],
            reverse=True
        )[:limit]


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    manager = ApplicationManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "open" and len(sys.argv) > 2:
            result = manager.open_application(sys.argv[2])
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "close" and len(sys.argv) > 2:
            result = manager.close_application(sys.argv[2])
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "list":
            apps = manager.list_applications()
            print("\n".join(apps))
        
        elif command == "running":
            running = manager.get_running_applications()
            print(json.dumps(running, indent=2, default=str))
        
        elif command == "search" and len(sys.argv) > 2:
            results = manager.search_applications(sys.argv[2])
            print(json.dumps(results, indent=2, default=str))
        
        else:
            print("Usage: app_manager.py [open|close|list|running|search] [app_name]")
    else:
        # Demo mode
        print("Application Manager Demo")
        print("-" * 50)
        
        # Test opening an app
        result = manager.open_application("chrome")
        print(f"Open Chrome: {result['message']}")
        
        # Check if running
        is_running = manager.is_running("chrome")
        print(f"Chrome running: {is_running}")
        
        # Get app info
        info = manager.get_application_info("vscode")
        if info:
            print(f"VS Code info: {info['display_name']} (v{info['version']})")
        
        # Search for apps
        results = manager.search_applications("browser")
        print(f"Browser search results: {len(results)} apps found")