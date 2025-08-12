#!/usr/bin/env python3
"""
Simple task runner to replace the Makefile.

Usage:
    python tasks.py <command>

Available commands:
    test              - Run all tests
    test-unit         - Run unit tests only
    test-security     - Run security validation tests
    test-integration  - Run integration tests
    test-stress       - Run stress tests
    test-coverage     - Run tests with coverage report
    lint              - Run code linting
    clean             - Clean test artifacts
    help              - Show this help message

Example:
    python tasks.py test
    python tasks.py lint
    python tasks.py test-coverage
"""

import sys
import subprocess
import shutil
import pathlib
from typing import List


def run_cmd(cmd: str | List[str], description: str = ""):
    """Run a command and return the exit code."""
    if description:
        print(f"🚀 {description}")

    if isinstance(cmd, str):
        # Split the command string, but keep quoted arguments together
        import shlex

        cmd = shlex.split(cmd)

    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def run_test():
    """Run all tests."""
    return run_cmd("uv run pytest tests/ -v", "Running all tests")


def run_test_unit():
    """Run unit tests only."""
    return run_cmd(
        "uv run pytest tests/test_snowflake_utils.py -v", "Running unit tests"
    )


def run_test_security():
    """Run security validation tests (excluding concurrent tests for reliability)."""
    return run_cmd(
        "uv run pytest tests/test_security.py -k 'not concurrent' -v",
        "Running security tests",
    )


def run_test_integration():
    """Run integration tests."""
    return run_cmd(
        "uv run pytest tests/test_integration.py -v", "Running integration tests"
    )


def run_test_stress():
    """Run stress tests."""
    return run_cmd(
        "uv run pytest tests/test_security_stress.py -v", "Running stress tests"
    )


def run_test_coverage():
    """Run tests with coverage report."""
    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/",
        "--cov=utils",
        "--cov=pages",
        "--cov=components",
        "--cov-report=html",
        "--cov-report=term-missing",
    ]
    return run_cmd(cmd, "Running tests with coverage report")


def run_lint():
    """Run code linting."""
    print("🧹 Running code linting and formatting")

    # Run ruff check with fixes
    exit_code1 = run_cmd("uv run ruff check --fix", "Checking and fixing code issues")

    # Run ruff format
    exit_code2 = run_cmd("uv run ruff format", "Formatting code")

    return max(exit_code1, exit_code2)


def run_clean():
    """Clean test artifacts."""
    print("🧹 Cleaning test artifacts")

    try:
        # Remove directories
        dirs_to_remove = [".pytest_cache", "htmlcov"]
        for dir_name in dirs_to_remove:
            dir_path = pathlib.Path(dir_name)
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed {dir_name}/")

        # Remove .coverage file
        coverage_file = pathlib.Path(".coverage")
        if coverage_file.exists():
            coverage_file.unlink()
            print("   Removed .coverage")

        # Remove __pycache__ directories
        pycache_count = 0
        for pycache_dir in pathlib.Path(".").rglob("__pycache__"):
            if pycache_dir.is_dir():
                shutil.rmtree(pycache_dir)
                pycache_count += 1
        if pycache_count > 0:
            print(f"   Removed {pycache_count} __pycache__ directories")

        # Remove .pyc files
        pyc_count = 0
        for pyc_file in pathlib.Path(".").rglob("*.pyc"):
            pyc_file.unlink()
            pyc_count += 1
        if pyc_count > 0:
            print(f"   Removed {pyc_count} .pyc files")

        print("✅ Cleanup completed")
        return 0

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 1


def help_cmd():
    """Show help message."""
    print(__doc__)
    return 0


# Entry point functions for project.scripts
def test():
    """CLI entry point for test command."""
    sys.exit(run_test())


def test_unit():
    """CLI entry point for test-unit command."""
    sys.exit(run_test_unit())


def test_security():
    """CLI entry point for test-security command."""
    sys.exit(run_test_security())


def test_integration():
    """CLI entry point for test-integration command."""
    sys.exit(run_test_integration())


def test_stress():
    """CLI entry point for test-stress command."""
    sys.exit(run_test_stress())


def test_coverage():
    """CLI entry point for test-coverage command."""
    sys.exit(run_test_coverage())


def lint():
    """CLI entry point for lint command."""
    sys.exit(run_lint())


def clean():
    """CLI entry point for clean command."""
    sys.exit(run_clean())


# For backward compatibility and direct execution
def main():
    """Main entry point for direct execution."""
    if len(sys.argv) < 2:
        help_cmd()
        return 1

    command = sys.argv[1].replace("-", "_")

    # Map commands to functions
    commands = {
        "test": run_test,
        "test_unit": run_test_unit,
        "test_security": run_test_security,
        "test_integration": run_test_integration,
        "test_stress": run_test_stress,
        "test_coverage": run_test_coverage,
        "lint": run_lint,
        "clean": run_clean,
        "help": help_cmd,
    }

    if command in commands:
        return commands[command]()
    else:
        print(f"❌ Unknown command: {sys.argv[1]}")
        print("Run the help command to see available commands.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
