# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Benjamin Stanley Frohman
import numpy as np
import pytest

from mk1 import feature_map, feature_state, gram, kernel, kernel_closed_form
from mk1.kernel import CNOT, I2, VARIANTS, kron, rz

rng = np.random.default_rng(0)
PTS = rng.normal(scale=1.5, size=(12, 2))


@pytest.mark.parametrize("v", VARIANTS)
def test_unitary(v):
    for x in PTS:
        u = feature_map(x, v)
        assert np.allclose(u.conj().T @ u, np.eye(4))


@pytest.mark.parametrize("v", VARIANTS)
def test_self_symmetry_bounds(v):
    for x in PTS:
        assert kernel(x, x, v) == pytest.approx(1.0)
        for y in PTS:
            k = kernel(x, y, v)
            assert -1e-12 <= k <= 1 + 1e-12
            assert k == pytest.approx(kernel(y, x, v))


@pytest.mark.parametrize("v", VARIANTS)
def test_compute_uncompute_equals_state_overlap(v):
    for x in PTS:
        for y in PTS:
            ov = abs(np.vdot(feature_state(y, v), feature_state(x, v))) ** 2
            assert kernel(x, y, v) == pytest.approx(ov)


@pytest.mark.parametrize("v", VARIANTS)
def test_closed_form(v):
    for x in PTS:
        for y in PTS:
            assert kernel(x, y, v) == pytest.approx(kernel_closed_form(x, y, v), abs=1e-12)


@pytest.mark.parametrize("v", VARIANTS)
def test_gram_psd(v):
    k = gram(PTS, v)
    assert np.allclose(k, k.T)
    assert np.linalg.eigvalsh(k).min() > -1e-10


def test_legacy_middle_gate_commutes_with_cnot():
    for t in rng.normal(size=5):
        g = kron(rz(t), I2)
        assert np.allclose(CNOT @ g @ CNOT, g)


def test_zz_variant_is_entangling_and_differs_from_legacy():
    x, y = np.array([0.7, -1.1]), np.array([0.2, 0.4])
    assert kernel(x, y, "zz") != pytest.approx(kernel(x, y, "legacy"))
    # the "zz" phase CNOT (I⊗RZ) CNOT equals exp(-i θ/2 Z⊗Z)
    t = 0.9
    zz = np.diag(np.exp(-1j * t / 2 * np.array([1, -1, -1, 1])))
    assert np.allclose(CNOT @ kron(I2, rz(t)) @ CNOT, zz)


def test_render(tmp_path):
    from mk1.tower import render

    k = render(tmp_path)
    assert (tmp_path / "mk1-tower.gif").exists()
    assert np.allclose(np.load(tmp_path / "gram.npy"), k)
