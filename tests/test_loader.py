from pathlib import Path

import pytest
import yaml

from evalite.loader import load_suite


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_load_valid_suite():
    suite = load_suite(EXAMPLES_DIR / "qa_suite.yaml")
    assert suite.suite == "qa_basics"
    assert len(suite.cases) == 5
    assert suite.cases[0].scorer == "exact"


def test_invalid_scorer_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.dump({
        "suite": "test",
        "cases": [{"id": "c1", "prompt": "hi", "expected": "ho", "scorer": "typo"}],
    }))
    with pytest.raises(ValueError):
        load_suite(bad)


def test_missing_required_field_raises(tmp_path):
    bad = tmp_path / "missing.yaml"
    bad.write_text(yaml.dump({
        "suite": "test",
        "cases": [{"id": "c1", "expected": "ho", "scorer": "exact"}],
    }))
    with pytest.raises(ValueError):
        load_suite(bad)
