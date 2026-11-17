#!/usr/bin/env python3
"""Check the audit output: every line must be a theorem whose axioms are a subset of
{propext, Classical.choice, Quot.sound}.  Writes the sorted listing plus a summary."""
import re, sys
raw = open(sys.argv[1]).read().splitlines()
ok = {'propext', 'Classical.choice', 'Quot.sound'}
rows, bad = [], []
for l in raw:
    if not l.strip(): continue
    m = re.match(r"'(.*)' depends on axioms: \[(.*)\] \[module (.*)\]$", l)
    n = re.match(r"'(.*)' does not depend on any axioms \[module (.*)\]$", l)
    if m:
        ax = [a.strip() for a in m.group(2).split(',')]
        rows.append((m.group(3), m.group(1), ax))
        if not set(ax) <= ok: bad.append(f'NONSTANDARD AXIOMS {m.group(1)}: {sorted(set(ax) - ok)}')
    elif n: rows.append((n.group(2), n.group(1), []))
    else: bad.append(f'UNEXPECTED OUTPUT: {l}')
rows.sort()
for mod, name, ax in rows:
    print(f"'{name}' depends on axioms: [{', '.join(ax)}]" if ax else f"'{name}' does not depend on any axioms")
for b in bad: print(b)
nmods = len({r[0] for r in rows})
if bad or not rows:
    print(f'AUDIT FAIL: {len(bad)} problems, {len(rows)} theorems'); sys.exit(1)
print(f'AUDIT PASS: {len(rows)} theorems in {nmods} modules depend only on propext, Classical.choice, Quot.sound (or on no axioms)')
