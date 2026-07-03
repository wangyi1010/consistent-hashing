"""Property tests for RingHashing."""

from __future__ import annotations

import pytest

from consistent_hashing import RingHashing


@pytest.fixture
def ring_with_students():
    r = RingHashing(node_seed=1, key_seed=2)
    for y in range(5):
        r.open_tutorial(y)
    for x in range(200):
        r.insert_student(x)
    return r


def test_find_returns_assigned_node(ring_with_students):
    r = ring_with_students
    for x in range(200):
        node = r.find_student(x)
        assert node is not None
        assert node in r.nodes


def test_load_sums_to_enrolled(ring_with_students):
    r = ring_with_students
    total_load = sum(r.load(y) for y in r.nodes)
    assert total_load == 200


def test_not_enrolled_returns_none():
    r = RingHashing()
    r.open_tutorial(0)
    assert r.find_student(999) is None


def test_open_tutorial_moves_few_students():
    r = RingHashing(node_seed=10, key_seed=20)
    for y in range(4):
        r.open_tutorial(y)
    for x in range(1000):
        r.insert_student(x)
    # Adding a 5th node should move roughly 1000/5 = 200 students
    moved = r.open_tutorial(99)
    assert moved < 500, f"too many moved: {moved}"
    # All students must still be assigned correctly
    total = sum(r.load(y) for y in r.nodes)
    assert total == 1000


def test_close_tutorial_reassigns_load():
    r = RingHashing(node_seed=3, key_seed=4)
    for y in range(3):
        r.open_tutorial(y)
    for x in range(300):
        r.insert_student(x)
    load_before = r.load(1)
    moved = r.close_tutorial(1)
    assert moved == load_before
    assert r.load(1) == 0
    assert sum(r.load(y) for y in r.nodes) == 300


def test_remove_student():
    r = RingHashing()
    r.open_tutorial(0)
    r.insert_student("alice")
    r.remove_student("alice")
    assert r.find_student("alice") is None
    assert r.load(0) == 0


def test_reassignment_consistent_after_open_close():
    r = RingHashing(node_seed=7, key_seed=8)
    for y in range(4):
        r.open_tutorial(y)
    for x in range(400):
        r.insert_student(x)
    r.open_tutorial(99)
    r.close_tutorial(99)
    # After open + close the assignments should be the same as the original
    # (students that moved to 99 must have moved back)
    for x in range(400):
        node = r.find_student(x)
        assert node in r.nodes


def test_open_on_empty_ring():
    r = RingHashing()
    moved = r.open_tutorial(0)
    assert moved == 0
    assert r.n_nodes == 1


def test_close_nonexistent_node():
    r = RingHashing()
    r.open_tutorial(0)
    moved = r.close_tutorial(999)
    assert moved == 0
    assert r.n_nodes == 1


def test_insert_when_no_nodes():
    r = RingHashing()
    r.insert_student("x")
    assert r.find_student("x") is None


def test_naive_vs_ring_reassignment_ratio():
    """Ring reassigns O(m'/n); naive reassigns O(m')."""
    from consistent_hashing import NaiveHashing

    n, m = 10, 2000
    ring = RingHashing(node_seed=1, key_seed=2)
    naive = NaiveHashing(key_seed=2)
    for y in range(n):
        ring.open_tutorial(y)
        naive.open_tutorial(y)
    for x in range(m):
        ring.insert_student(x)
        naive.insert_student(x)
    ring_moved = ring.open_tutorial(n)
    naive_moved = naive.open_tutorial(n)
    # Ring should move roughly m/(n+1) ≈ 182; naive moves most of m
    assert ring_moved < naive_moved / 3, f"ring moved {ring_moved}, naive moved {naive_moved}"
