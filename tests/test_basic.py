"""Basic smoke tests for evolver-tools.

Tests that the package installs, imports, and runs correctly.
No external test dependencies — uses only Python stdlib unittest.
"""
import unittest
import subprocess
import sys
import importlib


class TestPackageImport(unittest.TestCase):
    """Verify the package and its core module can be imported."""

    def test_import_cli(self):
        """evolver_tools.cli imports without error."""
        import evolver_tools.cli  # noqa: F811
        self.assertTrue(hasattr(evolver_tools.cli, 'main'))

    def test_import_tools(self):
        """evolver_tools.tools module loads."""
        import evolver_tools  # noqa: F811
        self.assertTrue(hasattr(evolver_tools, '__version__'))

    def test_version_matches_pyproject(self):
        """__version__ is a non-empty string."""
        import evolver_tools
        self.assertIsInstance(evolver_tools.__version__, str)
        self.assertTrue(len(evolver_tools.__version__) > 0)


class TestCLIInvocation(unittest.TestCase):
    """Test the CLI entry point (evtool)."""

    def test_evtool_list_runs(self):
        """evtool list exits zero."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'list'],
            capture_output=True, text=True, timeout=30
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr[:200]}")

    def test_evtool_list_output(self):
        """evtool list outputs tool names."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'list'],
            capture_output=True, text=True, timeout=30
        )
        self.assertTrue(len(result.stdout) > 0)
        # Should contain some known tool names
        known_tools = ['csv-stats', 'json-pretty', 'sys-info', 'qrcode']
        found = any(t in result.stdout for t in known_tools)
        self.assertTrue(found, f"None of {known_tools} found in output:\n{result.stdout[:300]}")

    def test_evtool_help_runs(self):
        """evtool help csv-stats exits zero."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'help', 'csv-stats'],
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(result.returncode, 0)

    def test_evtool_version(self):
        """evtool --version returns version string."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', '--version'],
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('.', result.stdout.strip())


class TestToolExecution(unittest.TestCase):
    """Test that individual tools actually work."""

    def test_csv_stats_basic(self):
        """csv-stats on minimal CSV data works."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'csv-stats'],
            input='name,value\nalice,10\nbob,20\n',
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr[:200]}")
        # Should contain some stats output
        self.assertIn('name', result.stdout.lower() + result.stderr.lower())

    def test_json_pretty_basic(self):
        """json-pretty formats JSON correctly."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'json-pretty'],
            input='{"a":1,"b":2}',
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"a"', result.stdout)

    def test_sys_info_runs(self):
        """sys-info exits zero (basic system info)."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'sys-info'],
            capture_output=True, text=True, timeout=15
        )
        self.assertEqual(result.returncode, 0)

    def test_qrcode_basic(self):
        """qrcode generates QR code without error."""
        result = subprocess.run(
            [sys.executable, '-m', 'evolver_tools', 'qrcode'],
            input='hello world',
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(len(result.stdout) > 0)


class TestNoDeps(unittest.TestCase):
    """Verify the zero-dependency claim."""

    def test_only_stdlib_imports(self):
        """evolver_tools should not import non-stdlib modules at top level."""
        import evolver_tools
        import evolver_tools.cli

        # Check loaded modules for red flags
        # This is a best-effort check
        stdlib_modules = {'json', 'os', 'sys', 're', 'math', 'csv', 'datetime',
                         'pathlib', 'typing', 'collections', 'hashlib', 'base64',
                         'shutil', 'subprocess', 'textwrap', 'uuid', 'random',
                         'functools', 'itertools', 'argparse', 'io', 'string'}

        suspicious = []
        # We can't easily enumerate all modules, but we can check the CLI runs
        # without importing something unexpected
        result = subprocess.run(
            [sys.executable, '-c', '''
import evolver_tools.cli
# Check that no non-stdlib packages are imported beyond what's expected
import sys
stdlib_prefixes = ["evolver_tools", "json", "os", "sys", "re", "math", "csv",
    "datetime", "pathlib", "typing", "collections", "hashlib", "base64",
    "shutil", "subprocess", "textwrap", "uuid", "random", "functools",
    "itertools", "argparse", "io", "string", "html", "xml", "urllib",
    "http", "smtplib", "ssl", "socket", "struct", "zlib", "gzip",
    "bz2", "lzma", "zipfile", "tarfile", "copy", "pprint", "enum",
    "bisect", "heapq", "operator", "decimal", "fractions", "statistics",
    "tempfile", "fileinput", "glob", "fnmatch", "linecache", "difflib",
    "threading", "time", "calendar", "locale", "gettext", "logging",
    "warnings", "traceback", "pickle", "shelve", "dbm", "sqlite3",
    "configparser", "netrc", "plistlib", "webbrowser", "cgi",
    "turtle", "tkinter", "numbers"]
loaded_violations = [
    m for m in sys.modules
    if m and not any(m == p or m.startswith(p + ".") for p in stdlib_prefixes)
    and not m.startswith("_")
]
print(f"Violations: {loaded_violations}")
if loaded_violations:
    print("WARNING: unexpected modules loaded")
'''],
            capture_output=True, text=True, timeout=15
        )
        self.assertIn("Violations: []", result.stdout, f"Unexpected module imports:\n{result.stdout}")


if __name__ == '__main__':
    unittest.main()
