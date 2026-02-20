import os

class CodeEditorManager:
    """Manages code editing and file creation"""
    
    def create_code_file(self, filename, language="python", content=""):
        """Create a code file"""
        if not '.' in filename:
            if language == "python":
                filename += ".py"
            elif language == "javascript":
                filename += ".js"
            elif language == "html":
                filename += ".html"
            elif language == "css":
                filename += ".css"
            elif language == "java":
                filename += ".java"
            else:
                filename += ".txt"
        
        try:
            with open(filename, "w") as f:
                if content:
                    f.write(content)
                else:
                    if language == "python":
                        f.write(f'#!/usr/bin/env python3\n"""\n{filename}\n"""\n\n')
                    elif language == "html":
                        f.write(f'<!DOCTYPE html>\n<html>\n<head>\n<title>{filename}</title>\n</head>\n<body>\n\n</body>\n</html>')
            
            return f"Created {filename} with {language} content"
        except Exception as e:
            return f"Could not create file: {e}"
    
    def open_in_vscode(self, filename=None):
        """Open file or folder in VS Code"""
        try:
            if filename:
                os.system(f'code "{filename}"')
                return f"Opening {filename} in VS Code"
            else:
                os.system("code .")
                return "Opening current directory in VS Code"
        except:
            return "VS Code not found. Install it from https://code.visualstudio.com/"
    
    def write_code(self, code, filename="code.py"):
        """Write code to a file"""
        try:
            with open(filename, "a") as f:
                f.write(code + "\n")
            return f"Code written to {filename}"
        except:
            return "Could not write code"
