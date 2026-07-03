"""Property tests for NaiveHashing."""

from __future__ import annotations

from consistent_hashing import NaiveHashing


def test_load_balance():
    n = NaiveHashing()
    for y in range(5):
        n.open_tutorial(y)
    for x in range(500):
        n.insert_student(x)
    assert sum(n.load(y) for y in n.nodes) == 500


def test_find_student():
    n = NaiveHashing()
    n.open_tutorial(0)
    n.insert_student("bob")
    assert n.find_student("bob") == 0
    assert n.find_student("nobody") is None


def test_remove_student():
    n = NaiveHashing()
    n.open_tutorial(0)
    n.insert_student(42)
    n.remove_student(42)
    assert n.find_student(42) is None
    assert n.load(0) == 0


def test_open_tutorial_reassigns_many():
    n = NaiveHashing(key_seed=5)
    for y in range(4):
        n.open_tutorial(y)
    for x in range(1000):
        n.insert_student(x)
    moved = n.open_tutorial(99)
    # Modular hashing rehashes almost everything
    assert moved > 500


def test_close_tutorial():
    n = NaiveHashing()
    for y in range(3):
        n.open_tutorial(y)
    for x in range(300):
        n.insert_student(x)
    moved = n.close_tutorial(1)
    assert moved > 0
    assert sum(n.load(y) for y in n.nodes) == 300
