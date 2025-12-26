import os
import re
import sys
import logging
import yaml
from typing import Dict, Any

# Configure logging
def setup_logging(name: str = "notion_researcher") -> logging.Logger:
    """
    Configures and returns a logger with standard formatting.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)

logger = logging.getLogger(__name__)

CONFIG_FILE = "config.yaml"
CONFIG_TEMPLATE = """# Notion Researcher Configuration
notion_token: "ntn_YOUR_TOKEN_HERE"
root_page_id: "YOUR_ROOT_PAGE_ID_HERE"
"""

class ConfigLoader:
    @staticmethod
    def load_config() -> Dict[str, str]:
        """
        Loads configuration from config.yaml.
        If file doesn't exist, creates a template.
        """
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"Configuration file '{CONFIG_FILE}' not found.")
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(CONFIG_TEMPLATE)
            logger.info(f"✅ Created template '{CONFIG_FILE}'.")
            # We don't exit here anymore to allow CLI override
            return {}

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return {}

def extract_page_id(input_str: str) -> str:
    """
    Extracts a 32-character Notion Page ID from a string (raw ID or URL).
    Ignores query parameters (after '?').
    
    Args:
        input_str: Raw Page ID or Notion URL.
        
    Returns:
        The 32-character Page ID.
        
    Raises:
        ValueError: If no valid ID is found.
    """
    # Remove query parameters to avoid false positives
    clean_input = input_str.split('?')[0]
    
    # Match 32-character hex string
    match = re.search(r'([a-f0-9]{32})', clean_input)
    if match:
        return match.group(1)
    
    raise ValueError(f"Could not extract a valid 32-char Page ID from: '{input_str}'")
