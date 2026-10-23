#!/usr/bin/env python3
"""Validate, check and archive an OpenSpec-style change. Standard library only.

Layout (relative to the repo root):
  openspec/specs/<domain>/spec.md                   current truth
  openspec/changes/<name>/proposal.md
  openspec/changes/<name>/specs/<domain>/spec.md    delta: ADDED / MODIFIED / REMOVED
  openspec/changes/archive/<date>-<name>/           finished changes

Commands:
  validate <change-dir>
      Check the delta files: headers, unique names, at least one scenario per
      requirement, SHALL or MUST in the requirement text.
  check <change-dir> --tests <tests-dir> [<tests-dir> ...]
      For every scenario in the delta, look for `def test_<slug>` in the tests.
      Reports missing tests and tests that still skip.
  apply <change-dir> --specs <specs-dir> --archive <archive-dir> [--date YYYY-MM-DD] [--dry-run]
      Merge the deltas into the specs, then move the change folder into the archive.
      Everything is validated in memory first. Nothing is written on an error.

  remerge <archived-change-dir> --specs <specs-dir> [--dry-run]
      Re-apply the deltas of an already archived change to the specs. Nothing is moved.
      Use it after a git conflict in a spec file.

Exit code 0 = ok, 1 = problems found, 2 = bad usage.
"""
import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

REQ_RE = re.compile(r"^### Requirement:[ \t]*(.+?)[ \t]*$")
SCN_RE = re.compile(r"^#### Scenario:[ \t]*(.+?)[ \t]*$")
H2_RE = re.compile(r"^## (.+?)[ \t]*$")
SECTIONS = ("ADDED", "MODIFIED", "REMOVED")


class SpecError(Exception):
    pass


def read(path):
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def split_blocks(lines):
    """Split lines into (preamble_lines, [(name, block_lines)]). A block starts at a
    requirement header and ends before the next requirement header or any `## ` header."""
    pre, blocks, cur_name, cur = [], [], None, []
    for line in lines:
        m = REQ_RE.match(line)
        if m or H2_RE.match(line):
            if cur_name is not None:
                blocks.append((cur_name, cur))
                cur_name, cur = None, []
            if m:
                cur_name, cur = m.group(1), [line]
                continue
        if cur_name is not None:
            cur.append(line)
        else:
            pre.append(line)
    if cur_name is not None:
        blocks.append((cur_name, cur))
    return pre, blocks


def split_spec(lines):
    """Split a current spec into (preamble, [(name, block)], tail). The tail is every
    `## ` section after the requirements, such as `## Notes`. It stays at the end."""
    pre, blocks, tail = [], [], []
    cur_name, cur, seen_req, in_tail = None, [], False, False
    for line in lines:
        if in_tail:
            tail.append(line)
            continue
        m, h = REQ_RE.match(line), H2_RE.match(line)
        if m:
            if cur_name is not None:
                blocks.append((cur_name, cur))
            cur_name, cur = m.group(1), [line]
            continue
        if h:
            title = h.group(1).strip().lower()
            if cur_name is not None or (seen_req and title != "requirements"):
                if cur_name is not None:
                    blocks.append((cur_name, cur))
                    cur_name, cur = None, []
                in_tail = True
                tail.append(line)
                continue
            if title == "requirements":
                seen_req = True
        (cur if cur_name is not None else pre).append(line)
    if cur_name is not None:
        blocks.append((cur_name, cur))
    return pre, blocks, tail


def trim(block):
    out = list(block)
    while out and not out[-1].strip():
        out.pop()
    return out


def parse_delta(path):
    """Return {'purpose': str|None, 'ADDED': [(name, lines)], 'MODIFIED': [...], 'REMOVED': [...]}"""
    text = read(path)
    lines = text.split("\n")
    result = {"purpose": None, "ADDED": [], "MODIFIED": [], "REMOVED": []}
    sections, cur, buf = [], None, []
    for line in lines:
        m = H2_RE.match(line)
        if m:
            if cur is not None:
                sections.append((cur, buf))
            cur, buf = m.group(1).strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        sections.append((cur, buf))
    for title, body in sections:
        if title.lower() == "purpose":
            result["purpose"] = "\n".join(body).strip()
            continue
        m = re.match(r"^(ADDED|MODIFIED|REMOVED)\s+Requirements$", title, re.I)
        if not m:
            raise SpecError(f"{path}: unknown section '## {title}'. Allowed: Purpose, ADDED Requirements, MODIFIED Requirements, REMOVED Requirements")
        _, blocks = split_blocks(body)
        result[m.group(1).upper()].extend((n, trim(b)) for n, b in blocks)
    return result


def scenarios_of(block_lines):
    return [m.group(1) for m in (SCN_RE.match(l) for l in block_lines) if m]


def validate_delta(path):
    errs, warns = [], []
    try:
        d = parse_delta(path)
    except SpecError as e:
        return [str(e)], []
    names = [n for sec in SECTIONS for n, _ in d[sec]]
    for n in sorted({n for n in names if names.count(n) > 1}):
        errs.append(f"{path}: requirement '{n}' appears more than once")
    scn = []
    for sec in ("ADDED", "MODIFIED"):
        for name, block in d[sec]:
            ss = scenarios_of(block)
            if not ss:
                errs.append(f"{path}: requirement '{name}' ({sec}) has no '#### Scenario:'")
            if not re.search(r"\b(SHALL|MUST)\b", "\n".join(block)):
                warns.append(f"{path}: requirement '{name}' has no SHALL or MUST")
            scn.extend(ss)
    for s in sorted({s for s in scn if scn.count(s) > 1}):
        errs.append(f"{path}: scenario '{s}' appears more than once")
    slugs = {}
    for s in scn:
        slugs.setdefault(slug(s), []).append(s)
    for k, v in slugs.items():
        if len(set(v)) > 1:
            errs.append(f"{path}: scenarios {v} give the same test name test_{k}")
    if not any(d[s] for s in SECTIONS):
        errs.append(f"{path}: delta has no requirements")
    return errs, warns


def delta_files(change):
    root = Path(change) / "specs"
    return sorted(root.glob("*/spec.md")) if root.is_dir() else []


def merge_spec(domain, spec_text, delta):
    """Return the new spec text. Raises SpecError on conflicts."""
    if spec_text is None:
        if delta["MODIFIED"] or delta["REMOVED"]:
            raise SpecError(f"{domain}: spec does not exist yet, so it cannot have MODIFIED or REMOVED requirements")
        purpose = delta["purpose"] or "TBD"
        pre = [f"# {domain} Specification", "", "## Purpose", purpose, "", "## Requirements"]
        blocks, tail = [], []
    else:
        lines = spec_text.split("\n")
        pre, blocks, tail = split_spec(lines)
        pre = list(pre)
        if not any(re.match(r"^## Requirements\s*$", l) for l in pre):
            pre += ["", "## Requirements"]
    index = {n: i for i, (n, _) in enumerate(blocks)}
    blocks = [(n, trim(b)) for n, b in blocks]
    for name, block in delta["REMOVED"]:
        if name not in index:
            raise SpecError(f"{domain}: REMOVED requirement '{name}' not found in the spec")
    for name, block in delta["MODIFIED"]:
        if name not in index:
            raise SpecError(f"{domain}: MODIFIED requirement '{name}' not found in the spec")
    for name, block in delta["ADDED"]:
        if name in index:
            raise SpecError(f"{domain}: ADDED requirement '{name}' already exists. Use MODIFIED")
    removed = {n for n, _ in delta["REMOVED"]}
    modified = dict(delta["MODIFIED"])
    out = []
    for name, block in blocks:
        if name in removed:
            continue
        out.append((name, modified.get(name, block)))
    out.extend(delta["ADDED"])
    text = "\n".join(trim(pre)) + "\n"
    for _, block in out:
        text += "\n" + "\n".join(block) + "\n"
    tail = trim(tail)
    if tail:
        text += "\n" + "\n".join(tail) + "\n"
    return text


def cmd_validate(a):
    files = delta_files(a.change)
    if not files:
        print(f"No delta files under {a.change}/specs/*/spec.md")
        return 1
    bad = 0
    for f in files:
        errs, warns = validate_delta(f)
        for w in warns:
            print("warning:", w)
        for e in errs:
            print("error:", e)
        bad += len(errs)
    print("valid" if not bad else f"{bad} error(s)")
    return 1 if bad else 0


def cmd_check(a):
    files = delta_files(a.change)
    tests = {}
    for t in a.tests:
        for p in sorted(Path(t).rglob("*.py")) if Path(t).is_dir() else []:
            tests[p] = read(p)
    missing, skipped, ok = [], [], 0
    for f in files:
        d = parse_delta(f)
        for sec in ("ADDED", "MODIFIED"):
            for name, block in d[sec]:
                for sc in scenarios_of(block):
                    fn = f"test_{slug(sc)}"
                    pat = re.compile(rf"^[ \t]*(?:async[ \t]+)?def {re.escape(fn)}\b", re.M)
                    found = [(p, t) for p, t in tests.items() if pat.search(t)]
                    if not found:
                        missing.append((f.parent.name, sc, fn))
                        continue
                    p, t = found[0]
                    m = pat.search(t)
                    start = m.start()
                    nxt = re.search(r"^(?:@|def |async def |class )", t[m.end():], re.M)
                    body = t[max(0, start - 200): m.end() + (nxt.start() if nxt else len(t))]
                    if re.search(r"pytest\.skip\(|mark\.skip\b|unittest\.skip|NotImplementedError", body):
                        skipped.append((f.parent.name, sc, fn))
                    else:
                        ok += 1
    print(f"scenarios with a passing-shape test: {ok}")
    for dom, sc, fn in missing:
        print(f"missing: [{dom}] '{sc}' -> {fn}")
    for dom, sc, fn in skipped:
        print(f"still skipped: [{dom}] '{sc}' -> {fn}")
    return 1 if (missing or skipped) else 0


def cmd_apply(a):
    change = Path(a.change)
    if not change.is_dir():
        print(f"Not a folder: {change}")
        return 2
    specs, archive = Path(a.specs), Path(a.archive)
    date = a.date or datetime.date.today().isoformat()
    target = archive / f"{date}-{change.name}"
    if target.exists():
        print(f"Archive target exists: {target}")
        return 1
    files = delta_files(change)
    writes = []
    all_errs = []
    for f in files:
        errs, _ = validate_delta(f)
        all_errs += errs
    if all_errs:
        for e in all_errs:
            print("error:", e)
        return 1
    try:
        for f in files:
            domain = f.parent.name
            spec_path = specs / domain / "spec.md"
            old = read(spec_path) if spec_path.exists() else None
            writes.append((spec_path, merge_spec(domain, old, parse_delta(f)), old is None))
    except SpecError as e:
        print("error:", e)
        return 1
    for p, _, new in writes:
        print(("create " if new else "update ") + str(p))
    print(f"move {change} -> {target}")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    for p, text, _ in writes:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
    archive.mkdir(parents=True, exist_ok=True)
    shutil.move(str(change), str(target))
    print("done")
    return 0


def cmd_remerge(a):
    """Re-apply the deltas of an archived change to the specs, without moving anything.
    Used after a git conflict in a spec file: take the other side's spec, then run this."""
    files = delta_files(a.change)
    if not files:
        print(f"No delta files under {a.change}/specs/*/spec.md")
        return 1
    writes = []
    try:
        for f in files:
            domain = f.parent.name
            spec_path = Path(a.specs) / domain / "spec.md"
            old = read(spec_path) if spec_path.exists() else None
            writes.append((spec_path, merge_spec(domain, old, parse_delta(f)), old is None))
    except SpecError as e:
        print("error:", e)
        return 1
    for p, text, new in writes:
        print(("create " if new else "update ") + str(p))
        if not a.dry_run:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="\n")
    print("dry run: nothing written" if a.dry_run else "done")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("change"); v.set_defaults(fn=cmd_validate)
    c = sub.add_parser("check"); c.add_argument("change"); c.add_argument("--tests", nargs="+", required=True); c.set_defaults(fn=cmd_check)
    p = sub.add_parser("apply"); p.add_argument("change"); p.add_argument("--specs", required=True)
    p.add_argument("--archive", required=True); p.add_argument("--date"); p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_apply)
    r = sub.add_parser("remerge"); r.add_argument("change"); r.add_argument("--specs", required=True); r.add_argument("--dry-run", action="store_true"); r.set_defaults(fn=cmd_remerge)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except SpecError as e:
        print("error:", e)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
