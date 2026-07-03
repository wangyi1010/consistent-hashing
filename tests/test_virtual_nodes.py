"""Property tests for VirtualNodeHashing."""

from __future__ import annotations

import statistics

import pytest

from consistent_hashing import VirtualNodeHashing


@pytest.fixture
def vring():
    r = VirtualNodeHashing(k=50, node_seed=1, key_seed=2)
    for y in range(5):
        r.open_tutorial(y)
    for x in range(1000):
        r.insert_student(x)
    return r


def test_all_enrolled(vring):
    total = sum(vring.load(y) for y in vring.nodes)
    assert total == 1000


def test_find_student(vring):
    for x in range(1000):
        assert vring.find_student(x) in vring.nodes


def test_variance_lower_than_ring():
    """k=150 virtual nodes should have lower load std-dev than k=1 (plain ring)."""
    from consistent_hashing import RingHashing

    n_nodes, m = 10, 5000

    ring = RingHashing(node_seed=1, key_seed=2)
    vring = VirtualNodeHashing(k=150, node_seed=1, key_seed=2)
    for y in range(n_nodes):
        ring.open_tutorial(y)
        vring.open_tutorial(y)
    for x in range(m):
        ring.insert_student(x)
        vring.insert_student(x)

    ring_loads = [ring.load(y) for y in ring.nodes]
    vring_loads = [vring.load(y) for y in vring.nodes]

    ring_cv = statistics.stdev(ring_loads) / statistics.mean(ring_loads)
    vring_cv = statistics.stdev(vring_loads) / statistics.mean(vring_loads)
    assert vring_cv < ring_cv, (
        f"virtual nodes (k=150) cv={vring_cv:.3f} not < ring cv={ring_cv:.3f}"
    )


def test_open_tutorial_moves_few(vring):
    moved = vring.open_tutorial(99)
    total = sum(vring.load(y) for y in vring.nodes)
    assert total == 1000
    assert moved < 500


def test_close_tutorial(vring):
    load_2 = vring.load(2)
    moved = vring.close_tutorial(2)
    assert moved == load_2
    total = sum(vring.load(y) for y in vring.nodes)
    assert total == 1000


def test_k1_matches_ring_semantics():
    """VirtualNodeHashing with k=1 should behave like RingHashing."""
    from consistent_hashing import RingHashing

    n, m = 5, 200
    ring = RingHashing(node_seed=3, key_seed=4)
    vring = VirtualNodeHashing(k=1, node_seed=3, key_seed=4)
    for y in range(n):
        ring.open_tutorial(y)
        vring.open_tutorial(y)
    for x in range(m):
        ring.insert_student(x)
        vring.insert_student(x)
    for x in range(m):
        assert ring.find_student(x) == vring.find_student(x), f"mismatch at key {x}"
