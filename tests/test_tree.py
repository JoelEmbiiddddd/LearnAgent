import os
import tempfile
import unittest

from echocodeview.server import build_tree, find_default_entry


def flatten_paths(nodes):
    collected = []
    for node in nodes:
        if node["type"] == "file":
            collected.append(node["path"])
        else:
            collected.extend(flatten_paths(node["children"]))
    return collected


class TreeTests(unittest.TestCase):
    def test_build_tree_recurses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "guides", "deep"))
            os.makedirs(os.path.join(temp_dir, ".codex"))
            os.makedirs(os.path.join(temp_dir, "Server"))
            with open(
                os.path.join(temp_dir, "README.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("# Root")
            with open(
                os.path.join(temp_dir, "guides", "intro.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("# Intro")
            with open(
                os.path.join(temp_dir, "guides", "deep", "detail.md"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("# Detail")
            with open(
                os.path.join(temp_dir, ".codex", "hidden.md"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("# Hidden")
            with open(
                os.path.join(temp_dir, "Server", "README.md"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("# Server")

            tree = build_tree(temp_dir)
            paths = set(flatten_paths(tree))

            self.assertIn("README.md", paths)
            self.assertIn("guides/intro.md", paths)
            self.assertIn("guides/deep/detail.md", paths)
            self.assertNotIn(".codex/hidden.md", paths)
            self.assertNotIn("Server/README.md", paths)

    def test_find_default_entry_prefers_readme(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(
                os.path.join(temp_dir, "README.md"), "w", encoding="utf-8"
            ) as handle:
                handle.write("# Root")
            tree = build_tree(temp_dir)
            default_entry = find_default_entry(temp_dir, tree)
            self.assertEqual(default_entry, "README.md")


if __name__ == "__main__":
    unittest.main()
