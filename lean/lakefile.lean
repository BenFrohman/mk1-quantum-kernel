import Lake
open Lake DSL

package «MK1» where
  leanOptions := #[⟨`autoImplicit, false⟩, ⟨`relaxedAutoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "0c154d67103f74be3a0f2c509f72ccbf5be9f2a7"

@[default_target]
lean_lib «MK1» where
