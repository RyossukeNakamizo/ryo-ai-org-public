# /qa Reference — Severity Rubric, Review Checklist, Debug Heuristics

Consult this on every run. Keep findings grounded in these definitions so severity
grading is consistent and the review checklist is fully covered.

---

## Severity rubric

Grade by **impact × likelihood**, not by how hard the fix is.

| Severity | Definition | Typical examples |
|----------|-----------|------------------|
| **Critical** | Causes data loss/corruption, security breach, or production outage. Exploitable or guaranteed to fail in normal use. Ship-blocker. | RCE/SQLi/auth bypass, secret leaked in code, unbounded resource exhaustion, money/state-corrupting bug, guaranteed crash on the happy path. |
| **High** | Wrong results, crashes, or vulnerabilities under realistic but non-default conditions. Should be fixed before merge. | Null/None deref on a reachable path, race condition, missing authz check on a real route, off-by-one corrupting output, unhandled error that loses data. |
| **Medium** | Real defect with limited blast radius, or a latent issue likely to bite later. Fix soon. | Edge case mishandled (empty/huge/negative input), missing error handling on a rare path, N+1 query, misleading API contract, flaky behavior. |
| **Low** | Maintainability, readability, minor performance, or style that doesn't affect correctness now. Nice to fix. | Dead code, unclear naming, duplicated logic, missing test for a minor branch, micro-inefficiency, inconsistent formatting. |

**Tie-breakers:** if unsure between two levels, pick the higher one and label the
finding **(unverified)** with what would confirm it. Security and data-integrity
findings round **up**.

---

## Review checklist (scan every dimension)

### 1. Correctness / bugs
- Off-by-one, wrong operator, inverted condition, wrong variable.
- Incorrect assumptions about return values (e.g. functions that can return null/empty/error).
- State mutation order; aliasing; shared mutable state.
- Concurrency: races, deadlocks, non-atomic check-then-act, missing locks/awaits.
- Floating-point/precision and integer overflow where it matters.

### 2. Edge cases & error handling
- Empty / null / undefined / zero / negative / very large inputs.
- Boundary indices; empty collections; single-element collections.
- Error paths: are errors caught, logged, surfaced, and recoverable? Any swallowed exceptions?
- Resource cleanup on the error path (files, sockets, locks, transactions).
- Idempotency and partial-failure behavior for retried operations.

### 3. Security
- Input validation / injection (SQL, command, path traversal, template, deserialization).
- AuthN/AuthZ: is every sensitive operation gated, and at the right layer?
- Secrets in code/logs; PII handling; sensitive data in error messages.
- Unsafe defaults; missing TLS/cert verification; weak crypto/randomness.
- SSRF, open redirects, XSS/output encoding for anything reaching a browser.

### 4. Performance
- Algorithmic complexity (accidental O(n²)+); work inside hot loops.
- N+1 queries / round-trips; missing batching, caching, or pagination.
- Unbounded growth (memory, queues, result sets); missing limits/backpressure.
- Blocking calls on async/hot paths.

### 5. Maintainability / readability
- Naming, function size, duplication, dead code, magic numbers.
- Leaky or surprising abstractions; unclear ownership/contracts.
- Comments that are stale or that explain *what* instead of *why*.

### 6. Tests
- Are the changed paths covered? Are edge cases tested?
- Would a regression test have caught this? If a bug is found, propose one.

---

## Language-specific debugging heuristics

Detect the language, then bias your search toward its common failure modes.
This is a prompt for where to look — not an exhaustive list.

| Language | High-yield bug patterns to check first |
|----------|----------------------------------------|
| **Python** | `None` from `dict.get`/regex/`re.match`; mutable default args; late-binding closures in loops; `except:` swallowing; int vs float division; encoding (`str`/`bytes`); shadowed builtins; `is` vs `==`. |
| **JavaScript / TypeScript** | `undefined`/`null` access; `==` vs `===`; missing `await` (floating promises); `this` rebinding; array mutation vs copy; `NaN` propagation; off-by-one in slice; TS `any` hiding type holes; unhandled rejections. |
| **Java / Kotlin** | NPE on reachable paths; `equals`/`hashCode` mismatch; mutable shared state without sync; resource leaks (try-with-resources missing); integer overflow; autoboxing in hot loops; checked-exception swallowing. |
| **Go** | Ignored `err`; nil map writes; goroutine leaks; loop-variable capture (pre-1.22); slice aliasing/append surprises; missing `defer` cleanup; data races (run with `-race`). |
| **C / C++** | Buffer overruns; use-after-free / double-free; uninitialized memory; integer overflow/signedness; missing bounds checks; ownership/lifetime; UB from aliasing. |
| **Rust** | `unwrap`/`expect` panics; index out of bounds; integer overflow in release; `unsafe` invariants; lock ordering / deadlock; `?` swallowing context. |
| **C#** | NullReferenceException; `async void`; not disposing `IDisposable`; LINQ deferred-execution surprises; boxing; `==` on reference types. |
| **Ruby** | `nil` errors (`NoMethodError on nil`); mutating shared constants; symbol vs string keys; monkey-patch collisions; `rescue` too broad. |
| **PHP** | Loose `==` comparisons; undefined index/null; SQL injection via string concat; type juggling; `@` error suppression. |
| **SQL** | Missing indexes; implicit type casts defeating indexes; NULL semantics in `NOT IN`; cartesian joins; transaction isolation / lost updates. |
| **Shell / Bash** | Unquoted expansions; missing `set -euo pipefail`; word splitting; `[ ]` vs `[[ ]]`; non-portable constructs; subshell variable loss. |

### General debug method (language-agnostic)
1. **Reproduce deterministically** before theorizing. A non-reproducible bug needs a repro first.
2. **Bisect the failure surface**: narrow input, narrow code path, narrow time window. Binary-search the diff (`git log`, `git bisect`) when a regression.
3. **Read the actual error** — exact message, exact frame. Don't pattern-match to a similar-looking bug.
4. **Confirm the mechanism** before proposing a fix: which line, which value, which branch.
5. **Prefer the minimal fix** at the root cause over patching symptoms downstream.
6. **Verify**: re-run the repro; add/adjust a regression test; check you didn't break neighbors.
