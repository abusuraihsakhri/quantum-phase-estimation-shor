# Quantum Phase Estimation (QPE) & Shor's Algorithm

Real implementation of Quantum Phase Estimation using state vector simulation in pure Python (stdlib only).

## What This Actually Does

- **QPE algorithm** — estimates eigenvalue e^(2πiφ) of a unitary U given eigenvector |ψ⟩
- **Controlled-U^(2^k) operations** — binary exponentiation of unitary matrices
- **Inverse QFT on ancilla register** — extracts phase from interference pattern
- **Phase extraction** — continued fractions to recover rational phases
- **Precision analysis** — n ancilla qubits → precision 2^(-n)
- **Shor's order finding** — finds r such that a^r ≡ 1 (mod N)
- **Simplified factoring** — uses order finding to factor composites

### Algorithm Steps

1. Prepare n ancilla qubits in |+⟩^⊗n (Hadamard on each)
2. Apply controlled-U^(2^k) for each ancilla qubit k
3. Apply inverse QFT to ancilla register
4. Measure ancilla → binary fraction 0.b₁b₂...bₙ ≈ φ

## Usage

```bash
# Estimate phase φ = 0.25 with 4 ancilla qubits
python cli.py estimate --phase 0.25 --ancilla 4 --show-probs

# Sweep phases to test accuracy
python cli.py sweep --ancilla 4 --samples 16

# Find order: 2^r ≡ 1 (mod 15)
python cli.py order --a 2 --N 15 --ancilla 8

# Factor a number
python cli.py factors --N 15 --ancilla 8

# Show precision analysis
python cli.py precision --max-ancilla 10
```

## API

```python
from qpe_engine.engine import quantum_phase_estimation, shor_order_finding

# QPE for phase 0.25
result = quantum_phase_estimation(0.25, n_ancilla=4)
print(f"Estimated: {result['estimated_phase']}, Error: {result['phase_error']}")

# Shor's order finding
result = shor_order_finding(a=2, N=15, n_ancilla=8)
print(f"Order: {result['estimated_order']}")
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Limitations

- State vector simulation: exponential memory, practical for n ≤ ~15
- Modular exponentiation is simplified (not a full quantum circuit)
- No noise model
- Factoring uses classical order verification
