import os
import subprocess
import webbrowser

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
        """Open a macOS application with web fallback"""
        app_name_lower = app_name.lower()
        
        # Web fallbacks for common apps if not installed
        web_fallbacks = {
            "spotify": "https://open.spotify.com",
            "whatsapp": "https://web.whatsapp.com",
            "discord": "https://discord.com/app",
            "slack": "https://app.slack.com/client",
            "telegram": "https://web.telegram.org",
            "instagram": "https://www.instagram.com",
            "twitter": "https://twitter.com",
            "x": "https://twitter.com",
            "gmail": "https://mail.google.com",
            "outlook": "https://outlook.office.com/mail"
        }
        
        target_app = None
        if app_name_lower in self.applications:
            target_app = self.applications[app_name_lower]
        else:
            for key, app_command in self.applications.items():
                if key in app_name_lower:
                    target_app = app_command
                    break
        
        if target_app:
            try:
                # Use subprocess to capture error instead of os.system printing to stderr
                result = subprocess.run(
                    ['open', '-a', target_app], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    return f"{target_app} opened successfully"
                else:
                    # App launch failed, check fallback
                    if app_name_lower in web_fallbacks:
                        webbrowser.open(web_fallbacks[app_name_lower])
                        return f"Could not find {target_app} app. Opening web version."
                    return f"Could not open {target_app}. It might not be installed."
            except Exception as e:
                return f"Error opening {target_app}: {e}"
        
        # Exact match not found, try generic web fallback
        if app_name_lower in web_fallbacks:
             webbrowser.open(web_fallbacks[app_name_lower])
             return f"App not configured, but opening {app_name} web version."

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
