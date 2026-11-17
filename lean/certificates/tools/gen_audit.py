#!/usr/bin/env python3
"""Kernel-certificate helper: list this repository's built Lean modules and write a Lean
file that runs `collectAxioms` (the function behind `#print axioms`) on every theorem
declared in them.  Usage: python3 certificates/tools/gen_audit.py OUT.lean MODULES.txt"""
import os, subprocess, sys
out, modlist = sys.argv[1], sys.argv[2]
files = subprocess.check_output(['git', 'ls-files', '*.lean']).decode().split()
roots = ['.lake/build/lib/lean', '.lake/build/lib', 'build/lib']
mods = []
for f in files:
    if f.startswith(('.lake/', 'lake-packages/')) or os.path.basename(f) in ('lakefile.lean',):
        continue
    rel = f[:-5]
    if any(os.path.exists(os.path.join(r, rel + '.olean')) for r in roots):
        mods.append(rel.replace('/', '.'))
mods.sort()
open(modlist, 'w').write('\n'.join(mods) + '\n')
names = ', '.join('`' + '.'.join('«' + p + '»' for p in m.split('.')) for m in mods)
imports = '\n'.join('import ' + '.'.join('«' + p + '»' for p in m.split('.')) for m in mods)
open(out, 'w').write(f"""import Lean
{imports}

open Lean Elab Command

/-- Prints `#print axioms`-style lines for every theorem declared in the listed modules. -/
elab "#kernel_certificate_audit" : command => do
  let env ← getEnv
  let mods : Array Name := #[{names}]
  for m in mods do
    match env.getModuleIdx? m with
    | none => IO.println s!"MODULE NOT LOADED {{m}}"
    | some i =>
      for n in (env.header.moduleData[i.toNat]!).constNames do
        match env.find? n with
        | some (.thmInfo _) =>
          if !n.isInternal then
            let ax ← collectAxioms n
            let axs := ", ".intercalate (ax.toList.map toString)
            if ax.isEmpty then IO.println s!"'{{n}}' does not depend on any axioms [module {{m}}]"
            else IO.println s!"'{{n}}' depends on axioms: [{{axs}}] [module {{m}}]"
        | _ => pure ()

#kernel_certificate_audit
""")
print(f'{len(mods)} modules')
