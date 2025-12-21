import os
import tempfile
import unittest

from echocodeview.server import create_app


class ServerTests(unittest.TestCase):
    def test_app_renders_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = os.path.join(temp_dir, "README.md")
            with open(md_path, "w", encoding="utf-8") as handle:
                handle.write("# Hello\n\nContent")

            app = create_app(temp_dir, "README.md")
            client = app.test_client()

            response = client.get("/view/README.md")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Hello", response.data)


if __name__ == "__main__":
    unittest.main()
