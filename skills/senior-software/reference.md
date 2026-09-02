# Reference — Design Principles & Refactoring Heuristics

Language-agnostic. Apply what fits the task and the codebase; name a principle only
when it actually drives a decision or tradeoff. Do not recite this file.

---

## 1. Design principles

### SOLID (apply, don't worship)

- **Single Responsibility** — a module/class/function has one reason to change. The
  smell is a name with "and" in it, or a file that imports from unrelated domains.
- **Open/Closed** — extend behavior by adding code, not editing stable core. Reach
  for this only when variation points are real and recurring; premature abstraction
  is its own debt.
- **Liskov Substitution** — subtypes must honor the base contract (no surprise
  exceptions, no narrowed inputs / widened outputs).
- **Interface Segregation** — many small focused interfaces beat one fat one;
  callers shouldn't depend on methods they never call.
- **Dependency Inversion** — depend on abstractions at module boundaries, concretes
  inside. Inject what varies (clock, IO, randomness) to keep cores testable.

### Coupling & cohesion

- High cohesion inside a unit, low coupling between units.
- Prefer **data flowing through explicit arguments/returns** over shared mutable
  state. Hidden coupling via globals/singletons is the common source of "spooky
  action at a distance."
- Stable things should not depend on volatile things. Depend in the direction of
  stability.

### API design

- **Make the common case easy and the wrong case hard.** Good defaults; required
  arguments for things with no safe default.
- **Be hard to misuse.** Prefer types/enums over stringly-typed flags; make illegal
  states unrepresentable where the language allows.
- **Smallest surface that does the job.** Every public symbol is a future
  maintenance contract. Keep internals internal.
- **Consistency beats local cleverness** — match the naming, argument order, and
  error style of sibling APIs in the same codebase.
- **Explicit over implicit** — no surprising side effects, no hidden IO behind a
  pure-looking name.
- Consider evolution: how does this API add a parameter or a variant later without
  breaking callers?

### Naming

- Name by **intent / role**, not implementation (`retryBudget`, not `intCounter`).
- Length scales with scope: tiny loop var can be short; an exported symbol earns a
  full, searchable name.
- Booleans read as predicates (`isExpired`, `hasAccess`). Functions are verbs;
  values are nouns.
- Avoid encodings, redundant prefixes, and near-synonyms that imply a distinction
  that doesn't exist (`getUser` vs `fetchUser` vs `loadUser` in one codebase).

### Error handling

- **Fail fast at boundaries; trust inside.** Validate untrusted input at the edge;
  don't re-check the same invariant in every inner function.
- Distinguish **expected** outcomes (return a result/option/error value) from
  **exceptional** ones (throw / panic). Don't use exceptions for normal control flow.
- Preserve context — wrap errors with what was being attempted; never swallow an
  error silently or log-and-continue past a corrupted state.
- Clean up deterministically (defer / finally / RAII / context managers). Match the
  resource-handling idiom the language and codebase already use.
- An error message is for the person debugging at 3am: say what failed, with which
  inputs, and what the caller can do.

---

## 2. Refactoring heuristics (smell → remedy)

Behavior must stay observable-equivalent. One coherent improvement per pass.

| Smell | Signal | Remedy |
|-------|--------|--------|
| **Duplication** | Same logic in 2+ places, edited in lockstep | Extract function/module; parameterize the difference |
| **Long function** | Doesn't fit on a screen; many responsibilities | Extract cohesive sub-steps with intention-revealing names |
| **Long parameter list** | 5+ args, several always passed together | Introduce a parameter object / struct |
| **Primitive obsession** | Raw strings/ints carrying domain meaning | Introduce a small value type / enum |
| **Feature envy** | Method uses another object's data more than its own | Move the method to where the data lives |
| **Leaky abstraction** | Callers must know internal details to use it right | Tighten the interface; hide internals |
| **Shotgun surgery** | One change forces edits across many files | Consolidate the responsibility into one place |
| **Divergent change** | One module changes for many unrelated reasons | Split by reason-to-change (SRP) |
| **Conditional complexity** | Deep nesting, repeated type-switch | Guard clauses, polymorphism/strategy, table dispatch |
| **Temporal coupling** | Methods must be called in a hidden required order | Encode the sequence in the type/API so misuse won't compile |
| **Dead code** | Unreferenced symbols, unreachable branches | Delete it (version control is the archive) |
| **Comment-as-apology** | Comment explains *what* awkward code does | Rename/extract so the code says it; keep comments for *why* |

### Safe-refactor discipline

1. **Establish a behavior baseline first.** Identify the tests that pin current
   behavior. If coverage is thin, add a **characterization test** that captures
   current output *before* touching the code.
2. **Small steps, each reversible.** Rename, then extract, then inline — not all at
   once. Keep it green between steps where tooling allows.
3. **Separate refactor commits from behavior-change commits.** Never mix "tidy" and
   "fix/feature" in one diff; it makes review and bisecting impossible.
4. **Verify equivalence.** Re-run the baseline tests; state the exact command. If
   the language has it, lean on type-checker + formatter + linter as cheap guards.
5. If you discover a bug mid-refactor, **stop and surface it** — fixing it is a
   behavior change and belongs in its own change with the user's call.

---

## 3. Decision recording (ADR)

Keep design decisions cheap to record and easy to find later:

```
## ADR: <short imperative title>
**Status:** Proposed | Accepted
**Context:** What forces/constraints are in play? What problem, at what scale,
under what deadline and existing stack?
**Decision:** What we are doing, stated plainly.
**Consequences:** What gets better, what gets worse, what we now must live with,
and what follow-up work this creates.
```

Record an ADR when the decision is **expensive to reverse** or **non-obvious to the
next reader**. Skip it for routine, local choices.
