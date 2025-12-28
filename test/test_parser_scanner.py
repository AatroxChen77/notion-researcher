import unittest
from src.parser import parse_inline_elements

class TestParserInlineScanner(unittest.TestCase):
    def test_scanner_precedence_code_over_math(self):
        # Code should protect $ from being parsed as math
        text = "`echo $PATH`"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text']['content'], "echo $PATH")
        self.assertTrue(result[0]['annotations'].get('code'))
        self.assertNotIn('equation', result[0])

    def test_scanner_precedence_math_over_link(self):
        # Math should protect [] from being parsed as link
        text = "$a[i]$"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'equation')
        self.assertEqual(result[0]['equation']['expression'], "a[i]")

    def test_scanner_precedence_math_in_link(self):
        # This is tricky: strict scanner says Math > Link.
        # So [Link $E=mc^2$](url) 
        # The math regex matches $...$ first?
        # Actually, if we look at the master regex:
        # r'(?P<code>`[^`]+`)|(?P<math>\$[^\$]+\$)|(?P<image>...)|(?P<link>\[[^\]]+\]\([^\)]+\))|(?P<bold>...)'
        # If we have "Click [here $x$](url)", 
        # The link regex `\[[^\]]+\]\([^\)]+\)` matches the WHOLE thing first?
        # NO. The scanner finds the FIRST match at the EARLIEST position.
        # "Click " -> Plain text
        # "[here " -> Link regex starts match at index 6. Math starts at index 12.
        # If link regex matches successfully, it wins because it starts earlier? 
        # Wait, re.finditer scans from left to right.
        # If multiple regexes match starting at the same position, the one defined first wins.
        # If "Click [here $x$](url)"
        # At index 6: `[`
        # Link regex matches `[here $x$](url)`? Yes.
        # Math regex matches `$x$` (starts later).
        # So Link should win if it matches from the current position.
        
        # BUT, what if we have "$E=mc^2$ and [Link](url)"
        # At index 0: `$`
        # Math matches `$E=mc^2$`. Link doesn't match. Math wins.
        
        # Test: Math with link-like characters
        text = "$P(A|B)$"
        result = parse_inline_elements(text)
        self.assertEqual(result[0]['type'], 'equation')
        self.assertEqual(result[0]['equation']['expression'], "P(A|B)")

    def test_mixed_elements(self):
        # "Code `x` and Math $y$ and [Link](z)"
        text = "Code `x` and Math $y$ and [Link](z)"
        result = parse_inline_elements(text)
        # Expected: 
        # 1. "Code " (text)
        # 2. "x" (code)
        # 3. " and Math " (text)
        # 4. "y" (equation)
        # 5. " and " (text)
        # 6. "Link" (link)
        
        self.assertEqual(len(result), 6)
        self.assertEqual(result[1]['text']['content'], "x")
        self.assertTrue(result[1]['annotations']['code'])
        self.assertEqual(result[3]['equation']['expression'], "y")
        self.assertEqual(result[5]['text']['content'], "Link")
        self.assertEqual(result[5]['text']['link']['url'], "z")

    def test_image_ignore(self):
        # Image syntax should be treated as text (or ignored by inline parser)
        # so it doesn't break. The scanner has an 'image' group that appends as text.
        text = "![Img](url)"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'text')
        self.assertEqual(result[0]['text']['content'], "![Img](url)")
        # Should NOT have link property
        self.assertIsNone(result[0]['text'].get('link'))

    def test_bold_parsing(self):
        text = "**Bold**"
        result = parse_inline_elements(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text']['content'], "Bold")
        self.assertTrue(result[0]['annotations']['bold'])

if __name__ == '__main__':
    unittest.main()
