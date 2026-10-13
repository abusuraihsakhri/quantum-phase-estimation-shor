"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {qpeProbabilities, orderFindingProbabilities, bestRational, powMod} = require("./app.js");

test("exact binary phase produces a single outcome", () => {
  const probabilities = qpeProbabilities(0.25, 4);
  assert.ok(Math.abs(probabilities[4] - 1) < 1e-12);
  assert.ok(Math.abs(probabilities.reduce((a, b) => a + b, 0) - 1) < 1e-10);
});

test("phase is periodic modulo one", () => {
  const a = qpeProbabilities(0.25, 4);
  const b = qpeProbabilities(1.25, 4);
  const c = qpeProbabilities(-0.75, 4);
  for (let k = 0; k < a.length; k++) {
    assert.ok(Math.abs(a[k] - b[k]) < 1e-10);
    assert.ok(Math.abs(a[k] - c[k]) < 1e-10);
  }
});

test("non-dyadic phases yield normalized distributions", () => {
  const probs = qpeProbabilities(1 / 3, 7);
  assert.ok(Math.abs(probs.reduce((a, b) => a + b, 0) - 1) < 1e-10);
});

test("modular order distribution is normalized and recovers order 4 mod 15", () => {
  const result = orderFindingProbabilities(2, 15, 8);
  assert.ok(Math.abs(result.probabilities.reduce((a, b) => a + b, 0) - 1) < 1e-9);
  assert.equal(result.estimatedOrder, 4);
  assert.equal(result.classicalOrder, 4);
});

test("modular order 2 mod 15", () => {
  const result = orderFindingProbabilities(4, 15, 8);
  assert.equal(result.estimatedOrder, 2);
});

test("input validation rejects invalid registers and non-coprime bases", () => {
  assert.throws(() => qpeProbabilities(Infinity, 4), RangeError);
  assert.throws(() => qpeProbabilities(0.5, 20), RangeError);
  assert.throws(() => orderFindingProbabilities(3, 15, 8), RangeError);
});

test("classical modular utilities", () => {
  assert.equal(powMod(2, 4, 15), 1);
  assert.deepEqual(bestRational(0.25, 15), [1, 4]);
});
