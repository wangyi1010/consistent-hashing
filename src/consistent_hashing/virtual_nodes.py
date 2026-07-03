"""
Virtual-node consistent hashing (Problem 4, COMP5270 Assignment 2).

Each node y is given k virtual positions on the ring:
  g_1(y), g_2(y), ..., g_k(y)

A student x is assigned to the node y whose virtual position is the
ring successor of h(x).  k = 1 reduces to plain ring hashing.

Why k > 1 reduces variance:
  With 1 position per node the arc owned by y is a single interval
  of expected length M/n but high variance.  With k positions the
  arc is the union of k smaller intervals (expected length M/(kn) each),
  and the total load m_y = sum of k i.i.d. portions, so
  Var[m_y] ≈ (1/k) Var[ring hashing with k·n nodes].

Problem 4g shows k = O(log(1/δ) / ε²) suffices for
(1 ± ε)·m'/n load with probability 1 − δ.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from typing import Generic, Hashable, TypeVar

from ._hash import sha64

K = TypeVar("K", bound=Hashable)
N = TypeVar("N", bound=int | str)


def _ring_bisect_left(ring: list[tuple[int, N]], pos: int) -> int:
    lo, hi = 0, len(ring)
    while lo < hi:
        mid = (lo + hi) // 2
        if ring[mid][0] < pos:
            lo = mid + 1
        else:
            hi = mid
    return lo


class VirtualNodeHashing(Generic[K, N]):
    """
    Ring consistent hashing with k virtual nodes per server.

    Interface identical to RingHashing; only the internal ring structure
    differs (k entries per logical node instead of 1).

    Node IDs must be orderable (int or str).
    """

    def __init__(self, k: int = 150, *, node_seed: int = 1, key_seed: int = 2) -> None:
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        self.k = k
        self._node_seed = node_seed
        self._key_seed = key_seed
        # ring stores (pos, (node, replica_index))
        self._ring: list[tuple[int, tuple[N, int]]] = []
        self._nodes: set[N] = set()
        # per-node sorted key positions (across all k arcs)
        self._node_kpos: dict[N, list[int]] = defaultdict(list)
        self._kpos_key: dict[int, K] = {}
        self._enrolled: dict[K, N] = {}

    # -- internal --

    def _vpos(self, node: N, replica: int) -> int:
        # replica 0 uses the same hash as RingHashing so k=1 gives identical assignments
        key = node if replica == 0 else (node, replica)
        return sha64(key, self._node_seed)

    def _key_pos(self, key: K) -> int:
        return sha64(key, self._key_seed)

    def _successor(self, pos: int) -> N:
        i = _ring_bisect_left(self._ring, pos) % len(self._ring)
        return self._ring[i][1][0]

    # -- public API --

    def find_student(self, x: K) -> N | None:
        return self._enrolled.get(x)

    def load(self, y: N) -> int:
        return len(self._node_kpos.get(y, ()))

    def insert_student(self, x: K) -> None:
        if x in self._enrolled or not self._ring:
            return
        kp = self._key_pos(x)
        node = self._successor(kp)
        self._enrolled[x] = node
        self._kpos_key[kp] = x
        bisect.insort(self._node_kpos[node], kp)

    def remove_student(self, x: K) -> None:
        node = self._enrolled.pop(x, None)
        if node is None:
            return
        kp = self._key_pos(x)
        self._kpos_key.pop(kp, None)
        sl = self._node_kpos[node]
        idx = bisect.bisect_left(sl, kp)
        if idx < len(sl) and sl[idx] == kp:
            sl.pop(idx)

    def open_tutorial(self, y: N) -> int:
        """Add node y with k virtual positions. Returns students reassigned."""
        if y in self._nodes:
            return 0
        self._nodes.add(y)
        self._node_kpos[y] = []
        total_moved = 0

        for r in range(self.k):
            yp = self._vpos(y, r)
            if not self._ring:
                self._ring.append((yp, (y, r)))
                continue

            ins = _ring_bisect_left(self._ring, yp)
            prev_p = self._ring[(ins - 1) % len(self._ring)][0]
            succ_node = self._ring[ins % len(self._ring)][1][0]

            bisect.insort(self._ring, (yp, (y, r)))

            sl = self._node_kpos[succ_node]
            if prev_p < yp:
                lo = bisect.bisect_right(sl, prev_p)
                hi = bisect.bisect_right(sl, yp)
                to_move = sl[lo:hi]
                del sl[lo:hi]
            else:
                lo = bisect.bisect_right(sl, prev_p)
                high_part = sl[lo:]
                del sl[lo:]
                hi = bisect.bisect_right(sl, yp)
                low_part = sl[:hi]
                del sl[:hi]
                to_move = high_part + low_part

            for kp in to_move:
                bisect.insort(self._node_kpos[y], kp)
                self._enrolled[self._kpos_key[kp]] = y
            total_moved += len(to_move)

        return total_moved

    def close_tutorial(self, y: N) -> int:
        """Remove node y; its students scatter to k successor virtual nodes."""
        if y not in self._nodes:
            return 0
        self._nodes.discard(y)

        # Remove all k virtual positions from ring
        to_remove = [(self._vpos(y, r), (y, r)) for r in range(self.k)]
        for entry in to_remove:
            idx = bisect.bisect_left(self._ring, entry)
            if idx < len(self._ring) and self._ring[idx] == entry:
                self._ring.pop(idx)

        students = self._node_kpos.pop(y, [])
        if not students:
            return 0

        if not self._ring:
            for kp in students:
                k = self._kpos_key.pop(kp, None)
                if k is not None:
                    self._enrolled.pop(k, None)
            return len(students)

        for kp in students:
            succ = self._successor(kp)
            bisect.insort(self._node_kpos[succ], kp)
            self._enrolled[self._kpos_key[kp]] = succ

        return len(students)

    @property
    def n_nodes(self) -> int:
        return len(self._nodes)

    @property
    def nodes(self) -> frozenset[N]:
        return frozenset(self._nodes)
