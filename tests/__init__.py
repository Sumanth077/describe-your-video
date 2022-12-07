"""Testing suite including integration and unit tests."""
from pathlib import Path

TEST_DATA = Path(__file__).parent / "data"
INPUT_FILES = list((TEST_DATA).iterdir())