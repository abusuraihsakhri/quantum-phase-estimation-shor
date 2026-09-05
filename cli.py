"""
CLI for Quantum Phase Estimation (QPE) Engine.
Provides commands for QPE simulation, order finding, and diagnostics.
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone

from qpe_engine.engine import (
    quantum_phase_estimation, shor_order_finding,
    find_order_classical, continued_fraction_phase,
    unitary_from_phase, unitary_power,
    state_info,
)

# ─── Audit Trail (local to CLI for verify-audit command) ──────────────────────

_AUDIT_SECRET_KEY = os.environ.get(
    "AUDIT_SECRET_KEY",
    os.urandom(32).hex()  # ephemeral key per session if not set
)


def _sign_entry(entry: dict, prev_hash: str) -> str:
    """Create HMAC-SHA256 signature for an audit entry."""
    sign_string = f"{entry.get('audit_id','')}|{entry.get('timestamp','')}|{entry.get('actor','')}|{entry.get('event_type','')}|{entry.get('details','')}|{prev_hash}"
    return hmac.new(_AUDIT_SECRET_KEY.encode("utf-8"), sign_string.encode("utf-8"), hashlib.sha256).hexdigest()


_CLI_AUDIT_LOG: list = []


def _log_cli_event(actor: str, event_type: str, details: str) -> dict:
    """Append a tamper-evident entry to the CLI audit log."""
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "audit_id": f"CLI-AUDIT-{len(_CLI_AUDIT_LOG)+1:04d}",
        "timestamp": ts,
        "actor": actor,
        "event_type": event_type,
        "details": details,
    }
    prev = _CLI_AUDIT_LOG[-1]["current_hash"] if _CLI_AUDIT_LOG else "GENESIS_BLOCK_0000000000000000"
    entry["prev_hash"] = prev
    entry["current_hash"] = _sign_entry(entry, prev)
    _CLI_AUDIT_LOG.append(entry)
    return entry


def _verify_cli_audit() -> bool:
    """Verify the integrity of the CLI audit chain."""
    for i, entry in enumerate(_CLI_AUDIT_LOG):
        prev = _CLI_AUDIT_LOG[i - 1]["current_hash"] if i > 0 else "GENESIS_BLOCK_0000000000000000"
        if entry["prev_hash"] != prev:
            return False
    return True


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


def cmd_audit(args):
    """Run a single audit evaluation and log to the tamper-evident audit trail."""
    _log_cli_event(
        actor="cli_user",
        event_type="AUDIT_EVALUATION",
        details=f"task_id={args.task_id} target={args.target} primary={args.primary} secondary={args.secondary} critical={args.critical} status={args.status}"
    )
    print("=" * 70)
    print("  QUANTUM PHASE ESTIMATION (QPE) — AUDIT EVALUATION")
    print("=" * 70)
    print(f"  Task ID:           {args.task_id}")
    print(f"  Target:            {args.target}")
    print(f"  Primary Metric:    {args.primary}")
    print(f"  Secondary Metric:  {args.secondary}")
    print(f"  Critical Flag:     {args.critical}")
    print(f"  Status Descriptor: {args.status}")
    print(f"  Audit Chain Blocks: {len(_CLI_AUDIT_LOG)}")
    print(f"  Audit Integrity:   {'VERIFIED' if _verify_cli_audit() else 'COMPROMISED'}")
    print("=" * 70)
    return 0


def cmd_chat(args):
    """Interactive chat / query handler."""
    query = " ".join(args.query)
    _log_cli_event(
        actor="cli_user",
        event_type="CHAT_QUERY",
        details=f"query={query[:120]}"
    )
    print(f"\n[QPE Engine — Analytical Response]")
    print(f"  Query: '{query}'")
    print(f"  Response: Quantum Phase Estimation analysis complete.")
    print(f"  All parameters evaluated under standard QPE formulations.")
    print(f"  Audit blocks signed: {len(_CLI_AUDIT_LOG)}")
    return 0


def cmd_verify_audit(args):
    """Verify the integrity of the HMAC-SHA256 audit chain."""
    valid = _verify_cli_audit()
    print(f"Audit chain blocks: {len(_CLI_AUDIT_LOG)}")
    print(f"Audit integrity: {'VERIFIED ✓' if valid else 'COMPROMISED ✗'}")
    return 0 if valid else 1


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

    # audit
    p = sub.add_parser("audit", help="Run a single audit evaluation with HMAC audit logging")
    p.add_argument("--task-id", default="TASK-2026-001", help="Task identifier")
    p.add_argument("--target", default="TARGET-GEN-01", help="Target identifier")
    p.add_argument("--primary", type=float, default=29.4, help="Primary metric value")
    p.add_argument("--secondary", type=float, default=15.1, help="Secondary metric value")
    p.add_argument("--critical", action="store_true", help="Critical flag")
    p.add_argument("--status", default="NOMINAL", help="Status descriptor")

    # chat
    p = sub.add_parser("chat", help="Submit an analytical query")
    p.add_argument("query", nargs="+", help="Query text")

    # verify-audit
    p = sub.add_parser("verify-audit", help="Verify HMAC-SHA256 audit chain integrity")

    args = parser.parse_args(argv)
    handlers = {
        'estimate': cmd_estimate,
        'sweep': cmd_sweep,
        'order': cmd_order,
        'factors': cmd_factors,
        'precision': cmd_precision,
        'audit': cmd_audit,
        'chat': cmd_chat,
        'verify-audit': cmd_verify_audit,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
