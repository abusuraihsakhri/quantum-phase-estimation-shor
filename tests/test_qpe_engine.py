"""
Tests for Quantum Phase Estimation Engine.
Real QPE verification using mathematical properties.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import math
import cmath
import pytest
from qpe_engine.engine import (
    phase_gate, unitary_from_phase, unitary_power, matrix_multiply,
    zero_state, basis_state, state_probabilities, normalize_state, fidelity,
    apply_single_qubit_gate, apply_controlled_unitary,
    apply_qft, apply_inverse_qft, reverse_qubits,
    quantum_phase_estimation, extract_ancilla_probabilities,
    find_order_classical, continued_fraction_phase,
    shor_order_finding, state_info,
)


# ─── Gate Tests ──────────────────────────────────────────────────────────────

class TestGates:
    def test_phase_gate_unitary(self):
        for phi in [0.0, 0.25, 0.5, 0.75, 0.123]:
            P = phase_gate(phi)
            P_dag = [[P[j][i].conjugate() for j in range(2)] for i in range(2)]
            product = matrix_multiply(P_dag, P)
            for i in range(2):
                for j in range(2):
                    expected = 1.0 if i == j else 0.0
                    assert abs(product[i][j] - expected) < 1e-10

    def test_phase_gate_eigenvalue(self):
        phi = 0.25
        P = phase_gate(phi)
        # |1⟩ should be eigenvector with eigenvalue e^(2πiφ)
        eigenvalue = P[1][1]
        expected = cmath.exp(2j * cmath.pi * phi)
        assert abs(eigenvalue - expected) < 1e-10

    def test_unitary_power_identity(self):
        U = unitary_from_phase(0.3)
        U0 = unitary_power(U, 0)
        for i in range(2):
            for j in range(2):
                expected = 1.0 if i == j else 0.0
                assert abs(U0[i][j] - expected) < 1e-10

    def test_unitary_power_squared(self):
        U = unitary_from_phase(0.3)
        U2 = unitary_power(U, 2)
        UU = matrix_multiply(U, U)
        for i in range(2):
            for j in range(2):
                assert abs(U2[i][j] - UU[i][j]) < 1e-10

    def test_unitary_power_binary_exp(self):
        U = unitary_from_phase(0.123)
        U7 = unitary_power(U, 7)
        # U^7 = U * U^2 * U^4
        U2 = matrix_multiply(U, U)
        U4 = matrix_multiply(U2, U2)
        U7_check = matrix_multiply(matrix_multiply(U, U2), U4)
        for i in range(2):
            for j in range(2):
                assert abs(U7[i][j] - U7_check[i][j]) < 1e-10

    def test_matrix_multiply_identity(self):
        I = [[complex(1, 0), complex(0, 0)], [complex(0, 0), complex(1, 0)]]
        U = unitary_from_phase(0.5)
        result = matrix_multiply(I, U)
        for i in range(2):
            for j in range(2):
                assert abs(result[i][j] - U[i][j]) < 1e-10


# ─── State Vector Tests ─────────────────────────────────────────────────────

class TestStateVectors:
    def test_zero_state(self):
        state = zero_state(3)
        assert len(state) == 8
        assert abs(state[0] - 1.0) < 1e-12

    def test_basis_state(self):
        state = basis_state(4, 7)
        assert len(state) == 16
        assert abs(state[7] - 1.0) < 1e-12

    def test_probabilities_sum_to_one(self):
        state = [complex(1 / math.sqrt(3)), complex(1 / math.sqrt(3)), complex(1 / math.sqrt(3))]
        probs = state_probabilities(state)
        assert abs(sum(probs) - 1.0) < 1e-10

    def test_fidelity_same(self):
        state = basis_state(3, 5)
        assert abs(fidelity(state, state) - 1.0) < 1e-10

    def test_fidelity_orthogonal(self):
        s1 = basis_state(3, 0)
        s2 = basis_state(3, 1)
        assert abs(fidelity(s1, s2)) < 1e-10


# ─── QFT Tests ───────────────────────────────────────────────────────────────

class TestQFT:
    def test_qft_roundtrip(self):
        for s in range(8):
            state = basis_state(3, s)
            result = apply_inverse_qft(apply_qft(state, 3), 3)
            assert fidelity(state, result) > 1 - 1e-10

    def test_qft_of_zero_gives_uniform(self):
        state = basis_state(3, 0)
        result = apply_qft(state, 3)
        for p in state_probabilities(result):
            assert abs(p - 0.125) < 1e-10

    def test_reverse_qubits(self):
        state = basis_state(3, 1)  # |001⟩
        result = reverse_qubits(state, 3)
        assert abs(result[4] - 1.0) < 1e-10  # |100⟩


# ─── QPE Core Tests ─────────────────────────────────────────────────────────

class TestQPE:
    def test_qpe_exact_quarter(self):
        """Phase 0.25 = 1/4 should be exactly representable with ≥2 ancilla qubits."""
        result = quantum_phase_estimation(0.25, 4)
        assert result['success']
        assert result['phase_error'] < 1e-10

    def test_qpe_exact_half(self):
        """Phase 0.5 = 1/2."""
        result = quantum_phase_estimation(0.5, 3)
        assert result['success']

    def test_qpe_exact_eighth(self):
        """Phase 0.125 = 1/8 with 3 ancilla qubits."""
        result = quantum_phase_estimation(0.125, 3)
        assert result['success']

    def test_qpe_precision_increases_with_qubits(self):
        """More ancilla qubits → better precision."""
        phi = 0.3
        errors = []
        for n in range(2, 8):
            result = quantum_phase_estimation(phi, n)
            errors.append(result['phase_error'])
        # Error should generally decrease
        for i in range(len(errors) - 1):
            assert errors[i + 1] <= errors[i] + 1e-10

    def test_qpe_probabilities_sum_to_one(self):
        result = quantum_phase_estimation(0.25, 4)
        total = sum(result['ancilla_probabilities'])
        assert abs(total - 1.0) < 1e-10

    def test_qpe_measurement_binary_format(self):
        result = quantum_phase_estimation(0.25, 4)
        assert len(result['best_measurement_binary']) == 4
        assert all(c in '01' for c in result['best_measurement_binary'])

    def test_qpe_zero_phase(self):
        """Phase 0.0 should estimate to 0."""
        result = quantum_phase_estimation(0.0, 4)
        assert result['estimated_phase'] < 0.01 or abs(result['estimated_phase'] - 1.0) < 0.01

    def test_qpe_three_quarter_phase(self):
        """Phase 0.75 = 3/4."""
        result = quantum_phase_estimation(0.75, 4)
        assert result['success']

    def test_qpe_multiple_ancilla_counts(self):
        """Test QPE with different ancilla counts for phase 1/3."""
        phi = 1.0 / 3.0
        for n in [3, 4, 5, 6]:
            result = quantum_phase_estimation(phi, n)
            assert result['phase_error'] < 2 ** (-n) + 0.01

    def test_qpe_returns_all_fields(self):
        result = quantum_phase_estimation(0.25, 4)
        required = ['true_phase', 'estimated_phase', 'phase_error', 'n_ancilla',
                     'precision', 'ancilla_probabilities', 'best_measurement',
                     'best_measurement_binary', 'success']
        for key in required:
            assert key in result


# ─── Continued Fractions ─────────────────────────────────────────────────────

class TestContinuedFractions:
    def test_cf_simple_fraction(self):
        p, r = continued_fraction_phase(0.25, 100)
        assert p == 1 and r == 4

    def test_cf_half(self):
        p, r = continued_fraction_phase(0.5, 100)
        assert p == 1 and r == 2

    def test_cf_one_third(self):
        p, r = continued_fraction_phase(1.0 / 3.0, 100)
        assert p == 1 and r == 3

    def test_cf_two_fifths(self):
        p, r = continued_fraction_phase(2.0 / 5.0, 100)
        assert p == 2 and r == 5

    def test_cf_max_denom_constraint(self):
        # With max_denom=3, can't represent 2/5 exactly
        p, r = continued_fraction_phase(2.0 / 5.0, 3)
        assert r <= 3


# ─── Order Finding ───────────────────────────────────────────────────────────

class TestOrderFinding:
    def test_order_2_mod_15(self):
        """2^4 ≡ 1 (mod 15), so order of 2 mod 15 is 4."""
        r = find_order_classical(2, 15)
        assert r == 4

    def test_order_7_mod_15(self):
        """7^4 ≡ 1 (mod 15)."""
        r = find_order_classical(7, 15)
        assert r == 4

    def test_order_4_mod_15(self):
        """4^2 ≡ 1 (mod 15)."""
        r = find_order_classical(4, 15)
        assert r == 2

    def test_order_11_mod_15(self):
        """11^2 ≡ 1 (mod 15)."""
        r = find_order_classical(11, 15)
        assert r == 2

    def test_order_coprime_required(self):
        """gcd(3, 15) = 3, so no order exists."""
        r = find_order_classical(3, 15)
        assert r == -1

    def test_order_verification(self):
        """Verify a^r ≡ 1 (mod N) for found orders."""
        for a, N in [(2, 15), (7, 15), (4, 15), (11, 15), (2, 21)]:
            r = find_order_classical(a, N)
            if r > 0:
                assert pow(a, r, N) == 1


# ─── Shor's Algorithm ────────────────────────────────────────────────────────

class TestShorOrderFinding:
    def test_shor_trivial_factor(self):
        """gcd(6, 15) = 3, should find trivial factor."""
        result = shor_order_finding(6, 15)
        assert result['trivial_factor'] == 3

    def test_shor_order_2_mod_15(self):
        result = shor_order_finding(2, 15, n_ancilla=8)
        assert result['true_order'] == 4

    def test_shor_returns_all_fields(self):
        result = shor_order_finding(2, 15, 8)
        assert 'a' in result
        assert 'N' in result
        assert 'method' in result


# ─── CLI Tests ───────────────────────────────────────────────────────────────

class TestCLI:
    def test_estimate_command(self):
        from cli import main
        assert main(["estimate", "--phase", "0.25", "--ancilla", "4"]) == 0

    def test_estimate_show_probs(self):
        from cli import main
        assert main(["estimate", "--phase", "0.25", "--ancilla", "4", "--show-probs"]) == 0

    def test_sweep_command(self):
        from cli import main
        assert main(["sweep", "--ancilla", "4", "--samples", "8"]) == 0

    def test_order_command(self):
        from cli import main
        assert main(["order", "--a", "2", "--N", "15", "--ancilla", "8"]) == 0

    def test_factors_command(self):
        from cli import main
        assert main(["factors", "--N", "15", "--ancilla", "8"]) == 0

    def test_factors_even(self):
        from cli import main
        assert main(["factors", "--N", "14"]) == 0

    def test_precision_command(self):
        from cli import main
        assert main(["precision", "--max-ancilla", "8"]) == 0
