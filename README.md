# consistent-hashing

Three consistent-hashing implementations with empirical verification of their
theoretical guarantees, derived from COMP5270 (Randomised Algorithms) Assignment 2.

---

## The problem

You manage a large course with *m* students and *n* tutorials.  You need a
data structure that:

1. **Assigns** each student to a tutorial quickly.
2. **Balances** load — no tutorial gets too many students.
3. **Minimises churn** — when a tutorial opens or closes, as few students
   as possible should be reassigned.

The naive solution (assign student *x* to tutorial `h(x) mod n`) satisfies (1)
and (2) but breaks (3): changing *n* by 1 rehashes almost every student.

---

## How ring hashing fixes it

Map both students and tutorials onto a ring of size *M* = 2^64 using independent
hash functions:

$$h : \text{students} \to [M], \qquad g : \text{tutorials} \to [M]$$

Student *x* is assigned to the tutorial *y* whose ring position *g*(*y*) is
the smallest value ≥ *h*(*x*) (wrapping around).

When a new tutorial opens at position *p*, only the students in the arc
(*predecessor*, *p*] are affected — an expected fraction **1/n** of all students.
When a tutorial closes, only its own load (also expected *m'/n*) is redistributed.

---

## Virtual nodes reduce variance

With one position per tutorial the load variance is high: a tutorial that
happens to own a long arc gets disproportionately many students.  Giving
each tutorial *k* virtual positions (Problem 4) spreads the ownership
over *k* independent arcs, reducing variance by a factor of *k*:

$$\operatorname{Var}[m_y^{(k)}] \approx \frac{1}{k} \operatorname{Var}[m_y^{(1)}] = O\!\left(\frac{m'^2}{kn^2}\right)$$

Setting *k* = O(log(1/δ) / ε²) guarantees load within (1 ± ε)·*m'*/*n*
with probability ≥ 1 − δ (Problem 4g).

---

## Implementations

| Class | Description | Open/Close cost |
|---|---|---|
| `NaiveHashing` | `h(x) mod n` — baseline | O(*m'*) |
| `RingHashing` | One ring position per node | O(*m'*/*n*) expected |
| `VirtualNodeHashing(k)` | *k* virtual positions per node | O(*m'*/*n*) expected, lower variance |

All three share the same interface (Problems 2 & 3):

```python
import consistent_hashing as ch

ring = ch.RingHashing()
ring.open_tutorial(0)          # add node
ring.open_tutorial(1)
ring.insert_student("alice")   # enroll student
ring.find_student("alice")     # → 0 or 1
ring.load(0)                   # → int
ring.close_tutorial(0)         # remove node; alice moves to 1
```

---

## Empirical results

### Reassignment on topology change

```
m=2000 students, n=10 nodes, 20 open/close trials each

Implementation         Op          avg moved     % of m       theory
--------------------------------------------------------------------
Naive                  open           1820.5      91.0%       ~m=2000
Naive                  close          1800.0      90.0%       ~m=2000
Ring                   open            127.7       6.4%     ~m/10=200
Ring                   close           162.9       8.1%     ~m/10=200
VNode k=50             open            181.7       9.1%     ~m/10=200
VNode k=50             close           196.7       9.8%     ~m/10=200
VNode k=150            open            193.8       9.7%     ~m/10=200
VNode k=150            close           196.4       9.8%     ~m/10=200
```

Ring and virtual-node variants reassign ≈ *m*/*n* students; naive reassigns ≈ 90%.

### Load balance (n=20 nodes, m=5000 students)

```
Implementation             mean      max      min      std    max/exp
----------------------------------------------------------------------
Naive                     250.0      272      229    12.60       1.09x
Ring (k=1)                250.0     1299       20   308.51       5.20x
VNode k=10                250.0      379      152    73.11       1.52x
VNode k=50                250.0      323      177    38.53       1.29x
VNode k=150               250.0      301      195    26.24       1.20x
```

Key observation: ring hashing (k=1) has *worse* max-load than naive (5.2x vs 1.1x
of mean).  This is because arc-length variance is high with only one position per
node — a single unlucky node can own 5× its fair share of the ring.  This is the
motivation for Problem 4: virtual nodes with k=150 bring the maximum down to 1.2x,
consistent with Var[*m_y*] = O(*m'^2* / (*kn*²)).

---

## Quickstart

```bash
git clone https://github.com/wangyi1010/consistent-hashing
cd consistent-hashing
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
python3 benchmarks/measure_reassignment.py
python3 benchmarks/measure_load.py
```

---

## Design notes

- **Exact hash space**: ring size is 2^64 (SHA-256 prefix), collision probability < 1/2^64 per pair.
- **Efficient open/close**: each node maintains a sorted list of its students' ring positions; `open_tutorial` claims the new arc in O(log n + moved) without scanning all *m'* students.
- **k=1 equivalence**: `VirtualNodeHashing(k=1)` produces identical assignments to `RingHashing` for the same seeds (verified by test).
- **No external dependencies**: stdlib only (`hashlib`, `bisect`); `matplotlib` optional for plotting.

---

## Connection to production systems

This construction is the core of Amazon DynamoDB's partition layer, Apache
Cassandra's token ring, and Akamai's CDN routing.  Real deployments typically
use k = 100–200 virtual nodes.  The `close_tutorial` operation corresponds to
*decommissioning* a node; only the decommissioned node's data needs to move —
exactly the O(*m'*/*n*) bound shown here.

---

## Background

- COMP5270 Assignment 2, Problems 1–4 (University of Sydney, S1 2026).
- Karger et al., *Consistent Hashing and Random Trees*, STOC 1997.
- DeCandia et al., *Dynamo: Amazon's Highly Available Key-value Store*, SOSP 2007.
