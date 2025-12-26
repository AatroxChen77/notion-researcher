import os
import sys
import argparse
from datetime import datetime
from src.utils import setup_logging, ConfigLoader, extract_page_id
from src.client import NotionSync
from src.parser import parse_markdown_to_blocks

# Initialize logging globally for the main entry point
logger = setup_logging()

def main():
    parser = argparse.ArgumentParser(description="Notion Researcher - Sync Markdown to Notion")
    parser.add_argument("file", help="Path to the Markdown file")
    parser.add_argument("--title", "-t", help="Title for the new Notion page")
    parser.add_argument("--target", "-p", help="Target Notion Page ID or URL (overrides config.yaml)")
    
    args = parser.parse_args()

    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # 1. Load Configuration
    config = ConfigLoader.load_config()
    
    # Resolve Notion Token
    token = config.get("notion_token")
    if not token or "YOUR_TOKEN_HERE" in token:
        logger.error("❌ Missing valid 'notion_token' in config.yaml.")
        sys.exit(1)
        
    # Resolve Root Page ID
    root_page_id = None
    
    # Priority 1: CLI Argument
    if args.target:
        try:
            root_page_id = extract_page_id(args.target)
            logger.info(f"🎯 Using Target Page ID from CLI: {root_page_id}")
        except ValueError as e:
            logger.error(f"❌ Invalid --target argument: {e}")
            sys.exit(1)
            
    # Priority 2: Config File
    elif config.get("root_page_id") and "YOUR_ROOT_PAGE_ID_HERE" not in config.get("root_page_id"):
        root_page_id = config.get("root_page_id")
        logger.info(f"📂 Using Root Page ID from config.yaml: {root_page_id}")
        
    # Cold Start / Failure
    else:
        logger.error("❌ No Target Page ID found. Please either:\n"
                     "   1. Provide it via --target <id_or_url>\n"
                     "   2. Set 'root_page_id' in config.yaml")
        sys.exit(1)
        
    # 2. Determine Title
    page_title = args.title
    if not page_title:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        page_title = f"{timestamp} Log"
        
    # 3. Initialize Client and Sync
    try:
        # Dependency Injection: Pass token and ID explicitly
        syncer = NotionSync(token=token, root_page_id=root_page_id)
        
        new_page_id, new_page_url = syncer.create_child_page(page_title)
        
        logger.info(f"Parsing file: {args.file}")
        blocks = parse_markdown_to_blocks(args.file)
        
        syncer.push_blocks(new_page_id, blocks)
        logger.info(f"✨ Sync complete! View your page here: {new_page_url}")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
