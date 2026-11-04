/-
Copyright (c) 2026 Benjamin Stanley Frohman. Released under Apache 2.0 license as described in
the file LICENSE.
Authors: Benjamin Stanley Frohman
-/
import Mathlib

/-!
# Fidelity kernels from unitary feature maps

MK-1 estimates the quantum kernel `K(x, x') = |⟨ψ(x') | ψ(x)⟩|²` where `ψ(x) = U(x) |0⟩` and
`U(x)` is a unitary feature-map circuit. This file proves, for an arbitrary family of unit
vectors in a complex inner product space (in particular for any unitary feature map):

* `fidelity_self`: `K(x, x) = 1`;
* `fidelity_symm`: `K(x, y) = K(y, x)`;
* `fidelity_nonneg`, `fidelity_le_one`: `0 ≤ K ≤ 1`;
* `computeUncompute_eq_fidelity`: the compute-uncompute probability
  `|⟨0| U(y)⁻¹ U(x) |0⟩|²` equals `K(x, y)`;
* `fidelity_gram_posSemidef`: for finitely many points in `ℂⁿ`, the Gram matrix of `K`
  is positive semidefinite (so `K` is a valid kernel for an SVM).

Nothing here is specific to the ZZ feature map; these are standard facts.
-/

open scoped InnerProductSpace ComplexConjugate ComplexOrder

namespace MK1

variable {X E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℂ E]

/-- The fidelity kernel of a family of states `ψ`. -/
noncomputable def fidelity (ψ : X → E) (x y : X) : ℝ := ‖⟪ψ y, ψ x⟫_ℂ‖ ^ 2

theorem fidelity_symm (ψ : X → E) (x y : X) : fidelity ψ x y = fidelity ψ y x := by
  simp only [fidelity, norm_inner_symm]

theorem fidelity_nonneg (ψ : X → E) (x y : X) : 0 ≤ fidelity ψ x y := by
  unfold fidelity; positivity

theorem fidelity_self (ψ : X → E) (h : ∀ x, ‖ψ x‖ = 1) (x : X) : fidelity ψ x x = 1 := by
  simp [fidelity, inner_self_eq_norm_sq_to_K, h]

theorem fidelity_le_one (ψ : X → E) (h : ∀ x, ‖ψ x‖ = 1) (x y : X) : fidelity ψ x y ≤ 1 := by
  unfold fidelity
  have := norm_inner_le_norm (𝕜 := ℂ) (ψ y) (ψ x)
  rw [h, h, one_mul] at this
  exact pow_le_one₀ (norm_nonneg _) this

/-- States prepared by a unitary feature map `U` from a unit reference vector `v`. -/
def featureState (U : X → E ≃ₗᵢ[ℂ] E) (v : E) (x : X) : E := U x v

theorem norm_featureState (U : X → E ≃ₗᵢ[ℂ] E) {v : E} (hv : ‖v‖ = 1) (x : X) :
    ‖featureState U v x‖ = 1 := by
  simp [featureState, hv]

/-- Compute-uncompute: the probability of returning to `v` after `U(x)` then `U(y)⁻¹`
is the fidelity kernel. -/
theorem computeUncompute_eq_fidelity (U : X → E ≃ₗᵢ[ℂ] E) (v : E) (x y : X) :
    ‖⟪v, (U y).symm (U x v)⟫_ℂ‖ ^ 2 = fidelity (featureState U v) x y := by
  unfold fidelity featureState
  congr 2
  rw [← (U y).inner_map_map v, LinearIsometryEquiv.apply_symm_apply]

section Gram

variable {n : ℕ}

/-- `a ↦ a ⊗ conj a`, as a vector indexed by pairs. -/
noncomputable def lift (a : EuclideanSpace ℂ (Fin n)) : EuclideanSpace ℂ (Fin n × Fin n) :=
  WithLp.toLp 2 fun p => a p.1 * conj (a p.2)

theorem inner_lift (a b : EuclideanSpace ℂ (Fin n)) :
    ⟪lift a, lift b⟫_ℂ = ((‖⟪a, b⟫_ℂ‖ ^ 2 : ℝ) : ℂ) := by
  rw [Complex.ofReal_pow, ← Complex.mul_conj', inner_conj_symm]
  simp only [lift, PiLp.inner_apply, RCLike.inner_apply, Fintype.sum_prod_type,
    map_mul, Complex.conj_conj, Finset.sum_mul_sum]
  refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => ?_
  ring

/-- The Gram matrix of the fidelity kernel is positive semidefinite. -/
theorem fidelity_gram_posSemidef {ι : Type*} [Finite ι] (ψ : X → EuclideanSpace ℂ (Fin n))
    (pts : ι → X) :
    (Matrix.of fun i j => ((fidelity ψ (pts j) (pts i) : ℝ) : ℂ)).PosSemidef := by
  have h := Matrix.posSemidef_gram ℂ (fun i => lift (ψ (pts i)))
  convert h using 1
  ext i j
  simp [fidelity, inner_lift]

end Gram

section Circuit

/-- CNOT on two qubits, control = first tensor factor (basis order |00⟩,|01⟩,|10⟩,|11⟩). -/
def cnot : Matrix (Fin 4) (Fin 4) ℂ := !![1, 0, 0, 0; 0, 1, 0, 0; 0, 0, 0, 1; 0, 0, 1, 0]

/-- A diagonal phase on the control qubit, `diag(a, b) ⊗ I`. -/
def onControl (a b : ℂ) : Matrix (Fin 4) (Fin 4) ℂ := !![a, 0, 0, 0; 0, a, 0, 0; 0, 0, b, 0; 0, 0, 0, b]

/-- A diagonal phase on the target qubit, `I ⊗ diag(a, b)`. -/
def onTarget (a b : ℂ) : Matrix (Fin 4) (Fin 4) ℂ := !![a, 0, 0, 0; 0, b, 0, 0; 0, 0, a, 0; 0, 0, 0, b]

/-- A phase gate on the *control* qubit passes straight through the CNOT sandwich: no
entangling `ZZ` phase is produced. This is the situation in the original MK-1 script. -/
theorem cnot_onControl_cnot (a b : ℂ) : cnot * onControl a b * cnot = onControl a b := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [cnot, onControl, Matrix.mul_apply, Fin.sum_univ_four]

/-- On the *target* qubit the sandwich gives the `ZZ` phase `diag(a, b, b, a)` (a function of the parity of the two bits). -/
theorem cnot_onTarget_cnot (a b : ℂ) :
    cnot * onTarget a b * cnot = !![a, 0, 0, 0; 0, b, 0, 0; 0, 0, b, 0; 0, 0, 0, a] := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [cnot, onTarget, Matrix.mul_apply, Fin.sum_univ_four]

end Circuit

end MK1
