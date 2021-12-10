from pathlib import Path

from smokestack.ci.configuration import load


def test_load() -> None:
    path = Path("smokestack-ci.sample.yml")
    loaded = load(path)
    assert loaded["branch_name_env"] == "CIRCLE_BRANCH"
