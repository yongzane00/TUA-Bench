"""Generate a standalone variant config from baseline.yaml.

harbor 0.6.3 accepts a single -c, so variants cannot be overlays — each must
be a complete JobConfig. This keeps the 40-task list and protocol in
baseline.yaml as the single source of truth and stamps out full files.

    python subset/make_variant.py qwen38-flash-next/harness0-attempt1 n_attempts=1

Put each variant under a folder named after its model (qwen38-flash-next/, qwen36-35b-a3b/, ...),
matching jobs/<model>/. baseline.yaml is the qwen3.8-flash-next protocol; other models override
agents.0.model_name, agents.0.kwargs.api_base and agents.0.kwargs.model_info.*.

Naming convention: harness<N>-<description>. harness0-* are the default-harness
baseline (H0), harness1/2/3-* the single interventions, harnessstar-* the
combined system. Use the same name for the job dir, so config and results line
up: -o jobs/<name>.

Dotted paths index into the parsed YAML; list indices are integers. Values are
parsed as YAML scalars, so 20, 0.7, true and null all come through typed.
A key must already exist in baseline.yaml (guards against typos); prefix it
with + to add a new one, e.g. +agents.0.import_path=pkg.module:Class.
"""

import pathlib
import sys

import yaml

CONFIGS = pathlib.Path(__file__).resolve().parent


def set_path(tree, dotted: str, value, allow_new: bool = False) -> None:
    keys = dotted.split(".")
    node = tree
    for key in keys[:-1]:
        node = node[int(key)] if isinstance(node, list) else node[key]
    last = keys[-1]
    if isinstance(node, list):
        node[int(last)] = value
    else:
        if last not in node and not allow_new:
            raise KeyError(f"{dotted!r}: {last!r} is not in baseline.yaml (prefix with + to add it)")
        node[last] = value


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.exit(__doc__)
    name, assignments = argv[0], argv[1:]

    config = yaml.safe_load((CONFIGS / "baseline.yaml").read_text(encoding="utf8"))
    applied = []
    for assignment in assignments:
        if "=" not in assignment:
            sys.exit(f"expected key=value, got {assignment!r}")
        dotted, raw = assignment.split("=", 1)
        allow_new = dotted.startswith("+")
        dotted = dotted.removeprefix("+")
        set_path(config, dotted, yaml.safe_load(raw), allow_new)
        applied.append(f"#   {dotted} = {raw}")

    out = CONFIGS / "variants" / f"{name}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    header = [
        f"# {name} — generated from baseline.yaml by make_variant.py.",
        "# Do not hand-edit; regenerate instead. Changes vs baseline:",
        *applied,
        f"#\n#   harbor run -c subset/variants/{name}.yaml -o jobs/{name}\n",
    ]
    out.write_text("\n".join(header) + yaml.safe_dump(config, sort_keys=False), encoding="utf8")
    print(f"wrote {out.relative_to(CONFIGS.parent)}")
    for line in applied:
        print(line.replace("#  ", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
