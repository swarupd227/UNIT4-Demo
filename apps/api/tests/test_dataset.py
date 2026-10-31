from pathlib import Path

import pytest

from data.generator.main import generate
from data.generator.verify import verify


def test_same_seed_gives_byte_identical_data(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    generate(first)
    generate(second)
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_dataset_meets_the_specification(tmp_path: Path) -> None:
    generate(tmp_path)
    assert verify(tmp_path)


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


@pytest.mark.parametrize(
    ("relative_path", "old", "new"),
    [
        ("documents/billing_policy.md", "more than 15%", "more than 10%"),  # M1 conflict removed
        ("erpx_sim/fx_rate.csv", "0.872", "0.871654"),  # M7 cause hidden
        ("cr_source/dimension_value.csv", "ADVRISK  ", "ADVRISK2"),  # M9 duplicate removed
        ("studio/legal_entity.csv", "dormant", "trading"),  # M5 entity no longer dormant
    ],
)
def test_verifier_fails_when_a_planted_issue_is_removed(
    tmp_path: Path, relative_path: str, old: str, new: str
) -> None:
    generate(tmp_path)
    _replace(tmp_path / relative_path, old, new)
    assert not verify(tmp_path)
