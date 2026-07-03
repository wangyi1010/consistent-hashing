"""
Naive modular hashing (Problem 1, COMP5270 Assignment 2).

Each student x is assigned to tutorial h(x) mod n.  When n changes,
O(m') students must be reassigned — the whole point of the prelude.
This class is the baseline that consistent hashing fixes.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Generic, Hashable, TypeVar

from ._hash import sha64

K = TypeVar("K", bound=Hashable)
N = TypeVar("N")


class NaiveHashing(Generic[K, N]):
    """
    Modular assignment: student → tutorial h(x) mod n.

    OpenTutorial / CloseTutorial reassign O(m') students on average
    because the modular residues all shift when n changes.
    """

    def __init__(self, *, key_seed: int = 2) -> None:
        self._key_seed = key_seed
        self._nodes: list[N] = []
        self._enrolled: dict[K, N] = {}
        self._load: dict[N, set[K]] = defaultdict(set)

    # -- internal --

    def _assign(self, x: K) -> N | None:
        if not self._nodes:
            return None
        idx = sha64(x, self._key_seed) % len(self._nodes)
        return self._nodes[idx]

    # -- public API --

    def find_student(self, x: K) -> N | None:
        return self._enrolled.get(x)

    def load(self, y: N) -> int:
        return len(self._load.get(y, ()))

    def insert_student(self, x: K) -> None:
        if x in self._enrolled or not self._nodes:
            return
        node = self._assign(x)
        self._enrolled[x] = node
        self._load[node].add(x)

    def remove_student(self, x: K) -> None:
        node = self._enrolled.pop(x, None)
        if node is not None:
            self._load[node].discard(x)

    def open_tutorial(self, y: N) -> int:
        """Add tutorial y; reassign every enrolled student. Returns count moved."""
        self._nodes.append(y)
        reassigned = 0
        for x in list(self._enrolled):
            old = self._enrolled[x]
            new = self._assign(x)
            if new != old:
                self._load[old].discard(x)
                self._load[new].add(x)
                self._enrolled[x] = new
                reassigned += 1
        return reassigned

    def close_tutorial(self, y: N) -> int:
        """Remove tutorial y; reassign every enrolled student. Returns count moved."""
        if y not in self._nodes:
            return 0
        self._nodes.remove(y)
        self._load.pop(y, None)
        reassigned = 0
        for x in list(self._enrolled):
            old = self._enrolled[x]
            new = self._assign(x)
            if new is None:
                del self._enrolled[x]
                reassigned += 1
            elif new != old:
                self._load[old].discard(x)
                self._load[new].add(x)
                self._enrolled[x] = new
                reassigned += 1
        return reassigned

    @property
    def n_nodes(self) -> int:
        return len(self._nodes)

    @property
    def nodes(self) -> list[N]:
        return list(self._nodes)
