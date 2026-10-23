#!/usr/bin/env python3
"""Unpack a plain-text skill pack into a Claude Code .claude folder.

Only the Python 3 standard library is used. No network, no npm, no archives.

Pack format: every file starts with a line "@@@@FILE@@@@ <relative path>".
The content is every line after it, up to the next such line.

Usage:
  python3 unpack.py <pack.txt> <path-to-.claude>            install
  python3 unpack.py --force <pack.txt> <path-to-.claude>    overwrite existing skill folders
  python3 unpack.py --replace <pack.txt> <path-to-.claude>  remove the old install of this pack, then install
  python3 unpack.py --list <pack.txt>                       list files in the pack
  python3 unpack.py --remove <pack-name> <path-to-.claude>  remove an installed pack
"""
import sys
from pathlib import Path, PurePosixPath

MARK = "@@@@FILE@@@@ "
ALLOWED_TOP = ("skills", "agents")


def parse(pack_path):
    text = Path(pack_path).read_text(encoding="utf-8", newline="")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    files, cur_path, cur = [], None, []
    for raw in lines:
        line = raw.rstrip("\r")
        if line.startswith(MARK):
            if cur_path is not None:
                files.append((cur_path, cur))
            cur_path, cur = line[len(MARK):].strip(), []
        elif cur_path is not None:
            cur.append(raw)
    if cur_path is not None:
        files.append((cur_path, cur))
    return [(p, "\n".join(c) + "\n" if c else "") for p, c in files]


def check_path(rel, pack_name):
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise SystemExit(f"Refusing unsafe path in pack: {rel}")
    top = p.parts[0]
    if top not in ALLOWED_TOP and top != f"skillpack-{pack_name}":
        raise SystemExit(f"Refusing path outside skills/, agents/ or skillpack-{pack_name}/: {rel}")
    return p


def install(pack_path, target, force):
    target = Path(target)
    files = parse(pack_path)
    if not files:
        raise SystemExit("No files found in the pack. Is this the right .txt file?")
    names = {PurePosixPath(r).parts[0][len("skillpack-"):] for r, _ in files if PurePosixPath(r).parts[0].startswith("skillpack-")}
    pack_name = names.pop() if len(names) == 1 else Path(pack_path).stem
    for rel, _ in files:
        check_path(rel, pack_name)
    # skill and agent units: skills/<name>/ folders and agents/<file>
    units = {}
    for rel, _ in files:
        parts = PurePosixPath(rel).parts
        if parts[0] == "skills" and len(parts) > 2:
            units[("skills", parts[1])] = target / "skills" / parts[1]
        elif parts[0] == "agents":
            units[("agents", parts[1])] = target / "agents" / parts[1]
    existing = sorted(k[1] for k, v in units.items() if v.exists())
    skip = set()
    if existing and not force:
        skip = {k for k, v in units.items() if v.exists()}
        print(f"Skipping {len(skip)} existing item(s). Use --replace to swap in a new version of this pack, or --force to overwrite:")
        for k in sorted(skip):
            print(f"  {k[0]}/{k[1]}")
    written, manifest = 0, []
    for rel, content in files:
        parts = PurePosixPath(rel).parts
        key = (parts[0], parts[1]) if parts[0] in ALLOWED_TOP and len(parts) > 1 else None
        if key in skip:
            continue
        dest = target.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8", newline="")
        manifest.append(rel)
        written += 1
    meta = target / f"skillpack-{pack_name}"
    meta.mkdir(parents=True, exist_ok=True)
    old = meta / "MANIFEST.txt"
    prev = old.read_text(encoding="utf-8").splitlines() if old.exists() else []
    merged = sorted(set(prev) | set(manifest) | {f"skillpack-{pack_name}/MANIFEST.txt"})
    old.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"Wrote {written} file(s) into {target}")
    print(f"Next: restart Claude Code, type /skills, then run /yr-coding-skills" if pack_name == "yr-coding-skills" else "Next: restart Claude Code and type /skills")


def remove(pack_name, target):
    target = Path(target)
    meta = target / f"skillpack-{pack_name}"
    manifest = meta / "MANIFEST.txt"
    if not manifest.exists():
        raise SystemExit(f"No manifest at {manifest}. Nothing to remove.")
    n = 0
    for rel in manifest.read_text(encoding="utf-8").splitlines():
        rel = rel.strip()
        if not rel:
            continue
        p = check_path(rel, pack_name)
        f = target.joinpath(*p.parts)
        if f.is_file():
            f.unlink()
            n += 1
    # prune empty folders under skills/, agents/ and the pack folder
    for base in [target / "skills", target / "agents", meta]:
        if base.exists():
            for d in sorted((x for x in base.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
                if not any(d.iterdir()):
                    d.rmdir()
            if base != target / "skills" and base != target / "agents" and not any(base.iterdir()):
                base.rmdir()
    print(f"Removed {n} file(s) for pack {pack_name}")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if "--list" in flags and len(args) == 1:
        for rel, content in parse(args[0]):
            print(f"{len(content):8d}  {rel}")
        return
    if "--remove" in flags and len(args) == 2:
        return remove(args[0], args[1])
    if len(args) == 2 and flags == {"--replace"}:
        files = parse(args[0])
        names = {PurePosixPath(r).parts[0][len("skillpack-"):] for r, _ in files if PurePosixPath(r).parts[0].startswith("skillpack-")}
        pack_name = names.pop() if len(names) == 1 else Path(args[0]).stem
        if (Path(args[1]) / f"skillpack-{pack_name}" / "MANIFEST.txt").exists():
            remove(pack_name, args[1])
        else:
            print(f"No earlier install of {pack_name} found in {args[1]}.")
        return install(args[0], args[1], False)
    if len(args) == 2 and flags <= {"--force"}:
        return install(args[0], args[1], "--force" in flags)
    print(__doc__)
    raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
