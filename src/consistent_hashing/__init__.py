"""
consistent-hashing — three implementations compared.

  NaiveHashing       modular (h(x) mod n); O(m') reassignment on topology change
  RingHashing        ring / consistent hashing; O(m'/n) expected reassignment
  VirtualNodeHashing ring with k virtual nodes per server; reduces load variance

All three share the same interface:
  find_student(x)    → node | None
  load(y)            → int
  insert_student(x)
  remove_student(x)
  open_tutorial(y)   → int   (students reassigned)
  close_tutorial(y)  → int
"""

from .naive import NaiveHashing
from .ring import RingHashing
from .virtual_nodes import VirtualNodeHashing

__version__ = "0.1.0"
__all__ = ["NaiveHashing", "RingHashing", "VirtualNodeHashing"]
