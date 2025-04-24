\
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the path for the configuration file
CONFIG_FILE = Path(__file__).parent.parent / 'config.json' # Place config.json in the root directory

# Define default configuration settings
DEFAULT_CONFIG = {
    "ollama_base_url": "http://localhost:11434",
    "ollama_timeout": 60,
    "bot_name": "NiceBot",
    "default_model": None, # Will be populated by available models if None
    "source_urls": [],
    "theme_dark_mode": False,
    "available_models_cache": [] # Cache for available models
}

# In-memory storage for the current configuration
_config: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    # \"\"\"Loads configuration from the JSON file or uses defaults.\"\"\"
    global _config
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_data = json.load(f)
                # Merge loaded data with defaults to ensure all keys exist
                _config = {**DEFAULT_CONFIG, **loaded_data}
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config file {CONFIG_FILE}: {e}. Using default configuration.")
            _config = DEFAULT_CONFIG.copy()
    else:
        logger.warning(f"Config file {CONFIG_FILE} not found. Using default configuration.")
        _config = DEFAULT_CONFIG.copy()
    return _config # Ensure the config dictionary is always returned

def save_config() -> bool:
    # \"\"\"Saves the current configuration to the JSON file.\"\"\"
    global _config
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(_config, f, indent=4)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except IOError as e:
        logger.error(f"Error saving config file {CONFIG_FILE}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving config: {e}")
        return False

def get_config() -> Dict[str, Any]:
    # \"\"\"Returns the current configuration dictionary.\"\"\"
    if not _config: # Load if not already loaded
        load_config()
    return _config

def update_config_value(key: str, value: Any) -> None:
    # \"\"\"Updates a specific value in the configuration.\"\"\"
    global _config
    if not _config:
        load_config()
    _config[key] = value
    logger.info(f"Configuration value '{key}' updated.")

def get_available_models_cache() -> List[str]:
    # \"\"\"Gets the cached list of available models.\"\"\"
    return get_config().get("available_models_cache", [])

def set_available_models_cache(models: List[str]) -> None:
    # \"\"\"Sets the cached list of available models in the config.\"\"\"
    update_config_value("available_models_cache", models)
    # Optionally save immediately, or rely on explicit save from UI
    # save_config()

def get_default_model() -> Optional[str]:
    #  \"\"\"Gets the default model, trying the first cached model if not set.\"\"\"
     config = get_config()
     default = config.get("default_model")
     if not default:
         cached_models = config.get("available_models_cache", [])
         if cached_models:
             return cached_models[0]
     return default

def set_default_model(model_name: Optional[str]) -> None:
    # \"\"\"Sets the default model.\"\"\"
    update_config_value("default_model", model_name)
