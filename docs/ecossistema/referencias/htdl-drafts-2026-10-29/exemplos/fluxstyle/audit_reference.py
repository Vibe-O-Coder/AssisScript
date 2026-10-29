#!/usr/bin/env python3
"""Audit the numerical proposal, not an FS/SSC compiler or browser.

Run with: python -B exemplos/fluxstyle/audit_reference.py
The coefficient perturbation is an expected counterexample to the former
universal tolerance claim. Its detection is a successful audit check.
"""
import itertools
import json

import spring_reference as ref


def perturbed_trajectory(coefficients, target, steps):
    x, v = ref.q(-target), 0
    values = [0.0]
    calm = 0
    sleeping = False
    for _ in range(steps):
        if not sleeping:
            x, v = (
                ref.fx_mul(coefficients[0], x) + ref.fx_mul(coefficients[1], v),
                ref.fx_mul(coefficients[2], x) + ref.fx_mul(coefficients[3], v),
            )
            calm = calm + 1 if abs(x) < ref.REST_X and abs(v) < ref.REST_V else 0
            if calm >= ref.REST_STEPS:
                x = v = 0
                sleeping = True
        values.append(target + x / ref.ONE)
    return values


def scheduler_probe():
    phase = 0
    simulated = discarded = 0
    records = []
    for elapsed_ms in (1000, 8, 1):
        due, phase = divmod(phase + elapsed_ms * 120, 1000)
        executed = min(due, 8)
        simulated += executed
        discarded += due - executed
        records.append({"elapsedMs": elapsed_ms, "executed": executed,
                        "discarded": due - executed, "phase": phase})
    assert records[0]["executed"] == 8 and records[0]["discarded"] == 112
    assert records[1]["executed"] == 0 and records[2]["executed"] == 1
    return {"frames": records, "simulated": simulated, "discarded": discarded}


def main():
    normal, matrix = ref.trace(4, 0.8, [(1, -8)], 120)
    reversal, _ = ref.trace(4, 0.8, [(1, -8), (11, 0)], 120)
    assert matrix == [64251, 461, -290983, 45727]
    assert ref.first_rest(normal) == 41
    assert ref.first_rest(reversal, 12) == 51

    worst_error = 0.0
    slowest_rest = 0.0
    grid_cases = 0
    for frequency in (0.5, 1, 2, 4, 6, 8, 10):
        for damping in (0.1, 0.3, 0.8, 1.0, 2.0, 4.0):
            trace, _ = ref.trace(frequency, damping, [(1, -8)], 60 * ref.STEPS)
            slowest_rest = max(slowest_rest, ref.first_rest(trace) / ref.STEPS)
            for step in range(1, 3 * ref.STEPS + 1):
                exact = ref.analytic(frequency, damping, 8, step * ref.DT)
                worst_error = max(worst_error, abs(trace[step][0] + 8 - exact))
            grid_cases += 1

    frequency, damping, target = 0.5, 0.1, -4096
    baseline, base_matrix = ref.trace(frequency, damping, [(1, target)], 2400)
    worst = {"deviationPx": 0.0}
    for deltas in itertools.product((-1, 1), repeat=4):
        changed = [value + delta for value, delta in zip(base_matrix, deltas)]
        trajectory = perturbed_trajectory(changed, target, 2400)
        for step in range(1, 2401):
            error = abs(trajectory[step] - baseline[step][0])
            if error > worst["deviationPx"]:
                worst = {"deviationPx": error, "step": step,
                         "coefficientErrorsUlp": list(deltas)}
    assert worst["deviationPx"] > 1 / 16
    worst.update({"frequencyHz": frequency, "dampingRatio": damping,
                  "targetPx": target, "formerTolerancePx": 1 / 16})

    literal_tie = ref.q(-0.5 / ref.ONE)
    product_tie = ref.fx_mul(-1, ref.ONE // 2)
    assert literal_tie == -1 and product_tie == 0
    try:
        ref.fx_mul(ref.INT64 - 1, 2)
    except OverflowError:
        overflow_check = "rejected"
    else:
        raise AssertionError("overflow was not detected")

    result = {
        "auditPassed": True,
        "scope": "Python reference and proposal checks; no FS/SSC engine",
        "goldenCard": {"coefficients": matrix, "restStep": 41,
                       "minimumPx": min(p for p, _ in normal),
                       "reversalRestStep": 51,
                       "reversalMinimumPx": min(p for p, _ in reversal)},
        "eightPixelGrid": {"cases": grid_cases,
                           "slowestRestSeconds": slowest_rest,
                           "maxErrorVsAnalyticFirst3SecondsPx": worst_error,
                           "coverage": "42 sampled pairs, 8 px step; not entire parameter domain"},
        "coefficientCounterexample": worst,
        "rounding": {"negativeHalfUlpLiteral": literal_tie,
                     "negativeHalfUlpProduct": product_tie,
                     "int64Overflow": overflow_check},
        "schedulerReference": scheduler_probe(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
