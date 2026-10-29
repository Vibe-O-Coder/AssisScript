#!/usr/bin/env python3
"""Reference emulation of the SSC 0.1 spring (see docs/11-ssc-referencia.md, section 6).

This is NOT the SSC compiler and NOT AssisScript. It reproduces, with Python integers,
the integer algorithm the documents propose, so the numbers quoted in the docs can be
checked and so a future AssisScript implementation has traces to compare against.

State is kept relative to the target: x = position - target, v = velocity (px/s).
Values have 16 fractional bits and int64-checked multiplication intermediates.
Coefficients are computed with floating point here; this is not a validated portable
fixed-point coefficient generator for an AssisScript engine.

Usage:
    python3 spring_reference.py            # prints the golden traces and tables
"""
import math

ONE = 1 << 16            # Q16.16
STEPS = 120              # fixed simulation steps per second
DT = 1.0 / STEPS
REST_X = ONE // 64       # 1/64 px
REST_V = ONE // 2        # 0.5 px/s
REST_STEPS = 3           # consecutive calm steps before sleeping
INT64 = 1 << 63


def q(x):
    """Real -> Q16.16, rounding half away from zero."""
    return int(math.floor(x * ONE + 0.5)) if x >= 0 else -int(math.floor(-x * ONE + 0.5))


def fx_mul(a, b):
    """Fixed16 product; nearest with ties toward positive infinity.

    Literal/coefficient conversion q() has a different, explicit tie rule:
    half away from zero. Both rules preserve the original golden traces.
    """
    raw = a * b
    if not -INT64 <= raw < INT64:
        raise OverflowError("int64 product overflow")
    p = raw + (ONE >> 1)
    if not -INT64 <= p < INT64:
        raise OverflowError("int64 rounding-bias overflow")
    return p >> 16


def coeffs(freq_hz, zeta):
    """Exact one-step transition matrix (m11, m12, m21, m22) for dt = 1/STEPS."""
    w = 2 * math.pi * freq_hz
    if zeta < 1:
        wd = w * math.sqrt(1 - zeta * zeta)
        e = math.exp(-zeta * w * DT)
        c, s, k = math.cos(wd * DT), math.sin(wd * DT), zeta * w / wd
        return (e * (c + k * s), e * s / wd, -e * (w * w / wd) * s, e * (c - k * s))
    if zeta == 1:
        e = math.exp(-w * DT)
        return (e * (1 + w * DT), e * DT, -e * w * w * DT, e * (1 - w * DT))
    g = w * math.sqrt(zeta * zeta - 1)
    e = math.exp(-zeta * w * DT)
    ch, sh, k = math.cosh(g * DT), math.sinh(g * DT), zeta * w / g
    return (e * (ch + k * sh), e * sh / g, -e * (w * w / g) * sh, e * (ch - k * sh))


def analytic(freq_hz, zeta, x0, t):
    """Continuous solution with v0 = 0, used only to measure error."""
    w = 2 * math.pi * freq_hz
    if zeta < 1:
        wd = w * math.sqrt(1 - zeta * zeta)
        return math.exp(-zeta * w * t) * (x0 * math.cos(wd * t) + (zeta * w * x0 / wd) * math.sin(wd * t))
    if zeta == 1:
        return math.exp(-w * t) * x0 * (1 + w * t)
    s = math.sqrt(zeta * zeta - 1)
    r1, r2 = -w * (zeta - s), -w * (zeta + s)
    return x0 * (r2 * math.exp(r1 * t) - r1 * math.exp(r2 * t)) / (r2 - r1)


def trace(freq_hz, zeta, plan, nsteps):
    """Presentation starts resting at 0 px. plan = [(step, new_target_px), ...].
    Returns [(position_px, resting), ...] for steps 0..nsteps and the Q16.16 coefficients."""
    m = [q(c) for c in coeffs(freq_hz, zeta)]
    plan = dict(plan)
    pos = 0                       # screen position, Q16.16
    target = 0
    x = v = calm = 0
    resting = True
    out = [(0.0, True)]
    for i in range(1, nsteps + 1):
        if i in plan:             # target change: keep screen position and velocity
            target = q(plan[i])
            x = pos - target
            resting, calm = False, 0
        if not resting:
            x, v = fx_mul(m[0], x) + fx_mul(m[1], v), fx_mul(m[2], x) + fx_mul(m[3], v)
            calm = calm + 1 if (abs(x) < REST_X and abs(v) < REST_V) else 0
            if calm >= REST_STEPS:
                x = v = 0
                resting = True
        pos = target + x
        out.append((pos / ONE, resting))
    return out, m


def first_rest(tr, after=1):
    return next(i for i, (_, r) in enumerate(tr) if r and i >= after)


def main():
    print("Overshoot theory exp(-pi*z/sqrt(1-z^2)):")
    for z in (0.3, 0.5, 0.6, 0.7, 0.8, 0.9):
        print(f"  zeta={z}: {math.exp(-math.pi * z / math.sqrt(1 - z * z)) * 100:.2f}% of the distance")

    tr, m = trace(4, 0.8, [(1, -8.0)], 120)
    print("\nA) 4 Hz, zeta 0.8, target 0 -> -8 px at step 1. Coefficients Q16.16:", m)
    for i in (1, 2, 3, 4, 6, 9, 11, 16, 21, 26, 31, 41):
        print(f"  step {i:3d} ({i / STEPS * 1000:4.0f} ms): {tr[i][0]:9.4f} px")
    r = first_rest(tr)
    print(f"  rest at step {r} ({r / STEPS * 1000:.0f} ms); minimum {min(p for p, _ in tr):.4f} px")

    tr, _ = trace(4, 0.8, [(1, -8.0), (11, 0.0)], 120)
    r = first_rest(tr, 12)
    print(f"\nB) same, target back to 0 px at step 11: reversal at {min(p for p, _ in tr):.4f} px, "
          f"rest at step {r} ({r / STEPS * 1000:.0f} ms)")

    print("\nzeta table at 4 Hz, 8 px:")
    for z in (0.3, 0.5, 0.8, 1.0, 2.0):
        tr, _ = trace(4, z, [(1, -8.0)], 6 * STEPS)
        r = first_rest(tr)
        over = -8.0 - min(p for p, _ in tr)
        print(f"  zeta={z}: overshoot {over:.3f} px, rest at {r / STEPS * 1000:.0f} ms")

    print("\nrest time at zeta 0.8, 8 px:")
    for f in (0.5, 1, 4, 8):
        tr, _ = trace(f, 0.8, [(1, -8.0)], 6 * STEPS)
        print(f"  {f} Hz: {first_rest(tr) / STEPS * 1000:.0f} ms")

    worst, slowest = 0.0, 0
    for f in (0.5, 1, 2, 4, 6, 8, 10):
        for z in (0.1, 0.3, 0.8, 1.0, 2.0, 4.0):
            tr, _ = trace(f, z, [(1, -8.0)], 60 * STEPS)
            slowest = max(slowest, first_rest(tr) / STEPS)
            # error against the continuous solution (position relative to target, x0 = +8)
            for i in range(1, 3 * STEPS + 1):
                err = abs((tr[i][0] + 8.0) - analytic(f, z, 8.0, i * DT))
                worst = max(worst, err)
    print(f"\ngrid 7 freqs x 6 zetas: slowest rest {slowest:.2f} s, worst error vs analytic {worst:.4f} px")


if __name__ == "__main__":
    main()
