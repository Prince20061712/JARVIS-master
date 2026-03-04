"""
Enhanced Screen Capture Manager for macOS
Handles screenshots, screen recording, OCR, image processing, and more
"""

import datetime
import time
import os
import subprocess
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

import pyautogui
import pygetwindow as gw
import mss
import mss.tools
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import cv2
import pytesseract
from screeninfo import get_monitors
import Quartz
import AppKit
from Cocoa import NSWorkspace
from Quartz import CoreGraphics
import av
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaptureMode(Enum):
    """Capture modes for screenshots"""
    FULL_SCREEN = "full_screen"
    ACTIVE_WINDOW = "active_window"
    SELECTED_REGION = "selected_region"
    ALL_MONITORS = "all_monitors"
    SPECIFIC_MONITOR = "specific_monitor"
    CURSOR_ONLY = "cursor_only"
    MENU_BAR = "menu_bar"
    DOCK = "dock"


class ImageFormat(Enum):
    """Supported image formats"""
    PNG = "png"
    JPEG = "jpg"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"
    PDF = "pdf"


class RecordingFormat(Enum):
    """Supported recording formats"""
    MP4 = "mp4"
    GIF = "gif"
    MOV = "mov"
    AVI = "avi"
    WEBM = "webm"


class ImageEffect(Enum):
    """Image effects for processing"""
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    INVERT = "invert"
    BLUR = "blur"
    SHARPEN = "sharpen"
    EDGE_DETECT = "edge_detect"
    EMBOSS = "emboss"
    CONTOUR = "contour"
    THUMBNAIL = "thumbnail"
    WATERMARK = "watermark"


@dataclass
class CaptureResult:
    """Result of a capture operation"""
    success: bool
    file_path: Optional[Path]
    message: str
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    size: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenInfo:
    """Information about a screen/monitor"""
    id: int
    name: str
    width: int
    height: int
    left: int
    top: int
    is_primary: bool
    scale_factor: float


@dataclass
class WindowInfo:
    """Information about a window"""
    title: str
    handle: int
    left: int
    top: int
    width: int
    height: int
    is_active: bool
    is_minimized: bool
    process_name: Optional[str] = None
    bundle_id: Optional[str] = None


class ScreenshotError(Exception):
    """Custom exception for screenshot operations"""
    pass


class RecordingError(Exception):
    """Custom exception for recording operations"""
    pass


class ScreenCaptureManager:
    """
    Enhanced Screen Capture Manager with comprehensive features:
    - Multiple capture modes (full screen, window, region, monitors)
    - Screen recording with audio
    - OCR (text extraction from images)
    - Image processing and effects
    - Scheduled captures
    - Hotkey support
    - Cloud upload integration
    - Batch processing
    - Undo/redo functionality
    - Annotations and markup
    """
    
    def __init__(self, config_path: Optional[Path] = None, 
                 output_dir: Optional[Path] = None):
        """
        Initialize the Screen Capture Manager
        
        Args:
            config_path: Path to configuration file
            output_dir: Default output directory for captures
        """
        self.config_path = config_path or Path.home() / ".config" / "screen_capture.json"
        self.output_dir = output_dir or Path.home() / "Pictures" / "Captures"
        self.temp_dir = Path.home() / ".cache" / "screen_capture"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Capture state
        self.last_capture: Optional[CaptureResult] = None
        self.capture_history: List[CaptureResult] = []
        self.recording_in_progress = False
        self.recording_frames: List[np.ndarray] = []
        self.recording_start_time: Optional[float] = None
        self.recording_thread: Optional[threading.Thread] = None
        self.recording_queue: queue.Queue = queue.Queue()
        
        # Selected region state
        self.selection_start: Optional[Tuple[int, int]] = None
        self.selection_end: Optional[Tuple[int, int]] = None
        self.selection_active = False
        
        # Screen info
        self.screens = self._get_screen_info()
        self.active_window = None
        
        # Configuration
        self.default_format = ImageFormat.PNG
        self.default_quality = 95
        self.include_cursor = True
        self.auto_save = True
        self.max_history = 100
        self.hotkeys_enabled = False
        
        # OCR configuration
        self.ocr_language = 'eng'
        self.ocr_psm = 3  # Page segmentation mode
        
        # Load configuration
        self._load_config()
        
        # Initialize hotkey listener if enabled
        if self.hotkeys_enabled:
            self._init_hotkeys()
    
    def _get_screen_info(self) -> List[ScreenInfo]:
        """Get information about all connected screens"""
        screens = []
        
        try:
            # Get all monitors using screeninfo
            for i, monitor in enumerate(get_monitors()):
                screen = ScreenInfo(
                    id=i,
                    name=monitor.name or f"Screen {i+1}",
                    width=monitor.width,
                    height=monitor.height,
                    left=monitor.x,
                    top=monitor.y,
                    is_primary=monitor.is_primary,
                    scale_factor=1.0  # Default scale factor
                )
                screens.append(screen)
            
            # Try to get scale factor using CoreGraphics
            if screens:
                main_display_id = CoreGraphics.CGMainDisplayID()
                screen = screens[0]  # Primary screen
                
                # Get scale factor
                mode = CoreGraphics.CGDisplayCopyDisplayMode(main_display_id)
                if mode:
                    width = CoreGraphics.CGDisplayModeGetWidth(mode)
                    pixel_width = CoreGraphics.CGDisplayModeGetPixelWidth(mode)
                    screen.scale_factor = pixel_width / width if width > 0 else 1.0
        
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            
            # Fallback to pyautogui
            width, height = pyautogui.size()
            screens.append(ScreenInfo(
                id=0,
                name="Main Screen",
                width=width,
                height=height,
                left=0,
                top=0,
                is_primary=True,
                scale_factor=1.0
            ))
        
        return screens
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                    self.default_format = ImageFormat(config.get('default_format', 'png'))
                    self.default_quality = config.get('default_quality', 95)
                    self.include_cursor = config.get('include_cursor', True)
                    self.auto_save = config.get('auto_save', True)
                    self.max_history = config.get('max_history', 100)
                    self.hotkeys_enabled = config.get('hotkeys_enabled', False)
                    self.ocr_language = config.get('ocr_language', 'eng')
                    
                    # Output directory
                    output_dir = config.get('output_dir')
                    if output_dir:
                        self.output_dir = Path(output_dir)
                        self.output_dir.mkdir(parents=True, exist_ok=True)
                    
                    logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'default_format': self.default_format.value,
                'default_quality': self.default_quality,
                'include_cursor': self.include_cursor,
                'auto_save': self.auto_save,
                'max_history': self.max_history,
                'hotkeys_enabled': self.hotkeys_enabled,
                'ocr_language': self.ocr_language,
                'output_dir': str(self.output_dir)
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _init_hotkeys(self):
        """Initialize hotkey listeners (requires additional setup)"""
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    if key == keyboard.Key.f1:
                        # F1 for full screenshot
                        asyncio.create_task(self.take_screenshot_async(mode=CaptureMode.FULL_SCREEN))
                    elif key == keyboard.Key.f2:
                        # F2 for window screenshot
                        asyncio.create_task(self.take_screenshot_async(mode=CaptureMode.ACTIVE_WINDOW))
                    elif key == keyboard.Key.f3:
                        # F3 for region selection
                        self.start_region_selection()
                except AttributeError:
                    pass
            
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            logger.info("Hotkey listeners initialized")
        
        except ImportError:
            logger.warning("pynput not installed. Hotkeys disabled.")
            self.hotkeys_enabled = False
    
    def get_windows(self) -> List[WindowInfo]:
        """Get list of all windows"""
        windows = []
        
        try:
            # Get all windows using AppKit
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.frontmostApplication()
            
            for window in gw.getAllWindows():
                try:
                    window_info = WindowInfo(
                        title=window.title,
                        handle=window._hWnd,
                        left=window.left,
                        top=window.top,
                        width=window.width,
                        height=window.height,
                        is_active=window.isActive,
                        is_minimized=window.isMinimized
                    )
                    
                    # Try to get process name
                    if window_info.is_active and active_app:
                        window_info.process_name = active_app.localizedName()
                        window_info.bundle_id = active_app.bundleIdentifier()
                    
                    windows.append(window_info)
                except Exception as e:
                    logger.error(f"Error getting window info: {e}")
            
            # Sort by active window first, then by title
            windows.sort(key=lambda w: (not w.is_active, w.title))
        
        except Exception as e:
            logger.error(f"Error getting windows: {e}")
        
        return windows
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Get the currently active window"""
        windows = self.get_windows()
        for window in windows:
            if window.is_active and not window.is_minimized:
                return window
        return None
    
    def take_screenshot(self, mode: Union[str, CaptureMode] = CaptureMode.FULL_SCREEN,
                       output_path: Optional[Path] = None,
                       image_format: Union[str, ImageFormat] = ImageFormat.PNG,
                       quality: int = 95,
                       include_cursor: Optional[bool] = None,
                       apply_effects: Optional[List[Union[str, ImageEffect]]] = None,
                       metadata: Optional[Dict] = None) -> CaptureResult:
        """
        Take a screenshot with advanced options
        
        Args:
            mode: Capture mode
            output_path: Custom output path (auto-generated if None)
            image_format: Output image format
            quality: JPEG quality (1-100, only for JPEG)
            include_cursor: Include cursor in screenshot
            apply_effects: List of effects to apply
            metadata: Additional metadata to save
            
        Returns:
            CaptureResult object
        """
        result = CaptureResult(
            success=False,
            file_path=None,
            message="",
            metadata=metadata or {}
        )
        
        try:
            # Convert string mode to enum
            if isinstance(mode, str):
                mode = CaptureMode(mode)
            
            # Set options
            include_cursor = include_cursor if include_cursor is not None else self.include_cursor
            if isinstance(image_format, str):
                image_format = ImageFormat(image_format)
            
            # Generate output path if not provided
            if output_path is None:
                output_path = self._generate_filename(mode, image_format)
            
            # Capture based on mode
            if mode == CaptureMode.FULL_SCREEN:
                image = self._capture_full_screen(include_cursor)
                result.size = pyautogui.size()
            
            elif mode == CaptureMode.ACTIVE_WINDOW:
                image = self._capture_active_window(include_cursor)
                if image:
                    active_window = self.get_active_window()
                    if active_window:
                        result.size = (active_window.width, active_window.height)
            
            elif mode == CaptureMode.SELECTED_REGION:
                image = self._capture_selected_region(include_cursor)
                start = self.selection_start
                end = self.selection_end
                if image and start is not None and end is not None:
                    width = abs(end[0] - start[0])
                    height = abs(end[1] - start[1])
                    result.size = (width, height)
            
            elif mode == CaptureMode.ALL_MONITORS:
                # Capture all monitors and combine
                images = []
                total_width = 0
                max_height = 0
                
                with mss.mss() as sct:
                    for i, monitor in enumerate(sct.monitors[1:], 1):
                        screenshot = sct.grab(monitor)
                        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                        images.append(img)
                        total_width += monitor['width']
                        max_height = max(max_height, monitor['height'])
                    
                    # Combine images horizontally
                    combined = Image.new('RGB', (total_width, max_height))
                    x_offset = 0
                    for img in images:
                        combined.paste(img, (x_offset, 0))
                        x_offset += img.width
                    
                    image = combined
                    result.size = (total_width, max_height)
            
            elif mode == CaptureMode.SPECIFIC_MONITOR:
                # Capture specific monitor (need monitor ID in metadata)
                meta = metadata or {}
                monitor_id = int(meta.get('monitor_id', 0))
                image = self._capture_monitor(monitor_id, include_cursor)
                if image and monitor_id < len(self.screens):
                    screen = self.screens[monitor_id]
                    result.size = (screen.width, screen.height)
            
            elif mode == CaptureMode.CURSOR_ONLY:
                image = self._capture_cursor()
                result.size = (32, 32)  # Default cursor size
            
            elif mode == CaptureMode.MENU_BAR:
                image = self._capture_menu_bar()
                result.size = (self.screens[0].width, 30) if self.screens else None
            
            elif mode == CaptureMode.DOCK:
                image = self._capture_dock()
                result.size = (self.screens[0].width, 80) if self.screens else None
            
            else:
                raise ScreenshotError(f"Unsupported capture mode: {mode}")
            
            if image is None:
                raise ScreenshotError("Failed to capture image")
            
            # Apply effects if specified
            if apply_effects:
                image = self.apply_image_effects(image, apply_effects)
            
            # Save image
            self._save_image(image, output_path, image_format, quality)
            
            # Update result
            result.success = True
            result.file_path = output_path
            if isinstance(image_format, Enum):
                result.format = str(image_format.value)
            else:
                result.format = str(image_format)
            result.message = f"Screenshot saved to {output_path}"
            
            # Add to history
            self.last_capture = result
            self.capture_history.append(result)
            
            # Trim history
            if len(self.capture_history) > self.max_history:
                self.capture_history = self.capture_history[-self.max_history:] # type: ignore
            
            logger.info(result.message)
        
        except ScreenshotError as e:
            result.message = str(e)
            logger.error(f"Screenshot error: {e}")
        
        except Exception as e:
            result.message = f"Unexpected error: {e}"
            logger.exception("Unexpected error in take_screenshot")
        
        return result
    
    async def take_screenshot_async(self, **kwargs) -> CaptureResult:
        """Async version of take_screenshot"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.take_screenshot, **kwargs)
    
    def _capture_full_screen(self, include_cursor: bool = True) -> Optional[Image.Image]:
        """Capture full screen"""
        try:
            if include_cursor:
                return pyautogui.screenshot()
            else:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                    return Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")
            return None
    
    def _capture_active_window(self, include_cursor: bool = True) -> Optional[Image.Image]:
        """Capture active window"""
        try:
            active_window = self.get_active_window()
            if not active_window:
                raise ScreenshotError("No active window found")
            
            region = (
                active_window.left,
                active_window.top,
                active_window.width,
                active_window.height
            )
            
            return pyautogui.screenshot(region=region)
        
        except Exception as e:
            logger.error(f"Error capturing active window: {e}")
            return None
    
    def _capture_monitor(self, monitor_id: int, include_cursor: bool = True) -> Optional[Image.Image]:
        """Capture specific monitor"""
        try:
            with mss.mss() as sct:
                if monitor_id < len(sct.monitors):
                    monitor = sct.monitors[monitor_id + 1]  # mss monitors start at 1
                    sct_img = sct.grab(monitor)
                    return Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                else:
                    raise ScreenshotError(f"Monitor {monitor_id} not found")
        except Exception as e:
            logger.error(f"Error capturing monitor {monitor_id}: {e}")
            return None
    
    def _capture_selected_region(self, include_cursor: bool = True) -> Optional[Image.Image]:
        """Capture selected region"""
        try:
            start = self.selection_start
            end = self.selection_end
            if start is None or end is None:
                # If no region selected, start interactive selection
                self.start_region_selection()
                return None
            
            x1, y1 = start
            x2, y2 = end
            
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            if width == 0 or height == 0:
                raise ScreenshotError("Invalid region size")
            
            region = (left, top, width, height)
            return pyautogui.screenshot(region=region)
        
        except Exception as e:
            logger.error(f"Error capturing region: {e}")
            return None
    
    def _capture_cursor(self) -> Optional[Image.Image]:
        """Capture only the cursor"""
        try:
            # Get cursor position and image
            x, y = pyautogui.position()
            
            # Create a small image with cursor
            # This is a simplified version - actual cursor capture is complex
            img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            
            # Draw a simple cursor arrow
            draw = ImageDraw.Draw(img)
            draw.polygon([(0, 0), (20, 0), (0, 20)], fill=(255, 255, 255))
            
            return img
        
        except Exception as e:
            logger.error(f"Error capturing cursor: {e}")
            return None
    
    def _capture_menu_bar(self) -> Optional[Image.Image]:
        """Capture the menu bar"""
        try:
            screen = self.screens[0]  # Menu bar is on primary screen
            region = (0, 0, screen.width, 30)  # Menu bar height is typically 30px
            return pyautogui.screenshot(region=region)
        
        except Exception as e:
            logger.error(f"Error capturing menu bar: {e}")
            return None
    
    def _capture_dock(self) -> Optional[Image.Image]:
        """Capture the Dock"""
        try:
            screen = self.screens[0]
            # Dock is typically at bottom of screen
            dock_height = 80
            region = (0, screen.height - dock_height, screen.width, dock_height)
            return pyautogui.screenshot(region=region)
        
        except Exception as e:
            logger.error(f"Error capturing dock: {e}")
            return None
    
    def start_region_selection(self):
        """Start interactive region selection"""
        self.selection_active = True
        self.selection_start = None
        self.selection_end = None
        
        # Show selection overlay
        self._show_selection_overlay()
    
    def _show_selection_overlay(self):
        """Show a transparent overlay for region selection"""
        # This would typically use a GUI framework like PyQt or Tkinter
        # For now, we'll log that selection is active
        logger.info("Region selection active - click and drag to select area")
        
        # In a real implementation, you would:
        # 1. Create a full-screen transparent window
        # 2. Track mouse events
        # 3. Draw selection rectangle
        # 4. Capture on mouse release
    
    def _generate_filename(self, mode: CaptureMode, format: ImageFormat) -> Path:
        """Generate a filename for the screenshot"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        mode_names = {
            CaptureMode.FULL_SCREEN: "full",
            CaptureMode.ACTIVE_WINDOW: "window",
            CaptureMode.SELECTED_REGION: "region",
            CaptureMode.ALL_MONITORS: "all",
            CaptureMode.SPECIFIC_MONITOR: "monitor",
            CaptureMode.CURSOR_ONLY: "cursor",
            CaptureMode.MENU_BAR: "menubar",
            CaptureMode.DOCK: "dock"
        }
        
        mode_name = mode_names.get(mode, "capture")
        filename = f"screenshot_{mode_name}_{timestamp}.{format.value}"
        
        return self.output_dir / filename
    
    def _save_image(self, image: Image.Image, path: Path, 
                    format: ImageFormat, quality: int):
        """Save image to file"""
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert format for PIL
            pil_format = {
                ImageFormat.PNG: 'PNG',
                ImageFormat.JPEG: 'JPEG',
                ImageFormat.GIF: 'GIF',
                ImageFormat.BMP: 'BMP',
                ImageFormat.TIFF: 'TIFF',
                ImageFormat.WEBP: 'WEBP',
                ImageFormat.PDF: 'PDF'
            }.get(format, 'PNG')
            
            # Save with appropriate options
            if format == ImageFormat.JPEG:
                image.save(path, pil_format, quality=quality, optimize=True)
            elif format == ImageFormat.PNG:
                image.save(path, pil_format, optimize=True)
            else:
                image.save(path, pil_format)
        
        except Exception as e:
            raise ScreenshotError(f"Failed to save image: {e}")
    
    def apply_image_effects(self, image: Image.Image, 
                           effects: List[Union[str, ImageEffect]]) -> Image.Image:
        """Apply multiple effects to an image"""
        result = image.copy()
        
        for effect in effects:
            if isinstance(effect, str):
                effect = ImageEffect(effect)
            
            if effect == ImageEffect.GRAYSCALE:
                result = result.convert('L')
            
            elif effect == ImageEffect.SEPIA:
                result = self._apply_sepia(result)
            
            elif effect == ImageEffect.INVERT:
                if result.mode == 'RGBA':
                    r, g, b, a = result.split()
                    rgb_image = Image.merge('RGB', (r, g, b))
                    inverted = Image.eval(rgb_image, lambda x: 255 - x)
                    r, g, b = inverted.split()
                    result = Image.merge('RGBA', (r, g, b, a))
                else:
                    result = Image.eval(result, lambda x: 255 - x)
            
            elif effect == ImageEffect.BLUR:
                result = result.filter(ImageFilter.GaussianBlur(radius=2))
            
            elif effect == ImageEffect.SHARPEN:
                result = result.filter(ImageFilter.SHARPEN)
            
            elif effect == ImageEffect.EDGE_DETECT:
                result = result.filter(ImageFilter.FIND_EDGES)
            
            elif effect == ImageEffect.EMBOSS:
                result = result.filter(ImageFilter.EMBOSS)
            
            elif effect == ImageEffect.CONTOUR:
                result = result.filter(ImageFilter.CONTOUR)
            
            elif effect == ImageEffect.THUMBNAIL:
                result.thumbnail((800, 600))
            
            elif effect == ImageEffect.WATERMARK:
                result = self._add_watermark(result)
        
        return result
    
    def _apply_sepia(self, image: Image.Image) -> Image.Image:
        """Apply sepia tone effect"""
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        width, height = image.size
        pixels = image.load()
        
        for py in range(height):
            for px in range(width):
                r, g, b = image.getpixel((px, py))
                
                # Calculate sepia values
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                # Clamp values
                pixels[px, py] = (
                    min(255, tr),
                    min(255, tg),
                    min(255, tb)
                )
        
        return image
    
    def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to image"""
        result = image.copy()
        draw = ImageDraw.Draw(result)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            font = ImageFont.load_default()
        
        # Add timestamp watermark
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get text size
        bbox = draw.textbbox((0, 0), timestamp, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position in bottom right corner
        x = result.width - text_width - 10
        y = result.height - text_height - 10
        
        # Draw semi-transparent background
        draw.rectangle(
            [x-5, y-5, x+text_width+5, y+text_height+5],
            fill=(0, 0, 0, 128)
        )
        
        # Draw text
        draw.text((x, y), timestamp, fill=(255, 255, 255), font=font)
        
        return result
    
    def start_recording(self, mode: CaptureMode = CaptureMode.FULL_SCREEN,
                       output_path: Optional[Path] = None,
                       format: Union[str, RecordingFormat] = RecordingFormat.MP4,
                       fps: int = 30,
                       with_audio: bool = False,
                       max_duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Start screen recording
        
        Args:
            mode: Capture mode
            output_path: Output file path
            format: Recording format
            fps: Frames per second
            with_audio: Include audio in recording
            max_duration: Maximum duration in seconds (None for unlimited)
            
        Returns:
            Dictionary with recording info
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "recording_id": None,
            "output_path": None
        }
        
        try:
            if self.recording_in_progress:
                raise RecordingError("Recording already in progress")
            
            if isinstance(format, str):
                format = RecordingFormat(format)
            
            # Generate output path if not provided
            if output_path is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.{format.value}"
                output_path = self.output_dir / filename
            
            # Prepare recording
            self.recording_in_progress = True
            self.recording_frames = []
            self.recording_start_time = time.time()
            
            # Get screen dimensions
            if mode == CaptureMode.FULL_SCREEN:
                width, height = pyautogui.size()
            elif mode == CaptureMode.ACTIVE_WINDOW:
                active_window = self.get_active_window()
                if active_window:
                    width, height = active_window.width, active_window.height
                else:
                    width, height = pyautogui.size()
            else:
                width, height = pyautogui.size()
            
            # Start recording in a separate thread
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                args=(mode, output_path, format, fps, width, height, with_audio, max_duration)
            )
            if self.recording_thread is not None:
                self.recording_thread.start()
            
            result["success"] = True
            result["message"] = f"Recording started: {output_path}"
            result["recording_id"] = id(self.recording_thread)
            result["output_path"] = str(output_path)
            
            logger.info(result["message"])
        
        except RecordingError as e:
            result["message"] = str(e)
            logger.error(f"Recording error: {e}")
        
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            logger.exception("Error starting recording")
        
        return result
    
    def _recording_worker(self, mode: CaptureMode, output_path: Path,
                          format: RecordingFormat, fps: int,
                          width: int, height: int, with_audio: bool,
                          max_duration: Optional[int]):
        """Worker thread for recording"""
        try:
            frame_interval = 1.0 / fps
            frames_written = 0
            
            # Use PyAV for video encoding
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            container = av.open(str(output_path), 'w')
            stream = container.add_stream('libx264', rate=fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = 'yuv420p'
            
            while self.recording_in_progress:
                frame_start = time.time()
                
                # Capture frame
                if mode == CaptureMode.FULL_SCREEN:
                    screenshot = pyautogui.screenshot()
                elif mode == CaptureMode.ACTIVE_WINDOW:
                    active_window = self.get_active_window()
                    if active_window:
                        region = (active_window.left, active_window.top,
                                 active_window.width, active_window.height)
                        screenshot = pyautogui.screenshot(region=region)
                    else:
                        screenshot = pyautogui.screenshot()
                else:
                    screenshot = pyautogui.screenshot()
                
                # Convert to numpy array
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Encode frame
                av_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
                for packet in stream.encode(av_frame):
                    container.mux(packet)
                
                frames_written += 1
                
                # Check duration
                if max_duration is not None and self.recording_start_time is not None:
                    elapsed = float(time.time() - self.recording_start_time)
                    if elapsed >= float(max_duration):
                        self.stop_recording()
                        break
                
                # Maintain frame rate
                elapsed_frame = float(time.time() - frame_start)
                sleep_time = float(max(0.0, float(frame_interval) - elapsed_frame))
                time.sleep(sleep_time)
            
            # Flush encoder
            for packet in stream.encode():
                container.mux(packet)
            
            container.close()
            
            logger.info(f"Recording finished: {frames_written} frames, saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Recording worker error: {e}")
    
    def stop_recording(self) -> Dict[str, Any]:
        """Stop the current recording"""
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "duration": None,
            "frame_count": None,
            "output_path": None
        }
        
        try:
            if not self.recording_in_progress:
                raise RecordingError("No recording in progress")
            
            self.recording_in_progress = False
            
            if self.recording_thread is not None:
                self.recording_thread.join(timeout=10)
            
            duration = float(time.time() - self.recording_start_time) if self.recording_start_time is not None else 0.0
            
            result["success"] = True
            result["message"] = "Recording stopped"
            result["duration"] = duration
            result["frame_count"] = len(self.recording_frames)
            
            logger.info(f"Recording stopped. Duration: {duration:.2f}s")
        
        except RecordingError as e:
            result["message"] = str(e)
            logger.error(f"Recording error: {e}")
        
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            logger.exception("Error stopping recording")
        
        return result
    
    def extract_text(self, image_path: Optional[Path] = None,
                    image: Optional[Image.Image] = None,
                    language: Optional[str] = None,
                    psm: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image_path: Path to image file
            image: PIL Image object
            language: OCR language (default: eng)
            psm: Page segmentation mode
            
        Returns:
            Dictionary with extracted text and metadata
        """
        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "text": "",
            "confidence": 0.0,
            "words": []
        }
        
        try:
            # Load image
            if image_path:
                img = Image.open(image_path)
            elif image:
                img = image
            else:
                raise ScreenshotError("No image provided")
            
            # Preprocess image for better OCR
            img = img.convert('L')  # Grayscale
            img = img.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Set OCR options
            lang = language or self.ocr_language
            custom_config = f'--psm {psm or self.ocr_psm} -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,;:!?()[]{{}}@#$%^&*_+-= '
            
            # Extract text
            text = pytesseract.image_to_string(img, lang=lang, config=custom_config)
            
            # Get confidence data
            data = pytesseract.image_to_data(img, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
            
            words: List[Dict[str, Any]] = []
            confidences: List[float] = []
            for i in range(len(data['text'])):
                conf_val = float(data['conf'][i])
                if conf_val > 0:  # Filter out low confidence
                    words.append({
                        'text': str(data['text'][i]),
                        'confidence': conf_val,
                        'bbox': (
                            int(data['left'][i]),
                            int(data['top'][i]),
                            int(data['width'][i]),
                            int(data['height'][i])
                        )
                    })
                    confidences.append(conf_val)
            
            # Calculate average confidence
            avg_confidence = float(sum(confidences)) / len(confidences) if confidences else 0.0
            
            result["success"] = True
            result["text"] = text.strip()
            result["confidence"] = avg_confidence
            result["words"] = words
            result["message"] = f"Extracted {len(words)} words with {avg_confidence:.1f}% confidence"
            
            logger.info(result["message"])
        
        except Exception as e:
            result["message"] = f"OCR error: {e}"
            logger.error(f"OCR error: {e}")
        
        return result
    
    def find_text_on_screen(self, text: str, case_sensitive: bool = False,
                           region: Optional[Tuple[int, int, int, int]] = None) -> List[Dict]:
        """
        Find text on screen using OCR
        
        Args:
            text: Text to search for
            case_sensitive: Case sensitive search
            region: Screen region to search (left, top, width, height)
            
        Returns:
            List of matches with positions
        """
        matches = []
        
        try:
            # Capture screen region
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Extract text with positions
            data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            search_text = text if case_sensitive else text.lower()
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    compare_word = word if case_sensitive else word.lower()
                    if search_text in compare_word:
                        matches.append({
                            'text': word,
                            'confidence': float(data['conf'][i]),
                            'bbox': (
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            )
                        })
        
        except Exception as e:
            logger.error(f"Error finding text on screen: {e}")
        
        return matches
    
    def add_annotation(self, image_path: Path, annotations: List[Dict],
                      output_path: Optional[Path] = None) -> CaptureResult:
        """
        Add annotations to an image
        
        Args:
            image_path: Path to source image
            annotations: List of annotation dictionaries with type and coordinates
            output_path: Output path for annotated image
            
        Returns:
            CaptureResult object
        """
        result = CaptureResult(
            success=False,
            file_path=None,
            message=""
        )
        
        try:
            # Load image
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img, 'RGBA')
            
            # Try to load a font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            except:
                font = ImageFont.load_default()
            
            # Apply annotations
            for ann in annotations:
                ann_type = ann.get('type', 'rectangle')
                
                if ann_type == 'rectangle':
                    # Draw rectangle
                    x1, y1, x2, y2 = ann['bbox']
                    color = ann.get('color', (255, 0, 0, 128))
                    width = ann.get('width', 2)
                    
                    for i in range(width):
                        draw.rectangle(
                            [x1+i, y1+i, x2-i, y2-i],
                            outline=color[:3],
                            width=1
                        )
                
                elif ann_type == 'circle':
                    # Draw circle
                    x, y, radius = ann['center'][0], ann['center'][1], ann['radius']
                    color = ann.get('color', (0, 255, 0, 128))
                    
                    draw.ellipse(
                        [x-radius, y-radius, x+radius, y+radius],
                        outline=color[:3],
                        width=2
                    )
                
                elif ann_type == 'text':
                    # Add text
                    x, y = ann['position']
                    text = ann['text']
                    color = ann.get('color', (255, 255, 255, 255))
                    
                    # Add background for better visibility
                    bbox = draw.textbbox((x, y), text, font=font)
                    draw.rectangle(
                        [bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2],
                        fill=(0, 0, 0, 128)
                    )
                    
                    draw.text((x, y), text, fill=color, font=font)
                
                elif ann_type == 'arrow':
                    # Draw arrow
                    start = ann['start']
                    end = ann['end']
                    color = ann.get('color', (0, 0, 255, 255))
                    
                    draw.line([start, end], fill=color, width=3)
                    
                    # Draw arrowhead
                    angle = np.arctan2(end[1]-start[1], end[0]-start[0])
                    arrow_length = 10
                    
                    arrow1 = (
                        end[0] - arrow_length * np.cos(angle - np.pi/6),
                        end[1] - arrow_length * np.sin(angle - np.pi/6)
                    )
                    arrow2 = (
                        end[0] - arrow_length * np.cos(angle + np.pi/6),
                        end[1] - arrow_length * np.sin(angle + np.pi/6)
                    )
                    
                    draw.line([end, arrow1], fill=color, width=2)
                    draw.line([end, arrow2], fill=color, width=2)
            
            # Save annotated image
            if output_path is None:
                output_path = image_path.parent / f"annotated_{image_path.name}"
            
            img.save(output_path)
            
            result.success = True
            result.file_path = output_path
            result.message = f"Annotations added to {output_path}"
        
        except Exception as e:
            result.message = f"Error adding annotations: {e}"
            logger.exception("Annotation error")
        
        return result
    
    def schedule_capture(self, interval: int, count: Optional[int] = None,
                        mode: CaptureMode = CaptureMode.FULL_SCREEN,
                        until: Optional[datetime.datetime] = None) -> str:
        """
        Schedule periodic captures
        
        Args:
            interval: Interval between captures in seconds
            count: Number of captures (None for unlimited)
            mode: Capture mode
            until: Stop at this datetime
            
        Returns:
            Schedule ID
        """
        schedule_id = self._generate_id()
        
        def capture_job():
            nonlocal count
            while True:
                if count is not None and count <= 0:
                    break
                if until and datetime.datetime.now() >= until:
                    break
                
                self.take_screenshot(mode=mode)
                
                if count is not None:
                    count -= 1
                
                time.sleep(interval)
        
        thread = threading.Thread(target=capture_job, daemon=True)
        thread.start()
        
        logger.info(f"Scheduled capture started with ID: {schedule_id}")
        
        return schedule_id
    
    def get_capture_history(self, limit: int = 10) -> List[CaptureResult]:
        """Get recent capture history"""
        return self.capture_history[-limit:] # type: ignore
    
    def undo_last_capture(self) -> Optional[CaptureResult]:
        """Undo/delete last capture"""
        if self.capture_history:
            last = self.capture_history.pop()
            if last.file_path and last.file_path.exists():
                last.file_path.unlink()
                logger.info(f"Deleted last capture: {last.file_path}")
            return last
        return None
    
    def upload_to_cloud(self, file_path: Path, service: str = "dropbox") -> Dict[str, Any]:
        """
        Upload capture to cloud storage
        
        Args:
            file_path: Path to file to upload
            service: Cloud service name
            
        Returns:
            Dictionary with upload result
        """
        result = {"success": False, "message": ""}
        
        try:
            if service.lower() == "dropbox":
                # Dropbox upload (requires dropbox SDK)
                try:
                    import dropbox
                    # This would require configured credentials
                    result["message"] = "Dropbox upload not configured"
                except ImportError:
                    result["message"] = "Dropbox SDK not installed"
            
            elif service.lower() == "google_drive":
                # Google Drive upload
                result["message"] = "Google Drive upload not configured"
            
            elif service.lower() == "icloud":
                # iCloud upload
                # On macOS, we can copy to iCloud Drive
                icloud_path = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"
                if icloud_path.exists():
                    dest = icloud_path / file_path.name
                    import shutil
                    shutil.copy2(file_path, dest)
                    result["success"] = True
                    result["message"] = f"Uploaded to iCloud Drive: {dest}"
                else:
                    result["message"] = "iCloud Drive not available"
            
            else:
                result["message"] = f"Unknown cloud service: {service}"
        
        except Exception as e:
            result["message"] = f"Upload error: {e}"
        
        return result
    
    def batch_process(self, input_dir: Path, output_dir: Path,
                     effect: ImageEffect, pattern: str = "*.png") -> List[CaptureResult]:
        """
        Batch process multiple images
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            effect: Effect to apply
            pattern: File pattern to match
            
        Returns:
            List of results
        """
        results = []
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for input_path in input_dir.glob(pattern):
                try:
                    # Load image
                    img = Image.open(input_path)
                    
                    # Apply effect
                    processed = self.apply_image_effects(img, [effect])
                    
                    # Save
                    output_path = output_dir / input_path.name
                    processed.save(output_path)
                    
                    results.append(CaptureResult(
                        success=True,
                        file_path=output_path,
                        message=f"Processed {input_path.name}"
                    ))
                
                except Exception as e:
                    results.append(CaptureResult(
                        success=False,
                        file_path=None,
                        message=f"Failed to process {input_path.name}: {e}"
                    ))
        
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
        
        return results
    
    def compare_images(self, image1_path: Path, image2_path: Path) -> Dict[str, Any]:
        """
        Compare two images and highlight differences
        
        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            
        Returns:
            Dictionary with comparison results
        """
        result = {
            "success": False,
            "message": "",
            "diff_score": 0.0,
            "diff_image": None,
            "identical": False
        }
        
        try:
            # Load images
            img1 = Image.open(image1_path).convert('RGB')
            img2 = Image.open(image2_path).convert('RGB')
            
            # Resize if dimensions differ
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            
            # Convert to numpy arrays
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Calculate difference
            diff = cv2.absdiff(arr1, arr2)
            
            # Calculate diff score (mean squared error)
            mse = np.mean((arr1 - arr2) ** 2)
            diff_score = 100 - (mse / (255 * 255)) * 100
            
            # Create diff image
            diff_img = Image.fromarray(diff)
            
            # Save diff image
            diff_path = self.output_dir / f"diff_{image1_path.stem}_{image2_path.stem}.png"
            diff_img.save(diff_path)
            
            result["success"] = True
            result["diff_score"] = diff_score
            result["diff_image"] = str(diff_path)
            result["identical"] = diff_score == 100
            result["message"] = f"Diff score: {diff_score:.2f}%"
        
        except Exception as e:
            result["message"] = f"Error comparing images: {e}"
            logger.error(f"Image comparison error: {e}")
        
        return result
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import hashlib
        import time
        return hashlib.md5(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:16]
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information related to screen capture"""
        info = {
            "screens": [
                {
                    "id": s.id,
                    "name": s.name,
                    "resolution": f"{s.width}x{s.height}",
                    "primary": s.is_primary,
                    "scale_factor": s.scale_factor
                }
                for s in self.screens
            ],
            "total_screens": len(self.screens),
            "default_output": str(self.output_dir),
            "default_format": self.default_format.value,
            "hotkeys_enabled": self.hotkeys_enabled,
            "total_captures": len(self.capture_history),
            "last_capture": str(self.last_capture.file_path) if self.last_capture else None,
            "recording_in_progress": self.recording_in_progress
        }
        
        return info
    
    def configure(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self._save_config()
        logger.info("Configuration updated")


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import pprint
    
    manager = ScreenCaptureManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "screenshot":
            mode = sys.argv[2] if len(sys.argv) > 2 else "full_screen"
            result = manager.take_screenshot(mode=mode)
            print(result.message)
        
        elif command == "record":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            result = manager.start_recording(max_duration=duration)
            print(result["message"])
            time.sleep(duration)
            result = manager.stop_recording()
            print(result["message"])
        
        elif command == "windows":
            windows = manager.get_windows()
            for w in windows[:10]:
                print(f"{w.title}: {w.width}x{w.height}")
        
        elif command == "ocr" and len(sys.argv) > 2:
            result = manager.extract_text(image_path=Path(sys.argv[2]))
            print(f"Text: {result['text']}")
            print(f"Confidence: {result['confidence']:.1f}%")
        
        elif command == "find" and len(sys.argv) > 2:
            matches = manager.find_text_on_screen(sys.argv[2])
            for m in matches:
                print(f"Found '{m['text']}' at {m['bbox']}")
        
        elif command == "info":
            info = manager.get_system_info()
            pprint.pprint(info)
        
        else:
            print("Usage: screen_manager.py [screenshot|record|windows|ocr|find|info] [args]")
    else:
        # Demo mode
        print("Screen Capture Manager Demo")
        print("-" * 50)
        
        # Get system info
        print("\nSystem Info:")
        info = manager.get_system_info()
        for screen in info['screens']:
            print(f"  {screen['name']}: {screen['resolution']}")
        
        # Take a test screenshot
        print("\nTaking screenshot...")
        result = manager.take_screenshot()
        print(f"  {result.message}")
        
        # Get windows
        print("\nActive windows:")
        windows = manager.get_windows()
        for w in windows[:5]:
            print(f"  {w.title[:50]}...")