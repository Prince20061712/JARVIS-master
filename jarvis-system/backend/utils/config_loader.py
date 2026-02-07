import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    """
    try:
        # Resolve absolute path relative to this file
        base_dir = Path(__file__).parent.parent # assistant-robot/
        config_file = base_dir / config_path
        
        if not config_file.exists():
             # Try absolute in case it was passed
             config_file = Path(config_path)

        if not config_file.exists():
            print(f"Config file not found: {config_file}")
            return {}

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            return config or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}
