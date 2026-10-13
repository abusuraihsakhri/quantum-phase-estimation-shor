"""Regressions for order finding, authentication, and legacy CLI paths."""
import csv
import math
from pathlib import Path

import pytest

from agents.base import AuditTrail
from cli import _CLI_AUDIT_LOG, _log_cli_event, _verify_cli_audit
from qpe_engine import engine
from qpe_engine.cli import main as agent_main, parse_bool
from qpe_engine.engine import modular_exponentiation_matrix


def test_modular_multiplication_is_a_permutation():
    matrix = modular_exponentiation_matrix(2, 15, 4)
    assert len(matrix) == 16
    for col in range(16):
        assert sum(abs(matrix[row][col]) ** 2 for row in range(16)) == 1
    for row in matrix:
        assert sum(abs(x) ** 2 for x in row) == 1
    assert matrix[2][1] == 1
    assert matrix[0][0] == 1
    with pytest.raises(ValueError):
        modular_exponentiation_matrix(3, 15, 4)


def test_qpe_wraparound_and_bounded_registers():
    a = engine.quantum_phase_estimation(0.25, 4)
    b = engine.quantum_phase_estimation(1.25, 4)
    c = engine.quantum_phase_estimation(-0.75, 4)
    assert a["best_measurement"] == b["best_measurement"] == c["best_measurement"] == 4
    assert b["phase_error"] < 1e-10
    with pytest.raises(ValueError):
        engine.quantum_phase_estimation(0.25, 13)
    with pytest.raises(TypeError):
        engine.quantum_phase_estimation(0.25, True)


@pytest.mark.parametrize("a,N,order", [(2, 15, 4), (4, 15, 2), (7, 15, 4), (2, 21, 6)])
def test_modular_order_finding(a, N, order):
    result = engine.shor_order_finding(a, N, 8)
    assert result["success"]
    assert result["estimated_order"] == order
    assert result["method"] == "modular_multiplication_qpe"
    assert abs(sum(result["qpe_result"]["ancilla_probabilities"]) - 1) < 1e-9


def test_classical_order_is_diagnostic_only(monkeypatch):
    monkeypatch.setattr(engine, "find_order_classical", lambda a, n: 999)
    result = engine.shor_order_finding(2, 15, 8)
    assert result["true_order"] == 999
    assert result["estimated_order"] == 4


def test_audit_hmac_detects_modified_payload():
    audit = AuditTrail("test-secret")
    audit.log("worker", "system", "TEST", {"item": "ok"})
    assert audit.verify_integrity()
    public_copy = audit.get_trail()
    public_copy[0]["payload_hash"] = "0" * 64
    assert audit.verify_integrity()
    audit.logs[0]["payload_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_cli_hmac_detects_modified_details():
    _CLI_AUDIT_LOG.clear()
    try:
        _log_cli_event("tester", "TEST", "safe")
        assert _verify_cli_audit()
        _CLI_AUDIT_LOG[0]["details"] = "changed"
        assert not _verify_cli_audit()
    finally:
        _CLI_AUDIT_LOG.clear()


@pytest.mark.parametrize("value, expected", [("false", False), ("0", False), ("no", False),
                                               ("true", True), ("1", True), ("YES", True)])
def test_csv_boolean_parser(value, expected):
    assert parse_bool(value) is expected


def test_batch_cli_handles_false_without_critical_alert(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    with source.open("w", newline="", encoding="utf8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "task_id", "target_identifier", "primary_metric", "secondary_metric",
            "status_descriptor", "is_critical_flag"
        ])
        writer.writeheader()
        writer.writerow({
            "task_id": "T1", "target_identifier": "KEY1",
            "primary_metric": "10", "secondary_metric": "5",
            "status_descriptor": "NOMINAL", "is_critical_flag": "false",
        })
    assert agent_main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["critical_count"] == "0"
    assert rows[0]["overall_status"] == "NOMINAL_OPTIMAL"
