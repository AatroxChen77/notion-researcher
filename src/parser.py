import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_inline_elements(text_content: str) -> List[Dict[str, Any]]:
    """
    Parses inline elements using a robust scanner approach (re.finditer).
    Priority: Inline Code > Math > Image (Ignore) > Link > Bold
    """
    if not text_content:
        return []

    # Master Regex with Named Groups
    # 1. Code: `...` (Backticks)
    # 2. Math: $...$ or $$...$$ (One or more $)
    # 3. Image: ![...](...) (Zero or more content)
    # 4. Link: [...](...) (Zero or more content - RELAXED from + to *)
    # 5. Bold: **...**
    pattern = re.compile(
        r'(?P<code>`[^`]+`)|'
        r'(?P<math>\$+(?:[^\$]+)\$+)|'
        r'(?P<image>!\[[^\]]*\]\([^\)]*\))|'
        r'(?P<link>\[[^\]]*\]\([^\)]*\))|'
        r'(?P<bold>\*\*[^\*]+\*\*)'
    )

    rich_text = []
    last_idx = 0

    for match in pattern.finditer(text_content):
        # 1. Handle Plain Text before the match
        if match.start() > last_idx:
            plain_text = text_content[last_idx:match.start()]
            rich_text.append({
                "type": "text",
                "text": {"content": plain_text}
            })

        # 2. Handle the Match based on Group Name
        kind = match.lastgroup
        full_match = match.group()

        if kind == 'code':
            content = full_match[1:-1] # Strip backticks
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"code": True}
            })
        
        elif kind == 'math':
            # Robustly strip all leading/trailing $ (handles $...$ and $$...$$)
            expression = full_match.strip('$')
            rich_text.append({
                "type": "equation",
                "equation": {"expression": expression}
            })

        elif kind == 'link':
            # Extract Text and URL from [Text](URL)
            # Relaxed regex to allow empty parts (.*?)
            m = re.match(r'^\[(.*?)\]\((.*?)\)$', full_match)
            if m:
                link_text = m.group(1)
                # If text is empty, use URL as text
                if not link_text:
                    link_text = m.group(2)
                
                link_url = m.group(2).strip()
                
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": link_text,
                        "link": {"url": link_url}
                    }
                })
            else:
                rich_text.append({"type": "text", "text": {"content": full_match}})

        elif kind == 'bold':
            content = full_match[2:-2] # Strip **
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            })
        
        elif kind == 'image':
            # Inline images are treated as plain text
            rich_text.append({"type": "text", "text": {"content": full_match}})

        last_idx = match.end()

    # 3. Handle Remaining Text
    if last_idx < len(text_content):
        rich_text.append({
            "type": "text",
            "text": {"content": text_content[last_idx:]}
        })

    return rich_text

def create_table_block(rows: List[str]) -> Optional[Dict[str, Any]]:
    """
    Constructs a Notion table block from a list of markdown table rows.
    Returns None if no valid rows are found.
    
    Args:
        rows: List of strings representing table rows.
        
    Returns:
        A Notion table block dictionary or None.
    """
    table_rows = []
    max_cols = 0
    
    parsed_rows = []
    for row in rows:
        # 1. Full-width Character Support: Normalize to half-width
        row = row.replace('｜', '|')
        
        # 2. Spacer/Divider Line Filter
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
            row_cells.append(parse_inline_elements(cell_text))
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": row_cells}
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

def parse_markdown_to_blocks(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a Markdown file into Notion blocks.
    Handles headings, bullet points, tables, equations, and images.
    
    Args:
        file_path: Path to the markdown file.
        
    Returns:
        List of Notion block objects.
    """
    blocks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []

    i = 0
    while i < len(lines):
        # Calculate indentation (spaces at the beginning)
        raw_line = lines[i].rstrip('\n') # Keep indentation, remove newline
        stripped_line = raw_line.strip()
        
        if not stripped_line:
            i += 1
            continue

        indent_level = len(raw_line) - len(raw_line.lstrip())
        
        # [NEW] Clean Artifact Noise (e.g., 1111, 2222) with Transparent Logging
        # Regex matches word boundary + digit + same digit 3+ times + word boundary
        
        # Helper callback for logging
        def _log_noise(match):
            noise = match.group()
            # Log with context (stripped_line is available in closure scope)
            logger.warning(f"🧹 [Noise Cleaning] Removed '{noise}' from line: '{stripped_line[:50]}...'")
            return ""

        # Apply cleaning with callback
        line = re.sub(r'\b(\d)\1{3,}\b', _log_noise, stripped_line)
        
        # --- Divider Detection ---
        if re.match(r'^[-*_]{3,}$', line):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
            continue

        # --- Code Block Detection ---
        if line.startswith('```'):
            # Extract language (if any)
            # Default to "plain text" if empty
            lang = line[3:].strip()
            if not lang:
                lang = "plain text"
            
            i += 1
            code_content = []
            
            while i < len(lines):
                # Don't strip content lines to preserve indentation
                # But check stripped version for closing fence
                current_line = lines[i] # Preserve original indentation
                if current_line.strip() == '```':
                    i += 1
                    break
                code_content.append(current_line.rstrip()) # Right strip only
                i += 1
            
            full_code = "\n".join(code_content)
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "language": lang,
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": full_code}
                    }]
                }
            })
            continue

        # --- Table Detection ---
        if line.startswith('|') or '｜' in line:
            table_buffer = []
            while i < len(lines) and (lines[i].strip().startswith('|') or '｜' in lines[i]):
                table_buffer.append(lines[i].rstrip())
                i += 1
            
            table_block = create_table_block(table_buffer)
            if table_block:
                blocks.append(table_block)
            continue

        # --- Image Detection ---
        image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
        if image_match:
            # caption = image_match.group(1) # Notion API image captions are complex, skipping for simplicity
            image_url = image_match.group(2)
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": image_url
                    }
                }
            })
            i += 1
            continue
            
        # --- Block Equation Detection ($$) ---
        if line == '$$':
            i += 1
            equation_buffer = []
            while i < len(lines) and lines[i].strip() != '$$':
                equation_buffer.append(lines[i].strip())
                i += 1
            
            # Skip the closing $$
            i += 1
            
            expression = " ".join(equation_buffer)
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {
                    "expression": expression
                }
            })
            continue

        # --- Headings ---
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_inline_elements(line[2:])}
            })
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_inline_elements(line[3:])}
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_inline_elements(line[4:])}
            })
        
        # [NEW] Fix for Notion limitation: Map H4, H5, H6 to Heading 3
        elif line.startswith('####'):
            # Strip all leading # and whitespace
            content = line.lstrip('#').strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_inline_elements(content)}
            })
            
        # --- Bullet Points ---
        elif line.startswith('- ') or line.startswith('* '):
            content = line[2:]
            new_block = {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_inline_elements(content)}
            }
            
            # Check for nesting
            if indent_level >= 2 and blocks and blocks[-1]["type"] in ["bulleted_list_item", "numbered_list_item"]:
                parent_type = blocks[-1]['type']
                if 'children' not in blocks[-1][parent_type]:
                    blocks[-1][parent_type]['children'] = []
                blocks[-1][parent_type]['children'].append(new_block)
            else:
                blocks.append(new_block)

        # --- Ordered List ---
        elif re.match(r'^\d+\.\s', line):
            content = re.sub(r'^\d+\.\s', '', line, count=1)
            new_block = {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_inline_elements(content)}
            }
            
            # Check for nesting
            if indent_level >= 2 and blocks and blocks[-1]["type"] in ["bulleted_list_item", "numbered_list_item"]:
                parent_type = blocks[-1]['type']
                if 'children' not in blocks[-1][parent_type]:
                    blocks[-1][parent_type]['children'] = []
                blocks[-1][parent_type]['children'].append(new_block)
            else:
                blocks.append(new_block)
            
        # --- Default: Paragraph with Implicit Nesting ---
        else:
            paragraph_block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": parse_inline_elements(line)}
            }

            # Check if we should nest this paragraph under the previous list item
            # Logic: If previous block is a list item, append as child regardless of indentation 
            # (as per previous requirement for unindented descriptions).
            # However, if we want strict indentation support, we might want to check indent_level here too.
            # But the user's previous request was specifically for "no indent" descriptions.
            # So we keep the previous logic: if previous is list, append.
            if blocks and blocks[-1]['type'] in ['bulleted_list_item', 'numbered_list_item']:
                parent_type = blocks[-1]['type']
                # Ensure 'children' list exists in the parent block's type object
                if 'children' not in blocks[-1][parent_type]:
                    blocks[-1][parent_type]['children'] = []
                
                blocks[-1][parent_type]['children'].append(paragraph_block)
            else:
                blocks.append(paragraph_block)
            
        i += 1
        
    return blocks
