"""
Enhanced System Utilities Manager for macOS
Handles system monitoring, hardware info, process management, and system operations
"""

import os
import platform
import psutil
import datetime
import urllib.parse
import requests
import subprocess
import shutil
import json
import hashlib
import socket
import ipaddress
import netifaces
import cpuinfo
import GPUtil
import screeninfo
import distro
import time
import threading
import queue
import re
import sys
import pwd
import grp
import stat
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta
import warnings

# Optional imports with fallbacks
try:
    import pyudev
    HAS_UDEV = True
except ImportError:
    HAS_UDEV = False

try:
    from geopy.geocoders import Nominatim
    from geopy.distance import distance
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False

try:
    import speedtest
    HAS_SPEEDTEST = True
except ImportError:
    HAS_SPEEDTEST = False

try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    HAS_NETIFACES = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMetricType(Enum):
    """Types of system metrics"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"
    BATTERY = "battery"
    TEMPERATURE = "temperature"
    FAN = "fan"
    GPU = "gpu"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


class SystemAction(Enum):
    """System actions that can be performed"""
    SHUTDOWN = "shutdown"
    RESTART = "restart"
    SLEEP = "sleep"
    HIBERNATE = "hibernate"
    LOCK = "lock"
    LOGOUT = "logout"


class TemperatureUnit(Enum):
    """Temperature units"""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


@dataclass
class SystemAlert:
    """System alert information"""
    level: AlertLevel
    metric: SystemMetricType
    message: str
    threshold: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class SystemSnapshot:
    """Point-in-time system snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    processes_count: int
    battery_percent: Optional[float]
    temperature: Optional[float]
    alerts: List[SystemAlert] = field(default_factory=list)


class SystemUtilitiesError(Exception):
    """Custom exception for system utilities errors"""
    pass


class SystemUtilitiesManager:
    """
    Enhanced System Utilities Manager with comprehensive features:
    - Real-time system monitoring
    - Hardware information gathering
    - Process management
    - Network utilities
    - File system operations
    - System alerts and notifications
    - Performance tracking
    - Weather and location services
    - System maintenance tasks
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize System Utilities Manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path.home() / ".config" / "system_utils.json"
        
        # System state
        self.monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.alert_queue: queue.Queue = queue.Queue()
        self.snapshots: List[SystemSnapshot] = []
        self.max_snapshots = 1000
        self.alerts: List[SystemAlert] = []
        self.max_alerts = 100
        
        # Monitoring thresholds
        self.thresholds = {
            SystemMetricType.CPU: {"warning": 70, "critical": 90},
            SystemMetricType.MEMORY: {"warning": 80, "critical": 95},
            SystemMetricType.DISK: {"warning": 85, "critical": 95},
            SystemMetricType.TEMPERATURE: {"warning": 70, "critical": 85},
            SystemMetricType.BATTERY: {"warning": 20, "critical": 10}
        }
        
        # Performance metrics
        self.metrics: Dict[str, Any] = {
            "uptime": 0,
            "peak_cpu": 0,
            "peak_memory": 0,
            "total_alerts": 0,
            "resolved_alerts": 0,
            "snapshots_taken": 0
        }
        
        # Location services
        self.location_cache: Optional[Dict] = None
        self.location_cache_time: Optional[datetime] = None
        self.location_cache_duration = timedelta(hours=1)
        
        # Weather cache
        self.weather_cache: Dict[str, Tuple[str, datetime]] = {}
        self.weather_cache_duration = timedelta(minutes=30)
        
        # Network cache
        self.network_cache: Dict[str, Any] = {}
        self.network_cache_duration = timedelta(minutes=5)
        
        # Load configuration
        self.load_config()
        
        # Start monitoring if enabled
        if self.config.get("auto_monitor", False):
            self.start_monitoring()
        
        logger.info("System Utilities Manager initialized")
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "auto_monitor": False,
                    "monitoring_interval": 5,
                    "temperature_unit": "celsius",
                    "alert_notifications": True,
                    "log_performance": True,
                    "max_snapshots": 1000,
                    "thresholds": {
                        "cpu_warning": 70,
                        "cpu_critical": 90,
                        "memory_warning": 80,
                        "memory_critical": 95,
                        "disk_warning": 85,
                        "disk_critical": 95,
                        "temperature_warning": 70,
                        "temperature_critical": 85,
                        "battery_warning": 20,
                        "battery_critical": 10
                    }
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def start_monitoring(self, interval: int = 5) -> None:
        """
        Start system monitoring in background
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            logger.warning("Monitoring already running")
            return
        
        self.monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"System monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Take system snapshot
                snapshot = self.take_snapshot()
                self.snapshots.append(snapshot)
                
                # Trim snapshots if needed
                if len(self.snapshots) > self.max_snapshots:
                    self.snapshots = self.snapshots[-self.max_snapshots:]
                
                # Check thresholds
                self.check_thresholds(snapshot)
                
                # Update metrics
                self.update_metrics(snapshot)
                
                # Log performance if enabled
                if self.config.get("log_performance", False):
                    self.log_performance(snapshot)
                
                # Wait for next interval
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def take_snapshot(self) -> SystemSnapshot:
        """
        Take a point-in-time system snapshot
        
        Returns:
            SystemSnapshot object
        """
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            # Network info
            net_io = psutil.net_io_counters()
            
            # Process info
            processes = len(psutil.pids())
            
            # Battery info
            battery = self.get_battery_info()
            battery_percent = battery.get("percent", 0) if isinstance(battery, dict) else None
            
            # Temperature info
            temp = self.get_temperature()
            
            return SystemSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_bytes_sent=net_io.bytes_sent,
                network_bytes_recv=net_io.bytes_recv,
                processes_count=processes,
                battery_percent=battery_percent,
                temperature=temp
            )
            
        except Exception as e:
            logger.error(f"Failed to take snapshot: {e}")
            raise SystemUtilitiesError(f"Snapshot failed: {e}")
    
    def check_thresholds(self, snapshot: SystemSnapshot) -> None:
        """
        Check system thresholds and generate alerts
        
        Args:
            snapshot: System snapshot to check
        """
        try:
            # Check CPU
            self._check_metric_threshold(
                SystemMetricType.CPU,
                snapshot.cpu_percent,
                snapshot.timestamp
            )
            
            # Check Memory
            self._check_metric_threshold(
                SystemMetricType.MEMORY,
                snapshot.memory_percent,
                snapshot.timestamp
            )
            
            # Check Disk
            self._check_metric_threshold(
                SystemMetricType.DISK,
                snapshot.disk_percent,
                snapshot.timestamp
            )
            
            # Check Temperature
            if snapshot.temperature:
                self._check_metric_threshold(
                    SystemMetricType.TEMPERATURE,
                    snapshot.temperature,
                    snapshot.timestamp
                )
            
            # Check Battery
            if snapshot.battery_percent is not None:
                self._check_metric_threshold(
                    SystemMetricType.BATTERY,
                    snapshot.battery_percent,
                    snapshot.timestamp,
                    invert=True  # Lower is worse for battery
                )
                
        except Exception as e:
            logger.error(f"Failed to check thresholds: {e}")
    
    def _check_metric_threshold(self, metric: SystemMetricType, value: float, 
                                timestamp: datetime, invert: bool = False) -> None:
        """
        Check a single metric threshold
        
        Args:
            metric: Metric type
            value: Current value
            timestamp: Timestamp
            invert: Invert comparison (for metrics where lower is worse)
        """
        try:
            thresholds = self.thresholds.get(metric, {})
            
            # Check critical threshold
            if "critical" in thresholds:
                critical = thresholds["critical"]
                if (not invert and value >= critical) or (invert and value <= critical):
                    alert = SystemAlert(
                        level=AlertLevel.CRITICAL,
                        metric=metric,
                        message=f"{metric.value.upper()} critical: {value:.1f}% (threshold: {critical}%)",
                        threshold=critical,
                        current_value=value,
                        timestamp=timestamp
                    )
                    self.add_alert(alert)
                    return
            
            # Check warning threshold
            if "warning" in thresholds:
                warning = thresholds["warning"]
                if (not invert and value >= warning) or (invert and value <= warning):
                    alert = SystemAlert(
                        level=AlertLevel.WARNING,
                        metric=metric,
                        message=f"{metric.value.upper()} warning: {value:.1f}% (threshold: {warning}%)",
                        threshold=warning,
                        current_value=value,
                        timestamp=timestamp
                    )
                    self.add_alert(alert)
                    
        except Exception as e:
            logger.error(f"Failed to check metric threshold: {e}")
    
    def add_alert(self, alert: SystemAlert) -> None:
        """
        Add system alert
        
        Args:
            alert: Alert to add
        """
        try:
            # Check for duplicate unresolved alert
            for existing in self.alerts:
                if (existing.metric == alert.metric and 
                    not existing.resolved and
                    existing.level == alert.level):
                    # Update existing alert
                    existing.current_value = alert.current_value
                    existing.timestamp = alert.timestamp
                    return
            
            # Add new alert
            self.alerts.append(alert)
            self.alert_queue.put(alert)
            self.metrics["total_alerts"] += 1
            
            # Trim alerts if needed
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
            
            # Send notification if enabled
            if self.config.get("alert_notifications", True):
                self.send_alert_notification(alert)
                
        except Exception as e:
            logger.error(f"Failed to add alert: {e}")
    
    def resolve_alert(self, alert: SystemAlert) -> None:
        """
        Mark alert as resolved
        
        Args:
            alert: Alert to resolve
        """
        alert.resolved = True
        alert.resolution_time = datetime.now()
        self.metrics["resolved_alerts"] += 1
        logger.info(f"Alert resolved: {alert.message}")
    
    def send_alert_notification(self, alert: SystemAlert) -> None:
        """
        Send alert notification
        
        Args:
            alert: Alert to notify about
        """
        try:
            # Use platform-specific notifications
            if platform.system() == "Darwin":  # macOS
                script = f'''
                display notification "{alert.message}" with title "System Alert" subtitle "{alert.level.value.upper()}"
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True)
            elif platform.system() == "Linux":
                subprocess.run([
                    "notify-send",
                    f"System Alert - {alert.level.value.upper()}",
                    alert.message
                ])
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def update_metrics(self, snapshot: SystemSnapshot) -> None:
        """Update performance metrics"""
        try:
            self.metrics["uptime"] = time.time() - psutil.boot_time()
            self.metrics["peak_cpu"] = max(self.metrics["peak_cpu"], snapshot.cpu_percent)
            self.metrics["peak_memory"] = max(self.metrics["peak_memory"], snapshot.memory_percent)
            self.metrics["snapshots_taken"] += 1
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def log_performance(self, snapshot: SystemSnapshot) -> None:
        """Log performance data"""
        try:
            log_entry = {
                "timestamp": snapshot.timestamp.isoformat(),
                "cpu": snapshot.cpu_percent,
                "memory": snapshot.memory_percent,
                "disk": snapshot.disk_percent,
                "processes": snapshot.processes_count
            }
            
            log_file = Path.home() / ".cache" / "system_utils" / "performance.json"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to log file
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")
    
    def get_system_info(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Get detailed system information
        
        Args:
            detailed: Whether to include detailed hardware info
            
        Returns:
            Dictionary with system information
        """
        try:
            info = {
                "OS": platform.platform(),
                "OS Release": platform.release(),
                "OS Version": platform.version(),
                "Hostname": socket.gethostname(),
                "Architecture": platform.machine(),
                "Processor": platform.processor(),
                "CPU Cores": psutil.cpu_count(logical=False),
                "CPU Threads": psutil.cpu_count(logical=True),
                "CPU Usage": f"{psutil.cpu_percent(interval=1)}%",
                "CPU Frequency": self.get_cpu_frequency(),
                "Memory": self.get_memory_info(),
                "Disk": self.get_disk_info(),
                "Network": self.get_network_info(),
                "Battery": self.get_battery_info(),
                "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "Uptime": self.get_uptime(),
                "Users": self.get_logged_in_users(),
                "Python Version": sys.version,
                "Processes": len(psutil.pids())
            }
            
            if detailed:
                info.update({
                    "CPU Details": self.get_cpu_details(),
                    "GPU Details": self.get_gpu_info(),
                    "Disk Partitions": self.get_disk_partitions(),
                    "Network Interfaces": self.get_network_interfaces(),
                    "Environment Variables": dict(os.environ),
                    "Loaded Modules": list(sys.modules.keys())[:100]  # Limit to 100
                })
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}
    
    def get_cpu_frequency(self) -> Dict[str, str]:
        """Get CPU frequency information"""
        try:
            freq = psutil.cpu_freq()
            if freq:
                return {
                    "Current": f"{freq.current:.0f} MHz",
                    "Min": f"{freq.min:.0f} MHz" if freq.min else "N/A",
                    "Max": f"{freq.max:.0f} MHz" if freq.max else "N/A"
                }
            return {"info": "Frequency information not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_cpu_details(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        try:
            cpu_info = cpuinfo.get_cpu_info()
            return {
                "Brand": cpu_info.get('brand_raw', 'Unknown'),
                "Arch": cpu_info.get('arch', 'Unknown'),
                "Bits": cpu_info.get('bits', 'Unknown'),
                "Count": cpu_info.get('count', 'Unknown'),
                "Hz": cpu_info.get('hz_actual_friendly', 'Unknown'),
                "Flags": cpu_info.get('flags', [])[:20]  # Limit to 20 flags
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_memory_info(self) -> Dict[str, str]:
        """Get detailed memory information"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "Total": f"{mem.total / (1024**3):.2f} GB",
                "Available": f"{mem.available / (1024**3):.2f} GB",
                "Used": f"{mem.used / (1024**3):.2f} GB",
                "Free": f"{mem.free / (1024**3):.2f} GB",
                "Percent": f"{mem.percent}%",
                "Swap Total": f"{swap.total / (1024**3):.2f} GB" if swap.total else "N/A",
                "Swap Used": f"{swap.used / (1024**3):.2f} GB" if swap.total else "N/A",
                "Swap Percent": f"{swap.percent}%" if swap.total else "N/A"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_disk_info(self) -> Dict[str, str]:
        """Get disk usage information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                "Total": f"{disk.total / (1024**3):.2f} GB",
                "Used": f"{disk.used / (1024**3):.2f} GB",
                "Free": f"{disk.free / (1024**3):.2f} GB",
                "Percent": f"{disk.percent}%"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_disk_partitions(self) -> List[Dict[str, str]]:
        """Get disk partition information"""
        try:
            partitions = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "Device": part.device,
                        "Mountpoint": part.mountpoint,
                        "Filesystem": part.fstype,
                        "Total": f"{usage.total / (1024**3):.2f} GB",
                        "Used": f"{usage.used / (1024**3):.2f} GB",
                        "Free": f"{usage.free / (1024**3):.2f} GB",
                        "Percent": f"{usage.percent}%"
                    })
                except:
                    continue
            return partitions
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            io_counters = psutil.net_io_counters()
            connections = psutil.net_connections()
            
            info = {
                "Bytes Sent": f"{io_counters.bytes_sent / (1024**2):.2f} MB",
                "Bytes Received": f"{io_counters.bytes_recv / (1024**2):.2f} MB",
                "Packets Sent": io_counters.packets_sent,
                "Packets Received": io_counters.packets_recv,
                "Errors In": io_counters.errin,
                "Errors Out": io_counters.errout,
                "Drops In": io_counters.dropin,
                "Drops Out": io_counters.dropout,
                "Connections": len(connections),
                "Hostname": socket.gethostname(),
                "IP Addresses": self.get_ip_addresses()
            }
            
            # Get network interfaces
            if HAS_NETIFACES:
                info["Interfaces"] = self.get_network_interfaces()
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_ip_addresses(self) -> Dict[str, str]:
        """Get IP addresses for all interfaces"""
        try:
            addresses = {}
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        addresses[interface] = addr.address
                        break
            return addresses
        except Exception as e:
            return {"error": str(e)}
    
    def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """Get detailed network interface information"""
        try:
            interfaces = []
            stats = psutil.net_if_stats()
            
            for interface, addrs in psutil.net_if_addrs().items():
                interface_info = {
                    "name": interface,
                    "addresses": [],
                    "stats": {}
                }
                
                # Add addresses
                for addr in addrs:
                    address_info = {
                        "family": "IPv4" if addr.family == socket.AF_INET else "IPv6" if addr.family == socket.AF_INET6 else "Other",
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    }
                    interface_info["addresses"].append(address_info)
                
                # Add stats if available
                if interface in stats:
                    stat = stats[interface]
                    interface_info["stats"] = {
                        "isup": stat.isup,
                        "duplex": str(stat.duplex),
                        "speed": f"{stat.speed} Mb/s" if stat.speed > 0 else "Unknown",
                        "mtu": stat.mtu
                    }
                
                interfaces.append(interface_info)
            
            return interfaces
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get battery information"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                # Calculate time left
                if battery.secsleft > 0:
                    hours = battery.secsleft // 3600
                    minutes = (battery.secsleft % 3600) // 60
                    time_left = f"{hours}h {minutes}m"
                elif battery.secsleft == -1:
                    time_left = "Unknown"
                else:
                    time_left = "Calculating..."
                
                info = {
                    "percent": battery.percent,
                    "percent_formatted": f"{battery.percent}%",
                    "power_plugged": battery.power_plugged,
                    "time_left_seconds": battery.secsleft,
                    "time_left_formatted": time_left,
                    "status": "Charging" if battery.power_plugged else "Discharging"
                }
                
                # Add voltage if available (macOS specific)
                if platform.system() == "Darwin":
                    try:
                        result = subprocess.run(
                            ["pmset", "-g", "batt"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            # Parse voltage from output
                            match = re.search(r'(\d+)mV', result.stdout)
                            if match:
                                info["voltage"] = f"{int(match.group(1)) / 1000:.2f}V"
                    except:
                        pass
                
                return info
            else:
                return {"info": "No battery detected (desktop system)"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_temperature(self, unit: TemperatureUnit = TemperatureUnit.CELSIUS) -> Optional[float]:
        """
        Get system temperature
        
        Args:
            unit: Temperature unit
            
        Returns:
            Temperature value or None if not available
        """
        try:
            if platform.system() == "Darwin":  # macOS
                # Use osx-cpu-temp if available
                try:
                    result = subprocess.run(
                        ["osx-cpu-temp"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        temp = float(result.stdout.strip().replace('°C', ''))
                        return self.convert_temperature(temp, TemperatureUnit.CELSIUS, unit)
                except:
                    pass
                    
            elif platform.system() == "Linux":
                # Read from thermal zones
                thermal_dir = Path("/sys/class/thermal")
                if thermal_dir.exists():
                    temps = []
                    for thermal_zone in thermal_dir.glob("thermal_zone*/temp"):
                        try:
                            with open(thermal_zone) as f:
                                temp = int(f.read().strip()) / 1000  # Convert to Celsius
                                temps.append(temp)
                        except:
                            continue
                    
                    if temps:
                        avg_temp = sum(temps) / len(temps)
                        return self.convert_temperature(avg_temp, TemperatureUnit.CELSIUS, unit)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get temperature: {e}")
            return None
    
    def convert_temperature(self, value: float, from_unit: TemperatureUnit, 
                           to_unit: TemperatureUnit) -> float:
        """Convert between temperature units"""
        if from_unit == to_unit:
            return value
        
        # Convert to Celsius first
        if from_unit == TemperatureUnit.FAHRENHEIT:
            celsius = (value - 32) * 5/9
        elif from_unit == TemperatureUnit.KELVIN:
            celsius = value - 273.15
        else:
            celsius = value
        
        # Convert from Celsius to target
        if to_unit == TemperatureUnit.FAHRENHEIT:
            return (celsius * 9/5) + 32
        elif to_unit == TemperatureUnit.KELVIN:
            return celsius + 273.15
        else:
            return celsius
    
    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information"""
        try:
            gpus = []
            
            # Try GPUtil
            try:
                for gpu in GPUtil.getGPUs():
                    gpus.append({
                        "name": gpu.name,
                        "driver": gpu.driver,
                        "memory_total": f"{gpu.memoryTotal} MB",
                        "memory_used": f"{gpu.memoryUsed} MB",
                        "memory_free": f"{gpu.memoryFree} MB",
                        "memory_util": f"{gpu.memoryUtil * 100:.1f}%",
                        "gpu_util": f"{gpu.load * 100:.1f}%",
                        "temperature": f"{gpu.temperature}°C"
                    })
            except:
                pass
            
            # macOS specific GPU info
            if platform.system() == "Darwin" and not gpus:
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        # Parse GPU info from system_profiler
                        lines = result.stdout.split('\n')
                        gpu_info = {}
                        for line in lines:
                            if "Chipset Model:" in line:
                                gpu_info["name"] = line.split(":")[1].strip()
                            elif "VRAM" in line:
                                gpu_info["memory"] = line.split(":")[1].strip()
                        
                        if gpu_info:
                            gpus.append(gpu_info)
                except:
                    pass
            
            return gpus if gpus else [{"info": "No GPU information available"}]
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_logged_in_users(self) -> List[Dict[str, str]]:
        """Get logged in users"""
        try:
            users = []
            for user in psutil.users():
                users.append({
                    "name": user.name,
                    "terminal": user.terminal,
                    "host": user.host,
                    "started": datetime.fromtimestamp(user.started).strftime("%Y-%m-%d %H:%M:%S"),
                    "pid": user.pid
                })
            return users
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_uptime(self) -> str:
        """Get system uptime as formatted string"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if seconds > 0 or not parts:
                parts.append(f"{seconds}s")
            
            return " ".join(parts)
        except Exception as e:
            return f"Error: {e}"
    
    def get_process_list(self, sort_by: str = "cpu", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of running processes
        
        Args:
            sort_by: Sort field (cpu, memory, name, pid)
            limit: Maximum number of processes to return
            
        Returns:
            List of process information dictionaries
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'status', 'create_time', 'username']):
                try:
                    pinfo = proc.info
                    pinfo['create_time'] = datetime.fromtimestamp(pinfo['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x.get('name', ''))
            elif sort_by == "pid":
                processes.sort(key=lambda x: x.get('pid', 0))
            
            return processes[:limit]
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def kill_process(self, pid: int, force: bool = False) -> str:
        """
        Kill a process by PID
        
        Args:
            pid: Process ID
            force: Whether to force kill
            
        Returns:
            Status message
        """
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
                return f"Process {pid} ({proc.name()}) forcefully terminated"
            else:
                proc.terminate()
                return f"Process {pid} ({proc.name()}) terminated"
        except psutil.NoSuchProcess:
            return f"Process {pid} not found"
        except psutil.AccessDenied:
            return f"Access denied to kill process {pid}"
        except Exception as e:
            return f"Error killing process: {e}"
    
    def get_system_services(self) -> List[Dict[str, str]]:
        """Get list of system services"""
        services = []
        
        if platform.system() == "Darwin":  # macOS
            try:
                # Get launchd services
                result = subprocess.run(
                    ["launchctl", "list"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n')[1:]:  # Skip header
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                services.append({
                                    "pid": parts[0],
                                    "status": parts[1],
                                    "name": parts[2]
                                })
            except:
                pass
                
        elif platform.system() == "Linux":
            try:
                # Try systemctl
                result = subprocess.run(
                    ["systemctl", "list-units", "--type=service", "--all", "--no-pager"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '.service' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                services.append({
                                    "name": parts[0],
                                    "load": parts[1],
                                    "active": parts[2],
                                    "sub": parts[3],
                                    "description": ' '.join(parts[4:])
                                })
            except:
                pass
        
        return services[:50]  # Limit to 50 services
    
    def get_location(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get current location based on IP
        
        Args:
            force_refresh: Whether to force cache refresh
            
        Returns:
            Location dictionary or None
        """
        if not force_refresh and self.location_cache:
            if datetime.now() - self.location_cache_time < self.location_cache_duration:
                return self.location_cache
        
        try:
            # Try ipapi.co first
            response = requests.get("https://ipapi.co/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.location_cache = {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("org")
                }
                self.location_cache_time = datetime.now()
                return self.location_cache
            
            # Fallback to ipinfo.io
            response = requests.get("https://ipinfo.io/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                loc = data.get("loc", "").split(",")
                self.location_cache = {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "latitude": float(loc[0]) if len(loc) > 0 else None,
                    "longitude": float(loc[1]) if len(loc) > 1 else None,
                    "timezone": data.get("timezone"),
                    "isp": data.get("org")
                }
                self.location_cache_time = datetime.now()
                return self.location_cache
                
        except Exception as e:
            logger.error(f"Failed to get location: {e}")
        
        return None
    
    def get_weather(self, city: Optional[str] = None, 
                   use_location: bool = True) -> str:
        """
        Get weather for a city or current location
        
        Args:
            city: City name (optional)
            use_location: Use current location if city not provided
            
        Returns:
            Weather information string
        """
        try:
            # Check cache
            cache_key = city or "current_location"
            if cache_key in self.weather_cache:
                weather, timestamp = self.weather_cache[cache_key]
                if datetime.now() - timestamp < self.weather_cache_duration:
                    return weather
            
            # Get city from location if not provided
            if not city and use_location:
                location = self.get_location()
                if location and location.get("city"):
                    city = location["city"]
            
            if not city:
                return "I couldn't determine your location for weather lookup."
            
            # Use wttr.in service with robust headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # Get detailed weather
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+%w+%h"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                weather_info = response.text.strip()
                if weather_info:
                    result = f"The weather in {city} is {weather_info}."
                    self.weather_cache[cache_key] = (result, datetime.now())
                    return result
                else:
                    return f"I couldn't retrieve the weather data for {city} right now."
            else:
                return f"I couldn't get the weather for {city}. Service returned status {response.status_code}."
                
        except requests.exceptions.Timeout:
            return f"The weather service timed out. Please try again."
        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"I encountered an error getting the weather: {str(e)}"
    
    def get_weather_forecast(self, city: Optional[str] = None, 
                            days: int = 3) -> str:
        """
        Get weather forecast
        
        Args:
            city: City name
            days: Number of days (1-5)
            
        Returns:
            Weather forecast string
        """
        try:
            if not city:
                location = self.get_location()
                if location and location.get("city"):
                    city = location["city"]
            
            if not city:
                return "I couldn't determine your location."
            
            days = min(max(days, 1), 5)  # Limit to 1-5 days
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t&days={days}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return f"Weather forecast for {city}:\n{response.text.strip()}"
            else:
                return f"Could not get forecast for {city}"
                
        except Exception as e:
            return f"Error getting forecast: {e}"
    
    def test_internet_speed(self) -> Dict[str, Any]:
        """Test internet speed"""
        if not HAS_SPEEDTEST:
            return {"error": "Speedtest library not installed"}
        
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            ping = st.results.ping
            
            result = {
                "download_mbps": round(download_speed, 2),
                "upload_mbps": round(upload_speed, 2),
                "ping_ms": round(ping, 2),
                "timestamp": datetime.now().isoformat(),
                "server": st.results.server.get("sponsor", "Unknown")
            }
            
            self.network_cache["speedtest"] = (result, datetime.now())
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_cached_speedtest(self) -> Optional[Dict[str, Any]]:
        """Get cached speedtest result"""
        if "speedtest" in self.network_cache:
            result, timestamp = self.network_cache["speedtest"]
            if datetime.now() - timestamp < self.network_cache_duration:
                return result
        return None
    
    def ping_host(self, host: str, count: int = 4) -> Dict[str, Any]:
        """
        Ping a host
        
        Args:
            host: Hostname or IP address
            count: Number of ping packets
            
        Returns:
            Ping results
        """
        try:
            # Determine ping command based on OS
            if platform.system() == "Windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse output
            if result.returncode == 0:
                # Extract statistics
                lines = result.stdout.split('\n')
                stats = {}
                
                for line in lines:
                    if "avg" in line and "=" in line:
                        # Linux/Unix format
                        parts = line.split('=')
                        if len(parts) > 1:
                            values = parts[1].split('/')
                            if len(values) >= 3:
                                stats = {
                                    "min_ms": float(values[0]),
                                    "avg_ms": float(values[1]),
                                    "max_ms": float(values[2])
                                }
                    elif "Average" in line and "=" in line:
                        # Windows format
                        parts = line.split('=')
                        if len(parts) > 1:
                            values = parts[1].split('ms')[0].split(',')
                            if len(values) >= 3:
                                stats = {
                                    "min_ms": float(values[0].strip()),
                                    "max_ms": float(values[1].strip()),
                                    "avg_ms": float(values[2].strip())
                                }
                
                return {
                    "host": host,
                    "packets_sent": count,
                    "packets_received": count,
                    "packet_loss": 0,
                    "statistics": stats,
                    "output": result.stdout
                }
            else:
                # Extract packet loss
                packet_loss = 100
                for line in result.stdout.split('\n'):
                    if "packet loss" in line.lower():
                        match = re.search(r'(\d+)%', line)
                        if match:
                            packet_loss = int(match.group(1))
                            break
                
                return {
                    "host": host,
                    "packets_sent": count,
                    "packets_received": count - int(count * packet_loss / 100),
                    "packet_loss": packet_loss,
                    "error": "Host unreachable" if packet_loss == 100 else "Partial packet loss",
                    "output": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Ping timeout", "host": host}
        except Exception as e:
            return {"error": str(e), "host": host}
    
    def traceroute(self, host: str) -> List[Dict[str, Any]]:
        """
        Perform traceroute to host
        
        Args:
            host: Hostname or IP address
            
        Returns:
            List of hops
        """
        hops = []
        
        try:
            # Determine traceroute command based on OS
            if platform.system() == "Windows":
                cmd = ["tracert", host]
            else:
                cmd = ["traceroute", host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    # Parse hop information
                    if line.strip() and not line.startswith("traceroute"):
                        # Simplified parsing
                        parts = line.split()
                        if len(parts) >= 2:
                            hop = {
                                "hop": len(hops) + 1,
                                "host": parts[1] if len(parts) > 1 else "Unknown",
                                "ip": parts[1] if len(parts) > 1 else "Unknown",
                                "rtt_ms": []
                            }
                            
                            # Extract RTT values
                            for i, part in enumerate(parts[2:], 2):
                                if "ms" in part:
                                    try:
                                        rtt = float(part.replace("ms", ""))
                                        hop["rtt_ms"].append(rtt)
                                    except:
                                        pass
                            
                            hops.append(hop)
            
            return hops
            
        except subprocess.TimeoutExpired:
            return [{"error": "Traceroute timeout"}]
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_network_connections(self) -> List[Dict[str, Any]]:
        """Get active network connections"""
        try:
            connections = []
            for conn in psutil.net_connections():
                conn_info = {
                    "fd": conn.fd,
                    "family": "IPv4" if conn.family == socket.AF_INET else "IPv6" if conn.family == socket.AF_INET6 else "Other",
                    "type": "TCP" if conn.type == socket.SOCK_STREAM else "UDP" if conn.type == socket.SOCK_DGRAM else "Other",
                    "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                    "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                    "status": conn.status,
                    "pid": conn.pid
                }
                
                # Get process name if PID exists
                if conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        conn_info["process"] = proc.name()
                    except:
                        conn_info["process"] = "Unknown"
                
                connections.append(conn_info)
            
            return connections
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_open_ports(self) -> List[Dict[str, Any]]:
        """Get list of open ports"""
        try:
            open_ports = []
            connections = psutil.net_connections()
            
            for conn in connections:
                if conn.status == 'LISTEN' and conn.laddr:
                    open_ports.append({
                        "port": conn.laddr.port,
                        "protocol": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",
                        "address": conn.laddr.ip,
                        "pid": conn.pid
                    })
            
            # Remove duplicates and sort
            unique_ports = []
            seen = set()
            for port in open_ports:
                key = (port["port"], port["protocol"])
                if key not in seen:
                    seen.add(key)
                    unique_ports.append(port)
            
            unique_ports.sort(key=lambda x: x["port"])
            return unique_ports
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_system_alerts(self, unresolved_only: bool = True) -> List[SystemAlert]:
        """
        Get system alerts
        
        Args:
            unresolved_only: Only return unresolved alerts
            
        Returns:
            List of alerts
        """
        if unresolved_only:
            return [a for a in self.alerts if not a.resolved]
        return self.alerts.copy()
    
    def clear_alerts(self, resolved_only: bool = True) -> None:
        """
        Clear alerts
        
        Args:
            resolved_only: Only clear resolved alerts
        """
        if resolved_only:
            self.alerts = [a for a in self.alerts if not a.resolved]
        else:
            self.alerts = []
        logger.info(f"Cleared alerts (resolved_only={resolved_only})")
    
    def get_system_snapshots(self, count: Optional[int] = None) -> List[SystemSnapshot]:
        """
        Get system snapshots
        
        Args:
            count: Number of snapshots to return
            
        Returns:
            List of snapshots
        """
        if count:
            return self.snapshots[-count:]
        return self.snapshots.copy()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        try:
            if not self.snapshots:
                return {"error": "No snapshots available"}
            
            # Calculate averages
            avg_cpu = sum(s.cpu_percent for s in self.snapshots) / len(self.snapshots)
            avg_memory = sum(s.memory_percent for s in self.snapshots) / len(self.snapshots)
            avg_disk = sum(s.disk_percent for s in self.snapshots) / len(self.snapshots)
            
            # Find peaks
            peak_cpu = max(s.cpu_percent for s in self.snapshots)
            peak_memory = max(s.memory_percent for s in self.snapshots)
            peak_disk = max(s.disk_percent for s in self.snapshots)
            
            # Calculate trends
            if len(self.snapshots) > 1:
                cpu_trend = self.snapshots[-1].cpu_percent - self.snapshots[0].cpu_percent
                memory_trend = self.snapshots[-1].memory_percent - self.snapshots[0].memory_percent
            else:
                cpu_trend = 0
                memory_trend = 0
            
            return {
                "period": {
                    "start": self.snapshots[0].timestamp.isoformat(),
                    "end": self.snapshots[-1].timestamp.isoformat(),
                    "snapshots": len(self.snapshots)
                },
                "averages": {
                    "cpu": f"{avg_cpu:.1f}%",
                    "memory": f"{avg_memory:.1f}%",
                    "disk": f"{avg_disk:.1f}%"
                },
                "peaks": {
                    "cpu": f"{peak_cpu:.1f}%",
                    "memory": f"{peak_memory:.1f}%",
                    "disk": f"{peak_disk:.1f}%"
                },
                "trends": {
                    "cpu": f"{cpu_trend:+.1f}%",
                    "memory": f"{memory_trend:+.1f}%"
                },
                "alerts": {
                    "total": self.metrics["total_alerts"],
                    "unresolved": len([a for a in self.alerts if not a.resolved])
                },
                "uptime": self.get_uptime()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup_temp_files(self, days_old: int = 7) -> Dict[str, Any]:
        """
        Clean up temporary files
        
        Args:
            days_old: Delete files older than this many days
            
        Returns:
            Cleanup statistics
        """
        try:
            temp_dirs = [
                "/tmp",
                "/var/tmp",
                str(Path.home() / ".cache"),
                str(Path.home() / "Downloads")
            ]
            
            stats = {
                "files_deleted": 0,
                "directories_deleted": 0,
                "space_freed": 0,
                "errors": []
            }
            
            cutoff_time = time.time() - (days_old * 24 * 3600)
            
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue
                
                for root, dirs, files in os.walk(temp_dir):
                    # Check files
                    for file in files:
                        try:
                            filepath = os.path.join(root, file)
                            if os.path.getmtime(filepath) < cutoff_time:
                                size = os.path.getsize(filepath)
                                os.remove(filepath)
                                stats["files_deleted"] += 1
                                stats["space_freed"] += size
                        except Exception as e:
                            stats["errors"].append(f"Error deleting {filepath}: {e}")
                    
                    # Check directories (if empty and old)
                    for dir in dirs:
                        try:
                            dirpath = os.path.join(root, dir)
                            if os.path.getmtime(dirpath) < cutoff_time and not os.listdir(dirpath):
                                os.rmdir(dirpath)
                                stats["directories_deleted"] += 1
                        except Exception as e:
                            stats["errors"].append(f"Error deleting {dirpath}: {e}")
            
            # Format space freed
            if stats["space_freed"] > 1024**3:
                stats["space_freed_formatted"] = f"{stats['space_freed'] / (1024**3):.2f} GB"
            elif stats["space_freed"] > 1024**2:
                stats["space_freed_formatted"] = f"{stats['space_freed'] / (1024**2):.2f} MB"
            else:
                stats["space_freed_formatted"] = f"{stats['space_freed'] / 1024:.2f} KB"
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_disk_usage_by_directory(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        Get disk usage by directory
        
        Args:
            path: Starting path
            
        Returns:
            List of directories with usage
        """
        try:
            usage = []
            
            for item in os.listdir(path):
                try:
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        size = self.get_directory_size(item_path)
                        usage.append({
                            "directory": item_path,
                            "size": size,
                            "size_formatted": self.format_size(size)
                        })
                except (PermissionError, OSError):
                    continue
            
            # Sort by size descending
            usage.sort(key=lambda x: x["size"], reverse=True)
            return usage[:20]  # Return top 20
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_directory_size(entry.path)
        except (PermissionError, OSError):
            pass
        return total
    
    def format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def execute_system_action(self, action: SystemAction) -> str:
        """
        Execute system action (shutdown, restart, etc.)
        
        Args:
            action: Action to perform
            
        Returns:
            Status message
        """
        try:
            if platform.system() == "Darwin":  # macOS
                if action == SystemAction.SHUTDOWN:
                    subprocess.run(["sudo", "shutdown", "-h", "now"])
                    return "Shutting down system..."
                elif action == SystemAction.RESTART:
                    subprocess.run(["sudo", "shutdown", "-r", "now"])
                    return "Restarting system..."
                elif action == SystemAction.SLEEP:
                    subprocess.run(["pmset", "sleepnow"])
                    return "Putting system to sleep..."
                elif action == SystemAction.LOCK:
                    subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
                    return "Locking screen..."
                elif action == SystemAction.LOGOUT:
                    subprocess.run(["osascript", "-e", 'tell application "System Events" to log out'])
                    return "Logging out..."
                    
            elif platform.system() == "Linux":
                if action == SystemAction.SHUTDOWN:
                    subprocess.run(["sudo", "shutdown", "now"])
                    return "Shutting down system..."
                elif action == SystemAction.RESTART:
                    subprocess.run(["sudo", "reboot"])
                    return "Restarting system..."
                elif action == SystemAction.SLEEP:
                    subprocess.run(["systemctl", "suspend"])
                    return "Putting system to sleep..."
                elif action == SystemAction.LOCK:
                    subprocess.run(["gnome-screensaver-command", "-l"])  # GNOME
                    return "Locking screen..."
                    
            return f"Action {action.value} executed"
            
        except Exception as e:
            return f"Failed to execute action: {e}"
    
    def get_system_logs(self, lines: int = 100) -> List[str]:
        """
        Get system logs
        
        Args:
            lines: Number of log lines to retrieve
            
        Returns:
            List of log lines
        """
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["log", "show", "--last", "1h", "--predicate", 'eventMessage contains "error"'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout.split('\n')[-lines:]
                    
            elif platform.system() == "Linux":
                # Try journalctl
                result = subprocess.run(
                    ["journalctl", "-n", str(lines)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout.split('\n')
                    
                # Fallback to syslog
                log_files = ["/var/log/syslog", "/var/log/messages"]
                for log_file in log_files:
                    if os.path.exists(log_file):
                        result = subprocess.run(
                            ["tail", "-n", str(lines), log_file],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if result.returncode == 0:
                            return result.stdout.split('\n')
            
            return ["No logs available"]
            
        except Exception as e:
            return [f"Error getting logs: {e}"]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def set_threshold(self, metric: SystemMetricType, warning: float, critical: float) -> None:
        """
        Set alert thresholds
        
        Args:
            metric: Metric type
            warning: Warning threshold
            critical: Critical threshold
        """
        self.thresholds[metric] = {"warning": warning, "critical": critical}
        
        # Update config
        if metric == SystemMetricType.CPU:
            self.config["thresholds"]["cpu_warning"] = warning
            self.config["thresholds"]["cpu_critical"] = critical
        elif metric == SystemMetricType.MEMORY:
            self.config["thresholds"]["memory_warning"] = warning
            self.config["thresholds"]["memory_critical"] = critical
        elif metric == SystemMetricType.DISK:
            self.config["thresholds"]["disk_warning"] = warning
            self.config["thresholds"]["disk_critical"] = critical
        elif metric == SystemMetricType.TEMPERATURE:
            self.config["thresholds"]["temperature_warning"] = warning
            self.config["thresholds"]["temperature_critical"] = critical
        elif metric == SystemMetricType.BATTERY:
            self.config["thresholds"]["battery_warning"] = warning
            self.config["thresholds"]["battery_critical"] = critical
        
        self.save_config()
        logger.info(f"Thresholds updated for {metric.value}")
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            self.save_config()
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    # Create system utilities manager
    with SystemUtilitiesManager() as manager:
        
        # Start monitoring
        manager.start_monitoring(interval=5)
        
        # Get system info
        info = manager.get_system_info(detailed=True)
        print("System Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*50)
        
        # Get battery info
        battery = manager.get_battery_info()
        print("\nBattery Information:")
        for key, value in battery.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*50)
        
        # Get weather
        weather = manager.get_weather("New York")
        print(f"\nWeather: {weather}")
        
        # Test internet speed
        print("\nTesting internet speed...")
        speed = manager.test_internet_speed()
        if "error" not in speed:
            print(f"  Download: {speed['download_mbps']} Mbps")
            print(f"  Upload: {speed['upload_mbps']} Mbps")
            print(f"  Ping: {speed['ping_ms']} ms")
        
        # Ping test
        print("\nPinging google.com...")
        ping_result = manager.ping_host("google.com")
        if "error" not in ping_result:
            stats = ping_result.get("statistics", {})
            print(f"  Avg RTT: {stats.get('avg_ms', 'N/A')} ms")
            print(f"  Packet loss: {ping_result.get('packet_loss', 0)}%")
        
        # Get performance report after some time
        time.sleep(30)
        report = manager.get_performance_report()
        print("\nPerformance Report:")
        print(f"  Period: {report.get('period', {}).get('start')} to {report.get('period', {}).get('end')}")
        print(f"  Avg CPU: {report.get('averages', {}).get('cpu')}")
        print(f"  Avg Memory: {report.get('averages', {}).get('memory')}")
        print(f"  Peak CPU: {report.get('peaks', {}).get('cpu')}")
        print(f"  Alerts: {report.get('alerts', {}).get('total')}")
        
        # Clean up temp files
        cleanup = manager.cleanup_temp_files(days_old=30)
        print(f"\nCleanup: {cleanup.get('files_deleted', 0)} files deleted, {cleanup.get('space_freed_formatted', '0')} freed")