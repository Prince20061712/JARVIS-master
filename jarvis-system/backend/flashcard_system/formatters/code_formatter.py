"""
Code formatter module for syntax highlighting, code analysis, and pretty printing.
Supports multiple programming languages with robust error handling and formatting.
"""

import re
import json
import html
import keyword
import builtins
import logging
import hashlib
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Tuple, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer, ClassNotFound
from pygments.formatters import HtmlFormatter, TerminalFormatter, LatexFormatter
from pygments.styles import get_all_styles, STYLE_MAP
from pygments.token import Token
import black
import autopep8
import jsbeautifier
import sqlparse
import htmlmin
import csscompressor
import rjsmin
import json as json_formatter

# For language detection
import chardet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProgrammingLanguage(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    BASH = "bash"
    POWERSHELL = "powershell"
    DOCKERFILE = "dockerfile"
    UNKNOWN = "unknown"


class CodeLanguage(str, Enum):
    """Alias for ProgrammingLanguage for backward compatibility."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    BASH = "bash"
    UNKNOWN = "unknown"


class FormatStyle(Enum):
    """Code formatting styles."""
    PEP8 = "pep8"  # Python
    GOOGLE = "google"  # Google style
    AIRBNB = "airbnb"  # JavaScript
    STANDARD = "standard"  # Standard style
    PRETTIER = "prettier"  # Prettier style
    MINIFIED = "minified"  # Minified/compressed
    PRETTY = "pretty"  # Pretty printed
    COMPACT = "compact"  # Compact but readable


class OutputFormat(Enum):
    """Output formats for formatted code."""
    HTML = "html"
    TERMINAL = "terminal"
    LATEX = "latex"
    PLAIN = "plain"
    MARKDOWN = "markdown"
    JSON = "json"
    SVG = "svg"
    RTF = "rtf"


@dataclass
class FormatOptions:
    """Options for code formatting."""
    style: FormatStyle = FormatStyle.PRETTY
    output_format: OutputFormat = OutputFormat.HTML
    line_numbers: bool = True
    max_line_length: int = 88
    indent_size: int = 4
    tab_width: int = 4
    wrap_lines: bool = True
    escape_html: bool = True
    css_class_prefix: str = "code"
    style_name: str = "monokai"
    font_size: Optional[str] = None
    font_family: Optional[str] = None
    background_color: Optional[str] = None
    timeout_seconds: int = 5
    validate_syntax: bool = True
    minify: bool = False
    preserve_comments: bool = True
    encoding: str = "utf-8"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "style": self.style.value,
            "output_format": self.output_format.value,
            "line_numbers": self.line_numbers,
            "max_line_length": self.max_line_length,
            "indent_size": self.indent_size,
            "tab_width": self.tab_width,
            "wrap_lines": self.wrap_lines,
            "escape_html": self.escape_html,
            "css_class_prefix": self.css_class_prefix,
            "style_name": self.style_name,
            "font_size": self.font_size,
            "font_family": self.font_family,
            "background_color": self.background_color,
            "validate_syntax": self.validate_syntax,
            "minify": self.minify,
            "preserve_comments": self.preserve_comments
        }


@dataclass
class FormatResult:
    """Result of code formatting operation."""
    original_code: str
    formatted_code: str
    language: ProgrammingLanguage
    detected_language: ProgrammingLanguage
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    line_count: int = 0
    character_count: int = 0
    token_count: int = 0
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_code": self.original_code,
            "formatted_code": self.formatted_code,
            "language": self.language.value,
            "detected_language": self.detected_language.value,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "line_count": self.line_count,
            "character_count": self.character_count,
            "token_count": self.token_count,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


@dataclass
class CodeBlock:
    """Represents a code block with metadata."""
    code: str
    language: ProgrammingLanguage
    file_name: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate hash after initialization."""
        if not self.hash:
            self.hash = hashlib.sha256(self.code.encode()).hexdigest()[:16]


@dataclass
class CodeAnalysis:
    """Results of code analysis."""
    language: ProgrammingLanguage
    line_count: int
    code_line_count: int  # Lines excluding comments and blanks
    comment_line_count: int
    blank_line_count: int
    function_count: int
    class_count: int
    import_count: int
    complexity_score: float
    maintainability_index: float
    has_syntax_errors: bool
    tokens: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "line_count": self.line_count,
            "code_line_count": self.code_line_count,
            "comment_line_count": self.comment_line_count,
            "blank_line_count": self.blank_line_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "complexity_score": self.complexity_score,
            "maintainability_index": self.maintainability_index,
            "has_syntax_errors": self.has_syntax_errors,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "issues": self.issues,
            "metrics": self.metrics
        }


class SyntaxHighlighter:
    """
    Handles syntax highlighting for code blocks using Pygments.
    """
    
    def __init__(self):
        """Initialize syntax highlighter."""
        self.available_styles = list(get_all_styles())
        self.default_style = "monokai"
        self._lexer_cache = {}
        self._formatter_cache = {}
        
    def get_lexer(
        self,
        language: Union[str, ProgrammingLanguage],
        code: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get a Pygments lexer for the specified language.
        
        Args:
            language: Programming language
            code: Optional code for guessing
            
        Returns:
            Pygments lexer or None
        """
        # Convert language to string
        if isinstance(language, ProgrammingLanguage):
            lang_str = language.value
        else:
            lang_str = language.lower()
        
        # Check cache
        cache_key = lang_str
        if cache_key in self._lexer_cache:
            return self._lexer_cache[cache_key]
        
        try:
            # Try to get lexer by name
            lexer = get_lexer_by_name(lang_str, stripall=True)
            self._lexer_cache[cache_key] = lexer
            return lexer
            
        except ClassNotFound:
            # Try to guess from code if available
            if code:
                try:
                    lexer = guess_lexer(code)
                    self._lexer_cache[cache_key] = lexer
                    return lexer
                except ClassNotFound:
                    pass
            
            # Fallback to text lexer
            try:
                lexer = get_lexer_by_name("text")
                self._lexer_cache[cache_key] = lexer
                return lexer
            except ClassNotFound:
                return None
    
    def get_formatter(
        self,
        output_format: OutputFormat,
        options: FormatOptions
    ) -> Optional[Any]:
        """
        Get a Pygments formatter for the specified output format.
        
        Args:
            output_format: Desired output format
            options: Formatting options
            
        Returns:
            Pygments formatter or None
        """
        # Check cache
        cache_key = f"{output_format.value}_{options.style_name}"
        if cache_key in self._formatter_cache:
            return self._formatter_cache[cache_key]
        
        try:
            formatter_kwargs = {
                "style": options.style_name,
                "linenos": options.line_numbers,
                "cssclass": options.css_class_prefix,
                "full": False,
                "nobackground": True,
                "stripnl": True,
                "stripall": True,
                "ensurenl": True
            }
            
            # Add font options if specified
            if options.font_size:
                formatter_kwargs["fontsize"] = options.font_size
            if options.font_family:
                formatter_kwargs["fontfamily"] = options.font_family
            
            if output_format == OutputFormat.HTML:
                formatter = HtmlFormatter(**formatter_kwargs)
            elif output_format == OutputFormat.TERMINAL:
                formatter = TerminalFormatter(**formatter_kwargs)
            elif output_format == OutputFormat.LATEX:
                formatter = LatexFormatter(**formatter_kwargs)
            elif output_format == OutputFormat.RTF:
                from pygments.formatters import RtfFormatter
                formatter = RtfFormatter(**formatter_kwargs)
            elif output_format == OutputFormat.SVG:
                from pygments.formatters import SvgFormatter
                formatter = SvgFormatter(**formatter_kwargs)
            else:
                return None
            
            self._formatter_cache[cache_key] = formatter
            return formatter
            
        except Exception as e:
            logger.warning(f"Failed to create formatter: {e}")
            return None
    
    def highlight(
        self,
        code: str,
        language: Union[str, ProgrammingLanguage],
        options: FormatOptions
    ) -> FormatResult:
        """
        Apply syntax highlighting to code.
        
        Args:
            code: Source code
            language: Programming language
            options: Formatting options
            
        Returns:
            FormatResult with highlighted code
        """
        start_time = datetime.now()
        
        try:
            # Get lexer
            lexer = self.get_lexer(language, code)
            if not lexer:
                return FormatResult(
                    original_code=code,
                    formatted_code=html.escape(code) if options.escape_html else code,
                    language=ProgrammingLanguage.UNKNOWN,
                    detected_language=ProgrammingLanguage.UNKNOWN,
                    success=False,
                    error_message="Could not determine language lexer"
                )
            
            # Get formatter
            formatter = self.get_formatter(options.output_format, options)
            if not formatter:
                # Fallback to plain text
                formatted = html.escape(code) if options.escape_html else code
            else:
                # Apply highlighting
                formatted = pygments.highlight(code, lexer, formatter)
            
            # Post-process based on options
            if options.minify and options.output_format == OutputFormat.HTML:
                # Minify HTML output
                formatted = htmlmin.minify(
                    formatted,
                    remove_comments=not options.preserve_comments,
                    remove_empty_space=True
                )
            
            # Calculate metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Token count
            tokens = list(lexer.get_tokens(code))
            token_count = len(tokens)
            
            # Detect actual language
            detected_lang = ProgrammingLanguage.UNKNOWN
            if hasattr(lexer, 'name'):
                try:
                    detected_lang = ProgrammingLanguage(lexer.name.lower())
                except ValueError:
                    pass
            
            return FormatResult(
                original_code=code,
                formatted_code=formatted,
                language=ProgrammingLanguage(language.value if isinstance(language, ProgrammingLanguage) else language),
                detected_language=detected_lang,
                success=True,
                execution_time_ms=execution_time,
                line_count=len(code.splitlines()),
                character_count=len(code),
                token_count=token_count
            )
            
        except Exception as e:
            logger.error(f"Syntax highlighting failed: {e}")
            return FormatResult(
                original_code=code,
                formatted_code=html.escape(code) if options.escape_html else code,
                language=ProgrammingLanguage.UNKNOWN,
                detected_language=ProgrammingLanguage.UNKNOWN,
                success=False,
                error_message=str(e),
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def get_css(self, style_name: str = "monokai") -> str:
        """
        Get CSS for syntax highlighting.
        
        Args:
            style_name: Pygments style name
            
        Returns:
            CSS string
        """
        try:
            return HtmlFormatter(style=style_name).get_style_defs('.code-highlight')
        except Exception as e:
            logger.error(f"Failed to generate CSS: {e}")
            return ""


class CodeFormatter:
    """
    Main code formatter class for formatting and analyzing code.
    Supports multiple languages with language-specific formatters.
    """
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize code formatter.
        
        Args:
            temp_dir: Temporary directory for external formatters
        """
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "jarvis_code_format"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.highlighter = SyntaxHighlighter()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        
        # Language-specific formatter availability
        self._check_formatters()
        
        logger.info(f"CodeFormatter initialized with temp dir: {self.temp_dir}")
    
    def _check_formatters(self):
        """Check availability of external formatters."""
        self.formatters_available = {
            "black": self._check_command("black"),
            "autopep8": self._check_command("autopep8"),
            "js-beautify": self._check_command("js-beautify"),
            "sqlformat": self._check_command("sqlformat"),
            "rustfmt": self._check_command("rustfmt"),
            "gofmt": self._check_command("gofmt"),
            "prettier": self._check_command("prettier"),
            "yapf": self._check_command("yapf")
        }
        
        logger.info(f"Formatters available: {self.formatters_available}")
    
    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                timeout=2,
                check=False
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def detect_language(
        self,
        code: str,
        file_name: Optional[str] = None
    ) -> ProgrammingLanguage:
        """
        Detect programming language from code.
        
        Args:
            code: Source code
            file_name: Optional filename for extension-based detection
            
        Returns:
            Detected programming language
        """
        # Try file extension first
        if file_name:
            ext = Path(file_name).suffix.lower()
            lang_from_ext = self._language_from_extension(ext)
            if lang_from_ext != ProgrammingLanguage.UNKNOWN:
                return lang_from_ext
        
        # Try Pygments lexer guessing
        try:
            lexer = guess_lexer(code)
            lexer_name = lexer.name.lower()
            
            # Map to our enum
            for lang in ProgrammingLanguage:
                if lang.value in lexer_name:
                    return lang
            
            # Special cases
            if "python" in lexer_name:
                return ProgrammingLanguage.PYTHON
            elif "javascript" in lexer_name:
                return ProgrammingLanguage.JAVASCRIPT
            elif "java" in lexer_name:
                return ProgrammingLanguage.JAVA
            elif "c++" in lexer_name or "cpp" in lexer_name:
                return ProgrammingLanguage.CPP
                
        except ClassNotFound:
            pass
        
        # Try basic heuristics
        if re.search(r'^import\s+\w+|^def\s+\w+\s*\(|^class\s+\w+\s*[:\(]', code, re.MULTILINE):
            return ProgrammingLanguage.PYTHON
        elif re.search(r'function\s+\w+\s*\(|const\s+\w+\s*=\s*\(|=>', code):
            return ProgrammingLanguage.JAVASCRIPT
        elif re.search(r'public\s+class|private\s+\w+|protected\s+\w+', code):
            return ProgrammingLanguage.JAVA
        elif re.search(r'#include\s*<|std::', code):
            return ProgrammingLanguage.CPP
        elif re.search(r'SELECT.*FROM|INSERT INTO|UPDATE.*SET', code, re.IGNORECASE):
            return ProgrammingLanguage.SQL
        elif re.search(r'<html|<div|<body', code, re.IGNORECASE):
            return ProgrammingLanguage.HTML
        elif re.search(r'\{[^}]+\}|\[[^\]]+\]|\{[^{}]*\}:', code):
            try:
                json.loads(code)
                return ProgrammingLanguage.JSON
            except:
                pass
        
        return ProgrammingLanguage.UNKNOWN
    
    def _language_from_extension(self, extension: str) -> ProgrammingLanguage:
        """Map file extension to programming language."""
        ext_map = {
            '.py': ProgrammingLanguage.PYTHON,
            '.js': ProgrammingLanguage.JAVASCRIPT,
            '.jsx': ProgrammingLanguage.JAVASCRIPT,
            '.ts': ProgrammingLanguage.TYPESCRIPT,
            '.tsx': ProgrammingLanguage.TYPESCRIPT,
            '.java': ProgrammingLanguage.JAVA,
            '.cpp': ProgrammingLanguage.CPP,
            '.cxx': ProgrammingLanguage.CPP,
            '.cc': ProgrammingLanguage.CPP,
            '.c': ProgrammingLanguage.C,
            '.h': ProgrammingLanguage.C,
            '.hpp': ProgrammingLanguage.CPP,
            '.cs': ProgrammingLanguage.CSHARP,
            '.go': ProgrammingLanguage.GO,
            '.rs': ProgrammingLanguage.RUST,
            '.rb': ProgrammingLanguage.RUBY,
            '.php': ProgrammingLanguage.PHP,
            '.swift': ProgrammingLanguage.SWIFT,
            '.kt': ProgrammingLanguage.KOTLIN,
            '.kts': ProgrammingLanguage.KOTLIN,
            '.sql': ProgrammingLanguage.SQL,
            '.html': ProgrammingLanguage.HTML,
            '.htm': ProgrammingLanguage.HTML,
            '.css': ProgrammingLanguage.CSS,
            '.scss': ProgrammingLanguage.SCSS,
            '.json': ProgrammingLanguage.JSON,
            '.yaml': ProgrammingLanguage.YAML,
            '.yml': ProgrammingLanguage.YAML,
            '.md': ProgrammingLanguage.MARKDOWN,
            '.markdown': ProgrammingLanguage.MARKDOWN,
            '.sh': ProgrammingLanguage.BASH,
            '.bash': ProgrammingLanguage.BASH,
            '.ps1': ProgrammingLanguage.POWERSHELL,
            '.dockerfile': ProgrammingLanguage.DOCKERFILE,
        }
        return ext_map.get(extension.lower(), ProgrammingLanguage.UNKNOWN)
    
    async def format_code(
        self,
        code: str,
        language: Optional[Union[str, ProgrammingLanguage]] = None,
        options: Optional[FormatOptions] = None,
        file_name: Optional[str] = None
    ) -> FormatResult:
        """
        Format code with syntax highlighting and language-specific formatting.
        
        Args:
            code: Source code to format
            language: Programming language (auto-detected if not provided)
            options: Formatting options
            file_name: Optional filename for context
            
        Returns:
            FormatResult with formatted code
        """
        options = options or FormatOptions()
        start_time = datetime.now()
        
        try:
            # Detect language if not provided
            detected_language = self.detect_language(code, file_name)
            
            if language is None:
                language = detected_language
            elif isinstance(language, str):
                try:
                    language = ProgrammingLanguage(language.lower())
                except ValueError:
                    language = ProgrammingLanguage.UNKNOWN
            
            # Apply language-specific formatting
            formatted_code = code
            warnings = []
            
            if language != ProgrammingLanguage.UNKNOWN and options.style != FormatStyle.PLAIN:
                try:
                    formatted_code = await self._apply_language_formatter(
                        code, language, options
                    )
                except Exception as e:
                    warnings.append(f"Language-specific formatting failed: {e}")
                    formatted_code = code
            
            # Apply syntax highlighting
            highlight_result = self.highlighter.highlight(
                formatted_code,
                language,
                options
            )
            
            # Combine results
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return FormatResult(
                original_code=code,
                formatted_code=highlight_result.formatted_code,
                language=language,
                detected_language=detected_language,
                success=highlight_result.success,
                error_message=highlight_result.error_message,
                execution_time_ms=execution_time,
                line_count=highlight_result.line_count,
                character_count=highlight_result.character_count,
                token_count=highlight_result.token_count,
                warnings=warnings,
                metadata={
                    "language_specific_formatting": bool(formatted_code != code),
                    "highlighting_applied": highlight_result.success
                }
            )
            
        except Exception as e:
            logger.error(f"Code formatting failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return FormatResult(
                original_code=code,
                formatted_code=html.escape(code) if options.escape_html else code,
                language=language or ProgrammingLanguage.UNKNOWN,
                detected_language=detected_language if 'detected_language' in locals() else ProgrammingLanguage.UNKNOWN,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time,
                line_count=len(code.splitlines()),
                character_count=len(code)
            )
    
    async def _apply_language_formatter(
        self,
        code: str,
        language: ProgrammingLanguage,
        options: FormatOptions
    ) -> str:
        """
        Apply language-specific formatters.
        
        Args:
            code: Source code
            language: Programming language
            options: Formatting options
            
        Returns:
            Formatted code
        """
        # Run blocking formatters in thread pool
        loop = asyncio.get_event_loop()
        
        try:
            if language == ProgrammingLanguage.PYTHON:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_python,
                    code,
                    options
                )
            elif language == ProgrammingLanguage.JAVASCRIPT:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_javascript,
                    code,
                    options
                )
            elif language == ProgrammingLanguage.JSON:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_json,
                    code,
                    options
                )
            elif language == ProgrammingLanguage.SQL:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_sql,
                    code,
                    options
                )
            elif language == ProgrammingLanguage.HTML:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_html,
                    code,
                    options
                )
            elif language == ProgrammingLanguage.CSS:
                return await loop.run_in_executor(
                    self.executor,
                    self._format_css,
                    code,
                    options
                )
            else:
                # No specific formatter, return original
                return code
                
        except TimeoutError:
            logger.warning(f"Formatter timed out for {language.value}")
            return code
        except Exception as e:
            logger.warning(f"Formatter failed for {language.value}: {e}")
            return code
    
    def _format_python(self, code: str, options: FormatOptions) -> str:
        """Format Python code."""
        try:
            if options.minify:
                # Remove comments and extra whitespace
                lines = []
                for line in code.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        lines.append(stripped)
                return '\n'.join(lines)
            
            # Try Black first
            if self.formatters_available.get("black"):
                try:
                    mode = black.Mode(
                        line_length=options.max_line_length,
                        string_normalization=True,
                        preview=True
                    )
                    return black.format_str(code, mode=mode)
                except Exception as e:
                    logger.debug(f"Black formatting failed: {e}")
            
            # Fallback to autopep8
            if self.formatters_available.get("autopep8"):
                try:
                    return autopep8.fix_code(
                        code,
                        options={
                            'aggressive': 1,
                            'max_line_length': options.max_line_length,
                            'indent_size': options.indent_size
                        }
                    )
                except Exception as e:
                    logger.debug(f"autopep8 formatting failed: {e}")
            
            return code
            
        except Exception as e:
            logger.warning(f"Python formatting failed: {e}")
            return code
    
    def _format_javascript(self, code: str, options: FormatOptions) -> str:
        """Format JavaScript code."""
        try:
            if options.minify:
                return rjsmin.jsmin(code)
            
            # Try js-beautify
            if self.formatters_available.get("js-beautify"):
                try:
                    js_options = {
                        "indent_size": options.indent_size,
                        "indent_char": " ",
                        "max_preserve_newlines": 2,
                        "preserve_newlines": options.preserve_comments,
                        "jslint_happy": False,
                        "space_after_anon_function": True,
                        "brace_style": "collapse",
                        "break_chained_methods": False,
                        "wrap_line_length": options.max_line_length
                    }
                    return jsbeautifier.beautify(code, js_options)
                except Exception as e:
                    logger.debug(f"js-beautify failed: {e}")
            
            # Try Prettier if available
            if self.formatters_available.get("prettier"):
                try:
                    return self._run_external_formatter(
                        ["prettier", "--parser", "babel"],
                        code
                    )
                except Exception as e:
                    logger.debug(f"Prettier failed: {e}")
            
            return code
            
        except Exception as e:
            logger.warning(f"JavaScript formatting failed: {e}")
            return code
    
    def _format_json(self, code: str, options: FormatOptions) -> str:
        """Format JSON code."""
        try:
            # Parse JSON
            data = json.loads(code)
            
            if options.minify:
                # Minify JSON
                return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            else:
                # Pretty print JSON
                return json.dumps(
                    data,
                    indent=options.indent_size,
                    ensure_ascii=False,
                    sort_keys=True
                )
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON: {e}")
            return code
        except Exception as e:
            logger.warning(f"JSON formatting failed: {e}")
            return code
    
    def _format_sql(self, code: str, options: FormatOptions) -> str:
        """Format SQL code."""
        try:
            if options.minify:
                # Minify SQL
                return ' '.join(code.split())
            
            # Format SQL
            return sqlparse.format(
                code,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                strip_comments=not options.preserve_comments,
                indent_width=options.indent_size
            )
            
        except Exception as e:
            logger.warning(f"SQL formatting failed: {e}")
            return code
    
    def _format_html(self, code: str, options: FormatOptions) -> str:
        """Format HTML code."""
        try:
            if options.minify:
                return htmlmin.minify(
                    code,
                    remove_comments=not options.preserve_comments,
                    remove_empty_space=True,
                    remove_optional_attribute_quotes=False
                )
            return code
        except Exception as e:
            logger.warning(f"HTML formatting failed: {e}")
            return code
    
    def _format_css(self, code: str, options: FormatOptions) -> str:
        """Format CSS code."""
        try:
            if options.minify:
                return csscompressor.compress(code)
            return code
        except Exception as e:
            logger.warning(f"CSS formatting failed: {e}")
            return code
    
    def _run_external_formatter(
        self,
        cmd: List[str],
        code: str,
        timeout: int = 5
    ) -> str:
        """Run an external formatter command."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.tmp',
            dir=self.temp_dir,
            delete=False
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            result = subprocess.run(
                cmd + [tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0:
                with open(tmp_path, 'r') as f:
                    formatted = f.read()
                return formatted
            else:
                logger.debug(f"External formatter failed: {result.stderr}")
                return code
                
        except subprocess.TimeoutExpired:
            logger.debug(f"External formatter timed out")
            return code
        except Exception as e:
            logger.debug(f"External formatter error: {e}")
            return code
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    async def format_batch(
        self,
        code_blocks: List[Union[str, CodeBlock]],
        options: Optional[FormatOptions] = None
    ) -> List[FormatResult]:
        """
        Format multiple code blocks in batch.
        
        Args:
            code_blocks: List of code strings or CodeBlock objects
            options: Formatting options
            
        Returns:
            List of FormatResult objects
        """
        tasks = []
        
        for block in code_blocks:
            if isinstance(block, CodeBlock):
                tasks.append(
                    self.format_code(
                        block.code,
                        block.language,
                        options,
                        block.file_name
                    )
                )
            else:
                tasks.append(self.format_code(block, None, options))
        
        return await asyncio.gather(*tasks)
    
    def extract_code_blocks(
        self,
        text: str,
        include_inline: bool = True
    ) -> List[CodeBlock]:
        """
        Extract code blocks from markdown or plain text.
        
        Args:
            text: Text containing code blocks
            include_inline: Whether to include inline code
            
        Returns:
            List of extracted code blocks
        """
        blocks = []
        
        # Extract markdown code blocks (```code```)
        markdown_pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(markdown_pattern, text, re.DOTALL)
        
        for lang, code in matches:
            language = ProgrammingLanguage.UNKNOWN
            if lang:
                try:
                    language = ProgrammingLanguage(lang.lower())
                except ValueError:
                    pass
            
            blocks.append(CodeBlock(
                code=code.strip(),
                language=language,
                description=f"Markdown code block ({lang})"
            ))
        
        # Extract inline code
        if include_inline:
            inline_pattern = r'`([^`]+)`'
            for match in re.findall(inline_pattern, text):
                blocks.append(CodeBlock(
                    code=match,
                    language=ProgrammingLanguage.UNKNOWN,
                    description="Inline code"
                ))
        
        return blocks
    
    async def analyze_code(self, code: str, language: Optional[ProgrammingLanguage] = None) -> CodeAnalysis:
        """
        Perform detailed analysis of code.
        
        Args:
            code: Source code to analyze
            language: Programming language (auto-detected if not provided)
            
        Returns:
            CodeAnalysis object with metrics
        """
        if language is None:
            language = self.detect_language(code)
        
        lines = code.splitlines()
        total_lines = len(lines)
        
        # Count different line types
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        # Language-specific analysis
        functions = []
        classes = []
        imports = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if not stripped:
                blank_lines += 1
                continue
            
            if stripped.startswith(('#', '//', '/*', '*', '--')):
                comment_lines += 1
                continue
            
            code_lines += 1
            
            # Language-specific pattern matching
            if language == ProgrammingLanguage.PYTHON:
                if stripped.startswith('def '):
                    func_name = stripped[4:].split('(')[0].strip()
                    functions.append({
                        'name': func_name,
                        'line': i + 1,
                        'type': 'function'
                    })
                elif stripped.startswith('class '):
                    class_name = stripped[6:].split('(')[0].split(':')[0].strip()
                    classes.append({
                        'name': class_name,
                        'line': i + 1,
                        'type': 'class'
                    })
                elif stripped.startswith('import ') or stripped.startswith('from '):
                    imports.append(stripped)
            
            elif language == ProgrammingLanguage.JAVASCRIPT:
                if re.match(r'function\s+\w+\s*\(', stripped):
                    func_name = re.findall(r'function\s+(\w+)\s*\(', stripped)
                    if func_name:
                        functions.append({
                            'name': func_name[0],
                            'line': i + 1,
                            'type': 'function'
                        })
                elif re.match(r'class\s+\w+', stripped):
                    class_name = re.findall(r'class\s+(\w+)', stripped)
                    if class_name:
                        classes.append({
                            'name': class_name[0],
                            'line': i + 1,
                            'type': 'class'
                        })
                elif stripped.startswith('import ') or stripped.startswith('const '):
                    if 'require(' in stripped or 'from ' in stripped:
                        imports.append(stripped)
        
        # Calculate complexity metrics
        complexity_score = self._calculate_complexity(code, language)
        maintainability_index = self._calculate_maintainability(
            code_lines,
            comment_lines,
            complexity_score
        )
        
        # Check for syntax errors
        has_syntax_errors = await self._check_syntax(code, language)
        
        # Tokenize code
        tokens = []
        try:
            lexer = self.highlighter.get_lexer(language, code)
            if lexer:
                for token_type, token_value in lexer.get_tokens(code):
                    tokens.append({
                        'type': str(token_type),
                        'value': token_value
                    })
        except Exception as e:
            logger.debug(f"Tokenization failed: {e}")
        
        return CodeAnalysis(
            language=language,
            line_count=total_lines,
            code_line_count=code_lines,
            comment_line_count=comment_lines,
            blank_line_count=blank_lines,
            function_count=len(functions),
            class_count=len(classes),
            import_count=len(imports),
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            has_syntax_errors=has_syntax_errors,
            tokens=tokens[:100],  # Limit tokens
            functions=functions,
            classes=classes,
            imports=imports,
            metrics={
                'lines_of_code': code_lines,
                'comment_density': comment_lines / max(total_lines, 1),
                'function_density': len(functions) / max(code_lines, 1) * 100
            }
        )
    
    def _calculate_complexity(self, code: str, language: ProgrammingLanguage) -> float:
        """
        Calculate code complexity score.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Complexity score (0-100)
        """
        # Simple cyclomatic complexity estimation
        complexity = 1.0  # Base complexity
        
        # Count decision points
        decision_keywords = {
            ProgrammingLanguage.PYTHON: ['if ', 'elif ', 'for ', 'while ', 'except', 'with '],
            ProgrammingLanguage.JAVASCRIPT: ['if ', 'else if', 'for ', 'while ', 'switch', 'catch'],
            ProgrammingLanguage.JAVA: ['if ', 'for ', 'while ', 'switch', 'catch'],
            ProgrammingLanguage.CPP: ['if ', 'for ', 'while ', 'switch', 'catch'],
        }
        
        keywords = decision_keywords.get(language, ['if ', 'for ', 'while '])
        
        for keyword in keywords:
            complexity += code.count(keyword) * 0.5
        
        # Count logical operators
        complexity += code.count('&&') * 0.3
        complexity += code.count('||') * 0.3
        complexity += code.count('?') * 0.2
        
        # Normalize to 0-100 scale
        normalized = min(100, complexity * 10)
        
        return round(normalized, 2)
    
    def _calculate_maintainability(
        self,
        code_lines: int,
        comment_lines: int,
        complexity: float
    ) -> float:
        """
        Calculate maintainability index.
        
        Args:
            code_lines: Number of code lines
            comment_lines: Number of comment lines
            complexity: Complexity score
            
        Returns:
            Maintainability index (0-100)
        """
        # Maintainability Index = MAX(0,(171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC))*100 / 171)
        # Simplified version
        
        if code_lines == 0:
            return 100.0
        
        # Halstead Volume approximation
        hv = code_lines * (1 + comment_lines / max(code_lines, 1))
        
        # Calculate MI
        mi = 171 - 5.2 * (hv ** 0.5) - 0.23 * complexity - 16.2 * (code_lines ** 0.5)
        mi = max(0, mi)
        
        # Normalize to 0-100
        normalized = (mi / 171) * 100
        
        return round(normalized, 2)
    
    async def _check_syntax(self, code: str, language: ProgrammingLanguage) -> bool:
        """
        Check code for syntax errors.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            True if syntax errors found
        """
        if language == ProgrammingLanguage.PYTHON:
            try:
                compile(code, '<string>', 'exec')
                return False
            except SyntaxError:
                return True
                
        elif language == ProgrammingLanguage.JSON:
            try:
                json.loads(code)
                return False
            except json.JSONDecodeError:
                return True
        
        # For other languages, use external tools if available
        if language == ProgrammingLanguage.JAVASCRIPT and self.formatters_available.get("prettier"):
            try:
                result = subprocess.run(
                    ["prettier", "--parser", "babel", "--check"],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode != 0
            except:
                pass
        
        return False
    
    def generate_html(
        self,
        code_blocks: List[Union[str, CodeBlock]],
        options: Optional[FormatOptions] = None,
        include_css: bool = True
    ) -> str:
        """
        Generate complete HTML page with formatted code blocks.
        
        Args:
            code_blocks: List of code blocks
            options: Formatting options
            include_css: Whether to include CSS
            
        Returns:
            Complete HTML page
        """
        options = options or FormatOptions()
        
        html_parts = ['<!DOCTYPE html><html><head><meta charset="UTF-8">']
        html_parts.append('<title>Formatted Code</title>')
        
        if include_css:
            css = self.highlighter.get_css(options.style_name)
            html_parts.append(f'<style>{css}</style>')
        
        html_parts.append('</head><body>')
        
        for i, block in enumerate(code_blocks):
            if isinstance(block, CodeBlock):
                code = block.code
                lang = block.language
                file_name = block.file_name
            else:
                code = block
                lang = None
                file_name = None
            
            # Format code
            result = asyncio.run(self.format_code(code, lang, options, file_name))
            
            # Add to HTML
            if file_name:
                html_parts.append(f'<h3>{file_name}</h3>')
            
            if result.success:
                html_parts.append(f'<div class="code-block">{result.formatted_code}</div>')
            else:
                html_parts.append(f'<pre>{html.escape(code)}</pre>')
        
        html_parts.append('</body></html>')
        
        return ''.join(html_parts)
    
    async def compare_versions(
        self,
        code1: str,
        code2: str,
        language: Optional[ProgrammingLanguage] = None
    ) -> Dict[str, Any]:
        """
        Compare two versions of code and highlight differences.
        
        Args:
            code1: First version
            code2: Second version
            language: Programming language
            
        Returns:
            Comparison results
        """
        import difflib
        
        if language is None:
            language = self.detect_language(code1)
        
        # Generate diff
        lines1 = code1.splitlines()
        lines2 = code2.splitlines()
        
        differ = difflib.SequenceMatcher(None, lines1, lines2)
        diff = list(differ.get_opcodes())
        
        # Analyze changes
        additions = 0
        deletions = 0
        modifications = 0
        
        for tag, i1, i2, j1, j2 in diff:
            if tag == 'replace':
                modifications += max(i2 - i1, j2 - j1)
            elif tag == 'delete':
                deletions += i2 - i1
            elif tag == 'insert':
                additions += j2 - j1
        
        # Format both versions
        formatted1 = await self.format_code(code1, language)
        formatted2 = await self.format_code(code2, language)
        
        return {
            "language": language.value,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "modifications": modifications,
                "total_changes": additions + deletions + modifications
            },
            "diff_blocks": diff,
            "formatted_version1": formatted1.formatted_code,
            "formatted_version2": formatted2.formatted_code,
            "version1_analysis": (await self.analyze_code(code1, language)).to_dict(),
            "version2_analysis": (await self.analyze_code(code2, language)).to_dict()
        }
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.cleanup()
        self.executor.shutdown(wait=False)