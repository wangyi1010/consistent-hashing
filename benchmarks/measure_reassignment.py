"""
Measure average reassignment fraction when adding/removing a node.

Theory (Problem 2d/e, COMP5270 A2):
  Naive   : reassigns O(m') — essentially all students get rehashed
  Ring    : reassigns O(m'/n) — only the claimed arc
  VNode   : reassigns O(m'/n) total (k arcs, each O(m'/(kn)))

Usage:
  python3 benchmarks/measure_reassignment.py [m] [seed]
  (defaults: m=2000 enrolled students, 10 nodes, seed=42)
"""

from __future__ import annotations

import random
import sys

import consistent_hashing as ch

N_NODES = 10
N_TRIALS = 20


def run(m: int, seed: int) -> None:
    rng = random.Random(seed)
    keys = list(range(m))

    print(f"m={m} students, n={N_NODES} nodes, {N_TRIALS} open/close trials each\n")
    print(f"{'Implementation':<22} {'Op':<8} {'avg moved':>12} {'% of m':>10} {'theory':>12}")
    print("-" * 68)

    configs = [
        (ch.NaiveHashing, "Naive", {}, False),
        (ch.RingHashing, "Ring", {}, True),
        (ch.VirtualNodeHashing, "VNode k=50", {"k": 50}, True),
        (ch.VirtualNodeHashing, "VNode k=150", {"k": 150}, True),
    ]
    for cls, label, k_arg, has_node_seed in configs:
        for op in ("open", "close"):
            totals = []
            for trial in range(N_TRIALS):
                seeds = {"key_seed": seed + 100 + trial}
                if has_node_seed:
                    seeds["node_seed"] = seed + trial
                inst = cls(**k_arg, **seeds)
                for y in range(N_NODES):
                    inst.open_tutorial(y)
                for x in keys:
                    inst.insert_student(x)
                if op == "open":
                    moved = inst.open_tutorial(N_NODES)  # add one more
                else:
                    victim = rng.randrange(N_NODES)
                    moved = inst.close_tutorial(victim)
                totals.append(moved)
            avg = sum(totals) / len(totals)
            expected = f"~m/{N_NODES}={m // N_NODES}" if label != "Naive" else f"~m={m}"
            print(f"{label:<22} {op:<8} {avg:>12.1f} {100 * avg / m:>9.1f}%  {expected:>12}")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    m = int(args[0]) if args else 2000
    seed = int(args[1]) if len(args) > 1 else 42
    run(m, seed)
