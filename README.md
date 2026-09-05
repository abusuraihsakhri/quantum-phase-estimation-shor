# Quantum Phase Estimation Shor

> **Domain:** Quantum Computing — Phase Estimation & Integer Factorization

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

A Python implementation of **Quantum Phase Estimation (QPE)** and **Shor's order-finding algorithm** using state-vector simulation. QPE estimates the eigenvalue e^(2πiφ) of a unitary operator, and Shor's algorithm uses this to find the order of an element modulo N — the core subroutine for integer factorization.

---

## ⚙️ Key Capabilities

- **Quantum Phase Estimation (QPE):** Full state-vector simulation with configurable ancilla qubit count
- **Shor's Order Finding:** Finds r such that a^r ≡ 1 (mod N) using QPE + continued fractions
- **Continued Fraction Expansion:** Extracts order from measured phase
- **Classical Verification:** Order-finding verification against brute-force classical method
- **CLI Interface:** Command-line tools for estimation, sweeping, factoring, and diagnostics
- **Enterprise Agent Suite:** Multi-worker evaluation system with PHI guard and HMAC-SHA256 audit trail
- **FastAPI REST API:** HTTP endpoints for audit, chat, and metrics
- **Prometheus Metrics:** Operational telemetry exporter

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/quantum-phase-estimation-shor.git
cd quantum-phase-estimation-shor

# Install dependencies (stdlib-only for core QPE; optional for API)
pip install --upgrade pip
pip install fastapi uvicorn pydantic pytest  # optional: for REST API and testing
```

---

## 🚀 CLI Quickstart

### QPE Commands (root `cli.py`)

```bash
# Estimate a phase
python cli.py estimate --phase 0.25 --ancilla 4

# Show probability distribution
python cli.py estimate --phase 0.25 --ancilla 4 --show-probs

# Sweep phases to test accuracy
python cli.py sweep --ancilla 4 --samples 16

# Find order using Shor's algorithm
python cli.py order --a 2 --N 15 --ancilla 8

# Factor a number
python cli.py factors --N 15 --ancilla 8

# Show precision analysis
python cli.py precision --max-ancilla 10

# Audit evaluation with HMAC logging
python cli.py audit --task-id TASK-001 --primary 29.4 --critical

# Submit an analytical query
python cli.py chat "Explain quantum phase estimation"

# Verify audit chain integrity
python cli.py verify-audit
```

### Agent Suite Commands (`qpe_engine/cli.py`)

```bash
# Run single task evaluation
python qpe_engine/cli.py audit --task-id TASK-001

# Batch process CSV records
python qpe_engine/cli.py batch -i sample.csv -o results.csv

# Launch FastAPI REST server
python qpe_engine/cli.py serve --host 127.0.0.1 --port 8000
```

---

## 🧪 Testing

```bash
# Run the full test suite
pytest -v

# Run with coverage
pytest -v --tb=short
```

The test suite includes:
- **Gate tests:** Unitary verification, eigenvalue checks, matrix multiplication
- **State vector tests:** Basis states, probabilities, fidelity
- **QFT tests:** Roundtrip fidelity, uniform superposition, qubit reversal
- **QPE core tests:** Exact phases, precision scaling, probability normalization
- **Continued fractions:** Fraction reconstruction, denominator constraints
- **Order finding:** Classical and quantum order-finding verification
- **CLI tests:** All command interfaces
- **Security tests:** PHI guard enforcement, HMAC audit integrity

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t quantum-phase-estimation-shor .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key quantum-phase-estimation-shor

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## 📁 Project Structure

```
quantum-phase-estimation-shor/
├── cli.py                    # Root CLI (QPE + audit/chat commands)
├── qpe_engine/
│   ├── __init__.py           # Package init
│   ├── engine.py             # Core QPE, QFT, Shor's algorithm
│   ├── cli.py                # Agent suite CLI
│   ├── models.py             # Pydantic data models
│   ├── agents.py             # QPE coordinator
│   └── server.py             # FastAPI application factory
├── agents/
│   ├── __init__.py           # Enterprise suite init
│   ├── base.py               # PHI guard, HMAC audit trail
│   ├── models.py             # Task payload, dossier schemas
│   ├── workers.py            # Specialized evaluation workers
│   ├── supervisor.py         # Multi-agent orchestrator
│   ├── llm_factory.py        # LLM provider abstraction
│   ├── learning.py           # Bayesian calibration engine
│   ├── streamer.py           # WebSocket telemetry
│   ├── metrics.py            # Prometheus metrics collector
│   └── api.py                # FastAPI REST endpoints
├── web/
│   └── index.html            # Operations console UI
├── tests/
│   ├── test_qpe_engine.py    # QPE, QFT, Shor tests
│   ├── test_enrichment.py    # Enrichment suite tests
│   └── test_quantum_phase_estimation_shor.py  # Agent/security tests
├── enrichment.py             # Enrichment feature engines
├── simulator.py              # High-throughput simulation
├── Dockerfile                # Container build
├── docker-compose.yml        # Container orchestration
└── pyproject.toml            # Project metadata
```

---

## 🛡️ Security

- **PHI Outbound Guard:** Regex-based detection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Input Validation:** Bounds checking on all QPE parameters (ancilla count, phase values, modular arithmetic inputs)
- **No Hardcoded Secrets:** Audit key sourced from `AUDIT_SECRET_KEY` environment variable

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
