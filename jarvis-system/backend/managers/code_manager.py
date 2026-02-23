"""
Enhanced Code Editor Manager for macOS
Handles code file creation, editing, project management, and integration with development tools
"""

import os
import sys
import subprocess
import json
import logging
import tempfile
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import ast
import black
import autopep8
import jedi
import pylint
import radon
from radon.complexity import cc_visit
from radon.metrics import h_visit
import git
from git import Repo
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sublime
import vscode
import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import TerminalFormatter
import importlib
import pkg_resources

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    JAVA = "java"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    PERL = "perl"
    LUA = "lua"
    SHELL = "shell"
    SQL = "sql"
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"


class Editor(Enum):
    """Supported code editors"""
    VSCODE = "vscode"
    SUBLIME = "sublime"
    ATOM = "atom"
    PYCHARM = "pycharm"
    INTELLIJ = "intellij"
    ECLIPSE = "eclipse"
    VIM = "vim"
    NEOVIM = "neovim"
    EMACS = "emacs"
    XCODE = "xcode"
    ANDROID_STUDIO = "android_studio"
    DEFAULT = "default"


class CodeTemplate(Enum):
    """Code templates for different languages"""
    PYTHON_SCRIPT = "python_script"
    PYTHON_CLASS = "python_class"
    PYTHON_MAIN = "python_main"
    JAVASCRIPT_FUNCTION = "javascript_function"
    JAVASCRIPT_CLASS = "javascript_class"
    HTML5 = "html5"
    HTML_BASIC = "html_basic"
    CSS3 = "css3"
    JAVA_CLASS = "java_class"
    JAVA_MAIN = "java_main"
    CPP_BASIC = "cpp_basic"
    GO_BASIC = "go_basic"
    RUST_BASIC = "rust_basic"
    SQL_SELECT = "sql_select"
    SQL_CREATE = "sql_create"
    REACT_COMPONENT = "react_component"
    REACT_HOOK = "react_hook"
    VUE_COMPONENT = "vue_component"
    ANGULAR_COMPONENT = "angular_component"


@dataclass
class CodeFile:
    """Code file information"""
    path: Path
    language: Language
    size: int
    created: datetime
    modified: datetime
    lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    imports: List[str] = field(default_factory=list)
    functions: List[Dict] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=list)
    complexity: Optional[float] = None
    maintainability: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    todos: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class Project:
    """Project information"""
    name: str
    path: Path
    language: Language
    files: List[CodeFile] = field(default_factory=list)
    git_repo: Optional[git.Repo] = None
    virtual_env: Optional[Path] = None
    dependencies: List[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    last_build: Optional[datetime] = None
    build_status: Optional[str] = None
    test_coverage: Optional[float] = None


class CodeAnalysisError(Exception):
    """Custom exception for code analysis errors"""
    pass


class CodeEditorManager:
    """
    Enhanced Code Editor Manager with comprehensive features:
    - Multi-language support with templates
    - Code analysis and metrics
    - Project management
    - Git integration
    - Code formatting and linting
    - Auto-completion and suggestions
    - Snippet management
    - Build and run support
    - Dependency management
    - Multiple editor support
    """
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        Initialize the Code Editor Manager
        
        Args:
            workspace_dir: Default workspace directory
        """
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.projects: Dict[str, Project] = {}
        self.current_project: Optional[Project] = None
        self.recent_files: List[Path] = []
        self.snippets: Dict[str, Dict] = self._load_snippets()
        self.editor_paths = self._find_editors()
        self.temp_dir = Path(tempfile.gettempdir()) / "code_manager"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Language configurations
        self.language_configs = self._init_language_configs()
        
        # Template library
        self.templates = self._init_templates()
        
        logger.info(f"Code Editor Manager initialized with workspace: {self.workspace_dir}")
    
    def _find_editors(self) -> Dict[Editor, Optional[Path]]:
        """Find installed code editors"""
        editor_paths = {}
        
        # Common editor paths on macOS
        editor_locations = {
            Editor.VSCODE: [
                "/Applications/Visual Studio Code.app",
                "/usr/local/bin/code",
                "/opt/homebrew/bin/code"
            ],
            Editor.SUBLIME: [
                "/Applications/Sublime Text.app",
                "/Applications/Sublime Text 3.app",
                "/usr/local/bin/subl"
            ],
            Editor.ATOM: [
                "/Applications/Atom.app",
                "/usr/local/bin/atom"
            ],
            Editor.PYCHARM: [
                "/Applications/PyCharm.app",
                "/Applications/PyCharm CE.app"
            ],
            Editor.INTELLIJ: [
                "/Applications/IntelliJ IDEA.app",
                "/Applications/IntelliJ IDEA CE.app"
            ],
            Editor.VIM: [
                "/usr/bin/vim",
                "/usr/local/bin/vim"
            ],
            Editor.NEOVIM: [
                "/usr/local/bin/nvim"
            ],
            Editor.XCODE: [
                "/Applications/Xcode.app"
            ]
        }
        
        for editor, paths in editor_locations.items():
            for path in paths:
                p = Path(path)
                if p.exists():
                    editor_paths[editor] = p
                    break
            else:
                editor_paths[editor] = None
        
        return editor_paths
    
    def _init_language_configs(self) -> Dict[Language, Dict]:
        """Initialize language-specific configurations"""
        return {
            Language.PYTHON: {
                "extension": ".py",
                "shebang": "#!/usr/bin/env python3",
                "comment": "#",
                "formatter": "black",
                "linter": "pylint",
                "test_framework": "pytest",
                "build_cmd": ["python", "-m", "py_compile"],
                "run_cmd": ["python"],
                "indent": 4,
                "keywords": ["def", "class", "import", "from", "if", "else", "for", "while"]
            },
            Language.JAVASCRIPT: {
                "extension": ".js",
                "comment": "//",
                "formatter": "prettier",
                "linter": "eslint",
                "test_framework": "jest",
                "run_cmd": ["node"],
                "indent": 2,
                "keywords": ["function", "class", "const", "let", "var", "if", "else", "for"]
            },
            Language.TYPESCRIPT: {
                "extension": ".ts",
                "comment": "//",
                "formatter": "prettier",
                "linter": "tslint",
                "run_cmd": ["ts-node"],
                "indent": 2,
                "keywords": ["function", "class", "interface", "type", "const", "let"]
            },
            Language.HTML: {
                "extension": ".html",
                "comment": "<!-- -->",
                "formatter": "prettier",
                "indent": 2,
                "keywords": ["html", "head", "body", "div", "span", "script", "style"]
            },
            Language.CSS: {
                "extension": ".css",
                "comment": "/* */",
                "formatter": "prettier",
                "indent": 2,
                "keywords": ["color", "background", "margin", "padding", "font", "display"]
            },
            Language.JAVA: {
                "extension": ".java",
                "comment": "//",
                "formatter": "google-java-format",
                "linter": "checkstyle",
                "build_cmd": ["javac"],
                "run_cmd": ["java"],
                "indent": 4,
                "keywords": ["public", "private", "class", "void", "static", "final"]
            },
            Language.GO: {
                "extension": ".go",
                "comment": "//",
                "formatter": "gofmt",
                "linter": "golint",
                "build_cmd": ["go", "build"],
                "run_cmd": ["go", "run"],
                "indent": 8,
                "keywords": ["func", "type", "struct", "interface", "package", "import"]
            },
            Language.RUST: {
                "extension": ".rs",
                "comment": "//",
                "formatter": "rustfmt",
                "linter": "clippy",
                "build_cmd": ["cargo", "build"],
                "run_cmd": ["cargo", "run"],
                "indent": 4,
                "keywords": ["fn", "let", "mut", "impl", "struct", "enum", "trait"]
            }
        }
    
    def _init_templates(self) -> Dict[CodeTemplate, str]:
        """Initialize code templates"""
        return {
            CodeTemplate.PYTHON_SCRIPT: """#!/usr/bin/env python3
\"\"\"
{filename}
\"\"\"

import sys
import os


def main():
    \"\"\"Main function\"\"\"
    pass


if __name__ == "__main__":
    main()
""",
            CodeTemplate.PYTHON_CLASS: """#!/usr/bin/env python3
\"\"\"
{filename}
\"\"\"


class {class_name}:
    \"\"\"{class_name} class\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the class\"\"\"
        pass
    
    def method(self):
        \"\"\"Example method\"\"\"
        pass
""",
            CodeTemplate.HTML5: """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>{title}</h1>
    </header>
    
    <main>
        <p>Hello, World!</p>
    </main>
    
    <footer>
        <p>&copy; {year}</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
""",
            CodeTemplate.JAVA_CLASS: """/**
 * {class_name} class
 */
public class {class_name} {
    
    /**
     * Constructor
     */
    public {class_name}() {
        // Initialize
    }
    
    /**
     * Main method
     */
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""",
            CodeTemplate.REACT_COMPONENT: """import React from 'react';
import './{component_name}.css';

interface {component_name}Props {
    // Define props here
}

const {component_name}: React.FC<{component_name}Props> = (props) => {
    return (
        <div className="{component_name_lower}">
            <h1>{component_name}</h1>
        </div>
    );
};

export default {component_name};
""",
            CodeTemplate.SQL_CREATE: """-- Create table
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_{table_name}_created ON {table_name}(created_at);
"""
        }
    
    def _load_snippets(self) -> Dict[str, Dict]:
        """Load code snippets"""
        # Default snippets
        return {
            "python": {
                "for": "for item in {iterable}:\n    {pass}",
                "if": "if {condition}:\n    {pass}",
                "class": "class {ClassName}:\n    def __init__(self):\n        {pass}",
                "def": "def {function_name}({params}):\n    \"\"\"{docstring}\"\"\"\n    {pass}",
                "try": "try:\n    {pass}\nexcept {Exception} as e:\n    print(f\"Error: {e}\")"
            },
            "javascript": {
                "for": "for (let i = 0; i < {array}.length; i++) {\n    {pass}\n}",
                "if": "if ({condition}) {\n    {pass}\n}",
                "function": "function {functionName}({params}) {\n    {pass}\n}",
                "arrow": "const {functionName} = ({params}) => {\n    {pass}\n}",
                "try": "try {\n    {pass}\n} catch (error) {\n    console.error(error);\n}"
            }
        }
    
    def _detect_language(self, filename: str, content: str = "") -> Language:
        """Detect programming language from filename and content"""
        ext = Path(filename).suffix.lower()
        
        # Map extensions to languages
        extension_map = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.html': Language.HTML,
            '.htm': Language.HTML,
            '.css': Language.CSS,
            '.java': Language.JAVA,
            '.kt': Language.KOTLIN,
            '.kts': Language.KOTLIN,
            '.swift': Language.SWIFT,
            '.c': Language.C,
            '.h': Language.C,
            '.cpp': Language.CPP,
            '.hpp': Language.CPP,
            '.cc': Language.CPP,
            '.cs': Language.CSHARP,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.php': Language.PHP,
            '.rb': Language.RUBY,
            '.pl': Language.PERL,
            '.lua': Language.LUA,
            '.sh': Language.SHELL,
            '.bash': Language.SHELL,
            '.zsh': Language.SHELL,
            '.sql': Language.SQL,
            '.json': Language.JSON,
            '.xml': Language.XML,
            '.yaml': Language.YAML,
            '.yml': Language.YAML,
            '.md': Language.MARKDOWN,
            '.markdown': Language.MARKDOWN,
            '.txt': Language.TEXT
        }
        
        language = extension_map.get(ext, Language.TEXT)
        
        # Try to guess from content if extension is ambiguous
        if language == Language.TEXT and content:
            try:
                lexer = guess_lexer(content)
                if 'Python' in lexer.name:
                    language = Language.PYTHON
                elif 'JavaScript' in lexer.name:
                    language = Language.JAVASCRIPT
                elif 'HTML' in lexer.name:
                    language = Language.HTML
                elif 'CSS' in lexer.name:
                    language = Language.CSS
            except:
                pass
        
        return language
    
    def _get_language_config(self, language: Language) -> Dict:
        """Get configuration for a language"""
        return self.language_configs.get(language, self.language_configs[Language.TEXT])
    
    def create_code_file(self, filename: Union[str, Path],
                        language: Union[str, Language] = Language.PYTHON,
                        template: Union[str, CodeTemplate] = None,
                        content: str = "",
                        open_in_editor: bool = False,
                        editor: Union[str, Editor] = Editor.VSCODE) -> Dict[str, Any]:
        """
        Create a code file with template support
        
        Args:
            filename: File name or path
            language: Programming language
            template: Template to use
            content: Additional content
            open_in_editor: Open file in editor after creation
            editor: Editor to use
            
        Returns:
            Dictionary with creation result
        """
        result = {
            "success": False,
            "message": "",
            "file_path": None,
            "language": None,
            "template_used": None
        }
        
        try:
            # Convert language to enum
            if isinstance(language, str):
                language = Language(language.lower())
            
            # Resolve file path
            file_path = Path(filename)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path
            
            # Add extension if missing
            if not file_path.suffix:
                config = self._get_language_config(language)
                file_path = file_path.with_suffix(config["extension"])
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate content from template
            final_content = content
            template_used = None
            
            if template:
                if isinstance(template, str):
                    template = CodeTemplate(template)
                
                template_used = template.value
                template_content = self.templates.get(template, "")
                
                # Fill template variables
                vars = {
                    "filename": file_path.name,
                    "class_name": file_path.stem.capitalize(),
                    "component_name": file_path.stem,
                    "component_name_lower": file_path.stem.lower(),
                    "title": file_path.stem.replace("_", " ").title(),
                    "year": datetime.now().year,
                    "table_name": file_path.stem.lower()
                }
                
                template_content = template_content.format(**vars)
                final_content = template_content + "\n" + content
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            result["success"] = True
            result["message"] = f"Created {file_path.name}"
            result["file_path"] = str(file_path)
            result["language"] = language.value
            result["template_used"] = template_used
            
            # Add to recent files
            self.recent_files.append(file_path)
            if len(self.recent_files) > 20:
                self.recent_files.pop(0)
            
            logger.info(f"Created code file: {file_path}")
            
            # Open in editor if requested
            if open_in_editor:
                open_result = self.open_in_editor(file_path, editor)
                result["editor_result"] = open_result
            
        except Exception as e:
            result["message"] = f"Error creating file: {e}"
            logger.exception("Code file creation error")
        
        return result
    
    def open_in_editor(self, file_or_project: Union[str, Path, None] = None,
                      editor: Union[str, Editor] = Editor.VSCODE,
                      line: Optional[int] = None,
                      column: Optional[int] = None) -> Dict[str, Any]:
        """
        Open file or project in code editor
        
        Args:
            file_or_project: File or project path (None for current workspace)
            editor: Editor to use
            line: Line number to navigate to
            column: Column number to navigate to
            
        Returns:
            Dictionary with open result
        """
        result = {
            "success": False,
            "message": "",
            "editor_used": None,
            "path": None
        }
        
        try:
            # Convert editor to enum
            if isinstance(editor, str):
                # Handle common names
                editor_map = {
                    "vscode": Editor.VSCODE,
                    "code": Editor.VSCODE,
                    "sublime": Editor.SUBLIME,
                    "subl": Editor.SUBLIME,
                    "atom": Editor.ATOM,
                    "pycharm": Editor.PYCHARM,
                    "intellij": Editor.INTELLIJ,
                    "vim": Editor.VIM,
                    "nvim": Editor.NEOVIM,
                    "xcode": Editor.XCODE
                }
                editor = editor_map.get(editor.lower(), Editor.VSCODE)
            
            # Resolve path
            if file_or_project:
                target_path = Path(file_or_project)
                if not target_path.is_absolute():
                    target_path = self.workspace_dir / target_path
            else:
                target_path = self.workspace_dir
            
            # Check if path exists
            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {target_path}")
            
            # Get editor path
            editor_path = self.editor_paths.get(editor)
            if not editor_path:
                raise Exception(f"Editor {editor.value} not found")
            
            # Build command
            if editor == Editor.VSCODE:
                cmd = [str(editor_path), '--new-window']
                if line and target_path.is_file():
                    cmd.append(f"{target_path}:{line}:{column or 1}")
                else:
                    cmd.append(str(target_path))
            
            elif editor == Editor.SUBLIME:
                cmd = [str(editor_path)]
                if line and target_path.is_file():
                    cmd.append(f"{target_path}:{line}")
                else:
                    cmd.append(str(target_path))
            
            elif editor == Editor.VIM:
                cmd = [str(editor_path), str(target_path)]
                if line:
                    cmd.append(f"+{line}")
            
            else:
                cmd = ['open', '-a', str(editor_path), str(target_path)]
            
            # Execute command
            subprocess.run(cmd, check=True)
            
            result["success"] = True
            result["message"] = f"Opened in {editor.value}"
            result["editor_used"] = editor.value
            result["path"] = str(target_path)
            
            logger.info(f"Opened {target_path} in {editor.value}")
            
        except FileNotFoundError as e:
            result["message"] = str(e)
            logger.error(f"Editor open error: {e}")
        except subprocess.CalledProcessError as e:
            result["message"] = f"Editor command failed: {e}"
            logger.error(f"Editor command error: {e}")
        except Exception as e:
            result["message"] = f"Error opening in editor: {e}"
            logger.exception("Editor open error")
        
        return result
    
    def write_code(self, code: str, filename: Union[str, Path] = "code.py",
                  mode: str = "a",
                  language: Optional[Union[str, Language]] = None,
                  format_code: bool = True) -> Dict[str, Any]:
        """
        Write code to a file with formatting
        
        Args:
            code: Code to write
            filename: Target filename
            mode: Write mode ('w' for overwrite, 'a' for append)
            language: Programming language (auto-detect if None)
            format_code: Format code before writing
            
        Returns:
            Dictionary with write result
        """
        result = {
            "success": False,
            "message": "",
            "file_path": None,
            "lines_written": 0
        }
        
        try:
            # Resolve file path
            file_path = Path(filename)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path
            
            # Detect language
            if not language:
                language = self._detect_language(file_path.name, code)
            elif isinstance(language, str):
                language = Language(language.lower())
            
            # Format code if requested
            if format_code and code.strip():
                try:
                    formatted_code = self.format_code(code, language)
                    if formatted_code:
                        code = formatted_code
                except Exception as e:
                    logger.warning(f"Code formatting failed: {e}")
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write code
            with open(file_path, mode, encoding='utf-8') as f:
                if mode == 'a' and file_path.exists() and file_path.stat().st_size > 0:
                    # Add newline before appending
                    f.write('\n')
                f.write(code)
            
            # Count lines
            lines_written = len(code.splitlines())
            
            result["success"] = True
            result["message"] = f"Code written to {file_path}"
            result["file_path"] = str(file_path)
            result["lines_written"] = lines_written
            
            # Add to recent files
            self.recent_files.append(file_path)
            
            logger.info(f"Wrote {lines_written} lines to {file_path}")
            
        except Exception as e:
            result["message"] = f"Error writing code: {e}"
            logger.exception("Code write error")
        
        return result
    
    def format_code(self, code: str, language: Language) -> Optional[str]:
        """
        Format code according to language standards
        
        Args:
            code: Code to format
            language: Programming language
            
        Returns:
            Formatted code or None if formatting failed
        """
        try:
            if language == Language.PYTHON:
                # Try black first
                try:
                    return black.format_str(code, mode=black.Mode())
                except:
                    # Fallback to autopep8
                    return autopep8.fix_code(code)
            
            elif language == Language.JAVASCRIPT:
                # Use prettier if available
                try:
                    import subprocess
                    result = subprocess.run(
                        ['prettier', '--stdin-filepath', 'dummy.js'],
                        input=code,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    return result.stdout
                except:
                    # Simple JS formatting
                    return code
            
            elif language == Language.JSON:
                # Pretty print JSON
                try:
                    data = json.loads(code)
                    return json.dumps(data, indent=2)
                except:
                    return code
            
            else:
                return code
                
        except Exception as e:
            logger.error(f"Formatting error: {e}")
            return code
    
    def analyze_code(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze code file for metrics and issues
        
        Args:
            file_path: Path to code file
            
        Returns:
            Dictionary with analysis results
        """
        result = {
            "success": False,
            "message": "",
            "file_info": None,
            "metrics": {},
            "issues": [],
            "suggestions": []
        }
        
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_language(file_path.name, content)
            
            # Basic stats
            lines = content.splitlines()
            total_lines = len(lines)
            code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith(('#', '//', '/*')))
            comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*')))
            blank_lines = total_lines - code_lines - comment_lines
            
            file_info = {
                "path": str(file_path),
                "language": language.value,
                "size": file_path.stat().st_size,
                "lines": {
                    "total": total_lines,
                    "code": code_lines,
                    "comments": comment_lines,
                    "blank": blank_lines
                },
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Language-specific analysis
            if language == Language.PYTHON:
                # Parse AST
                try:
                    tree = ast.parse(content)
                    
                    # Find imports
                    imports = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            imports.append(f"{node.module}.{node.names[0].name}")
                    
                    file_info["imports"] = imports
                    
                    # Find functions and classes
                    functions = []
                    classes = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.append({
                                "name": node.name,
                                "line": node.lineno,
                                "args": [arg.arg for arg in node.args.args]
                            })
                        elif isinstance(node, ast.ClassDef):
                            classes.append({
                                "name": node.name,
                                "line": node.lineno
                            })
                    
                    file_info["functions"] = functions
                    file_info["classes"] = classes
                    
                    # Calculate complexity with radon
                    try:
                        complexity_results = cc_visit(content)
                        avg_complexity = sum(c.complexity for c in complexity_results) / len(complexity_results) if complexity_results else 0
                        file_info["complexity"] = avg_complexity
                        
                        # Maintainability index
                        try:
                            mi_result = h_visit(content)
                            file_info["maintainability"] = mi_result.mi if mi_result else None
                        except:
                            pass
                    except:
                        pass
                    
                except SyntaxError as e:
                    result["issues"].append({
                        "type": "syntax",
                        "line": e.lineno,
                        "message": str(e)
                    })
            
            # Find TODOs and FIXMEs
            todos = []
            for i, line in enumerate(lines, 1):
                if 'TODO' in line or 'FIXME' in line:
                    todos.append({
                        "line": i,
                        "text": line.strip()
                    })
            
            file_info["todos"] = todos
            
            result["success"] = True
            result["message"] = f"Analysis complete for {file_path.name}"
            result["file_info"] = file_info
            
        except FileNotFoundError as e:
            result["message"] = str(e)
            logger.error(f"Code analysis error: {e}")
        except Exception as e:
            result["message"] = f"Error analyzing code: {e}"
            logger.exception("Code analysis error")
        
        return result
    
    def create_project(self, name: str, language: Union[str, Language],
                      path: Optional[Union[str, Path]] = None,
                      template: str = "basic",
                      init_git: bool = True,
                      create_virtual_env: bool = False) -> Dict[str, Any]:
        """
        Create a new project with structure
        
        Args:
            name: Project name
            language: Programming language
            path: Project path (defaults to workspace/name)
            template: Project template
            init_git: Initialize git repository
            create_virtual_env: Create virtual environment (Python only)
            
        Returns:
            Dictionary with project creation result
        """
        result = {
            "success": False,
            "message": "",
            "project_path": None,
            "language": None
        }
        
        try:
            # Convert language to enum
            if isinstance(language, str):
                language = Language(language.lower())
            
            # Determine project path
            if path:
                project_path = Path(path)
            else:
                project_path = self.workspace_dir / name
            
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create project structure based on language
            if language == Language.PYTHON:
                # Python project structure
                (project_path / "src").mkdir(exist_ok=True)
                (project_path / "tests").mkdir(exist_ok=True)
                (project_path / "docs").mkdir(exist_ok=True)
                
                # Create __init__.py files
                (project_path / "src" / "__init__.py").touch()
                (project_path / "tests" / "__init__.py").touch()
                
                # Create README
                with open(project_path / "README.md", 'w') as f:
                    f.write(f"# {name}\n\nProject description\n")
                
                # Create requirements.txt
                with open(project_path / "requirements.txt", 'w') as f:
                    f.write("# Add dependencies here\n")
                
                # Create setup.py
                with open(project_path / "setup.py", 'w') as f:
                    f.write(f"""from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    install_requires=[],
    author="",
    author_email="",
    description="",
    keywords="",
    url="",
)
""")
                
                # Create main module
                main_file = project_path / "src" / "main.py"
                self.create_code_file(main_file, language, template=CodeTemplate.PYTHON_MAIN)
                
                # Create virtual environment if requested
                if create_virtual_env:
                    import venv
                    venv.create(project_path / "venv", with_pip=True)
            
            elif language == Language.JAVASCRIPT:
                # Node.js project structure
                (project_path / "src").mkdir(exist_ok=True)
                (project_path / "tests").mkdir(exist_ok=True)
                
                # Create package.json
                package_json = {
                    "name": name,
                    "version": "1.0.0",
                    "description": "",
                    "main": "src/index.js",
                    "scripts": {
                        "test": "jest",
                        "start": "node src/index.js"
                    },
                    "keywords": [],
                    "author": "",
                    "license": "ISC",
                    "devDependencies": {},
                    "dependencies": {}
                }
                
                with open(project_path / "package.json", 'w') as f:
                    json.dump(package_json, f, indent=2)
                
                # Create README
                with open(project_path / "README.md", 'w') as f:
                    f.write(f"# {name}\n\nProject description\n")
                
                # Create main file
                main_file = project_path / "src" / "index.js"
                with open(main_file, 'w') as f:
                    f.write("console.log('Hello, World!');\n")
            
            # Initialize git repository
            if init_git:
                repo = git.Repo.init(project_path)
                
                # Create .gitignore
                gitignore_content = self._get_gitignore_template(language)
                with open(project_path / ".gitignore", 'w') as f:
                    f.write(gitignore_content)
                
                # Initial commit
                repo.index.add("*")
                repo.index.commit("Initial commit")
            
            # Create project object
            project = Project(
                name=name,
                path=project_path,
                language=language,
                git_repo=repo if init_git else None
            )
            
            self.projects[name] = project
            self.current_project = project
            
            result["success"] = True
            result["message"] = f"Created project: {name}"
            result["project_path"] = str(project_path)
            result["language"] = language.value
            
            logger.info(f"Created project {name} at {project_path}")
            
        except Exception as e:
            result["message"] = f"Error creating project: {e}"
            logger.exception("Project creation error")
        
        return result
    
    def _get_gitignore_template(self, language: Language) -> str:
        """Get .gitignore template for language"""
        templates = {
            Language.PYTHON: """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
dist/
build/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
""",
            Language.JAVASCRIPT: """# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
lerna-debug.log*

# Environment
.env
.env.local
.env.*.local

# Build
dist/
build/
*.tsbuildinfo

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
"""
        }
        
        return templates.get(language, "# .gitignore\n")
    
    def run_code(self, file_path: Union[str, Path],
                args: List[str] = None,
                capture_output: bool = False) -> Dict[str, Any]:
        """
        Run code file
        
        Args:
            file_path: Path to code file
            args: Command line arguments
            capture_output: Capture stdout/stderr
            
        Returns:
            Dictionary with execution result
        """
        result = {
            "success": False,
            "message": "",
            "stdout": "",
            "stderr": "",
            "return_code": -1
        }
        
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Detect language
            language = self._detect_language(file_path.name)
            config = self._get_language_config(language)
            
            # Build command
            if language == Language.PYTHON:
                cmd = ["python", str(file_path)]
            elif language == Language.JAVASCRIPT:
                cmd = ["node", str(file_path)]
            elif language == Language.JAVA:
                # Compile first
                class_name = file_path.stem
                compile_cmd = ["javac", str(file_path)]
                subprocess.run(compile_cmd, check=True, cwd=file_path.parent)
                cmd = ["java", "-cp", str(file_path.parent), class_name]
            else:
                raise Exception(f"Running {language.value} files is not supported")
            
            # Add arguments
            if args:
                cmd.extend(args)
            
            # Run command
            if capture_output:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=file_path.parent,
                    timeout=30
                )
                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr
                result["return_code"] = proc.returncode
                result["success"] = proc.returncode == 0
                result["message"] = "Execution completed"
            else:
                # Run in terminal
                subprocess.Popen(
                    cmd,
                    cwd=file_path.parent
                )
                result["success"] = True
                result["message"] = "Started execution in new terminal"
            
            logger.info(f"Executed {file_path}")
            
        except FileNotFoundError as e:
            result["message"] = str(e)
            logger.error(f"Code execution error: {e}")
        except subprocess.TimeoutExpired:
            result["message"] = "Execution timed out"
            logger.error("Code execution timeout")
        except subprocess.CalledProcessError as e:
            result["message"] = f"Compilation failed: {e}"
            logger.error(f"Code compilation error: {e}")
        except Exception as e:
            result["message"] = f"Error running code: {e}"
            logger.exception("Code execution error")
        
        return result
    
    def get_snippet(self, language: Union[str, Language],
                   snippet_name: str,
                   variables: Dict[str, str] = None) -> Optional[str]:
        """
        Get a code snippet
        
        Args:
            language: Programming language
            snippet_name: Snippet name
            variables: Variables to replace in snippet
            
        Returns:
            Snippet text or None if not found
        """
        if isinstance(language, str):
            language = Language(language.lower())
        
        lang_snippets = self.snippets.get(language.value, {})
        snippet = lang_snippets.get(snippet_name)
        
        if snippet and variables:
            for key, value in variables.items():
                snippet = snippet.replace(f"{{{key}}}", value)
        
        return snippet
    
    def add_snippet(self, language: Union[str, Language],
                   name: str,
                   template: str) -> bool:
        """
        Add a custom code snippet
        
        Args:
            language: Programming language
            name: Snippet name
            template: Snippet template
            
        Returns:
            Success status
        """
        try:
            if isinstance(language, str):
                language = Language(language.lower())
            
            if language.value not in self.snippets:
                self.snippets[language.value] = {}
            
            self.snippets[language.value][name] = template
            logger.info(f"Added snippet '{name}' for {language.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding snippet: {e}")
            return False
    
    def get_completions(self, code: str, line: int, column: int,
                       language: Union[str, Language]) -> List[Dict]:
        """
        Get code completions at position
        
        Args:
            code: Current code content
            line: Line number (1-indexed)
            column: Column number
            language: Programming language
            
        Returns:
            List of completion suggestions
        """
        completions = []
        
        try:
            if isinstance(language, str):
                language = Language(language.lower())
            
            if language == Language.PYTHON:
                # Use Jedi for Python completions
                script = jedi.Script(code, path='dummy.py')
                completions = script.complete(line, column)
                
                return [
                    {
                        "name": c.name,
                        "type": c.type,
                        "description": c.docstring(),
                        "complete": c.complete
                    }
                    for c in completions[:10]
                ]
            
            # For other languages, return simple completions
            # This could be extended with language servers
            
        except Exception as e:
            logger.error(f"Completion error: {e}")
        
        return completions
    
    def get_definition(self, code: str, line: int, column: int,
                      language: Union[str, Language]) -> Optional[Dict]:
        """
        Get definition location of symbol at position
        
        Args:
            code: Current code content
            line: Line number (1-indexed)
            column: Column number
            language: Programming language
            
        Returns:
            Definition location or None
        """
        try:
            if isinstance(language, str):
                language = Language(language.lower())
            
            if language == Language.PYTHON:
                script = jedi.Script(code, path='dummy.py')
                definitions = script.goto(line, column)
                
                if definitions:
                    defn = definitions[0]
                    return {
                        "name": defn.name,
                        "module": defn.module_name,
                        "line": defn.line,
                        "column": defn.column,
                        "description": defn.docstring()
                    }
            
        except Exception as e:
            logger.error(f"Definition error: {e}")
        
        return None
    
    def get_recent_files(self, limit: int = 10) -> List[Dict]:
        """Get recently opened/created files"""
        return [
            {
                "path": str(p),
                "name": p.name,
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat() if p.exists() else None
            }
            for p in self.recent_files[-limit:]
        ]
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        return [
            {
                "name": p.name,
                "path": str(p.path),
                "language": p.language.value,
                "files": len(p.files),
                "created": p.created.isoformat()
            }
            for p in self.projects.values()
        ]
    
    def search_in_files(self, search_term: str,
                       file_pattern: str = "*",
                       path: Optional[Union[str, Path]] = None) -> List[Dict]:
        """
        Search for text in files
        
        Args:
            search_term: Text to search for
            file_pattern: File pattern to search in
            path: Base path to search
            
        Returns:
            List of matches with file and line info
        """
        matches = []
        
        try:
            search_path = Path(path) if path else self.workspace_dir
            
            for file_path in search_path.rglob(file_pattern):
                if not file_path.is_file():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            if search_term in line:
                                matches.append({
                                    "file": str(file_path),
                                    "line": i,
                                    "content": line.strip(),
                                    "context": {
                                        "prev": None,  # Could add context
                                        "next": None
                                    }
                                })
                except (UnicodeDecodeError, PermissionError):
                    continue
                
                # Limit results
                if len(matches) > 100:
                    break
        
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return matches
    
    def install_dependency(self, dependency: str,
                          project: Optional[str] = None) -> Dict[str, Any]:
        """
        Install a dependency for a project
        
        Args:
            dependency: Dependency name
            project: Project name (uses current project if None)
            
        Returns:
            Installation result
        """
        result = {
            "success": False,
            "message": "",
            "dependency": dependency
        }
        
        try:
            # Get project
            target_project = None
            if project:
                target_project = self.projects.get(project)
            else:
                target_project = self.current_project
            
            if not target_project:
                raise Exception("No project specified")
            
            # Install based on project language
            if target_project.language == Language.PYTHON:
                cmd = [sys.executable, "-m", "pip", "install", dependency]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                
                if proc.returncode == 0:
                    # Update requirements.txt
                    req_file = target_project.path / "requirements.txt"
                    with open(req_file, 'a') as f:
                        f.write(f"{dependency}\n")
                    
                    target_project.dependencies.append(dependency)
                    result["success"] = True
                    result["message"] = f"Installed {dependency}"
                else:
                    result["message"] = f"Installation failed: {proc.stderr}"
            
            elif target_project.language == Language.JAVASCRIPT:
                cmd = ["npm", "install", dependency, "--save"]
                proc = subprocess.run(cmd, capture_output=True, text=True, cwd=target_project.path)
                
                if proc.returncode == 0:
                    result["success"] = True
                    result["message"] = f"Installed {dependency}"
                else:
                    result["message"] = f"Installation failed: {proc.stderr}"
            
            logger.info(result["message"])
            
        except Exception as e:
            result["message"] = f"Error installing dependency: {e}"
            logger.exception("Dependency installation error")
        
        return result
    
    def format_all_files(self, project: Optional[str] = None) -> Dict[str, Any]:
        """
        Format all files in a project
        
        Args:
            project: Project name (uses current project if None)
            
        Returns:
            Formatting result
        """
        result = {
            "success": False,
            "message": "",
            "files_formatted": 0,
            "errors": []
        }
        
        try:
            # Get project
            target_project = None
            if project:
                target_project = self.projects.get(project)
            else:
                target_project = self.current_project
            
            if not target_project:
                raise Exception("No project specified")
            
            # Find all code files
            extensions = {
                Language.PYTHON: ['.py'],
                Language.JAVASCRIPT: ['.js', '.jsx'],
                Language.TYPESCRIPT: ['.ts', '.tsx'],
                Language.HTML: ['.html', '.htm'],
                Language.CSS: ['.css'],
                Language.JSON: ['.json']
            }
            
            file_exts = extensions.get(target_project.language, [])
            
            for file_path in target_project.path.rglob('*'):
                if file_path.suffix in file_exts:
                    try:
                        # Read file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Format
                        formatted = self.format_code(content, target_project.language)
                        
                        if formatted and formatted != content:
                            # Write back
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(formatted)
                            result["files_formatted"] += 1
                            
                    except Exception as e:
                        result["errors"].append(f"{file_path}: {e}")
            
            result["success"] = True
            result["message"] = f"Formatted {result['files_formatted']} files"
            
        except Exception as e:
            result["message"] = f"Error formatting files: {e}"
            logger.exception("Formatting error")
        
        return result
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """Get information about current workspace"""
        info = {
            "workspace_dir": str(self.workspace_dir),
            "exists": self.workspace_dir.exists(),
            "projects": len(self.projects),
            "current_project": self.current_project.name if self.current_project else None,
            "recent_files": len(self.recent_files),
            "available_editors": [
                {"name": e.value, "available": p is not None}
                for e, p in self.editor_paths.items()
            ],
            "languages_supported": [lang.value for lang in Language]
        }
        
        # Count files by language
        if self.workspace_dir.exists():
            file_counts = {}
            for ext, lang in {
                '.py': 'python',
                '.js': 'javascript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json'
            }.items():
                count = len(list(self.workspace_dir.rglob(f"*{ext}")))
                if count > 0:
                    file_counts[lang] = count
            info["file_counts"] = file_counts
        
        return info


# CLI interface for testing
if __name__ == "__main__":
    import sys
    import pprint
    
    manager = CodeEditorManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create" and len(sys.argv) > 2:
            filename = sys.argv[2]
            language = sys.argv[3] if len(sys.argv) > 3 else "python"
            result = manager.create_code_file(filename, language)
            pprint.pprint(result)
        
        elif command == "open" and len(sys.argv) > 2:
            filename = sys.argv[2]
            editor = sys.argv[3] if len(sys.argv) > 3 else "vscode"
            result = manager.open_in_editor(filename, editor)
            pprint.pprint(result)
        
        elif command == "analyze" and len(sys.argv) > 2:
            filename = sys.argv[2]
            result = manager.analyze_code(filename)
            pprint.pprint(result)
        
        elif command == "project" and len(sys.argv) > 3:
            name = sys.argv[2]
            language = sys.argv[3]
            result = manager.create_project(name, language)
            pprint.pprint(result)
        
        elif command == "run" and len(sys.argv) > 2:
            filename = sys.argv[2]
            result = manager.run_code(filename)
            pprint.pprint(result)
        
        elif command == "search" and len(sys.argv) > 2:
            term = sys.argv[2]
            results = manager.search_in_files(term)
            pprint.pprint(results[:10])
        
        elif command == "info":
            info = manager.get_workspace_info()
            pprint.pprint(info)
        
        else:
            print("Usage: code_manager.py [create|open|analyze|project|run|search|info] [args]")
    else:
        # Demo mode
        print("Code Editor Manager Demo")
        print("-" * 50)
        
        # Get workspace info
        print("\nWorkspace Info:")
        info = manager.get_workspace_info()
        pprint.pprint(info)
        
        # Create a test file
        print("\nCreating test file:")
        result = manager.create_code_file("test.py", "python", template="python_script")
        print(f"  {result['message']}")
        
        # Analyze the file
        print("\nAnalyzing test file:")
        result = manager.analyze_code("test.py")
        if result['success']:
            file_info = result['file_info']
            print(f"  Language: {file_info['language']}")
            print(f"  Lines: {file_info['lines']['total']}")
        
        # Create a project
        print("\nCreating test project:")
        result = manager.create_project("test_project", "python", init_git=True)
        print(f"  {result['message']}")
        
        # Get completions
        print("\nTesting completions:")
        code = "import os\nos."
        completions = manager.get_completions(code, 2, 4, "python")
        print(f"  Found {len(completions)} completions")