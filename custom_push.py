import os
import re
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from notion_client import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class NotionSync:
    def __init__(self, token: Optional[str] = None, root_page_id: Optional[str] = None):
        """
        Initialize Notion Client and Root Page ID.
        Reads from environment variables if not provided.
        """
        self.token = token or os.getenv("NOTION_TOKEN", "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")
        self.root_page_id = root_page_id or os.getenv("PAGE_ID", "2d44f05de2a8807a8656f25e40709111")
        
        if not self.token:
            logger.error("Notion Token is missing")
            raise ValueError("Notion Token is missing")
        if not self.root_page_id:
            logger.error("Root Page ID is missing")
            raise ValueError("Root Page ID is missing")
            
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
        # Step 1: Split by equation ($)
        # Logic: Formulas have highest priority to prevent characters inside from being misidentified
        math_pattern = r'(\$[^\$]+\$)'
        segments = re.split(math_pattern, text_content)
        
        rich_text = []
        
        for seg in segments:
            if not seg:
                continue
                
            # Case A: Equation ($...$)
            if seg.startswith('$') and seg.endswith('$') and len(seg) > 2:
                expression = seg[1:-1] # Remove $
                rich_text.append({
                    "type": "equation",
                    "equation": {"expression": expression}
                })
            else:
                # Case B: Plain text, continue to check for **Bold**
                # Regex: match content inside **
                bold_pattern = r'(\*\*[^\*]+\*\*)'
                sub_segments = re.split(bold_pattern, seg)
                
                for sub in sub_segments:
                    if not sub:
                        continue
                    
                    # Identify Bold (**...**)
                    if sub.startswith('**') and sub.endswith('**') and len(sub) > 4:
                        content = sub[2:-2] # Remove **
                        rich_text.append({
                            "type": "text",
                            "text": {"content": content},
                            "annotations": {"bold": True} # Tell Notion to bold this
                        })
                    else:
                        # Plain text
                        rich_text.append({
                            "type": "text",
                            "text": {"content": sub}
                        })
                
        return rich_text

    def _create_table_block(self, rows: List[str]) -> Dict[str, Any]:
        """
        Constructs a Notion table block from a list of markdown table rows.
        Handles column count consistency (auto-complete missing columns).
        """
        table_rows = []
        max_cols = 0
        
        # First pass: parse rows and find max columns
        parsed_rows = []
        for row in rows:
            # Split by |
            # Standard markdown table: | col1 | col2 |
            cells = [cell.strip() for cell in row.split('|')]
            
            # Clean up empty leading/trailing cells from split if the row starts/ends with |
            if row.strip().startswith('|') and len(cells) > 0 and cells[0] == '':
                cells.pop(0)
            if row.strip().endswith('|') and len(cells) > 0 and cells[-1] == '':
                cells.pop()
                
            parsed_rows.append(cells)
            max_cols = max(max_cols, len(cells))
            
        # Second pass: construct Notion table rows
        for cells in parsed_rows:
            # Pad with empty strings if needed
            while len(cells) < max_cols:
                cells.append("")
                
            row_cells = []
            for cell_text in cells:
                # Recursively parse inline elements within cells
                row_cells.append(self._parse_inline_elements(cell_text))
                
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": row_cells
                }
            })
            
        return {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": max_cols,
                "has_column_header": False, 
                "has_row_header": False,
                "children": table_rows
            }
        }

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads a file and converts it to Notion blocks.
        Implements a state machine for Tables.
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
        
        for line in lines:
            line = line.strip()
            
            # --- Table State Machine ---
            # If line starts with |, it's part of a table
            if line.startswith('|'):
                if not in_table_mode:
                    in_table_mode = True
                    logger.debug("Entering table mode")
                table_buffer.append(line)
                continue 
            
            # If line does NOT start with |, check if we were in table mode
            if in_table_mode:
                # Flush the buffer
                if table_buffer:
                    logger.debug(f"Flushing table with {len(table_buffer)} rows")
                    blocks.append(self._create_table_block(table_buffer))
                    table_buffer = []
                in_table_mode = False
            
            # Skip empty lines
            if not line:
                continue

            # --- Standard Block Parsing ---
            
            # Heading 3 (###)
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": self._parse_inline_elements(line[4:])}
                })
            # Heading 2 (##)
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": self._parse_inline_elements(line[3:])}
                })
            # Heading 1 (#)
            elif line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": self._parse_inline_elements(line[2:])}
                })
            # Bullet List (- or *)
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": self._parse_inline_elements(line[2:])}
                })
            # Block Equation ($$ ... $$)
            elif line.startswith('$$') and line.endswith('$$'):
                expression = line[2:-2].strip()
                blocks.append({
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": expression}
                })
            # Default: Paragraph
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": self._parse_inline_elements(line)}
                })
        
        # Final flush if file ends with table
        if in_table_mode and table_buffer:
            logger.debug(f"Flushing final table with {len(table_buffer)} rows")
            blocks.append(self._create_table_block(table_buffer))
            
        return blocks

    def push_to_notion(self, blocks: List[Dict[str, Any]], target_page_id: str):
        """
        Pushes blocks to Notion in batches.
        """
        if not blocks:
            logger.warning("No blocks to push.")
            return

        logger.info(f"Pushing {len(blocks)} blocks to Page {target_page_id}...")
        
        # Batch upload (100 blocks per batch limit by Notion API)
        batch_size = 100
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
                # Log detailed error if possible
                import traceback
                logger.debug(traceback.format_exc())
                return

        logger.info("Push completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Sync Markdown file to Notion as a child page.")
    parser.add_argument("file_path", nargs="?", default="notes.md", help="Path to the Markdown file (default: notes.md)")
    parser.add_argument("--title", help="Title for the new Notion page. Defaults to timestamp.")
    
    args = parser.parse_args()
    
    target_file = args.file_path
    
    # Generate default title if not provided
    page_title = args.title
    if not page_title:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        page_title = f"{now_str} 科研笔记"

    try:
        syncer = NotionSync()
        
        # 1. Parse File
        logger.info(f"Parsing file: {target_file}")
        blocks = syncer.parse_file(target_file)
        
        if not blocks:
            logger.warning("No blocks generated from file. Aborting.")
            return

        # 2. Create Child Page
        new_page_id, new_page_url = syncer.create_child_page(page_title)
        
        # 3. Push Blocks to Child Page
        syncer.push_to_notion(blocks, new_page_id)
        
        print(f"\n🎉 页面创建成功！")
        print(f"👉 访问链接: {new_page_url}\n")
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
