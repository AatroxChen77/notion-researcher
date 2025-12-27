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
    parser = argparse.ArgumentParser(description="Notion Researcher - Sync Markdown to Notion",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("file", nargs="?", default="notes/tmp.md",help="Path to the Markdown file", metavar="FILE_PATH")
    parser.add_argument("--title", "-t", help="Title for the new Notion page", metavar="PAGE_TITLE")
    parser.add_argument("--target", "-p", help="Target Notion Page ID or URL (overrides config.yaml)", metavar="ID_OR_URL")
    parser.add_argument("--append", "-a", action="store_true", help="Append to target page instead of creating a child page")
    
    args = parser.parse_args()

    # Step 1: Validate File Existence
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    # Step 2: Fail Fast - Parse Markdown Immediately
    logger.info(f"Parsing file: {args.file}")
    try:
        blocks = parse_markdown_to_blocks(args.file)
    except Exception as e:
        logger.error(f"Failed to parse markdown: {e}")
        sys.exit(1)

    if not blocks:
        logger.warning(f"No content found in {args.file}. Exiting.")
        sys.exit(0)

    # Prepare Title
    page_title = args.title
    if not page_title:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        page_title = f"{timestamp} Log"
        
    # Optimization: Inject Title as H1 if Appending
    if args.append:
        title_block = {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": page_title}}]
            }
        }
        blocks.insert(0, title_block)
    
    # Step 3: Load Configuration (Only if parsing succeeded)
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
        
    # Step 4: Initialize Client and Sync
    try:
        # Dependency Injection: Pass token and ID explicitly
        syncer = NotionSync(token=token, root_page_id=root_page_id)
        
        target_page_id = None
        target_page_url = None # URL is not readily available if we append, unless we query, but we can skip showing it or assume user knows
        
        if args.append:
            logger.info(f"🔄 Appending content directly to page {root_page_id}...")
            target_page_id = root_page_id
        else:
            new_page_id, new_page_url = syncer.create_child_page(page_title)
            target_page_id = new_page_id
            target_page_url = new_page_url
        
        syncer.push_blocks(target_page_id, blocks)
        
        # Logging optimization
        final_url = target_page_url
        if not final_url and args.target and "http" in args.target:
             final_url = args.target
        
        if final_url:
             logger.info(f"✨ Sync complete! View your page here: {final_url}")
        else:
             logger.info(f"✨ Sync complete! Appended to page {target_page_id}.")
             
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
