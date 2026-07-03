"""
Measure load distribution (max/min/std-dev) across implementations.

Theory (Problem 2c, 4e, COMP5270 A2):
  Expected load per node: m'/n for all three implementations.
  Max load:
    Naive       : O(log n / log log n) w.h.p. (standard balls-in-bins)
    Ring (k=1)  : O(log n) w.h.p. from the Var[m_y] = O(m'^2/n^2) bound
    VNode (k=K) : variance shrinks by factor k; max load approaches m'/n

Usage:
  python3 benchmarks/measure_load.py [n] [m] [--plot out.png]
  (defaults: n=20 nodes, m=5000 students)
"""

from __future__ import annotations

import math
import statistics
import sys

import consistent_hashing as ch

K_VALUES = (1, 10, 50, 150)


def measure(inst, nodes, keys) -> tuple[float, float, float, float]:
    for y in nodes:
        inst.open_tutorial(y)
    for x in keys:
        inst.insert_student(x)
    loads = [inst.load(y) for y in nodes]
    mean = statistics.mean(loads)
    return mean, max(loads), min(loads), statistics.stdev(loads)


def run(n: int, m: int) -> None:
    nodes = list(range(n))
    keys = list(range(m))
    expected = m / n

    print(f"n={n} nodes, m={m} students, expected load per node = {expected:.1f}\n")
    print(f"{'Implementation':<22} {'mean':>8} {'max':>8} {'min':>8} {'std':>8} {'max/exp':>10}")
    print("-" * 70)

    naive = ch.NaiveHashing(key_seed=2)
    mean, mx, mn, std = measure(naive, nodes, keys)
    print(f"{'Naive':<22} {mean:>8.1f} {mx:>8} {mn:>8} {std:>8.2f} {mx / expected:>10.2f}x")

    ring = ch.RingHashing(node_seed=1, key_seed=2)
    mean, mx, mn, std = measure(ring, nodes, keys)
    print(f"{'Ring (k=1)':<22} {mean:>8.1f} {mx:>8} {mn:>8} {std:>8.2f} {mx / expected:>10.2f}x")

    for k in K_VALUES[1:]:
        vr = ch.VirtualNodeHashing(k=k, node_seed=1, key_seed=2)
        mean, mx, mn, std = measure(vr, nodes, keys)
        label = f"VNode k={k}"
        print(f"{label:<22} {mean:>8.1f} {mx:>8} {mn:>8} {std:>8.2f} {mx / expected:>10.2f}x")

    print()
    print(
        "Max-load theory: Ring ~ (log n)/n · m = "
        f"{math.log(n) / n * m:.0f}; "
        f"VNode k=150 should approach {expected:.0f}"
    )


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 20
    m = int(args[1]) if len(args) > 1 else 5000
    run(n, m)
