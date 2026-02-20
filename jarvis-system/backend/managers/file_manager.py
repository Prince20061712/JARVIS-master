import os
import shutil

class FileManager:
    """Manages file operations"""
    
    def list_files(self, directory="."):
        """List files in directory"""
        try:
            files = os.listdir(directory)
            return f"Files in {directory}: {', '.join(files[:10])}" + ("..." if len(files) > 10 else "")
        except:
            return f"Could not list files in {directory}"
    
    def create_file(self, filename):
        """Create a new file"""
        try:
            with open(filename, 'w') as f:
                pass
            return f"Created file: {filename}"
        except:
            return f"Could not create file: {filename}"
    
    def delete_file(self, filename):
        """Delete a file"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return f"Deleted file: {filename}"
            else:
                return f"File not found: {filename}"
        except:
            return f"Could not delete file: {filename}"
    
    def copy_file(self, source, destination):
        """Copy a file"""
        try:
            shutil.copy2(source, destination)
            return f"Copied {source} to {destination}"
        except:
            return f"Could not copy {source} to {destination}"
    
    def move_file(self, source, destination):
        """Move a file"""
        try:
            shutil.move(source, destination)
            return f"Moved {source} to {destination}"
        except:
            return f"Could not move {source} to {destination}"
