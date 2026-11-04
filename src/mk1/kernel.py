# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Benjamin Stanley Frohman
"""Exact statevector simulation of the MK-1 feature map and its fidelity kernel.

Qubit 0 is the first tensor factor and is the CNOT control.

Two variants:

* ``"zz"`` (default): H⊗H, RZ(2x0)⊗RZ(2x1), then CNOT · (I⊗RZ(2·x0·x1)) · CNOT, i.e. the
  entangling phase exp(-i x0 x1 Z⊗Z). This is one layer of a ZZ feature map in the style of
  Havlíček et al. (2019), with the simplified pair coefficient x0·x1.
* ``"legacy"``: the original MK-1 script, which put the middle RZ on the *control* qubit.
  That gate commutes with CNOT, so the CNOTs cancel and no entangling phase is produced; the
  kernel is then the product cos²(Δ0 + Δ01) cos²(Δ1) with Δ = x − x'.
"""

from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
ZERO = np.array([1, 0, 0, 0], dtype=complex)
VARIANTS = ("zz", "legacy")


def rz(theta: float) -> np.ndarray:
    return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=complex)


def kron(*ops: np.ndarray) -> np.ndarray:
    out = np.array([[1]], dtype=complex)
    for op in ops:
        out = np.kron(out, op)
    return out


def feature_map(x, variant: str = "zz") -> np.ndarray:
    """4x4 unitary U(x) for a length-2 input ``x`` (radians)."""
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    x0, x1 = float(x[0]), float(x[1])
    u = kron(H, H)
    u = kron(rz(2 * x0), rz(2 * x1)) @ u
    mid = kron(I2, rz(2 * x0 * x1)) if variant == "zz" else kron(rz(2 * x0 * x1), I2)
    return CNOT @ mid @ CNOT @ u


def feature_state(x, variant: str = "zz") -> np.ndarray:
    return feature_map(x, variant) @ ZERO


def kernel(x, xp, variant: str = "zz") -> float:
    """Compute-uncompute probability P(00) after U(x) then U(x')†."""
    psi = feature_map(xp, variant).conj().T @ feature_map(x, variant) @ ZERO
    return float(np.abs(psi[0]) ** 2)


def kernel_closed_form(x, xp, variant: str = "zz") -> float:
    """Independent formula, no matrices.

    The circuit maps |00> to (1/2) Σ_s exp(-i φ(s, x)) |s>, s ∈ {±1}², with
    φ = x0 s0 + x1 s1 + x0x1 s0s1 ("zz") or φ = (x0 + x0x1) s0 + x1 s1 ("legacy").
    """
    x0, x1, y0, y1 = float(x[0]), float(x[1]), float(xp[0]), float(xp[1])
    if variant == "legacy":
        return float(np.cos(x0 + x0 * x1 - y0 - y0 * y1) ** 2 * np.cos(x1 - y1) ** 2)
    d0, d1, d01 = x0 - y0, x1 - y1, x0 * x1 - y0 * y1
    amp = sum(np.exp(-1j * (d0 * s0 + d1 * s1 + d01 * s0 * s1)) for s0 in (1, -1) for s1 in (1, -1)) / 4
    return float(abs(amp) ** 2)


def gram(points, variant: str = "zz") -> np.ndarray:
    m = len(points)
    k = np.eye(m)
    for i in range(m):
        for j in range(i + 1, m):
            k[i, j] = k[j, i] = kernel(points[i], points[j], variant)
    return k
