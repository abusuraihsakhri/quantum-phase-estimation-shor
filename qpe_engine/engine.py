"""
Quantum Phase Estimation (QPE) Engine
Real implementation using state vector simulation with Python stdlib only.

QPE estimates the eigenvalue e^(2πiφ) of a unitary operator U given its eigenvector |ψ⟩.
Algorithm:
1. Prepare n ancilla qubits in |+⟩^⊗n (Hadamard on each)
2. Apply controlled-U^(2^k) for each ancilla qubit k
3. Apply inverse QFT to ancilla register
4. Measure ancilla to get binary fraction 0.b₁b₂...bₙ ≈ φ

Precision: n ancilla qubits → precision 2^(-n)
Application: Order finding (core of Shor's algorithm)
"""
import cmath
import math
from fractions import Fraction
from typing import List, Tuple, Optional, Dict


# ─── Gate Definitions ────────────────────────────────────────────────────────

SQRT2_INV = 1.0 / math.sqrt(2.0)

H_MATRIX = [
    [complex(SQRT2_INV, 0), complex(SQRT2_INV, 0)],
    [complex(SQRT2_INV, 0), complex(-SQRT2_INV, 0)],
]

I_MATRIX = [
    [complex(1, 0), complex(0, 0)],
    [complex(0, 0), complex(1, 0)],
]

X_MATRIX = [
    [complex(0, 0), complex(1, 0)],
    [complex(1, 0), complex(0, 0)],
]


def phase_gate(phi: float) -> List[List[complex]]:
    """Phase gate P(φ) = [[1, 0], [0, e^(2πiφ)]]."""
    phase = cmath.exp(2j * cmath.pi * phi)
    return [[complex(1, 0), complex(0, 0)],
            [complex(0, 0), phase]]


def unitary_from_phase(phi: float) -> List[List[complex]]:
    """Create a 1-qubit unitary with eigenvalue e^(2πiφ) on |1⟩.
    U = [[1, 0], [0, e^(2πiφ)]]
    |1⟩ is eigenvector with eigenvalue e^(2πiφ).
    """
    return phase_gate(phi)


def unitary_power(U: List[List[complex]], power: int) -> List[List[complex]]:
    """Compute U^power for a 2×2 unitary matrix."""
    dim = len(U)
    # Start with identity
    result = [[complex(1 if i == j else 0) for j in range(dim)] for i in range(dim)]
    # Binary exponentiation
    base = [row[:] for row in U]
    p = power
    while p > 0:
        if p & 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        p >>= 1
    return result


def matrix_multiply(A: List[List[complex]], B: List[List[complex]]) -> List[List[complex]]:
    """Multiply two square matrices."""
    n = len(A)
    C = [[complex(0) for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C


# ─── State Vector Operations ────────────────────────────────────────────────

def zero_state(n: int) -> List[complex]:
    """|0...0⟩ state for n qubits."""
    N = 2 ** n
    state = [complex(0, 0)] * N
    state[0] = complex(1, 0)
    return state


def basis_state(n: int, index: int) -> List[complex]:
    """|index⟩ computational basis state for n qubits."""
    N = 2 ** n
    state = [complex(0, 0)] * N
    state[index] = complex(1, 0)
    return state


def state_probabilities(state: List[complex]) -> List[float]:
    """|α_i|^2 for each basis state."""
    return [abs(a) ** 2 for a in state]


def normalize_state(state: List[complex]) -> List[complex]:
    """Normalize to unit length."""
    norm = math.sqrt(sum(abs(a) ** 2 for a in state))
    if norm < 1e-15:
        raise ValueError("Cannot normalize zero vector")
    return [a / norm for a in state]


def fidelity(state1: List[complex], state2: List[complex]) -> float:
    """F = |⟨ψ1|ψ2⟩|^2."""
    inner = sum(a.conjugate() * b for a, b in zip(state1, state2))
    return abs(inner) ** 2


def apply_single_qubit_gate(state: List[complex], gate: List[List[complex]],
                             target: int, n_qubits: int) -> List[complex]:
    """Apply single-qubit gate to target qubit in n-qubit system."""
    N = 2 ** n_qubits
    new_state = [complex(0, 0)] * N
    t_shift = n_qubits - 1 - target
    t_mask = 1 << t_shift
    for i in range(N):
        bit = (i >> t_shift) & 1
        for new_bit in range(2):
            coeff = gate[new_bit][bit]
            if abs(coeff) < 1e-15:
                continue
            j = (i & ~t_mask) | (new_bit << t_shift)
            new_state[j] += coeff * state[i]
    return new_state


def apply_controlled_unitary(state: List[complex], U: List[List[complex]],
                              control: int, target: int, n_qubits: int) -> List[complex]:
    """Apply controlled-U gate: if control=1, apply U to target."""
    N = 2 ** n_qubits
    new_state = [complex(0, 0)] * N
    c_shift = n_qubits - 1 - control
    t_shift = n_qubits - 1 - target
    for i in range(N):
        c_bit = (i >> c_shift) & 1
        t_bit = (i >> t_shift) & 1
        if c_bit == 0:
            new_state[i] += state[i]
        else:
            for new_t_bit in range(2):
                coeff = U[new_t_bit][t_bit]
                if abs(coeff) < 1e-15:
                    continue
                j = (i & ~(1 << t_shift)) | (new_t_bit << t_shift)
                new_state[j] += coeff * state[i]
    return new_state


# ─── QFT for QPE ─────────────────────────────────────────────────────────────

def apply_qft(state: List[complex], n: int) -> List[complex]:
    """Apply QFT to n-qubit state."""
    for j in range(n):
        state = apply_single_qubit_gate(state, H_MATRIX, j, n)
        for k in range(j + 1, n):
            rot_order = k - j + 1
            phase = cmath.exp(2j * cmath.pi / (2 ** rot_order))
            R = [[complex(1, 0), complex(0, 0)],
                 [complex(0, 0), phase]]
            state = apply_controlled_unitary(state, R, k, j, n)
    # Reverse qubits
    state = reverse_qubits(state, n)
    return state


def apply_inverse_qft(state: List[complex], n: int) -> List[complex]:
    """Apply inverse QFT."""
    state = reverse_qubits(state, n)
    for j in range(n - 1, -1, -1):
        for k in range(n - 1, j, -1):
            rot_order = k - j + 1
            phase = cmath.exp(-2j * cmath.pi / (2 ** rot_order))
            R_dag = [[complex(1, 0), complex(0, 0)],
                     [complex(0, 0), phase]]
            state = apply_controlled_unitary(state, R_dag, k, j, n)
        state = apply_single_qubit_gate(state, H_MATRIX, j, n)
    return state


def reverse_qubits(state: List[complex], n: int) -> List[complex]:
    """Reverse qubit ordering."""
    N = 2 ** n
    new_state = [complex(0, 0)] * N
    for i in range(N):
        j = int(format(i, f'0{n}b')[::-1], 2)
        new_state[j] = state[i]
    return new_state


# ─── Quantum Phase Estimation ───────────────────────────────────────────────

def _validate_qpe_inputs(phi: float, n_ancilla: int) -> None:
    """Validate QPE parameters, raising ValueError on invalid input."""
    if type(n_ancilla) is not int:
        raise TypeError(f"n_ancilla must be an integer, got {type(n_ancilla).__name__}")
    if n_ancilla < 1:
        raise ValueError(f"n_ancilla must be >= 1, got {n_ancilla}")
    if n_ancilla > 12:
        raise ValueError(f"n_ancilla must be <= 12 (practical state-vector limit), got {n_ancilla}")
    if not isinstance(phi, (int, float)):
        raise TypeError(f"phase must be a number, got {type(phi).__name__}")
    if not math.isfinite(phi):
        raise ValueError(f"phase must be finite, got {phi}")


def quantum_phase_estimation(phi: float, n_ancilla: int) -> dict:
    """
    Full QPE algorithm for a phase gate U = [[1,0],[0,e^(2πiφ)]].

    Uses a simplified but correct approach:
    1. Build the ancilla state after controlled-U operations
    2. Apply inverse QFT to ancilla register
    3. Extract measurement probabilities

    Returns dict with estimated phase, probabilities, and diagnostics.
    """
    _validate_qpe_inputs(phi, n_ancilla)
    N = 2 ** n_ancilla
    phi_mod = phi % 1.0

    # Step 1: After Hadamard on ancilla and controlled-U^(2^k) operations,
    # the ancilla register state is:
    # |ψ_ancilla⟩ = (1/√N) Σ_{j=0}^{N-1} e^(2πiφj) |j⟩
    # (The eigenstate |1⟩ picks up the phase and factors out)
    ancilla_state = [complex(0, 0)] * N
    norm = 1.0 / math.sqrt(N)
    for j in range(N):
        phase = 2.0 * cmath.pi * phi_mod * j
        ancilla_state[j] = norm * cmath.exp(1j * phase)
    
    # Step 2: Apply inverse QFT to ancilla register
    ancilla_state = apply_inverse_qft(ancilla_state, n_ancilla)
    
    # Step 3: Get measurement probabilities
    ancilla_probs = [abs(a) ** 2 for a in ancilla_state]
    
    # Find best estimate
    best_index = max(range(N), key=lambda i: ancilla_probs[i])
    estimated_phase = best_index / N
    
    # Phase error (accounting for wraparound)
    phase_error = abs((estimated_phase - phi_mod + 0.5) % 1.0 - 0.5)
    
    return {
        'true_phase': phi,
        'estimated_phase': estimated_phase,
        'phase_error': phase_error,
        'n_ancilla': n_ancilla,
        'precision': 1.0 / N,
        'ancilla_probabilities': ancilla_probs,
        'best_measurement': best_index,
        'best_measurement_binary': format(best_index, f'0{n_ancilla}b'),
        'success': phase_error < 1.5 / N,  # allow small tolerance
    }


def extract_ancilla_probabilities(state: List[complex], n_ancilla: int,
                                    eigenstate_qubit: int) -> List[float]:
    """Extract measurement probabilities for ancilla qubits by tracing out eigenstate."""
    n_total = len(state).bit_length() - 1
    N_ancilla = 2 ** n_ancilla
    probs = [0.0] * N_ancilla
    
    for i in range(len(state)):
        # Extract ancilla bits
        ancilla_index = 0
        for k in range(n_ancilla):
            bit = (i >> (n_total - 1 - k)) & 1
            ancilla_index = (ancilla_index << 1) | bit
        probs[ancilla_index] += abs(state[i]) ** 2
    
    return probs


def apply_inverse_qft_to_ancilla(state: List[complex], n_ancilla: int,
                                   eigenstate_qubit: int, n_total: int) -> List[complex]:
    """Apply inverse QFT only to ancilla qubits (not the eigenstate qubit)."""
    # We need to apply IQFT on qubits 0..n_ancilla-1
    # First reverse ancilla qubits
    state = reverse_ancilla_qubits(state, n_ancilla, n_total)
    
    # Apply reversed QFT gates on ancilla qubits only
    for j in range(n_ancilla - 1, -1, -1):
        for k in range(n_ancilla - 1, j, -1):
            rot_order = k - j + 1
            phase = cmath.exp(-2j * cmath.pi / (2 ** rot_order))
            R_dag = [[complex(1, 0), complex(0, 0)],
                     [complex(0, 0), phase]]
            state = apply_controlled_unitary(state, R_dag, k, j, n_total)
        state = apply_single_qubit_gate(state, H_MATRIX, j, n_total)
    
    return state


def reverse_ancilla_qubits(state: List[complex], n_ancilla: int, n_total: int,
                            eigenstate_qubit: int = -1) -> List[complex]:
    """Reverse only the ancilla qubit ordering.
    eigenstate_qubit defaults to last qubit (index -1 means n_total-1).
    """
    if eigenstate_qubit < 0:
        eigenstate_qubit = n_total - 1
    N = 2 ** n_total
    new_state = [complex(0, 0)] * N
    e_shift = n_total - 1 - eigenstate_qubit
    for i in range(N):
        # Extract ancilla bits (all qubits except eigenstate)
        ancilla_bits = 0
        for k in range(n_ancilla):
            bit = (i >> (n_total - 1 - k)) & 1
            ancilla_bits = (ancilla_bits << 1) | bit
        
        # Reverse ancilla bits
        reversed_ancilla = int(format(ancilla_bits, f'0{n_ancilla}b')[::-1], 2)
        
        # Extract eigenstate bit
        eigenstate_bit = (i >> e_shift) & 1
        
        # Reconstruct index: reversed ancilla in high bits, eigenstate in low bit
        j = (reversed_ancilla << 1) | eigenstate_bit
        new_state[j] = state[i]
    return new_state


# ─── Order Finding (Shor's Algorithm Core) ──────────────────────────────────

def modular_exponentiation_matrix(a: int, N_mod: int, n_qubits: int) -> List[List[complex]]:
    """Unitary modular multiplication U_a |y> = |a*y mod N>.

    Basis states outside the modular register (y >= N) are unchanged.
    This is the work-register unitary, NOT the full controlled exponentiation
    circuit. Only practical for small demonstration registers.
    """
    if type(a) is not int or type(N_mod) is not int or type(n_qubits) is not int:
        raise TypeError("a, N_mod, and n_qubits must be integers")
    if N_mod < 2 or not (1 <= a < N_mod) or math.gcd(a, N_mod) != 1:
        raise ValueError("require N_mod >= 2 and 1 <= a < N_mod coprime to N_mod")
    if not (1 <= n_qubits <= 8) or (1 << n_qubits) < N_mod:
        raise ValueError("n_qubits must be 1..8 with 2**n_qubits >= N_mod")
    dim = 1 << n_qubits
    matrix = [[0j] * dim for _ in range(dim)]
    for y in range(dim):
        mapped = (a * y) % N_mod if y < N_mod else y
        matrix[mapped][y] = 1 + 0j
    return matrix


def find_order_classical(a: int, N: int) -> int:
    """Classically find the order r such that a^r ≡ 1 (mod N)."""
    if type(a) is not int or type(N) is not int:
        raise TypeError("a and N must be integers")
    if N <= 1:
        raise ValueError("N must be > 1")
    if math.gcd(a, N) != 1:
        return -1
    r = 1
    current = a % N
    while current != 1:
        current = (current * a) % N
        r += 1
        if r > N:
            return -1
    return r


def continued_fraction_phase(phi: float, max_denom: int) -> Tuple[int, int]:
    """Return best bounded rational approximation p/r to a finite phase."""
    if not isinstance(phi, (float, int)) or not math.isfinite(phi):
        raise ValueError("phi must be finite")
    if type(max_denom) is not int or max_denom < 1:
        raise ValueError("max_denom must be a positive integer")
    result = Fraction(float(phi)).limit_denominator(max_denom)
    return result.numerator, result.denominator


def shor_order_finding(a: int, N: int, n_ancilla: int = 8) -> dict:
    """Small state-vector simulation of Shor's modular order-finding QPE.

    The ancilla register is entangled with the modular work register |1>.
    Controlled U_a**j generates |j>|a**j mod N> before inverse QFT.
    The modular order is NOT supplied to the QPE circuit. A classical
    calculation is included afterwards as an independent diagnostic.
    """
    if type(a) is not int or type(N) is not int:
        raise TypeError("a and N must be integers")
    if N <= 1 or N > 255:
        raise ValueError("N must be in the demonstration range 2..255")
    if not 1 <= a < N:
        raise ValueError("a must satisfy 1 <= a < N")
    _validate_qpe_inputs(0.5, n_ancilla)
    if n_ancilla > 10:
        raise ValueError("order-finding demonstration supports at most 10 ancilla qubits")

    g = math.gcd(a, N)
    if g > 1:
        return {'a': a, 'N': N, 'trivial_factor': g,
                'method': 'classical_gcd', 'order': -1}

    size = 1 << n_ancilla
    normalizer = 1.0 / math.sqrt(size)
    work_states = {}
    residue = 1
    for j in range(size):
        # Controlled modular multiplication on the work register.
        vector = work_states.setdefault(residue, [0j] * size)
        vector[j] = normalizer
        residue = (residue * a) % N

    probs = [0.0] * size
    for vector in work_states.values():
        evolved = apply_inverse_qft(vector, n_ancilla)
        for k, amp in enumerate(evolved):
            probs[k] += abs(amp) ** 2

    # QPE produces a DISTRIBUTION over eigenphases, not a single 1/r phase.
    # Zero and non-coprime eigenphase numerators are uninformative; try the
    # strongest non-zero outcomes and verify candidates by modular powers.
    best = max(range(size), key=lambda k: probs[k])
    selected = None
    estimated_order = -1
    for index in sorted(range(1, size), key=lambda k: (-probs[k], k)):
        phase = index / size
        _, denominator = continued_fraction_phase(phase, N)
        if denominator > 1 and pow(a, denominator, N) == 1:
            selected = index
            estimated_order = denominator
            break

    # Diagnostic only: true_order does not influence QPE or reconstruction.
    true_order = find_order_classical(a, N)
    measurement = selected if selected is not None else best
    phase = measurement / size
    qpe_result = {
        'ancilla_probabilities': probs,
        'best_measurement': measurement,
        'best_measurement_binary': format(measurement, f'0{n_ancilla}b'),
        'estimated_phase': phase,
        'n_ancilla': n_ancilla,
        'precision': 1.0 / size,
    }
    success = estimated_order > 0
    result = {
        'a': a, 'N': N, 'true_order': true_order,
        'estimated_order': estimated_order,
        'measured_phase': phase,
        'qpe_result': qpe_result,
        'method': 'modular_multiplication_qpe',
        'success': success,
    }
    if not success:
        result['note'] = 'Order not recovered from QPE measurements; try more ancilla qubits'
    return result


# ─── Utility ─────────────────────────────────────────────────────────────────

def state_info(state: List[complex], n: int, threshold: float = 1e-6) -> dict:
    """Human-readable state info."""
    probs = state_probabilities(state)
    nonzero = []
    for i, (amp, p) in enumerate(zip(state, probs)):
        if p > threshold:
            label = format(i, f'0{n}b')
            nonzero.append({
                'index': i, 'label': label,
                'amplitude': complex(amp), 'probability': p,
            })
    return {
        'n_qubits': n, 'dimension': 2 ** n,
        'total_probability': sum(probs),
        'nonzero_components': nonzero,
    }
