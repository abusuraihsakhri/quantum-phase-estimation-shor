# Quantum Phase Estimation and Shor Order Finding

A small, educational implementation of quantum phase estimation (QPE) and modular order finding. The project includes a standard-library Python simulator, a browser demonstration, and an optional, separate audit API.

## Features

- **QPE:** phase-gate eigenvalue estimation, inverse quantum Fourier transform, and measurement probabilities.
- **Modular order finding:** a state-vector simulation of the entangled modular multiplication register and phase reconstruction with bounded rational approximations. The classical order is computed **afterwards** for verification, not used to prepare the simulated distribution.
- **CLI:** phase estimation, sweeps, order finding, small factoring demonstrations, and precision tables.
- **Browser demonstration:** phase and modular-order probability distributions calculated locally with no backend, accounts, or dependencies.
- **Separate legacy audit layer:** heuristic metric thresholds, CSV batch processing, and an optional FastAPI service. These checks are *not* QPE calculations, clinical decision support, or conformance with a formal standard.

This is a **small-number numerical demonstration**, not quantum hardware, a scalable factorization system, or a security tool.

## Run the browser application

The static files are in `web/`; the GitHub Pages deployment workflow publishes that directory from `master` when Pages is configured for GitHub Actions. For local use:

```bash
python -m http.server 8080 --directory web
```

Then open `http://127.0.0.1:8080/`. No Python interpreter runs inside the web application: the small numerical algorithms have a standalone JavaScript implementation. Modern desktop and mobile browsers supporting ES2020 are sufficient.

## Run the Python simulator

Requires Python 3.9 or later.

```bash
python -m pip install -e .
python cli.py estimate --phase 0.25 --ancilla 4 --show-probs
python cli.py sweep --ancilla 5 --samples 16
python cli.py order --a 2 --N 15 --ancilla 8
python cli.py factors --N 15 --ancilla 8
python cli.py precision --max-ancilla 8
```

The QPE phase register supports up to 12 ancilla qubits. The modular-order demonstration supports up to 10 ancillas and modulus `2..255`; these bounds prevent impractical computation. The browser demonstration uses up to 10 ancillas and modulus `3..63` with a coprime base of at least 2. Order recovery can fail when precision is insufficient.

## Legacy audit CLI and HTTP service

The audit functionality is independent of quantum order finding. Install the optional API dependencies:

```bash
python -m pip install -e ".[api]"
python -m qpe_engine.cli audit --task-id TASK-001
python -m qpe_engine.cli batch -i sample.csv -o results.csv
python -m qpe_engine.cli serve --host 127.0.0.1 --port 8000
```

The package API offers `/health`, `/api/audit`, and `/api/chat`. An alternative legacy API is launched with `uvicorn agents.api:app --host 127.0.0.1 --port 8000`, which is also the Docker entry point:

```bash
docker build -t quantum-phase-estimation-shor .
docker run --rm -p 127.0.0.1:8000:8000 quantum-phase-estimation-shor
```

These development APIs are **not authenticated** and must not be exposed on public networks without adding authentication and access controls. The chat endpoints use a deterministic placeholder; they do not perform external language-model inference.

## Testing

```bash
python -m pip install -e ".[api,test]"
pytest -q
node --check web/app.js
node --test web/app.test.cjs
```

GitHub Actions checks Python 3.10, 3.11, and 3.12, plus browser numerical regressions.

## Privacy and audit limitations

The browser UI executes locally: it does not transmit inputs, load remote scripts, or persist results. Do not enter sensitive or patient data into the legacy API. Its regex-based identifier detection is not comprehensive de-identification. HMAC audit-chain verification checks integrity within the current process; logs are held only in memory, and a stable `AUDIT_SECRET_KEY` is needed to keep the signing key consistent across sessions. This is not durable, immutable audit storage.

## Technology and license

Python standard library for the numerical engine; optional FastAPI, Pydantic, and Uvicorn for the API; dependency-free HTML, CSS, and JavaScript for the browser demonstration. MIT License; see [LICENSE](LICENSE).
