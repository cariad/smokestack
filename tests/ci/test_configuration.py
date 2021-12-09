from smokestack.ci.configuration import load
from pathlib import Path

def test_load() -> None:
    path = Path("smokestack-ci.sample.yml")
    loaded = load(path)
    assert loaded["branch_name_env"] == "CIRCLE_BRANCH"
