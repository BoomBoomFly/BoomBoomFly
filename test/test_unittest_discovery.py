"""Bridge standard-library discovery into the repository's test directories.

The test directories intentionally are not Python packages.  Python 3.8's
``unittest discover`` does not recurse into such directories, so the documented
repository-wide command would otherwise report success after running zero
tests.  Pytest already discovers the files directly and ignores this module.
"""

from pathlib import Path
import unittest


__test__ = False
TEST_ROOT = Path(__file__).resolve().parent


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    """Load every immediate non-package test directory exactly once."""
    del loader, standard_tests
    suite = unittest.TestSuite()
    test_pattern = pattern or "test_*.py"
    for directory in sorted(TEST_ROOT.iterdir()):
        if not directory.is_dir() or (directory / "__init__.py").exists():
            continue
        if not any(directory.glob(test_pattern)):
            continue
        suite.addTests(
            unittest.TestLoader().discover(
                start_dir=str(directory),
                pattern=test_pattern,
            )
        )
    return suite
