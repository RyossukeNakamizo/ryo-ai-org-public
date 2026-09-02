# /qa Examples — One per input shape

Worked examples showing how the skill branches on the three input shapes and what
good output looks like. Abridged for illustration; real runs read the actual code.

---

## (a) File path → REVIEW mode

**Invocation:** `/qa src/auth/session.py`

**Output shape:**

> **Mode: REVIEW** — input is a file path; reviewing `src/auth/session.py` and its callers.
> Language detected: Python.
>
> ### [Critical] Session token compared with `==`, enabling timing attack
> - **Where:** `src/auth/session.py:88`
> - **Problem:** `if token == stored_token:` uses non-constant-time comparison on a secret.
> - **Why it matters:** Leaks token bytes via timing; defeats session integrity.
> - **Fix:** `if hmac.compare_digest(token, stored_token):`
>
> ### [High] `dict.get("user")` can return None and is dereferenced
> - **Where:** `src/auth/session.py:42`
> - **Problem:** `claims.get("user").id` — `get` returns `None` for malformed tokens.
> - **Why it matters:** `AttributeError` → 500 on attacker-controlled input.
> - **Fix:** guard for `None` and reject the request before access.
>
> **Prioritized actions:** 1) constant-time token compare (Critical). 2) null-guard claims (High). 3) add a malformed-token test (Medium).

---

## (b) Pasted error / stack trace → DEBUG mode

**Invocation:**
```
/qa Getting this in prod intermittently on checkout:

TypeError: Cannot read properties of undefined (reading 'total')
    at computeTax (src/checkout/tax.ts:31:24)
    at checkout (src/checkout/index.ts:77:19)
```

**Output shape:**

> **Mode: DEBUG** — input is a stack trace + description. Language detected: TypeScript.
>
> **Symptom:** `computeTax` throws on `undefined.total` during checkout; intermittent.
> **Reproduction:** Calling `checkout()` with a cart whose `lineItems` is `[]` reproduces it — `tax.ts:31` reads `cart.summary.total` but `summary` is built only when items exist (confirmed by reading `index.ts:60-77`). Ran `npm test -- tax` → fails with the same trace on the empty-cart case.
> **Root cause:** `src/checkout/tax.ts:31` — `cart.summary.total` assumes `summary` is always set; `index.ts:64` skips building `summary` when `lineItems.length === 0`, so `summary` is `undefined`.
> **Minimal fix:**
> ```diff
> - const base = cart.summary.total;
> + const base = cart.summary?.total ?? 0;
> ```
> **Verification:** `npm test -- tax` (now covers empty cart); confirm checkout with an empty cart returns tax `0` instead of throwing.
>
> *(unverified)* Intermittency is consistent with empty/abandoned carts reaching checkout; confirm via the prod log timestamps vs. cart sizes.

---

## (c) Empty → REVIEW current git diff

**Invocation:** `/qa`

**Behavior:** No argument → run `git diff HEAD` (then `git status`). Review only the changed hunks.

**Output shape:**

> **Mode: REVIEW** — no argument given; reviewing the working tree changes (`git diff HEAD`: 2 files, 31 lines). Language detected: Go.
>
> ### [High] Error from `json.Unmarshal` ignored
> - **Where:** `internal/api/handler.go:54` (diff hunk @@ added)
> - **Problem:** `json.Unmarshal(body, &req)` return value discarded; `req` used regardless.
> - **Why it matters:** Malformed body → zero-value `req` silently processed; wrong behavior, no error to client.
> - **Fix:** check `if err := json.Unmarshal(...); err != nil { return 400 }`.
>
> ### [Low] Duplicated validation block
> - **Where:** `internal/api/handler.go:60-66`
> - **Problem:** Same length check as `validate.go:12`.
> - **Why it matters:** Drift risk; fix one, miss the other.
> - **Fix:** call the existing `validateLen`.
>
> **Prioritized actions:** 1) handle the unmarshal error (High). 2) de-dupe validation (Low).
>
> *(If `git diff` were empty: state "no working changes detected; not a target" and ask for a file path or pasted error.)*

---

## Anti-patterns (do NOT do these)
- Inventing findings to fill a severity bucket when the code is clean.
- Proposing a fix in DEBUG mode without first confirming the root-cause line.
- Silently assuming the language; always state what you detected.
- Applying an `Edit` without being asked — default is to **propose**.
- A sprawling 20-point audit on a trivial 3-line diff. Right-size the effort.
