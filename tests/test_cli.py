"""Integration tests for Career Compiler CLI."""

from careercompiler.cli.main import main


def test_cli_profile_show() -> None:
    """CLI profile show runs successfully."""
    code = main(["profile", "show"])
    assert code == 0


def test_cli_parse_jd() -> None:
    """CLI parse-jd decomposes raw text."""
    code = main(["parse-jd", "Looking for a Python and Docker Engineer."])
    assert code == 0


def test_cli_diff() -> None:
    """CLI diff runs optimization and prints report."""
    code = main(["diff", "--jd", "Seeking Python and FastAPI developer."])
    assert code == 0
