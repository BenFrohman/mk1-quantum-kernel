#!/usr/bin/env python3
"""Apply the Frohman Lean module-header rule.

Copyright block before any import. Authors line is exactly
'Authors: Benjamin Stanley Frohman'. The module docstring /-/! comes
after the imports and its first line is a '#' heading.
"""
import re
import sys
from pathlib import Path

COPY = """/-
Copyright (c) {year} Benjamin Stanley Frohman. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Benjamin Stanley Frohman
-/"""

IMPORT_RE = re.compile(
    r"^(?:public\s+|private\s+)?(?:meta\s+)?import(?:\s+all)?\s+\S"
)
MODULE_RE = re.compile(r"^(?:module|prelude)\s*$")
DECL_RE = re.compile(
    r"^(?:theorem|lemma|def|abbrev|structure|inductive|axiom|instance)\s+(\S+)",
    re.M,
)
META_LINE = re.compile(
    r"^(?:--\s*)?(?:SPDX-|Author\s*:|Copyright\s)",
)


def module_title(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if rel.endswith(".lean"):
        rel = rel[: -len(".lean")]
    return rel.replace("/", ".")


def find_year(text: str) -> str:
    m = re.search(r"Copyright \(c\) (\d{4})", text)
    if m:
        return m.group(1)
    m = re.search(r"SPDX-FileCopyrightText:\s*(\d{4})", text)
    if m:
        return m.group(1)
    return "2026"


def foreign_copyright(text: str) -> bool:
    head = text[:700]
    if "Copyright" not in head and "SPDX-FileCopyrightText" not in head:
        return False
    window = head.split("import", 1)[0]
    return "Frohman" not in window and (
        "Copyright" in window or "SPDX-FileCopyrightText" in window
    )


def peel_copyright_block(text: str):
    """Drop one leading Frohman copyright comment. Keep its prose."""
    year = find_year(text)
    stripped = text.lstrip("\n")
    prose = []
    while stripped.startswith("--"):
        line, _, rest = stripped.partition("\n")
        if "SPDX-" in line or line.strip().startswith("-- Author") or line.strip().startswith("-- Copyright") or line.strip().startswith("-- License"):
            stripped = rest
            continue
        break
    if not stripped.startswith("/-") or stripped.startswith("/-!"):
        return stripped, prose, year
    end = stripped.find("-/", 2)
    if end < 0:
        return stripped, prose, year
    block = stripped[: end + 2]
    if "Copyright" not in block or "Frohman" not in block:
        return stripped, prose, year
    for ln in block.splitlines():
        s = ln.strip()
        if not s or s in {"/-", "-/"}:
            continue
        if s.startswith("Copyright (c) ") or s.startswith("Released under Apache 2.0"):
            continue
        if s.startswith("Authors:") or s.startswith("SPDX-"):
            continue
        if s == "Author: Benjamin Stanley Frohman":
            continue
        prose.append(ln.rstrip())
    return stripped[end + 2 :].lstrip("\n"), prose, year


def split_preamble(text: str):
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("/-!", i):
            end = text.find("-/", i + 3)
            if end < 0:
                break
            return text[:i], text[i : end + 2], text[end + 2 :]
        if text.startswith("/-", i):
            end = text.find("-/", i + 2)
            if end < 0:
                break
            i = end + 2
            continue
        if text.startswith("--", i):
            nl = text.find("\n", i)
            i = n if nl < 0 else nl + 1
            continue
        if text[i] in " \t\r\n":
            i += 1
            continue
        nl = text.find("\n", i)
        line = text[i: n if nl < 0 else nl].strip()
        if IMPORT_RE.match(line) or MODULE_RE.match(line):
            i = n if nl < 0 else nl + 1
            continue
        return text[:i], None, text[i:]
    return text, None, ""


def normalize_doc(doc: str | None, title: str) -> str:
    if doc is None:
        return f"/-!\n# {title}\n\nMachine-checked Lean 4 module.\n-/"
    inner = doc[3:]
    if inner.endswith("-/"):
        inner = inner[:-2]
    kept = []
    for ln in inner.splitlines():
        s = ln.strip()
        if s in {
            "Author: Benjamin Stanley Frohman",
            "Authors: Benjamin Stanley Frohman",
            "Authors: Frohman, Benjamin Stanley",
            "Authors: Benjamin Stanley Frohman (@BenFrohman)",
        }:
            continue
        if re.match(r"^(Date|License)\s*:", s):
            continue
        kept.append(ln.rstrip())
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    if not kept or not kept[0].strip().startswith("#"):
        kept.insert(0, f"# {title}")
        if len(kept) > 1 and kept[1].strip():
            kept.insert(1, "")
    return "/-!\n" + "\n".join(kept) + "\n-/"


def transform(text: str, title: str) -> str:
    if foreign_copyright(text):
        return text
    body, prose, year = peel_copyright_block(text)
    lines = body.splitlines(keepends=True)
    while lines:
        raw = lines[0].strip()
        if raw.startswith("--") and (
            "SPDX-" in raw or raw.startswith("-- Author") or raw.startswith("-- Copyright") or raw.startswith("-- License")
        ):
            lines.pop(0)
            continue
        break
    body = "".join(lines).lstrip("\n")
    preamble, doc, rest = split_preamble(body)
    if prose:
        if doc is None:
            doc = "/-!\n" + "\n".join(prose) + "\n-/"
        else:
            inner = doc[3:]
            if inner.endswith("-/"):
                inner = inner[:-2]
            doc = "/-!\n" + "\n".join(prose) + "\n" + inner.lstrip("\n")
            if not doc.rstrip().endswith("-/"):
                doc = doc.rstrip() + "\n-/"
    doc = normalize_doc(doc, title)
    pre = preamble.strip("\n")
    out = COPY.format(year=year) + "\n\n"
    if pre:
        out += pre + "\n\n"
    out += doc + "\n"
    tail = rest.lstrip("\n")
    if tail:
        if not tail.endswith("\n"):
            tail += "\n"
        out += "\n" + tail
    elif not out.endswith("\n"):
        out += "\n"
    return out


def decls(text: str):
    return DECL_RE.findall(text)


def fix_file(path: Path, root: Path) -> str:
    original = path.read_text(encoding="utf-8")
    title = module_title(path, root)
    updated = transform(original, title)
    if path.as_posix().endswith("RCW-Residuals-Lean/RCW/R2TwistFibers.lean") or (
        root.name == "RCW-Residuals-Lean" and path.name == "R2TwistFibers.lean"
    ):
        updated = updated.replace("namespace RCW_R2_TwistFibers", "namespace RCW.R2TwistFibers")
        updated = updated.replace("end RCW_R2_TwistFibers", "end RCW.R2TwistFibers")
    if decls(original) != decls(updated):
        raise SystemExit(f"declaration list changed: {path}")
    if original.count("sorry") != updated.count("sorry"):
        raise SystemExit(f"sorry count changed: {path}")
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return "fixed"
    return "ok"


def main():
    check = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--check"]
    root = Path(args[0])
    changed = 0
    ok = 0
    for path in sorted(root.rglob("*.lean")):
        if ".lake" in path.parts or ".git" in path.parts:
            continue
        if check:
            original = path.read_text(encoding="utf-8")
            title = module_title(path, root)
            updated = transform(original, title)
            if root.name == "RCW-Residuals-Lean" and path.name == "R2TwistFibers.lean":
                updated = updated.replace("namespace RCW_R2_TwistFibers", "namespace RCW.R2TwistFibers")
                updated = updated.replace("end RCW_R2_TwistFibers", "end RCW.R2TwistFibers")
            if updated != original:
                print(f"header drift: {path.relative_to(root)}")
                changed += 1
            else:
                ok += 1
            continue
        status = fix_file(path, root)
        if status == "fixed":
            changed += 1
        else:
            ok += 1
    if check:
        print(f"{root.name}: {changed} drifted, {ok} ok")
        if changed:
            raise SystemExit(1)
        return
    print(f"{root.name}: fixed {changed}, already ok {ok}")


if __name__ == "__main__":
    main()
