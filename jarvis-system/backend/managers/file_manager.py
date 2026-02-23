"""
Enhanced File Manager for macOS
Handles comprehensive file operations with safety features, monitoring, and advanced utilities
"""

import os
import shutil
import hashlib
import json
import logging
import stat
import time
import magic
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch
import zipfile
import tarfile
import gzip
import bz2
import pickle
import csv
import sqlite3
import plistlib
import pyperclip
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import humanize
import send2trash
import filecmp
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """File type categories"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    CODE = "code"
    CONFIG = "config"
    DATABASE = "database"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class FilePermission(Enum):
    """File permission types"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    READ_WRITE = "read_write"
    READ_EXECUTE = "read_execute"
    ALL = "all"
    NONE = "none"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    MERGE = "merge"
    PROMPT = "prompt"


class SortOrder(Enum):
    """Sort order for file listings"""
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    SIZE_ASC = "size_asc"
    SIZE_DESC = "size_desc"
    DATE_ASC = "date_asc"
    DATE_DESC = "date_desc"
    TYPE_ASC = "type_asc"
    TYPE_DESC = "type_desc"


@dataclass
class FileInfo:
    """Comprehensive file information"""
    path: Path
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime
    accessed: datetime
    is_file: bool
    is_dir: bool
    is_link: bool
    is_hidden: bool
    permissions: str
    owner: Optional[str] = None
    group: Optional[str] = None
    file_type: FileType = FileType.UNKNOWN
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    """Result of a file operation"""
    success: bool
    message: str
    source: Optional[Path] = None
    destination: Optional[Path] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    items_processed: int = 0
    items_failed: int = 0
    bytes_transferred: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileMonitorHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, callback):
        self.callback = callback
    
    def on_any_event(self, event):
        """Handle any file system event"""
        if not event.is_directory:
            self.callback({
                'type': event.event_type,
                'src_path': event.src_path,
                'dest_path': getattr(event, 'dest_path', None),
                'timestamp': datetime.now().isoformat()
            })


class FileManager:
    """
    Enhanced File Manager with comprehensive features:
    - Advanced file operations (copy, move, delete, rename)
    - File searching and filtering
    - Batch operations with progress tracking
    - File monitoring and watching
    - Compression and archiving
    - File type detection and analysis
    - Safe operations (trash, backup, versioning)
    - Metadata management
    - File synchronization
    - Permission management
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None,
                 enable_trash: bool = True,
                 enable_backup: bool = False,
                 max_history: int = 100):
        """
        Initialize the File Manager
        
        Args:
            workspace_dir: Default working directory
            enable_trash: Use trash instead of permanent delete
            enable_backup: Create backups before modifications
            max_history: Maximum number of operations to keep in history
        """
        self.workspace_dir = Path(workspace_dir).absolute() if workspace_dir else Path.cwd()
        self.enable_trash = enable_trash
        self.enable_backup = enable_backup
        self.max_history = max_history
        
        # Operation history
        self.operation_history: List[OperationResult] = []
        
        # File watchers
        self.watchers: Dict[str, Observer] = {}
        
        # Temporary directory for operations
        self.temp_dir = Path.home() / ".cache" / "file_manager"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize mimetypes
        mimetypes.init()
        
        logger.info(f"File Manager initialized with workspace: {self.workspace_dir}")
    
    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve and validate path"""
        if isinstance(path, str):
            path = Path(path)
        
        if not path.is_absolute():
            path = self.workspace_dir / path
        
        return path.resolve()
    
    def _get_file_info(self, path: Path) -> Optional[FileInfo]:
        """Get comprehensive file information"""
        try:
            stat_info = path.stat()
            
            # Determine file type
            file_type = self._detect_file_type(path)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type:
                try:
                    mime_type = magic.from_file(str(path), mime=True)
                except:
                    pass
            
            # Get owner and group (macOS)
            import pwd
            import grp
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except:
                owner = str(stat_info.st_uid)
                group = str(stat_info.st_gid)
            
            return FileInfo(
                path=path,
                name=path.name,
                extension=path.suffix.lower(),
                size=stat_info.st_size,
                created=datetime.fromtimestamp(stat_info.st_birthtime),
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                accessed=datetime.fromtimestamp(stat_info.st_atime),
                is_file=path.is_file(),
                is_dir=path.is_dir(),
                is_link=path.is_symlink(),
                is_hidden=path.name.startswith('.'),
                permissions=stat.filemode(stat_info.st_mode),
                owner=owner,
                group=group,
                file_type=file_type,
                mime_type=mime_type
            )
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return None
    
    def _detect_file_type(self, path: Path) -> FileType:
        """Detect file type based on extension and content"""
        if path.is_dir():
            return FileType.UNKNOWN
        
        ext = path.suffix.lower()
        
        # Text files
        if ext in ['.txt', '.rtf', '.md', '.markdown']:
            return FileType.TEXT
        
        # Images
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico']:
            return FileType.IMAGE
        
        # Audio
        if ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma']:
            return FileType.AUDIO
        
        # Video
        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return FileType.VIDEO
        
        # Documents
        if ext in ['.pdf', '.epub', '.mobi']:
            return FileType.DOCUMENT
        
        # Office documents
        if ext in ['.doc', '.docx', '.odt']:
            return FileType.DOCUMENT
        if ext in ['.xls', '.xlsx', '.ods', '.csv']:
            return FileType.SPREADSHEET
        if ext in ['.ppt', '.pptx', '.odp']:
            return FileType.PRESENTATION
        
        # Archives
        if ext in ['.zip', '.tar', '.gz', '.bz2', '.7z', '.rar']:
            return FileType.ARCHIVE
        
        # Executables
        if ext in ['.exe', '.app', '.dmg', '.pkg'] or os.access(path, os.X_OK):
            return FileType.EXECUTABLE
        
        # Code files
        if ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', 
                  '.swift', '.go', '.rs', '.php', '.rb', '.pl', '.sh', '.bat']:
            return FileType.CODE
        
        # Config files
        if ext in ['.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', 
                  '.plist', '.properties']:
            return FileType.CONFIG
        
        # Database files
        if ext in ['.db', '.sqlite', '.sqlite3']:
            return FileType.DATABASE
        
        return FileType.UNKNOWN
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        return humanize.naturalsize(size)
    
    def _generate_checksum(self, file_path: Path, algorithm: str = 'md5') -> Optional[str]:
        """Generate checksum for file"""
        try:
            hash_func = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error generating checksum for {file_path}: {e}")
            return None
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of a file before modification"""
        if not self.enable_backup:
            return None
        
        try:
            backup_dir = file_path.parent / '.backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{file_path.name}.{timestamp}.bak"
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            return backup_path
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def _add_to_history(self, result: OperationResult):
        """Add operation to history"""
        self.operation_history.append(result)
        if len(self.operation_history) > self.max_history:
            self.operation_history.pop(0)
    
    def list_directory(self, path: Union[str, Path] = ".",
                      pattern: Optional[str] = None,
                      include_hidden: bool = False,
                      include_dirs: bool = True,
                      include_files: bool = True,
                      sort_by: SortOrder = SortOrder.NAME_ASC,
                      max_results: Optional[int] = None) -> OperationResult:
        """
        List contents of a directory with filtering and sorting
        
        Args:
            path: Directory path
            pattern: File pattern to match (e.g., "*.txt")
            include_hidden: Include hidden files
            include_dirs: Include directories
            include_files: Include files
            sort_by: Sort order
            max_results: Maximum number of results
            
        Returns:
            OperationResult with list of files
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"Path does not exist: {target_path}")
            
            if not target_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {target_path}")
            
            items = []
            
            for item_path in target_path.iterdir():
                # Apply filters
                if not include_hidden and item_path.name.startswith('.'):
                    continue
                
                if item_path.is_dir() and not include_dirs:
                    continue
                
                if item_path.is_file() and not include_files:
                    continue
                
                if pattern and not fnmatch.fnmatch(item_path.name, pattern):
                    continue
                
                file_info = self._get_file_info(item_path)
                if file_info:
                    items.append(file_info)
            
            # Sort items
            if sort_by == SortOrder.NAME_ASC:
                items.sort(key=lambda x: x.name.lower())
            elif sort_by == SortOrder.NAME_DESC:
                items.sort(key=lambda x: x.name.lower(), reverse=True)
            elif sort_by == SortOrder.SIZE_ASC:
                items.sort(key=lambda x: x.size)
            elif sort_by == SortOrder.SIZE_DESC:
                items.sort(key=lambda x: x.size, reverse=True)
            elif sort_by == SortOrder.DATE_ASC:
                items.sort(key=lambda x: x.modified)
            elif sort_by == SortOrder.DATE_DESC:
                items.sort(key=lambda x: x.modified, reverse=True)
            elif sort_by == SortOrder.TYPE_ASC:
                items.sort(key=lambda x: (x.file_type.value, x.name.lower()))
            elif sort_by == SortOrder.TYPE_DESC:
                items.sort(key=lambda x: (x.file_type.value, x.name.lower()), reverse=True)
            
            # Limit results
            if max_results:
                items = items[:max_results]
            
            # Format output
            file_list = []
            for item in items:
                size_str = self._format_size(item.size) if item.is_file else "<DIR>"
                file_list.append({
                    'name': item.name,
                    'type': 'dir' if item.is_dir else 'file',
                    'size': size_str,
                    'modified': item.modified.isoformat(),
                    'hidden': item.is_hidden,
                    'extension': item.extension,
                    'file_type': item.file_type.value
                })
            
            result.success = True
            result.message = f"Found {len(items)} items in {target_path}"
            result.metadata['items'] = file_list
            result.metadata['total'] = len(items)
            result.metadata['path'] = str(target_path)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Directory listing error: {e}")
        except NotADirectoryError as e:
            result.message = str(e)
            logger.error(f"Directory listing error: {e}")
        except Exception as e:
            result.message = f"Error listing directory: {e}"
            logger.exception("Directory listing error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def create_file(self, file_path: Union[str, Path],
                   content: str = "",
                   overwrite: bool = False) -> OperationResult:
        """
        Create a new file with optional content
        
        Args:
            file_path: Path for the new file
            content: Initial content
            overwrite: Overwrite if exists
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            if target_path.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {target_path}")
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result.success = True
            result.message = f"Created file: {target_path}"
            result.source = target_path
            
            if content:
                result.metadata['size'] = len(content)
                result.bytes_transferred = len(content)
            
            logger.info(result.message)
            
        except FileExistsError as e:
            result.message = str(e)
            logger.error(f"File creation error: {e}")
        except Exception as e:
            result.message = f"Error creating file: {e}"
            logger.exception("File creation error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def read_file(self, file_path: Union[str, Path],
                 encoding: str = 'utf-8',
                 binary: bool = False) -> OperationResult:
        """
        Read file contents
        
        Args:
            file_path: Path to file
            encoding: Text encoding
            binary: Read as binary
            
        Returns:
            OperationResult with file content
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: {target_path}")
            
            if not target_path.is_file():
                raise IsADirectoryError(f"Path is a directory: {target_path}")
            
            # Read file
            if binary:
                with open(target_path, 'rb') as f:
                    content = f.read()
                result.metadata['content'] = content
                result.metadata['binary'] = True
            else:
                with open(target_path, 'r', encoding=encoding) as f:
                    content = f.read()
                result.metadata['content'] = content
                result.metadata['encoding'] = encoding
            
            file_info = self._get_file_info(target_path)
            
            result.success = True
            result.message = f"Read file: {target_path}"
            result.source = target_path
            result.metadata['size'] = file_info.size if file_info else 0
            result.metadata['file_info'] = file_info.__dict__ if file_info else {}
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"File read error: {e}")
        except IsADirectoryError as e:
            result.message = str(e)
            logger.error(f"File read error: {e}")
        except UnicodeDecodeError as e:
            result.message = f"Encoding error: {e}. Try binary mode."
            logger.error(f"File read encoding error: {e}")
        except Exception as e:
            result.message = f"Error reading file: {e}"
            logger.exception("File read error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def write_file(self, file_path: Union[str, Path],
                  content: Union[str, bytes],
                  encoding: str = 'utf-8',
                  append: bool = False,
                  backup: Optional[bool] = None) -> OperationResult:
        """
        Write content to file
        
        Args:
            file_path: Path to file
            content: Content to write
            encoding: Text encoding (for string content)
            append: Append to existing file
            backup: Create backup before writing
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            # Create backup if requested
            if backup or (backup is None and self.enable_backup):
                if target_path.exists():
                    backup_path = self._create_backup(target_path)
                    if backup_path:
                        result.metadata['backup'] = str(backup_path)
            
            # Determine write mode
            mode = 'ab' if append and isinstance(content, bytes) else 'a' if append else 'wb' if isinstance(content, bytes) else 'w'
            
            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(target_path, mode, encoding=encoding if 'b' not in mode else None) as f:
                bytes_written = f.write(content)
            
            result.success = True
            result.message = f"{'Appended to' if append else 'Wrote to'} file: {target_path}"
            result.source = target_path
            result.bytes_transferred = bytes_written
            
            logger.info(result.message)
            
        except Exception as e:
            result.message = f"Error writing file: {e}"
            logger.exception("File write error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def delete_file(self, file_path: Union[str, Path],
                   use_trash: Optional[bool] = None,
                   force: bool = False) -> OperationResult:
        """
        Delete a file or directory
        
        Args:
            file_path: Path to delete
            use_trash: Move to trash instead of permanent delete
            force: Force delete (ignore errors)
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                if force:
                    result.success = True
                    result.message = f"Path does not exist (ignored): {target_path}"
                    return result
                raise FileNotFoundError(f"Path not found: {target_path}")
            
            use_trash = use_trash if use_trash is not None else self.enable_trash
            
            if use_trash:
                # Move to trash
                send2trash.send2trash(str(target_path))
                result.message = f"Moved to trash: {target_path}"
            else:
                # Permanent delete
                if target_path.is_file():
                    target_path.unlink()
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
                result.message = f"Deleted: {target_path}"
            
            result.success = True
            result.source = target_path
            result.items_processed = 1
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Delete error: {e}")
        except PermissionError as e:
            result.message = f"Permission denied: {e}"
            logger.error(f"Delete permission error: {e}")
        except Exception as e:
            result.message = f"Error deleting: {e}"
            logger.exception("Delete error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def copy_file(self, source: Union[str, Path],
                 destination: Union[str, Path],
                 conflict: ConflictResolution = ConflictResolution.RENAME,
                 preserve_metadata: bool = True) -> OperationResult:
        """
        Copy file or directory
        
        Args:
            source: Source path
            destination: Destination path
            conflict: Conflict resolution strategy
            preserve_metadata: Preserve file metadata
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source not found: {src_path}")
            
            # Handle conflicts
            if dst_path.exists():
                if conflict == ConflictResolution.SKIP:
                    result.success = True
                    result.message = f"Skipped (already exists): {dst_path}"
                    return result
                elif conflict == ConflictResolution.RENAME:
                    dst_path = self._get_unique_path(dst_path)
                elif conflict == ConflictResolution.OVERWRITE:
                    pass  # Will overwrite
                else:
                    raise FileExistsError(f"Destination exists: {dst_path}")
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform copy
            if src_path.is_file():
                if preserve_metadata:
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copy(src_path, dst_path)
                bytes_copied = src_path.stat().st_size
                items_processed = 1
            else:
                if preserve_metadata:
                    shutil.copytree(src_path, dst_path, symlinks=True)
                else:
                    shutil.copytree(src_path, dst_path, symlinks=False)
                
                # Count items
                items_processed = sum(1 for _ in src_path.rglob('*')) + 1
                bytes_copied = sum(f.stat().st_size for f in src_path.rglob('*') if f.is_file())
            
            result.success = True
            result.message = f"Copied to: {dst_path}"
            result.source = src_path
            result.destination = dst_path
            result.items_processed = items_processed
            result.bytes_transferred = bytes_copied
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Copy error: {e}")
        except FileExistsError as e:
            result.message = str(e)
            logger.error(f"Copy error: {e}")
        except Exception as e:
            result.message = f"Error copying: {e}"
            logger.exception("Copy error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def move_file(self, source: Union[str, Path],
                 destination: Union[str, Path],
                 conflict: ConflictResolution = ConflictResolution.RENAME) -> OperationResult:
        """
        Move file or directory
        
        Args:
            source: Source path
            destination: Destination path
            conflict: Conflict resolution strategy
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            src_path = self._resolve_path(source)
            dst_path = self._resolve_path(destination)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Source not found: {src_path}")
            
            # Handle conflicts
            if dst_path.exists():
                if conflict == ConflictResolution.SKIP:
                    result.success = True
                    result.message = f"Skipped (already exists): {dst_path}"
                    return result
                elif conflict == ConflictResolution.RENAME:
                    dst_path = self._get_unique_path(dst_path)
                elif conflict == ConflictResolution.OVERWRITE:
                    # Delete destination before move
                    if dst_path.is_file():
                        dst_path.unlink()
                    else:
                        shutil.rmtree(dst_path)
                else:
                    raise FileExistsError(f"Destination exists: {dst_path}")
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get size info before move
            if src_path.is_file():
                bytes_moved = src_path.stat().st_size
                items_processed = 1
            else:
                bytes_moved = sum(f.stat().st_size for f in src_path.rglob('*') if f.is_file())
                items_processed = sum(1 for _ in src_path.rglob('*')) + 1
            
            # Perform move
            shutil.move(str(src_path), str(dst_path))
            
            result.success = True
            result.message = f"Moved to: {dst_path}"
            result.source = src_path
            result.destination = dst_path
            result.items_processed = items_processed
            result.bytes_transferred = bytes_moved
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Move error: {e}")
        except FileExistsError as e:
            result.message = str(e)
            logger.error(f"Move error: {e}")
        except Exception as e:
            result.message = f"Error moving: {e}"
            logger.exception("Move error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def _get_unique_path(self, path: Path) -> Path:
        """Generate a unique path by adding a number suffix"""
        if not path.exists():
            return path
        
        counter = 1
        while True:
            new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def rename_file(self, file_path: Union[str, Path],
                   new_name: str,
                   overwrite: bool = False) -> OperationResult:
        """
        Rename a file or directory
        
        Args:
            file_path: Path to rename
            new_name: New name (not full path)
            overwrite: Overwrite if destination exists
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            src_path = self._resolve_path(file_path)
            
            if not src_path.exists():
                raise FileNotFoundError(f"Path not found: {src_path}")
            
            dst_path = src_path.parent / new_name
            
            if dst_path.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {dst_path}")
            
            # Perform rename
            src_path.rename(dst_path)
            
            result.success = True
            result.message = f"Renamed to: {new_name}"
            result.source = src_path
            result.destination = dst_path
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Rename error: {e}")
        except FileExistsError as e:
            result.message = str(e)
            logger.error(f"Rename error: {e}")
        except Exception as e:
            result.message = f"Error renaming: {e}"
            logger.exception("Rename error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def search_files(self, search_path: Union[str, Path] = ".",
                    pattern: str = "*",
                    content_pattern: Optional[str] = None,
                    file_types: Optional[List[FileType]] = None,
                    min_size: Optional[int] = None,
                    max_size: Optional[int] = None,
                    modified_after: Optional[datetime] = None,
                    modified_before: Optional[datetime] = None,
                    recursive: bool = True,
                    max_results: Optional[int] = None) -> OperationResult:
        """
        Search for files with multiple criteria
        
        Args:
            search_path: Base path to search
            pattern: File name pattern
            content_pattern: Text to search in file content
            file_types: Filter by file types
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            modified_after: Modified after this date
            modified_before: Modified before this date
            recursive: Search recursively
            max_results: Maximum number of results
            
        Returns:
            OperationResult with matching files
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            base_path = self._resolve_path(search_path)
            
            if not base_path.exists():
                raise FileNotFoundError(f"Search path not found: {base_path}")
            
            matches = []
            
            # Determine search pattern
            if recursive:
                iterator = base_path.rglob(pattern)
            else:
                iterator = base_path.glob(pattern)
            
            for file_path in iterator:
                if not file_path.is_file():
                    continue
                
                file_info = self._get_file_info(file_path)
                if not file_info:
                    continue
                
                # Apply filters
                if file_types and file_info.file_type not in file_types:
                    continue
                
                if min_size and file_info.size < min_size:
                    continue
                
                if max_size and file_info.size > max_size:
                    continue
                
                if modified_after and file_info.modified < modified_after:
                    continue
                
                if modified_before and file_info.modified > modified_before:
                    continue
                
                # Search content if pattern provided
                if content_pattern:
                    try:
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                            if content_pattern not in content:
                                continue
                    except:
                        continue
                
                matches.append(file_info)
                
                if max_results and len(matches) >= max_results:
                    break
            
            result.success = True
            result.message = f"Found {len(matches)} matching files"
            result.metadata['matches'] = [m.__dict__ for m in matches]
            result.metadata['count'] = len(matches)
            result.items_processed = len(matches)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Search error: {e}")
        except Exception as e:
            result.message = f"Error searching: {e}"
            logger.exception("Search error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def get_file_info(self, file_path: Union[str, Path],
                     calculate_checksum: bool = False) -> OperationResult:
        """
        Get detailed information about a file or directory
        
        Args:
            file_path: Path to file
            calculate_checksum: Calculate file checksum
            
        Returns:
            OperationResult with file information
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {target_path}")
            
            file_info = self._get_file_info(target_path)
            
            if not file_info:
                raise Exception("Could not get file information")
            
            # Calculate checksum if requested
            if calculate_checksum and target_path.is_file():
                file_info.checksum = self._generate_checksum(target_path)
            
            # Additional info for directories
            if target_path.is_dir():
                files = list(target_path.rglob('*'))
                file_info.metadata['total_items'] = len(files)
                file_info.metadata['total_size'] = sum(f.stat().st_size for f in files if f.is_file())
                file_info.metadata['subdirectories'] = sum(1 for f in files if f.is_dir())
            
            result.success = True
            result.message = f"Information for: {target_path}"
            result.source = target_path
            result.metadata['file_info'] = file_info.__dict__
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"File info error: {e}")
        except Exception as e:
            result.message = f"Error getting file info: {e}"
            logger.exception("File info error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def create_directory(self, dir_path: Union[str, Path],
                        exist_ok: bool = True) -> OperationResult:
        """
        Create a new directory
        
        Args:
            dir_path: Directory path
            exist_ok: Don't error if directory exists
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(dir_path)
            
            target_path.mkdir(parents=True, exist_ok=exist_ok)
            
            result.success = True
            result.message = f"Created directory: {target_path}"
            result.source = target_path
            
            logger.info(result.message)
            
        except FileExistsError:
            result.message = f"Directory already exists: {target_path}"
            logger.error(f"Directory creation error: {result.message}")
        except Exception as e:
            result.message = f"Error creating directory: {e}"
            logger.exception("Directory creation error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def compress_files(self, files: List[Union[str, Path]],
                      archive_path: Union[str, Path],
                      format: str = 'zip',
                      password: Optional[str] = None) -> OperationResult:
        """
        Compress files into an archive
        
        Args:
            files: List of files/directories to compress
            archive_path: Output archive path
            format: Archive format ('zip', 'tar', 'gztar', 'bztar')
            password: Password for encrypted archive
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            archive_path = self._resolve_path(archive_path)
            
            # Resolve all source paths
            source_paths = [self._resolve_path(f) for f in files]
            
            # Verify all sources exist
            for src in source_paths:
                if not src.exists():
                    raise FileNotFoundError(f"Source not found: {src}")
            
            # Create temporary directory for files if needed
            temp_dir = None
            if password:
                # For encrypted archives, we'll need to use a temporary directory
                temp_dir = self.temp_dir / f"temp_{int(time.time())}"
                temp_dir.mkdir()
                
                # Copy files to temp directory
                for src in source_paths:
                    if src.is_file():
                        shutil.copy2(src, temp_dir)
                    else:
                        shutil.copytree(src, temp_dir / src.name)
                
                # Create encrypted zip
                import pyzipper
                with pyzipper.AESZipFile(archive_path, 'w', compression=pyzipper.ZIP_LZMA) as zf:
                    zf.setpassword(password.encode())
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zf.write(file_path, arcname)
            else:
                # Create standard archive
                if format == 'zip':
                    shutil.make_archive(str(archive_path.with_suffix('')), 'zip', root_dir=source_paths[0].parent)
                else:
                    shutil.make_archive(str(archive_path.with_suffix('')), format, root_dir=source_paths[0].parent)
            
            # Clean up temp directory
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            # Get archive size
            archive_size = archive_path.stat().st_size if archive_path.exists() else 0
            
            result.success = True
            result.message = f"Created archive: {archive_path}"
            result.destination = archive_path
            result.bytes_transferred = archive_size
            result.items_processed = len(source_paths)
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Compression error: {e}")
        except Exception as e:
            result.message = f"Error compressing files: {e}"
            logger.exception("Compression error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def extract_archive(self, archive_path: Union[str, Path],
                       extract_path: Union[str, Path],
                       password: Optional[str] = None) -> OperationResult:
        """
        Extract an archive
        
        Args:
            archive_path: Archive file path
            extract_path: Extraction destination
            password: Password for encrypted archive
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            archive_path = self._resolve_path(archive_path)
            extract_path = self._resolve_path(extract_path)
            
            if not archive_path.exists():
                raise FileNotFoundError(f"Archive not found: {archive_path}")
            
            # Create extraction directory
            extract_path.mkdir(parents=True, exist_ok=True)
            
            # Extract based on format
            if archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    if password:
                        zf.setpassword(password.encode())
                    zf.extractall(extract_path)
            elif archive_path.suffix in ['.tar', '.gz', '.bz2']:
                import tarfile
                mode = 'r:' + archive_path.suffix[1:] if archive_path.suffix != '.tar' else 'r'
                with tarfile.open(archive_path, mode) as tf:
                    tf.extractall(extract_path)
            
            # Count extracted items
            extracted_items = sum(1 for _ in extract_path.rglob('*'))
            
            result.success = True
            result.message = f"Extracted archive to: {extract_path}"
            result.source = archive_path
            result.destination = extract_path
            result.items_processed = extracted_items
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Extraction error: {e}")
        except Exception as e:
            result.message = f"Error extracting archive: {e}"
            logger.exception("Extraction error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def compare_files(self, file1: Union[str, Path],
                     file2: Union[str, Path],
                     shallow: bool = True) -> OperationResult:
        """
        Compare two files
        
        Args:
            file1: First file path
            file2: Second file path
            shallow: Use shallow comparison (quick)
            
        Returns:
            OperationResult with comparison results
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            path1 = self._resolve_path(file1)
            path2 = self._resolve_path(file2)
            
            if not path1.exists():
                raise FileNotFoundError(f"File not found: {path1}")
            
            if not path2.exists():
                raise FileNotFoundError(f"File not found: {path2}")
            
            # Compare files
            are_equal = filecmp.cmp(path1, path2, shallow=shallow)
            
            # Get additional info
            info1 = self._get_file_info(path1)
            info2 = self._get_file_info(path2)
            
            result.success = True
            result.message = f"Files are {'identical' if are_equal else 'different'}"
            result.metadata['identical'] = are_equal
            result.metadata['file1'] = info1.__dict__ if info1 else {}
            result.metadata['file2'] = info2.__dict__ if info2 else {}
            
            if not are_equal and not shallow:
                # Read and compare line by line for text files
                if info1 and info1.file_type == FileType.TEXT:
                    with open(path1, 'r') as f1, open(path2, 'r') as f2:
                        lines1 = f1.readlines()
                        lines2 = f2.readlines()
                        
                        differences = []
                        max_lines = max(len(lines1), len(lines2))
                        
                        for i in range(max_lines):
                            line1 = lines1[i] if i < len(lines1) else None
                            line2 = lines2[i] if i < len(lines2) else None
                            
                            if line1 != line2:
                                differences.append({
                                    'line': i + 1,
                                    'file1': line1,
                                    'file2': line2
                                })
                        
                        result.metadata['differences'] = differences[:100]  # Limit to 100 differences
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Comparison error: {e}")
        except Exception as e:
            result.message = f"Error comparing files: {e}"
            logger.exception("Comparison error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def watch_directory(self, path: Union[str, Path],
                       callback: Optional[callable] = None,
                       recursive: bool = True) -> str:
        """
        Watch a directory for changes
        
        Args:
            path: Directory to watch
            callback: Callback function for events
            recursive: Watch subdirectories
            
        Returns:
            Watcher ID
        """
        try:
            target_path = self._resolve_path(path)
            
            if not target_path.exists() or not target_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {target_path}")
            
            # Create event handler
            if callback is None:
                callback = self._default_watch_callback
            
            event_handler = FileMonitorHandler(callback)
            
            # Create and start observer
            observer = Observer()
            observer.schedule(event_handler, str(target_path), recursive=recursive)
            observer.start()
            
            # Store watcher
            watcher_id = str(int(time.time()))
            self.watchers[watcher_id] = observer
            
            logger.info(f"Started watching directory: {target_path} (ID: {watcher_id})")
            
            return watcher_id
            
        except Exception as e:
            logger.error(f"Error watching directory: {e}")
            raise
    
    def _default_watch_callback(self, event):
        """Default callback for file watch events"""
        logger.info(f"File event: {event}")
    
    def stop_watching(self, watcher_id: str) -> bool:
        """
        Stop watching a directory
        
        Args:
            watcher_id: Watcher ID from watch_directory
            
        Returns:
            Success status
        """
        if watcher_id in self.watchers:
            self.watchers[watcher_id].stop()
            self.watchers[watcher_id].join()
            del self.watchers[watcher_id]
            logger.info(f"Stopped watching: {watcher_id}")
            return True
        return False
    
    def batch_operation(self, files: List[Union[str, Path]],
                       operation: str,
                       destination: Optional[Union[str, Path]] = None,
                       **kwargs) -> OperationResult:
        """
        Perform batch operation on multiple files
        
        Args:
            files: List of files to process
            operation: Operation to perform ('copy', 'move', 'delete', 'info')
            destination: Destination directory (for copy/move)
            **kwargs: Additional arguments for the operation
            
        Returns:
            OperationResult with aggregated results
        """
        result = OperationResult(success=True, message="Batch operation completed")
        start_time = time.time()
        
        # Resolve all paths
        source_paths = [self._resolve_path(f) for f in files]
        
        if destination:
            dest_path = self._resolve_path(destination)
            dest_path.mkdir(parents=True, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for src in source_paths:
                if operation == 'copy' and destination:
                    dst = dest_path / src.name
                    future = executor.submit(self.copy_file, src, dst, **kwargs)
                elif operation == 'move' and destination:
                    dst = dest_path / src.name
                    future = executor.submit(self.move_file, src, dst, **kwargs)
                elif operation == 'delete':
                    future = executor.submit(self.delete_file, src, **kwargs)
                elif operation == 'info':
                    future = executor.submit(self.get_file_info, src, **kwargs)
                else:
                    continue
                
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    op_result = future.result(timeout=30)
                    if op_result.success:
                        result.items_processed += 1
                        result.bytes_transferred += op_result.bytes_transferred
                    else:
                        result.items_failed += 1
                        result.message += f"\n{op_result.message}"
                except Exception as e:
                    result.items_failed += 1
                    result.message += f"\nError: {e}"
        
        result.success = result.items_failed == 0
        result.duration = time.time() - start_time
        
        self._add_to_history(result)
        
        return result
    
    def get_disk_usage(self, path: Union[str, Path] = ".") -> OperationResult:
        """
        Get disk usage information
        
        Args:
            path: Path to check
            
        Returns:
            OperationResult with disk usage info
        """
        result = OperationResult(success=False, message="")
        
        try:
            target_path = self._resolve_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {target_path}")
            
            # Get disk usage
            usage = shutil.disk_usage(target_path)
            
            result.success = True
            result.message = f"Disk usage for {target_path}"
            result.metadata['total'] = self._format_size(usage.total)
            result.metadata['used'] = self._format_size(usage.used)
            result.metadata['free'] = self._format_size(usage.free)
            result.metadata['percent_used'] = (usage.used / usage.total) * 100
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Disk usage error: {e}")
        except Exception as e:
            result.message = f"Error getting disk usage: {e}"
            logger.exception("Disk usage error")
        
        return result
    
    def set_file_permissions(self, file_path: Union[str, Path],
                            mode: Union[int, str, FilePermission]) -> OperationResult:
        """
        Set file permissions
        
        Args:
            file_path: Path to file
            mode: Permission mode (octal, string, or FilePermission)
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        start_time = time.time()
        
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: {target_path}")
            
            # Convert mode to octal
            if isinstance(mode, FilePermission):
                permission_map = {
                    FilePermission.READ: 0o444,
                    FilePermission.WRITE: 0o222,
                    FilePermission.EXECUTE: 0o111,
                    FilePermission.READ_WRITE: 0o666,
                    FilePermission.READ_EXECUTE: 0o555,
                    FilePermission.ALL: 0o777,
                    FilePermission.NONE: 0o000
                }
                octal_mode = permission_map.get(mode, 0o644)
            elif isinstance(mode, str):
                # Convert string like "rwxr-xr-x" to octal
                octal_mode = int(mode, 8) if mode.startswith('0') else int(mode)
            else:
                octal_mode = mode
            
            # Set permissions
            target_path.chmod(octal_mode)
            
            result.success = True
            result.message = f"Set permissions for: {target_path}"
            result.source = target_path
            result.metadata['mode'] = oct(octal_mode)
            result.metadata['mode_str'] = stat.filemode(octal_mode)
            
            logger.info(result.message)
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Permission error: {e}")
        except Exception as e:
            result.message = f"Error setting permissions: {e}"
            logger.exception("Permission error")
        
        result.duration = time.time() - start_time
        self._add_to_history(result)
        
        return result
    
    def copy_to_clipboard(self, file_path: Union[str, Path]) -> OperationResult:
        """
        Copy file path to clipboard
        
        Args:
            file_path: Path to file
            
        Returns:
            OperationResult
        """
        result = OperationResult(success=False, message="")
        
        try:
            target_path = self._resolve_path(file_path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"File not found: {target_path}")
            
            pyperclip.copy(str(target_path))
            
            result.success = True
            result.message = f"Copied path to clipboard: {target_path}"
            
        except FileNotFoundError as e:
            result.message = str(e)
            logger.error(f"Clipboard error: {e}")
        except Exception as e:
            result.message = f"Error copying to clipboard: {e}"
            logger.exception("Clipboard error")
        
        return result
    
    def get_operation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent operation history"""
        return [r.__dict__ for r in self.operation_history[-limit:]]
    
    def undo_last_operation(self) -> Optional[OperationResult]:
        """
        Undo the last file operation (limited support)
        
        Returns:
            Undo operation result
        """
        if not self.operation_history:
            return None
        
        last_op = self.operation_history[-1]
        
        if last_op.success and last_op.source and last_op.destination:
            # Try to reverse the operation
            if last_op.message.startswith("Moved"):
                # Reverse move
                return self.move_file(last_op.destination, last_op.source)
            elif last_op.message.startswith("Copied"):
                # Delete copy
                return self.delete_file(last_op.destination)
            elif last_op.message.startswith("Deleted"):
                # Can't undelete
                return OperationResult(
                    success=False,
                    message="Cannot undelete files. Check trash.",
                    source=last_op.source
                )
        
        return None
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about current workspace"""
        info = {
            'workspace_dir': str(self.workspace_dir),
            'exists': self.workspace_dir.exists(),
            'is_directory': self.workspace_dir.is_dir() if self.workspace_dir.exists() else False,
            'enable_trash': self.enable_trash,
            'enable_backup': self.enable_backup,
            'max_history': self.max_history,
            'history_count': len(self.operation_history),
            'active_watchers': len(self.watchers),
            'temp_dir': str(self.temp_dir)
        }
        
        if self.workspace_dir.exists():
            usage = shutil.disk_usage(self.workspace_dir)
            info['disk_usage'] = {
                'total': self._format_size(usage.total),
                'used': self._format_size(usage.used),
                'free': self._format_size(usage.free)
            }
        
        return info
    
    def change_workspace(self, new_workspace: Union[str, Path]) -> bool:
        """
        Change the current workspace directory
        
        Args:
            new_workspace: New workspace path
            
        Returns:
            Success status
        """
        try:
            new_path = Path(new_workspace).resolve()
            new_path.mkdir(parents=True, exist_ok=True)
            self.workspace_dir = new_path
            logger.info(f"Changed workspace to: {self.workspace_dir}")
            return True
        except Exception as e:
            logger.error(f"Error changing workspace: {e}")
            return False


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import pprint
    
    manager = FileManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            path = sys.argv[2] if len(sys.argv) > 2 else "."
            result = manager.list_directory(path)
            pprint.pprint(result.metadata.get('items', []))
        
        elif command == "info" and len(sys.argv) > 2:
            result = manager.get_file_info(sys.argv[2])
            pprint.pprint(result.metadata.get('file_info', {}))
        
        elif command == "create" and len(sys.argv) > 2:
            result = manager.create_file(sys.argv[2])
            print(result.message)
        
        elif command == "delete" and len(sys.argv) > 2:
            result = manager.delete_file(sys.argv[2])
            print(result.message)
        
        elif command == "search" and len(sys.argv) > 2:
            pattern = sys.argv[2]
            result = manager.search_files(pattern=pattern)
            pprint.pprint(result.metadata.get('matches', []))
        
        elif command == "disk":
            path = sys.argv[2] if len(sys.argv) > 2 else "."
            result = manager.get_disk_usage(path)
            pprint.pprint(result.metadata)
        
        elif command == "history":
            history = manager.get_operation_history()
            pprint.pprint(history)
        
        else:
            print("Usage: file_manager.py [list|info|create|delete|search|disk|history] [args]")
    else:
        # Demo mode
        print("File Manager Demo")
        print("-" * 50)
        
        # Get workspace info
        print("\nWorkspace Info:")
        info = manager.get_workspace_info()
        pprint.pprint(info)
        
        # List current directory
        print("\nListing current directory:")
        result = manager.list_directory(max_results=5)
        for item in result.metadata.get('items', []):
            print(f"  {item['name']} ({item['size']})")
        
        # Create a test file
        print("\nCreating test file:")
        test_file = manager.workspace_dir / "test.txt"
        result = manager.create_file(test_file, content="Hello, World!")
        print(f"  {result.message}")
        
        # Get file info
        print("\nFile info:")
        result = manager.get_file_info(test_file)
        if result.success:
            info = result.metadata.get('file_info', {})
            print(f"  Name: {info.get('name')}")
            print(f"  Size: {info.get('size')}")
            print(f"  Type: {info.get('file_type')}")
        
        # Search for text files
        print("\nSearching for text files:")
        result = manager.search_files(pattern="*.txt")
        print(f"  Found {result.metadata.get('count', 0)} files")
        
        # Clean up
        print("\nCleaning up:")
        result = manager.delete_file(test_file)
        print(f"  {result.message}")