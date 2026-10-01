"""Basic skeleton test ensuring packages import cleanly and versions match."""

import careercompiler


def test_package_metadata() -> None:
    assert careercompiler.__version__ == "0.1.0"
