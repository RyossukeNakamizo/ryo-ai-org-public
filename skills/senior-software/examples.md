# Examples — Input Shapes & Expected Output

Three worked examples, one per input shape, plus anti-patterns. These illustrate the
*shape* of a good response, not fixed wording.

---

## Example A — Prose design request (shape A → DESIGN)

**Invocation:**
```
/senior-software design a rate limiter for the public API gateway; ~5k req/s, must be fair per-API-key, single region for now but multi-region later
```

**Expected response shape:**

> **Mode: DESIGN**
>
> **Problem & constraints**
> Per-API-key rate limiting at the gateway, ~5k req/s aggregate, fairness per key.
> Single region now; *assuming* multi-region is a 6–12 month concern, not day one.
> *Assuming* a shared cache (Redis-class) is already available — flag if not.
>
> **Options**
>
> 1. **Token bucket in shared Redis** — atomic Lua script per key.
>    *Tradeoffs:* smooth bursts, simple mental model, one network hop per request;
>    Redis becomes a hot dependency; multi-region needs per-region buckets + reconciliation.
> 2. **Sliding-window counter, local + async sync** — count locally, flush to shared store.
>    *Tradeoffs:* lowest latency, survives cache blips; weaker global fairness,
>    more moving parts.
>
> **Recommendation:** Option 1. At 5k req/s a single Redis handles the load with
> headroom, and the simpler invariant matters more than the latency saved by (2).
> Revisit at multi-region: shard buckets per region, accept regional fairness.
>
> ```
> ## ADR: Token-bucket rate limiting in shared Redis
> **Status:** Proposed
> **Context:** 5k req/s gateway, per-key fairness, single region now, multi-region later.
> **Decision:** Per-key token bucket via atomic Redis Lua; limit/refill from config.
> **Consequences:** Simple and fair within region; Redis is now on the hot path
> (needs HA); multi-region deferred — will require per-region buckets. Follow-up:
> decide failure mode (fail-open vs fail-closed) when Redis is unreachable.
> ```
>
> Want me to implement the bucket script + middleware? (would switch to IMPLEMENT)

Note: no full implementation — design stops at the recommendation + ADR.

---

## Example B — File path (shape B → IMPLEMENT or REFACTOR)

**Invocation:**
```
/senior-software src/auth/session.py  add idle-timeout expiry to sessions
```

**Expected response shape:**

> **Mode: IMPLEMENT** (language: Python, inferred from `.py`; follows the existing
> dataclass + `datetime` style in this file)
>
> **Assumptions & interface (confirm before I commit):**
> - New field `last_seen_at: datetime` on `Session`, updated on each access.
> - `is_expired(now)` returns `True` when `now - last_seen_at > idle_timeout`.
> - *Assuming* `idle_timeout` comes from existing `SETTINGS` (saw `SETTINGS.session_ttl`).
> - *Assuming* callers already hold the session object — no storage-layer change here.
>
> *(then the code, matching the file's naming + error style, applied via Edit)*
>
> **Added:** `last_seen_at` field, `touch()` updater, `is_expired()` check.
> **Follow-ups for you:** unit test for the boundary (exactly at timeout), wire
> `touch()` into the request middleware, and decide whether expiry is lazy (on
> access) or swept by a background job.

If instead the prose said "refactor", the response would open **Mode: REFACTOR**,
show a before/after diff, and assert behavior preservation + how to verify.

---

## Example C — Empty arguments (shape C → continue current diff)

**Invocation:**
```
/senior-software
```

**Expected behavior:**

1. Run `git status --short` + `git diff` to see in-progress work.
2. Infer the mode from what's changed.

> **Mode: REFACTOR** (inferred from current diff — extracting `validate_order()`
> out of the 120-line `submit_order()` in `orders/service.go`, half-done)
>
> **Improving:** `submit_order` mixes validation, pricing, and persistence (long
> function + divergent change). Continuing the extraction you started.
>
> *(diff completing the extraction, in the file's Go conventions)*
>
> **Behavior preserved:** pure code movement — same calls, same order, same errors.
> **Verify:** `go test ./orders/...` (covers submit happy-path + 2 validation cases);
> recommend adding a characterization test for the discount branch, which is uncovered.

If there is **no** repo or **no** changes:

> No git changes detected (and/or not a git repo). Tell me what to design,
> implement, or refactor — I won't invent work.

---

## Anti-patterns (do NOT do these)

- **Skipping the mode line.** Every response starts with `Mode: …`.
- **Writing full implementation in DESIGN mode** without being asked. Stop at the ADR.
- **Guessing a critical interface silently.** State the assumption, or ask one
  focused question.
- **Hardcoding a language.** Detect from extension/context; follow local conventions.
- **Claiming "refactor" while changing behavior.** If behavior changes, relabel it
  and let the user decide.
- **Gold-plating.** Don't rewrite a module when asked to fix a function. Note the
  bigger opportunity separately.
- **Inventing work on empty input** when there's no diff. Ask instead.
- **Reinventing existing helpers.** Grep first; reuse what's there.
