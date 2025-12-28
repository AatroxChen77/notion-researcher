
import sys
import os
import unittest
import json

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_inline_elements

class TestRecursiveFormatting(unittest.TestCase):
    def test_bold_with_math(self):
        text = "**$E=mc^2$**"
        result = parse_inline_elements(text)
        
        # Expected: A single equation object (since content is fully math)
        # Note: Notion doesn't support bolding equations, so we expect just the equation object.
        # But if there was text, it would be bold text + equation.
        
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['type'], 'equation')
        self.assertEqual(item['equation']['expression'], 'E=mc^2')

    def test_bold_with_mixed_content(self):
        text = "**Bold text and $math$**"
        result = parse_inline_elements(text)
        
        # Expected: 
        # 1. Text "Bold text and " (bold)
        # 2. Equation "math"
        
        self.assertEqual(len(result), 2)
        
        # Check text
        self.assertEqual(result[0]['type'], 'text')
        self.assertEqual(result[0]['text']['content'], 'Bold text and ')
        self.assertTrue(result[0]['annotations']['bold'])
        
        # Check equation
        self.assertEqual(result[1]['type'], 'equation')
        self.assertEqual(result[1]['equation']['expression'], 'math')

    def test_italic_with_math(self):
        text = "*$x$*"
        result = parse_inline_elements(text)
        
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['type'], 'equation')
        self.assertEqual(item['equation']['expression'], 'x')

    def test_nested_bold_italic(self):
        # This is tricky and depends on regex order. 
        # Our regex: Bold checked before Italic.
        # "**Italic inside bold**" -> Bold matches outer **...**.
        # Inside content: "Italic inside bold". Wait, if input is "**_Italic_**"
        
        text = "**_Italic inside bold_**"
        result = parse_inline_elements(text)
        
        # Recursive parsing should handle this.
        # Outer: Bold
        # Inner: "_Italic inside bold_" -> Italic
        
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['type'], 'text')
        self.assertEqual(item['text']['content'], 'Italic inside bold')
        self.assertTrue(item['annotations']['bold'])
        self.assertTrue(item['annotations']['italic'])

if __name__ == '__main__':
    unittest.main()
