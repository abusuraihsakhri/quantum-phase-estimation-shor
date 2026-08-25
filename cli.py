"""
CLI for Quantum Phase Estimation (QPE) Engine.
Provides commands for QPE simulation, order finding, and diagnostics.
"""
import argparse
import sys

from qpe_engine.engine import (
    quantum_phase_estimation, shor_order_finding,
    find_order_classical, continued_fraction_phase,
    unitary_from_phase, unitary_power,
    state_info,
)


def cmd_estimate(args):
    """Run QPE to estimate a phase."""
    result = quantum_phase_estimation(args.phase, args.ancilla)
    print(f"Quantum Phase Estimation:")
    print(f"  True phase:      φ = {result['true_phase']:.10f}")
    print(f"  Estimated phase: φ ≈ {result['estimated_phase']:.10f}")
    print(f"  Phase error:       {result['phase_error']:.2e}")
    print(f"  Ancilla qubits:    {result['n_ancilla']}")
    print(f"  Precision:         2^(-{result['n_ancilla']}) = {result['precision']:.2e}")
    print(f"  Best measurement:  |{result['best_measurement_binary']}⟩ (index {result['best_measurement']})")
    print(f"  Success:           {result['success']}")
    if args.show_probs:
        print(f"\n  Ancilla measurement probabilities:")
        probs = result['ancilla_probabilities']
        for i, p in enumerate(probs):
            if p > 0.001:
                bar = '█' * int(p * 40)
                n_a = result['n_ancilla']
                print(f"    |{format(i, f'0{n_a}b')}⟩: {bar:40s} {p:.6f}")
    return 0


def cmd_sweep(args):
    """Sweep phases and measure QPE accuracy."""
    n = args.ancilla
    n_phases = args.samples
    print(f"QPE sweep: {n_phases} phases, {n} ancilla qubits (precision {2**(-n):.6f})")
    print(f"{'Phase':>12s} {'Estimated':>12s} {'Error':>12s} {'Success':>8s}")
    print("-" * 50)
    successes = 0
    for i in range(n_phases):
        phi = i / n_phases
        result = quantum_phase_estimation(phi, n)
        status = "✓" if result['success'] else "✗"
        if result['success']:
            successes += 1
        print(f"{phi:12.6f} {result['estimated_phase']:12.6f} {result['phase_error']:12.2e} {status:>8s}")
    print(f"\nSuccess rate: {successes}/{n_phases} ({100*successes/n_phases:.1f}%)")
    return 0


def cmd_order(args):
    """Find order using Shor's algorithm (simplified)."""
    result = shor_order_finding(args.a, args.N, args.ancilla)
    print(f"Shor's Order Finding:")
    print(f"  a = {result['a']}, N = {result['N']}")
    if result.get('trivial_factor'):
        print(f"  Trivial factor found: {result['trivial_factor']}")
        print(f"  gcd({result['a']}, {result['N']}) = {result['trivial_factor']}")
        return 0
    print(f"  True order:      r = {result.get('true_order', 'unknown')}")
    print(f"  Estimated order: r ≈ {result.get('estimated_order', 'N/A')}")
    print(f"  Measured phase:  φ = {result.get('measured_phase', 'N/A')}")
    print(f"  Method:          {result['method']}")
    print(f"  Success:         {result['success']}")
    if result.get('note'):
        print(f"  Note: {result['note']}")
    return 0


def cmd_factors(args):
    """Factor a number using Shor's algorithm."""
    N = args.N
    print(f"Factoring N = {N}")
    
    # Check if N is even
    if N % 2 == 0:
        print(f"  Factor: {2} × {N // 2}")
        return 0
    
    # Try small values of a
    for a in range(2, min(N, 20)):
        g = __import__('math').gcd(a, N)
        if g > 1:
            print(f"  Found factor via gcd({a}, {N}) = {g}")
            print(f"  {N} = {g} × {N // g}")
            return 0
        
        result = shor_order_finding(a, N, args.ancilla)
        r = result.get('estimated_order', -1)
        if r > 0 and r % 2 == 0:
            x = pow(a, r // 2, N)
            if x != N - 1:
                f1 = __import__('math').gcd(x + 1, N)
                f2 = __import__('math').gcd(x - 1, N)
                if 1 < f1 < N:
                    print(f"  Found via Shor: a={a}, r={r}")
                    print(f"  {N} = {f1} × {N // f1}")
                    return 0
                if 1 < f2 < N:
                    print(f"  Found via Shor: a={a}, r={r}")
                    print(f"  {N} = {f2} × {N // f2}")
                    return 0
    
    print(f"  Could not factor {N} with {args.ancilla} ancilla qubits")
    return 1


def cmd_precision(args):
    """Show precision analysis for different ancilla counts."""
    print(f"QPE Precision Analysis:")
    print(f"{'Ancilla qubits':>15s} {'Precision':>15s} {'States':>10s}")
    print("-" * 45)
    for n in range(1, args.max_ancilla + 1):
        precision = 2 ** (-n)
        states = 2 ** n
        print(f"{n:15d} {precision:15.8f} {states:10d}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="quantum-phase-estimation-shor",
        description="Quantum Phase Estimation — real QPE and Shor's order finding"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # estimate
    p = sub.add_parser("estimate", help="Estimate a phase using QPE")
    p.add_argument("--phase", type=float, default=0.25, help="True phase φ (default: 0.25)")
    p.add_argument("--ancilla", type=int, default=4, help="Number of ancilla qubits (default: 4)")
    p.add_argument("--show-probs", action="store_true", help="Show probability distribution")

    # sweep
    p = sub.add_parser("sweep", help="Sweep phases to test QPE accuracy")
    p.add_argument("--ancilla", type=int, default=4, help="Number of ancilla qubits")
    p.add_argument("--samples", type=int, default=16, help="Number of phases to test")

    # order
    p = sub.add_parser("order", help="Find order using Shor's algorithm")
    p.add_argument("--a", type=int, required=True, help="Base a")
    p.add_argument("--N", type=int, required=True, help="Modulus N")
    p.add_argument("--ancilla", type=int, default=8, help="Number of ancilla qubits")

    # factors
    p = sub.add_parser("factors", help="Factor a number using Shor's algorithm")
    p.add_argument("--N", type=int, required=True, help="Number to factor")
    p.add_argument("--ancilla", type=int, default=8, help="Number of ancilla qubits")

    # precision
    p = sub.add_parser("precision", help="Show precision analysis")
    p.add_argument("--max-ancilla", type=int, default=10, help="Max ancilla qubits to show")

    args = parser.parse_args(argv)
    handlers = {
        'estimate': cmd_estimate,
        'sweep': cmd_sweep,
        'order': cmd_order,
        'factors': cmd_factors,
        'precision': cmd_precision,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
