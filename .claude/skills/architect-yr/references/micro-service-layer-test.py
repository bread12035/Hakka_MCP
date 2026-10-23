"""Layer test for a micro-service. Copy to tests/test_layers.py.

Set PACKAGE to the folder (or module prefix) that holds main.py, worker.py,
helper.py, models.py, common/ and config/. Import direction may only go down
ORDER. common and config are leaves that every layer may import.
Standard library only.
"""
import ast
from pathlib import Path

PACKAGE = "service"  # folder under the repo root or under src/
ORDER = ["main", "worker", "helper", "models"]
LEAVES = {"common", "config"}
BROKER_CALLS = {"ack", "nack", "basic_ack", "basic_nack", "reject"}


def _root():
    here = Path(__file__).resolve().parent.parent
    for cand in (here / "src" / PACKAGE, here / PACKAGE):
        if cand.is_dir():
            return cand
    raise AssertionError(f"package folder '{PACKAGE}' not found")


def _layer_of(path, root):
    rel = path.relative_to(root)
    first = rel.parts[0]
    name = first[:-3] if first.endswith(".py") else first
    return name


def _imported_layers(tree, pkg_prefix):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 1 and node.module:
                found.add(node.module.split(".")[0])
            elif node.level == 1 and not node.module:
                found.update(a.name.split(".")[0] for a in node.names)
            elif node.level == 0 and node.module and node.module.split(".")[0] == pkg_prefix:
                parts = node.module.split(".")
                if len(parts) > 1:
                    found.add(parts[1])
                else:
                    found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.Import):
            for a in node.names:
                parts = a.name.split(".")
                if parts[0] == pkg_prefix and len(parts) > 1:
                    found.add(parts[1])
    return found


def test_imports_only_point_down():
    root = _root()
    problems = []
    for path in sorted(root.rglob("*.py")):
        layer = _layer_of(path, root)
        if layer in LEAVES and layer not in ORDER:
            allowed = LEAVES
        elif layer in ORDER:
            allowed = set(ORDER[ORDER.index(layer) + 1:]) | LEAVES | {layer}
        else:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for target in _imported_layers(tree, root.name):
            if (target in ORDER or target in LEAVES) and target not in allowed:
                problems.append(f"{path.relative_to(root)}: {layer} must not import {target}")
    assert not problems, "\n".join(problems)


def test_only_worker_acks():
    root = _root()
    problems = []
    for path in sorted(root.rglob("*.py")):
        if _layer_of(path, root) == "worker":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in BROKER_CALLS:
                problems.append(f"{path.relative_to(root)}:{node.lineno}: ack or nack outside worker")
    assert not problems, "\n".join(problems)


def test_only_config_reads_environment():
    root = _root()
    problems = []
    for path in sorted(root.rglob("*.py")):
        if _layer_of(path, root) in ("config", "main"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in ("environ", "getenv") and isinstance(node.value, ast.Name) and node.value.id == "os":
                problems.append(f"{path.relative_to(root)}:{node.lineno}: environment read outside config")
    assert not problems, "\n".join(problems)
