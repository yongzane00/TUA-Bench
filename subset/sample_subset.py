"""Draw the frozen 40-task stratified subset for Project 4.

Deterministic: SEED is part of the protocol. Re-running reproduces the exact
subset. Design: 8 easy / 27 medium / 5 hard, drawn without replacement from
the 22 / 90 / 8 available. Hard is deliberately over-sampled for trajectory
analysis; the stratified estimator in score.py corrects the weighting.

    python subset/sample_subset.py          # print YAML block
"""

import collections
import glob
import pathlib
import random
import re

SEED = 20260918
WANT = {"easy": 8, "medium": 27, "hard": 5}
TASKS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tasks"


def population() -> dict[str, list[str]]:
    buckets = collections.defaultdict(list)
    for toml in sorted(glob.glob(str(TASKS_DIR / "*" / "task.toml"))):
        text = pathlib.Path(toml).read_text(encoding="utf8")
        difficulty = re.search(r'difficulty\s*=\s*"([^"]+)"', text).group(1)
        buckets[difficulty].append(pathlib.Path(toml).parent.name)
    return {k: sorted(v) for k, v in buckets.items()}


def draw() -> dict[str, list[str]]:
    pool = population()
    rng = random.Random(SEED)
    return {k: sorted(rng.sample(pool[k], n)) for k, n in WANT.items()}


if __name__ == "__main__":
    pool, selected = population(), draw()
    for level in ("easy", "medium", "hard"):
        print(f"      # {level}: {len(selected[level])} of {len(pool[level])}")
        for name in selected[level]:
            # Bare directory name, NOT "local/<name>": DatasetConfig matches
            # LocalTaskId.get_name() (the dir name) via fnmatch, so a "local/"
            # prefix never matches a local path: dataset.
            print(f'      - "{name}"')
