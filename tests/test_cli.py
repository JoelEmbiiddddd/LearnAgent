import unittest

from echocodeview.cli import parse_args


class CliTests(unittest.TestCase):
    def test_parse_args_with_root_path(self):
        parser, config = parse_args(["--serve", "/tmp/docs", "--no-open"])
        self.assertTrue(config["serve"])
        self.assertEqual(config["root_dir"], "/tmp/docs")
        self.assertFalse(config["open_browser"])
        self.assertIsNotNone(parser)

    def test_parse_args_with_dir_flag(self):
        _, config = parse_args(["--serve", "--dir", "/tmp/docs", "--port", "4100"])
        self.assertEqual(config["root_dir"], "/tmp/docs")
        self.assertEqual(config["port"], 4100)


if __name__ == "__main__":
    unittest.main()
