import os
import re
import sys
import logging
import argparse
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from notion_client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("notion_researcher")

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
        If file doesn't exist, creates a template and exits.
        """
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"Configuration file '{CONFIG_FILE}' not found.")
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(CONFIG_TEMPLATE)
            logger.info(f"✅ Created template '{CONFIG_FILE}'. Please fill in your Notion Token and Root Page ID.")
            sys.exit(1)

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            if not config or "notion_token" not in config or "root_page_id" not in config:
                logger.error(f"❌ Invalid '{CONFIG_FILE}'. Missing 'notion_token' or 'root_page_id'.")
                sys.exit(1)
                
            # Check for default placeholder values
            if "YOUR_TOKEN_HERE" in config["notion_token"] or "YOUR_ROOT_PAGE_ID_HERE" in config["root_page_id"]:
                logger.error(f"❌ Please update '{CONFIG_FILE}' with your actual credentials.")
                sys.exit(1)
                
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            sys.exit(1)

class NotionSync:
    def __init__(self, config: Dict[str, str]):
        """
        Initialize Notion Client with config.
        """
        self.token = config["notion_token"]
        self.root_page_id = config["root_page_id"]
        
        try:
            self.client = Client(auth=self.token)
            logger.info("Notion Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Notion Client: {e}")
            raise

    def create_child_page(self, title: str) -> Tuple[str, str]:
        """
        Creates a new child page under the root page.
        Returns: (new_page_id, new_page_url)
        """
        logger.info(f"Creating new child page: '{title}' under {self.root_page_id}...")
        try:
            parent = {"page_id": self.root_page_id}
            properties = {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
            response = self.client.pages.create(parent=parent, properties=properties)
            new_page_id = response["id"]
            new_page_url = response["url"]
            logger.info(f"✅ Child page created! ID: {new_page_id}")
            return new_page_id, new_page_url
        except Exception as e:
            logger.error(f"Failed to create child page: {e}")
            raise

    def _parse_inline_elements(self, text_content: str) -> List[Dict[str, Any]]:
        """
        Parses inline elements: LaTeX equations ($...$) and Bold (**...**).
        Priority: Equation > Bold
        """
        math_pattern = r'(\$[^\$]+\$)'
        segments = re.split(math_pattern, text_content)
        
        rich_text = []
        
        for seg in segments:
            if not seg:
                continue
                
            if seg.startswith('$') and seg.endswith('$') and len(seg) > 2:
                expression = seg[1:-1]
                rich_text.append({
                    "type": "equation",
                    "equation": {"expression": expression}
                })
            else:
                bold_pattern = r'(\*\*[^\*]+\*\*)'
                sub_segments = re.split(bold_pattern, seg)
                
                for sub in sub_segments:
                    if not sub:
                        continue
                    
                    if sub.startswith('**') and sub.endswith('**') and len(sub) > 4:
                        content = sub[2:-2]
                        rich_text.append({
                            "type": "text",
                            "text": {"content": content},
                            "annotations": {"bold": True}
                        })
                    else:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": sub}
                        })
                
        return rich_text

    def _create_table_block(self, rows: List[str]) -> Optional[Dict[str, Any]]:
        """
        Constructs a Notion table block from a list of markdown table rows.
        Returns None if no valid rows are found.
        """
        table_rows = []
        max_cols = 0
        
        parsed_rows = []
        for row in rows:
            # 1. Full-width Character Support: Normalize to half-width
            # Note: This is also done in parse_file, but kept here for safety if called independently
            row = row.replace('｜', '|')
            
            # 2. Spacer/Divider Line Filter
            # Skip lines that are separator lines (e.g., |---|---|) or empty spacer lines (e.g., |   |)
            # Regex explains: 
            # ^ starts with
            # [\s\|:\-－]+ matches only whitespace, pipe, colon, dash (half-width), or dash (full-width)
            # $ ends with
            if re.match(r'^[\s\|:\-－]+$', row):
                continue

            cells = [cell.strip() for cell in row.split('|')]
            if row.strip().startswith('|') and len(cells) > 0 and cells[0] == '':
                cells.pop(0)
            if row.strip().endswith('|') and len(cells) > 0 and cells[-1] == '':
                cells.pop()
            
            parsed_rows.append(cells)
            max_cols = max(max_cols, len(cells))
            
        if not parsed_rows:
            logger.warning(f"Table block creation failed: No valid rows found in buffer. First few lines: {rows[:3]}")
            return None

        for cells in parsed_rows:
            while len(cells) < max_cols:
                cells.append("")
            row_cells = []
            for cell_text in cells:
                row_cells.append(self._parse_inline_elements(cell_text))
            table_rows.append({
                "type": "table_row",
                "table_row": {"cells": row_cells}
            })
            
        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": max_cols,
                "has_column_header": False,  # Notion doesn't support setting this via API easily without extra logic
                "has_row_header": False,
                "children": table_rows
            }
        }

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads a file and converts it to Notion blocks.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        blocks = []
        lines = text.split('\n')
        
        table_buffer: List[str] = []
        in_table_mode = False
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # 3. Optimize Main Loop: Normalize full-width pipes immediately
            if '｜' in stripped_line:
                stripped_line = stripped_line.replace('｜', '|')
            
            # 4. Table Detection
            if stripped_line.startswith('|'):
                if not in_table_mode:
                    in_table_mode = True
                    logger.debug(f"Entered table mode at line {i+1}")
                table_buffer.append(stripped_line)
                continue 
            
            if in_table_mode:
                if table_buffer:
                    table_block = self._create_table_block(table_buffer)
                    if table_block:
                        blocks.append(table_block)
                        logger.debug(f"Created table block with {len(table_buffer)} raw rows.")
                    else:
                        # Warning is already logged in _create_table_block
                        pass
                    table_buffer = []
                in_table_mode = False
            
            if not stripped_line:
                continue

            # 5. Ordered List Support
            ordered_list_match = re.match(r'^(\d+)\.\s+(.*)', stripped_line)
            
            if stripped_line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": self._parse_inline_elements(stripped_line[4:])}
                })
            elif stripped_line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": self._parse_inline_elements(stripped_line[3:])}
                })
            elif stripped_line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": self._parse_inline_elements(stripped_line[2:])}
                })
            elif stripped_line.startswith('- ') or stripped_line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": self._parse_inline_elements(stripped_line[2:])}
                })
            elif ordered_list_match:
                content = ordered_list_match.group(2)
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": self._parse_inline_elements(content)}
                })
            elif stripped_line.startswith('$$') and stripped_line.endswith('$$'):
                expression = stripped_line[2:-2].strip()
                blocks.append({
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": expression}
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": self._parse_inline_elements(stripped_line)}
                })
        
        if in_table_mode and table_buffer:
            table_block = self._create_table_block(table_buffer)
            if table_block:
                blocks.append(table_block)
            else:
                pass
            
        return blocks

    def push_to_notion(self, blocks: List[Dict[str, Any]], target_page_id: str):
        """
        Pushes blocks to Notion in batches.
        """
        if not blocks:
            logger.warning("No blocks to push.")
            return

        logger.info(f"Pushing {len(blocks)} blocks to Page {target_page_id}...")
        
        batch_size = 50
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i : i + batch_size]
            try:
                self.client.blocks.children.append(
                    block_id=target_page_id,
                    children=batch
                )
                logger.info(f"Successfully pushed batch {i // batch_size + 1} ({len(batch)} blocks)")
            except Exception as e:
                logger.error(f"Error pushing batch {i // batch_size + 1}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                return

        logger.info("Push completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Notion Researcher - Sync Markdown to Notion")
    parser.add_argument("file", help="Path to the Markdown file")
    parser.add_argument("--title", "-t", help="Title for the new Notion page")
    
    args = parser.parse_args()
    
    # 1. Load Configuration
    config = ConfigLoader.load_config()
    
    # 2. Determine Title
    page_title = args.title
    if not page_title:
        page_title = datetime.now().strftime("%Y-%m-%d %H:%M Report")
        
    try:
        # 3. Initialize Syncer
        syncer = NotionSync(config)
        
        # 4. Parse File
        logger.info(f"Parsing file: {args.file}")
        blocks = syncer.parse_file(args.file)
        
        if not blocks:
            logger.warning("No blocks generated from file. Aborting.")
            return

        # 5. Create Child Page
        new_page_id, new_page_url = syncer.create_child_page(page_title)
        
        # 6. Push Blocks
        syncer.push_to_notion(blocks, new_page_id)
        
        print(f"\n🎉 成功发布！")
        print(f"👉 页面链接: {new_page_url}\n")
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
