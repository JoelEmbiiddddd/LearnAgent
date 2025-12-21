import unittest

from echocodeview.server import inject_mermaid_blocks


class MermaidTests(unittest.TestCase):
    def test_mermaid_block_transformed(self):
        source = "```mermaid\nflowchart LR\nA --> B\n```\n"
        output = inject_mermaid_blocks(source)
        self.assertIn('<div class="mermaid">', output)
        self.assertIn("flowchart LR", output)
        self.assertIn("</div>", output)


if __name__ == "__main__":
    unittest.main()
