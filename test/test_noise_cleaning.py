
import sys
import os
import unittest
import logging

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_markdown_to_blocks

# Configure logging to capture output
logging.basicConfig(level=logging.DEBUG)

class TestNoiseCleaning(unittest.TestCase):
    def create_temp_md(self, content):
        filename = "test_noise.md"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(content)
        return filename

    def tearDown(self):
        if os.path.exists("test_noise.md"):
            os.remove("test_noise.md")

    def test_zero_width_space_removal(self):
        # Input has \u200b inside the text
        md_content = "Text with\u200b zero width space"
        filename = self.create_temp_md(md_content)
        blocks = parse_markdown_to_blocks(filename)
        
        self.assertEqual(len(blocks), 1)
        # Verify content is cleaned
        self.assertEqual(blocks[0]['paragraph']['rich_text'][0]['text']['content'], "Text with zero width space")

    def test_empty_blockquote_skipping(self):
        # Input has empty blockquote lines which should be skipped
        md_content = """
> Valid Quote
> 
>
> Another Valid Quote
"""
        filename = self.create_temp_md(md_content)
        blocks = parse_markdown_to_blocks(filename)
        
        # Expected: 
        # 1. Quote "Valid Quote"
        # 2. Quote "Another Valid Quote"
        # The empty "> " and ">" lines should be skipped.
        
        # Note: Depending on implementation, "Valid Quote" might be one block and "Another Valid Quote" another.
        # Or if the parser doesn't merge quotes (which it currently doesn't seem to), they will be separate blocks.
        # The key is that we shouldn't have empty quote blocks in between.
        
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['quote']['rich_text'][0]['text']['content'], "Valid Quote")
        self.assertEqual(blocks[1]['quote']['rich_text'][0]['text']['content'], "Another Valid Quote")

    def test_mixed_noise(self):
        # Combined test
        md_content = """
1. Item 1
> 
\u200b
2. Item 2
"""
        filename = self.create_temp_md(md_content)
        blocks = parse_markdown_to_blocks(filename)
        
        # Expected:
        # 1. Numbered List Item "Item 1"
        # The "> " line is skipped.
        # The "\u200b" line becomes empty string after clean, then skipped by 'if not stripped_line' check? 
        # Wait, if we replace \u200b with '', it becomes empty string.
        # 2. Numbered List Item "Item 2"
        
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['numbered_list_item']['rich_text'][0]['text']['content'], "Item 1")
        self.assertEqual(blocks[1]['numbered_list_item']['rich_text'][0]['text']['content'], "Item 2")

if __name__ == '__main__':
    unittest.main()
