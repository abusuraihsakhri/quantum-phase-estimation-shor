"use strict";

/* Self-contained, dependency-free numerical simulations for GitHub Pages. */

function validateAncilla(n) {
  if (!Number.isInteger(n) || n < 1 || n > 10) {
    throw new RangeError("Ancilla qubits must be an integer from 1 to 10.");
  }
}

function qpeProbabilities(phi, n) {
  validateAncilla(n);
  if (!Number.isFinite(phi)) throw new RangeError("Phase must be finite.");
  const phase = ((phi % 1) + 1) % 1;
  const size = 2 ** n;
  const probabilities = [];
  for (let k = 0; k < size; k += 1) {
    const delta = phase - k / size;
    const denominator = Math.sin(Math.PI * delta);
    const value = Math.abs(denominator) < 1e-12
      ? 1
      : (Math.sin(Math.PI * size * delta) / (size * denominator)) ** 2;
    probabilities.push(value);
  }
  return probabilities;
}

function gcd(a, b) {
  while (b !== 0) [a, b] = [b, a % b];
  return a;
}

function powMod(base, exponent, modulus) {
  let result = 1;
  let factor = base % modulus;
  let power = exponent;
  while (power > 0) {
    if (power % 2) result = (result * factor) % modulus;
    factor = (factor * factor) % modulus;
    power = Math.floor(power / 2);
  }
  return result;
}

function bestRational(x, maxDenominator) {
  let bestP = 0;
  let bestQ = 1;
  let error = Math.abs(x);
  for (let q = 1; q <= maxDenominator; q += 1) {
    const p = Math.round(x * q);
    const distance = Math.abs(x - p / q);
    if (distance < error - 1e-12) {
      bestP = p;
      bestQ = q;
      error = distance;
    }
  }
  return [bestP, bestQ];
}

function orderFindingProbabilities(a, N, n) {
  validateAncilla(n);
  if (!Number.isInteger(a) || !Number.isInteger(N) ||
      N < 3 || N > 63 || a < 2 || a >= N || gcd(a, N) !== 1) {
    throw new RangeError("Require 3 ≤ N ≤ 63 and 2 ≤ a < N with gcd(a,N)=1.");
  }

  const size = 2 ** n;
  const workStates = new Map();
  let residue = 1;
  for (let j = 0; j < size; j += 1) {
    if (!workStates.has(residue)) workStates.set(residue, []);
    workStates.get(residue).push(j);
    residue = (residue * a) % N;
  }

  // Trace out the modular work register following the inverse Fourier transform.
  const probabilities = Array(size).fill(0);
  for (let k = 0; k < size; k += 1) {
    let total = 0;
    for (const positions of workStates.values()) {
      let real = 0;
      let imag = 0;
      for (const j of positions) {
        const angle = -2 * Math.PI * k * j / size;
        real += Math.cos(angle);
        imag += Math.sin(angle);
      }
      total += real * real + imag * imag;
    }
    probabilities[k] = total / (size * size);
  }

  let estimatedOrder = null;
  let selected = null;
  const ranks = Array.from({length: size - 1}, (_, i) => i + 1);
  ranks.sort((x, y) => probabilities[y] - probabilities[x] || x - y);
  for (const k of ranks) {
    const [, q] = bestRational(k / size, N);
    if (q > 1 && powMod(a, q, N) === 1) {
      selected = k;
      estimatedOrder = q;
      break;
    }
  }

  // Classical diagnostic does not determine the simulated probability distribution.
  let classicalOrder = 1;
  while (powMod(a, classicalOrder, N) !== 1 && classicalOrder <= N) classicalOrder += 1;
  return {probabilities, estimatedOrder, selected, classicalOrder};
}

function peakIndex(probabilities) {
  return probabilities.reduce((best, value, index, array) =>
    value > array[best] ? index : best, 0);
}

function renderDistribution(container, probabilities, chosen) {
  container.replaceChildren();
  const ranking = probabilities.map((probability, index) => ({probability, index}))
    .sort((a, b) => b.probability - a.probability || a.index - b.index);
  const shown = ranking.slice(0, 12);
  for (const entry of shown) {
    const row = document.createElement("div");
    row.className = "bar-row";
    const label = document.createElement("span");
    label.textContent = String(entry.index);
    label.className = entry.index === chosen ? "selected" : "";
    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = (100 * entry.probability).toFixed(2) + "%";
    track.append(fill);
    const value = document.createElement("span");
    value.textContent = (100 * entry.probability).toFixed(2) + "%";
    row.append(label, track, value);
    container.append(row);
  }
}

function initUI() {
  const phaseForm = document.getElementById("phase-form");
  const orderForm = document.getElementById("order-form");
  if (!phaseForm || !orderForm) return;

  phaseForm.addEventListener("submit", event => {
    event.preventDefault();
    const output = document.getElementById("phase-output");
    try {
      const phi = Number(document.getElementById("phase").value);
      const n = Number(document.getElementById("phase-ancilla").value);
      const probs = qpeProbabilities(phi, n);
      const k = peakIndex(probs);
      const estimate = k / (2 ** n);
      const normalized = ((phi % 1) + 1) % 1;
      const error = Math.abs(((estimate - normalized + 1.5) % 1) - 0.5);
      output.textContent = "Estimated phase: " + estimate.toFixed(6) +
        " · Circular error: " + error.toExponential(3) +
        " · Best outcome: " + k +
        " · Probability sum: " + probs.reduce((a, b) => a + b, 0).toFixed(6);
      renderDistribution(document.getElementById("phase-bars"), probs, k);
    } catch (error) {
      output.textContent = "Input error: " + error.message;
      document.getElementById("phase-bars").replaceChildren();
    }
  });

  orderForm.addEventListener("submit", event => {
    event.preventDefault();
    const output = document.getElementById("order-output");
    try {
      const a = Number(document.getElementById("base").value);
      const N = Number(document.getElementById("modulus").value);
      const n = Number(document.getElementById("order-ancilla").value);
      const result = orderFindingProbabilities(a, N, n);
      output.textContent = "QPE-derived order: " + (result.estimatedOrder ?? "not recovered") +
        " · Classical verification: " + result.classicalOrder +
        " · Probability sum: " +
        result.probabilities.reduce((x, y) => x + y, 0).toFixed(6);
      renderDistribution(document.getElementById("order-bars"), result.probabilities, result.selected);
    } catch (error) {
      output.textContent = "Input error: " + error.message;
      document.getElementById("order-bars").replaceChildren();
    }
  });

  phaseForm.requestSubmit();
  orderForm.requestSubmit();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initUI);
  } else {
    initUI();
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {qpeProbabilities, orderFindingProbabilities, bestRational, peakIndex, powMod};
}
