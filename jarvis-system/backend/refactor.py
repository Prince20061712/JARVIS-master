with open('main.py', 'r') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith("class AudioSystem:"):
        start_idx = i
    if line.startswith("# ========== MAIN JARVIS CLASS =========="):
        end_idx = i

if start_idx != -1 and end_idx != -1:
    imports = [
        "from managers.audio_manager import AudioSystem\n",
        "from managers.app_manager import ApplicationManager\n",
        "from managers.browser_manager import BrowserManager\n",
        "from managers.media_manager import MediaManager\n",
        "from managers.screen_manager import ScreenCaptureManager\n",
        "from managers.code_manager import CodeEditorManager\n",
        "from managers.system_manager import SystemUtilitiesManager\n",
        "from managers.voice_manager import VoiceTypingManager\n",
        "from managers.file_manager import FileManager\n\n"
    ]
    new_lines = lines[:start_idx] + imports + lines[end_idx:]
    with open('main.py', 'w') as f:
        f.writelines(new_lines)
    print("Successfully refactored main.py")
else:
    print(f"Could not find indices: start={start_idx}, end={end_idx}")
