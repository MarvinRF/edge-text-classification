"""Dependency rules between components, read from the code (ADR 0003).

- `bench`, `guard`, `ports` and `criteria` run on the edge device: they never
  import torch, transformers, datasets, `train` or `export`;
- only `data` and `train` reach the network (HTTP clients, the Hugging Face Hub);
- no file in `src/edgecls` exceeds 500 lines without a reason listed in LONG.

Imports are read from the AST, one by one, including those inside functions.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "edgecls"
ON_DEVICE = {"bench", "guard", "ports", "criteria"}
TRAINING_STACK = {"torch", "transformers", "datasets", "edgecls.train", "edgecls.export"}
NETWORK = {"http", "urllib", "requests", "httpx", "aiohttp", "huggingface_hub", "datasets"}
MAY_USE_NETWORK = {"data", "train"}
LINE_LIMIT = 500
# file -> reason. Empty today.
LONG: dict[str, str] = {}


def imported(file: Path, root: Path = ROOT) -> list[str]:
    """Absolute module names imported by the file; relative imports are resolved."""
    package = ".".join(file.relative_to(root / "src").with_suffix("").parts[:-1])
    found: list[str] = []
    for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                base = parts[: len(parts) - node.level + 1]
                module = ".".join([*base, node.module or ""]).rstrip(".")
            elif node.module:
                module = node.module
            else:
                continue
            # "from a import b" may bring submodule a.b: both count.
            found += [module, *(f"{module}.{a.name}" for a in node.names)]
    return found


def matches(module: str, forbidden: set[str]) -> bool:
    return any(module == f or module.startswith(f + ".") for f in forbidden)


def files() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def component(file: Path) -> str:
    """First path part under the package: `bench/x.py` -> bench, `ports.py` -> ports."""
    return file.relative_to(PACKAGE).with_suffix("").parts[0]


def test_reads_plain_from_relative_and_function_level_imports(tmp_path: Path) -> None:
    file = tmp_path / "src" / "edgecls" / "x" / "m.py"
    file.parent.mkdir(parents=True)
    file.write_text(
        "import torch\nfrom .y import z\ndef f():\n    from urllib import request\n",
        encoding="utf-8",
    )
    assert imported(file, root=tmp_path) == [
        "torch",
        "edgecls.x.y",
        "edgecls.x.y.z",
        "urllib",
        "urllib.request",
    ]


def test_rules_see_the_package() -> None:
    assert files(), "no source files found: the rules below would pass vacuously"


def test_on_device_code_never_imports_the_training_stack() -> None:
    bad = [
        f"{f.relative_to(ROOT)}: {m}"
        for f in files()
        if component(f) in ON_DEVICE
        for m in imported(f)
        if matches(m, TRAINING_STACK)
    ]
    assert bad == []


def test_only_data_and_train_use_the_network() -> None:
    bad = [
        f"{f.relative_to(ROOT)}: {m}"
        for f in files()
        if component(f) not in MAY_USE_NETWORK
        for m in imported(f)
        if matches(m, NETWORK)
    ]
    assert bad == []


def test_files_stay_short() -> None:
    bad = [
        f"{f.relative_to(ROOT)}: {n} lines"
        for f in files()
        if (n := len(f.read_text(encoding="utf-8").splitlines())) > LINE_LIMIT
        and str(f.relative_to(ROOT)) not in LONG
    ]
    assert bad == []
