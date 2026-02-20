import os
import platform
import psutil
import datetime
import urllib.parse
import requests

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
            # Use wttr.in service with robust headers and timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                weather_info = response.text.strip()
                if not weather_info:
                    return f"I couldn't retrieve the weather data for {city} right now."
                return f"The weather in {city} is {weather_info}."
            else:
                return f"I couldn't get the weather for {city}. Service returned status {response.status_code}."
        except requests.exceptions.Timeout:
            return f"The weather service timed out for {city}. Please try again."
        except Exception as e:
            return f"I encountered an error getting the weather: {str(e)}"
