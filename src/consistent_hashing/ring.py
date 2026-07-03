"""
Ring consistent hashing (Problems 2 & 3, COMP5270 Assignment 2).

Two hash functions map items onto a ring of size M = 2^64:
  h : students  → [M]   (key_seed)
  g : tutorials → [M]   (node_seed)

Student x is assigned to the tutorial y whose ring position g(y) is the
smallest value >= h(x) (wrapping around). This guarantees:

  - Expected load per tutorial: m'/n                  (uniform by symmetry)
  - OpenTutorial reassignments: O(m'/n) expected      (only the claimed arc)
  - CloseTutorial reassignments: O(m'/n) expected     (the closed node's load)
  - FindStudent: O(1) via enrolled dict; successor lookup O(log n)

The implementation stores, per node, a sorted list of enrolled key
positions so that OpenTutorial claims only the affected arc in
O(log n + reassigned) time without scanning all m' students.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from typing import Generic, Hashable, TypeVar

from ._hash import sha64

K = TypeVar("K", bound=Hashable)
N = TypeVar("N", bound=int | str)


def _ring_bisect_left(ring: list[tuple[int, N]], pos: int) -> int:
    """Index of the leftmost entry with ring_pos >= pos (position only, no type tie-break)."""
    lo, hi = 0, len(ring)
    while lo < hi:
        mid = (lo + hi) // 2
        if ring[mid][0] < pos:
            lo = mid + 1
        else:
            hi = mid
    return lo


class RingHashing(Generic[K, N]):
    """
    Consistent hashing on a 2^64-slot ring.

    Node IDs must be orderable (int or str) because the ring list is
    kept sorted by (position, node_id).  Hash collisions between two
    nodes are astronomically unlikely (1/2^64 per pair).
    """

    def __init__(self, *, node_seed: int = 1, key_seed: int = 2) -> None:
        self._node_seed = node_seed
        self._key_seed = key_seed
        self._ring: list[tuple[int, N]] = []  # sorted by (pos, node)
        self._npos: dict[N, int] = {}  # node → ring position
        self._node_kpos: dict[N, list[int]] = defaultdict(list)  # sorted key positions
        self._kpos_key: dict[int, K] = {}  # position → key
        self._enrolled: dict[K, N] = {}  # key → node

    # -- internal --

    def _node_pos(self, node: N) -> int:
        return sha64(node, self._node_seed)

    def _key_pos(self, key: K) -> int:
        return sha64(key, self._key_seed)

    def _successor(self, pos: int) -> N:
        """Node responsible for ring position pos."""
        i = _ring_bisect_left(self._ring, pos) % len(self._ring)
        return self._ring[i][1]

    def _ring_insert(self, pos: int, node: N) -> int:
        """Insert (pos, node) into _ring; return insertion index."""
        i = bisect.bisect_left(self._ring, (pos, node))
        self._ring.insert(i, (pos, node))
        return i

    # -- public API --

    def find_student(self, x: K) -> N | None:
        """O(1): return the node x is enrolled in, or None."""
        return self._enrolled.get(x)

    def load(self, y: N) -> int:
        """Number of students currently assigned to node y."""
        return len(self._node_kpos.get(y, ()))

    def insert_student(self, x: K) -> None:
        """Enroll x. No-op if already enrolled or no nodes exist."""
        if x in self._enrolled or not self._ring:
            return
        kp = self._key_pos(x)
        node = self._successor(kp)
        self._enrolled[x] = node
        self._kpos_key[kp] = x
        bisect.insort(self._node_kpos[node], kp)

    def remove_student(self, x: K) -> None:
        """Withdraw x. No-op if not enrolled."""
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
        """
        Add node y to the ring.  Returns number of students reassigned.

        Only students in the arc (predecessor_pos, y_pos] — expected
        fraction 1/n of all students — are moved from y's successor.
        """
        if y in self._npos:
            return 0
        yp = self._node_pos(y)
        self._npos[y] = yp

        if not self._ring:
            self._ring.append((yp, y))
            self._node_kpos[y] = []
            return 0

        ins = _ring_bisect_left(self._ring, yp)
        prev_p = self._ring[(ins - 1) % len(self._ring)][0]
        succ = self._ring[ins % len(self._ring)][1]

        self._ring_insert(yp, y)

        sl = self._node_kpos[succ]
        if prev_p < yp:
            # Normal arc: claim key positions in (prev_p, yp]
            lo = bisect.bisect_right(sl, prev_p)
            hi = bisect.bisect_right(sl, yp)
            to_move = sl[lo:hi]
            del sl[lo:hi]
        else:
            # Wrap-around arc: (prev_p, M) ∪ [0, yp]
            lo = bisect.bisect_right(sl, prev_p)
            high_part = sl[lo:]
            del sl[lo:]
            hi = bisect.bisect_right(sl, yp)
            low_part = sl[:hi]
            del sl[:hi]
            to_move = high_part + low_part

        self._node_kpos[y] = sorted(to_move)
        for kp in to_move:
            self._enrolled[self._kpos_key[kp]] = y

        return len(to_move)

    def close_tutorial(self, y: N) -> int:
        """
        Remove node y from the ring.  All of y's students move to y's
        successor.  Returns number of students reassigned.
        """
        if y not in self._npos:
            return 0
        yp = self._npos.pop(y)
        idx = bisect.bisect_left(self._ring, (yp, y))
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

        succ = self._ring[idx % len(self._ring)][1]
        sl = self._node_kpos[succ]
        for kp in students:
            bisect.insort(sl, kp)
            self._enrolled[self._kpos_key[kp]] = succ

        return len(students)

    @property
    def n_nodes(self) -> int:
        return len(self._ring)

    @property
    def nodes(self) -> frozenset[N]:
        return frozenset(self._npos)
