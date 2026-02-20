import os
import webbrowser
import urllib.parse

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
