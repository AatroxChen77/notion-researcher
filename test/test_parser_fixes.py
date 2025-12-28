import unittest
from src.parser import parse_inline_elements, parse_markdown_to_blocks

class TestParser(unittest.TestCase):
    
    # --- Task 1: Inline Code ---
    def test_inline_code_parsing(self):
        text = "Use `git status` now"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['text']['content'], "git status")
        self.assertTrue(result[1]['annotations'].get('code'))
        
    def test_inline_code_precedence(self):
        # Code should win over link syntax if wrapped in backticks
        text = "`[link](url)`"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text']['content'], "[link](url)")
        self.assertTrue(result[0]['annotations'].get('code'))
        
    # --- Task 2: Dividers ---
    def test_divider_parsing(self):
        with open("test_divider.md", "w") as f:
            f.write("Line 1\n---\nLine 2\n***\nLine 3\n___")
            
        blocks = parse_markdown_to_blocks("test_divider.md")
        self.assertEqual(len(blocks), 6) # P, Div, P, Div, P, Div
        self.assertEqual(blocks[1]['type'], 'divider')
        self.assertEqual(blocks[3]['type'], 'divider')
        self.assertEqual(blocks[5]['type'], 'divider')

    # --- Task 3: Code Blocks & Indentation ---
    def test_code_block_parsing(self):
        content = """
```python
def hello():
    print("world")
```
"""
        with open("test_code.md", "w") as f:
            f.write(content.strip())
            
        blocks = parse_markdown_to_blocks("test_code.md")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]['type'], 'code')
        self.assertEqual(blocks[0]['code']['language'], 'python')
        
        # Check indentation
        code_text = blocks[0]['code']['rich_text'][0]['text']['content']
        expected = 'def hello():\n    print("world")'
        self.assertEqual(code_text, expected)

if __name__ == '__main__':
    unittest.main()
