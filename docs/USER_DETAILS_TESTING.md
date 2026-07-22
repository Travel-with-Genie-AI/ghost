# User Details API — Testing Guide

How to manually test the two new self-service profile endpoints:
`update_mobile_number` and `get_user_details`. Mirrors the Bruno
collection at `bruno/User Details/`.

Both endpoints live in `ghost/api/user_details.py` — a standalone new
file. Nothing in `auth.py`, `ghost.py`, or `otp.py` was touched to add
these; the existing login/conversion/OTP flows are unaffected.

## Prerequisites

1. Local dev server running: `bench start` (default `http://localhost:8000`).
2. A valid OAuth access token for the user you want to test as — get one
   via `bruno/Direct Auth/Login.bru` (or `ghost.api.auth.login`), which
   returns `access_token` in its response.

```bash
export BASE_URL="http://localhost:8000"
export ACCESS_TOKEN="<paste access_token from login>"
```

## 1. Update Mobile Number — `update_mobile_number`

**Bruno file:** `User Details/Update Mobile Number.bru`

Sets/updates the logged-in caller's own `mobile_no`. Self-only — always
acts on the authenticated session's own user.

```bash
curl -X POST "$BASE_URL/api/method/ghost.api.user_details.update_mobile_number" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mobile_no": "+911234567890"}'
```

**Required:** `mobile_no`.

**Expect:** `{"success": true, "user", "mobile_no"}`

Rejects with a `ValidationError` if the number is already associated
with a **different** user account — try setting the same number as two
different logged-in users to confirm the second one fails.

## 2. Get User Details — `get_user_details`

**Bruno file:** `User Details/Get User Details.bru`

Returns the logged-in caller's own profile. No params — always self.

```bash
curl "$BASE_URL/api/method/ghost.api.user_details.get_user_details" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expect:** `{"success": true, "name", "email", "mobile_no", "first_name", "last_name", "full_name", "user_image"}`

Run Step 1 first (as the same user) to see a non-null `mobile_no` here.

## Common gotchas

- Both endpoints reject **Guest** outright — a missing/invalid
  `Authorization` header throws an `AuthenticationError`.
- Both are **self-only** — there's no user-id parameter on either
  endpoint. Testing "does user A see user B's data" means logging in as
  two different users (two different access tokens) and confirming each
  only ever sees/affects their own record.
- `update_mobile_number`'s uniqueness check mirrors the same lookup
  `ghost.api.auth.login` already relies on for phone-based login — a
  duplicate number would otherwise make phone login ambiguous between
  two accounts.
- Ghost users (`frappe.session.user` starting with `ghost_`) are allowed
  to use both endpoints — a ghost session is still a real `User` record,
  and any `mobile_no` set before conversion carries over normally via
  `convert_to_real_user`'s existing rename/migration logic.
