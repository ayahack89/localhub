import shutil
import tempfile
import unittest
from pathlib import Path
from typer.testing import CliRunner

from cli.main import app, VERSION
from Backend.services.session import SessionService
from Backend.services.access import clear_all_requests


class TestCLICommands(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        (self.repo_path / "README.md").write_text("# Test Repo", encoding="utf-8")
        clear_all_requests()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_all_requests()

    def test_cli_help(self):
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("LocalHub", result.stdout)
        self.assertIn("start", result.stdout)
        self.assertIn("clone", result.stdout)
        self.assertIn("status", result.stdout)
        self.assertIn("stop", result.stdout)
        self.assertIn("push", result.stdout)
        self.assertIn("version", result.stdout)

    def test_cli_version_command(self):
        result = self.runner.invoke(app, ["version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(VERSION, result.stdout)

    def test_cli_version_flag(self):
        result = self.runner.invoke(app, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(VERSION, result.stdout)

    def test_cli_status_command(self):
        result = self.runner.invoke(app, ["status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("LocalHub Session Status", result.stdout)

    def test_cli_start_invalid_directory(self):
        result = self.runner.invoke(app, ["start", "/nonexistent/invalid/path/12345"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("does not exist", result.stdout)

    def test_cli_start_file_instead_of_dir(self):
        file_path = self.repo_path / "README.md"
        result = self.runner.invoke(app, ["start", str(file_path)])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("is not a directory", result.stdout)

    def test_cli_push_outside_repo(self):
        result = self.runner.invoke(app, ["push"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Not in a LocalHub cloned repository directory", result.stdout)

    def test_cli_stop(self):
        result = self.runner.invoke(app, ["stop"])
        self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
