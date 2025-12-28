import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_inline_elements(text_content: str) -> List[Dict[str, Any]]:
    """
    Parses inline elements: LaTeX equations ($...$), Links ([...](...)), and Bold (**...**).
    Priority: Equation > Link > Bold
    
    Args:
        text_content: The raw text string to parse.
        
    Returns:
        A list of Notion rich text objects.
    """
    # 1. Split by Math
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
            # 2. Split by Inline Code (New Layer - Priority over Link/Bold)
            # Match content wrapped in backticks `...`
            # Use lookbehind/lookahead to avoid matching inside other structures if needed, 
            # but generally splitting sequentially works.
            code_pattern = r'(`[^`]+`)'
            code_segments = re.split(code_pattern, seg)
            
            for code_seg in code_segments:
                if not code_seg:
                    continue
                
                if code_seg.startswith('`') and code_seg.endswith('`') and len(code_seg) > 2:
                    content = code_seg[1:-1]
                    rich_text.append({
                        "type": "text",
                        "text": {"content": content},
                        "annotations": {"code": True}
                    })
                else:
                    # 3. Split by Link
                    # Use negative lookbehind to ensure we don't match images ![...]
                    link_pattern = r'(?<!\!)(\[[^\]]*\]\([^\)]*\))'
                    link_segments = re.split(link_pattern, code_seg)
                    
                    for link_seg in link_segments:
                        if not link_seg:
                            continue
                        
                        # Check if it matches the link pattern structure
                        if link_seg.startswith('[') and link_seg.endswith(')'):
                            # Extract text and url using strict anchored regex
                            match = re.match(r'^\[(.*?)\]\((.*?)\)$', link_seg)
                            if match:
                                link_text = match.group(1)
                                link_url = match.group(2).strip()
                                rich_text.append({
                                    "type": "text",
                                    "text": {
                                        "content": link_text,
                                        "link": {"url": link_url}
                                    }
                                })
                            else:
                                rich_text.append({
                                    "type": "text",
                                    "text": {"content": link_seg}
                                })
                        else:
                            # 4. Split by Bold
                            bold_pattern = r'(\*\*[^\*]+\*\*)'
                            sub_segments = re.split(bold_pattern, link_seg)
                            
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
        line = lines[i].rstrip()
        
        # Skip empty lines (unless part of a block structure if needed later)
        if not line:
            i += 1
            continue

        # --- Divider Detection ---
        if re.match(r'^[-*_]{3,}$', line.strip()):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
            i += 1
            continue

        # --- Code Block Detection ---
        if line.strip().startswith('```'):
            # Extract language (if any)
            # Default to "plain text" if empty
            lang = line.strip()[3:].strip()
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
        if line.strip().startswith('|') or '｜' in line:
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
        if line.strip() == '$$':
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
            
        # --- Bullet Points ---
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            content = line.strip()[2:]
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_inline_elements(content)}
            })

        # --- Ordered List ---
        elif re.match(r'^\d+\.\s', line.strip()):
            content = re.sub(r'^\d+\.\s', '', line.strip(), count=1)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_inline_elements(content)}
            })
            
        # --- Default: Paragraph ---
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": parse_inline_elements(line)}
            })
            
        i += 1
        
    return blocks
