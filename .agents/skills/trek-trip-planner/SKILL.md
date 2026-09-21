---
name: trek-trip-planner
description: Build, fill in, or script a complete trip plan on a TREK instance through its HTTP API — trips, days, places, day assignments, transports and bookings, packing lists, costs, files, and collaborators. Use whenever the user asks to create or complete a TREK trip/itinerary, add places, days, bookings or expenses to a TREK trip, automate or script TREK instead of clicking through the UI, or asks which TREK route or MCP tool performs some trip-planning operation (TREK 行程、旅行计划、行程规划、添加地点、预订、费用). Also use when a TREK write already failed and you need the correct route, required field, or permission gate.
---

# Building a trip plan in TREK

TREK is a self-hosted travel planner: a NestJS API (`server/src`) plus a React SPA
(`client/src`). This skill is about driving the **API** to build a plan, rather than
clicking the UI.

Prefer the API over the browser. Almost every planning operation is a single HTTP
call, while the same operation in the UI can require drag-and-drop — which is
unreliable to automate. In particular, assigning a place to a day is a drag gesture
in the planner, but a plain `POST` here.

**Evidence markers used throughout:**
- ✅ = executed against a live instance while writing this skill, with the real status code and response body recorded.
- 📖 = read from source, not executed. Cite the file before trusting it.

## 0. Which instance are you operating on?

**Settle this before the first call.** TREK is self-hosted, so more than one store can
be reachable at once and both look like "the" TREK. Picking wrong fails *silently*: the
call returns 200, the write lands somewhere, and nothing tells you it went to the host
you did not mean.

| Role | Base URL | Defined by |
|---|---|---|
| **Live instance** — what the MCP tools and the user's UI actually share | `https://trek.sakyaer.vip` | the `trek` entry in `~/.zcode/cli/config.json` |
| Local dev instance | `http://localhost:9999` | `scripts/run-local.sh [PORT]`, default `9999` |

The binding is a config value, not a fact about this repo — **confirm it instead of
reciting the table**, because it has already been switched once (local → remote, kept
as a timestamped `~/.zcode/cli/config.json.bak-*`):

```bash
grep -o 'https\?://[^"]*' ~/.zcode/cli/config.json | grep -i trek
```

**No file in this working tree describes the live data.** `server/data/travel.db` and
`server/uploads/` belong to the *local dev* instance. Reading them tells you what the
local instance holds; that is never a proxy for what the live instance holds, however
familiar the repo looks — and even when the two contain matching content.

✅ Verified the hard way. `delete_budget_item` (trip 8, items 7 and 8) returned
`{"success":true}` for the live instance while `server/data/travel.db` still listed
both rows and the same 25-item total. The MCP session was bound to
`trek.sakyaer.vip`; the file was the untouched dev copy. Re-issuing the identical
delete then returned `Budget item not found.` — that is what proves the first call
landed on a real store. The two stores held matching trip data (trip 8, 77 places,
14 days, identical `created_at`), so a look-alike copy is the *normal* case here, not
a warning sign.

Corollaries:

- **A write that "did not take" is usually a write that took elsewhere.** When a change
  is missing, check the binding before suspecting the row, the permission, or a cache.
- **Destructive calls need the target confirmed, not assumed.** Deleting from the wrong
  instance leaves you believing the work is done.
- **A restore re-publishes whatever the backup holds.** Restoring a local-made backup
  onto the live instance brings back rows that were deleted live — including private
  or scratch ones. Check a backup's contents before uploading it.

## 1. Access and authentication

Base URL is `$TREK_URL` — the instance you confirmed in §0, not an assumed one.
**Routes have no global prefix** — every path below is literal and served as-is
(`server/src/bootstrap.ts` sets no global prefix).

### Path A — REST, a session JWT (use this for anything the UI can do)

```bash
# 1. log in — returns a JWT and also sets the httpOnly `trek_session` cookie
curl -sS -X POST "$TREK_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"…"}'
# -> 200 {"token":"<jwt>","user":{...}}          📖 auth-public.controller.ts:82-108

# 2. use the JWT as a Bearer token
curl -sS "$TREK_URL/api/trips" -H "Authorization: Bearer $JWT"     # ✅ 200
```

The API accepts **either** the `trek_session` cookie **or**
`Authorization: Bearer <jwt>`; the cookie wins if both are present
(`server/src/nest/auth/jwt-verify.ts:19-25`). A script has no cookie jar, so use the
Bearer form.

Login is rate-limited to 10 attempts / 15 min per IP
(`auth-public.controller.ts:86`). If `require_mfa` is on, login instead returns
`{"mfa_required":true,"mfa_token":"…"}` and you must finish at
`POST /api/auth/mfa/verify-login`.

**The internal `/api/*` routes accept only a session JWT.** The static `trek_…`
tokens are *not* valid there — they are checked by a different guard that rejects
anything not starting with `trek_` and is mounted on `/api/v1`
(`server/src/nest/public-api/api-token.guard.ts:57-77`). And `/api/v1` is
**read-only**: `GET /api/v1/trips`, `/bucket-list`, `/trips/:id`, `/stats`. So an
API key cannot create a trip. Don't reach for one.

### Path B — MCP at `/mcp` (richer tool surface, needs a one-time enable)

TREK ships an MCP server exposing **248 tools** (counted from `tools/list`; the
`README.md` figure of 199 is stale), each calling the same domain service as its REST
route — e.g. `create_trip` → `TripsService.create`, exactly what `POST /api/trips`
calls (`server/src/nest/trips/trips.mcp.ts:120`). It is a StreamableHTTP endpoint at
exactly `/mcp`, with sessions driven by the `Mcp-Session-Id` header
(`server/src/nest/mcp-transport/mcp-transport.service.ts:148-247`).

**Prefer this surface for agent work**, because it has tools the REST API has no
single route for: `create_and_assign_place` (create a place already scheduled on a
day, in one call), `assign_place_to_day`, `move_assignment`,
`reorder_day_assignments`, `create_transport`, `create_transit_journey`.

Two prerequisites, both of which otherwise look like a broken server:

1. **The `mcp` addon is seeded disabled** (`enabled: 0` — `server/src/db/seeds.ts:120`).
   Until an admin turns it on every `/mcp` call is **403** and the OAuth discovery
   endpoints 404 (`mcp-transport.service.ts:162-165`):
   ```bash
   PUT /api/admin/addons/mcp   {"enabled":true}    # 📖 admin.controller.ts:262
   ```
   Tell the two failure modes apart without any credential: addon off ⇒ **403**;
   addon on with a bad token ⇒ **401** carrying
   `WWW-Authenticate: Bearer realm="TREK MCP"`.

2. **A credential — two grants, pick by client type.** A *machine client*
   (`client_credentials`) needs no browser and is the right choice for an agent; a
   *browser client* (`authorization_code`) needs one consent click. TREK's
   `wiki/MCP-Setup.md` claims `mcp-remote` cannot do `client_credentials` — **that is
   out of date**, `mcp-remote` ≥ 0.13 has `--client-credentials` (verified working).
   A static `trek_…` token still works but is **deprecated**, and TREK says so itself:
   the first `list_trips`/`get_trip_summary` in the session returns a deprecation
   notice inside the tool *result* (`STATIC_TOKEN_DEPRECATION_NOTICE`,
   `mcp-transport/mcp-transport.constants.ts:78`), injected only when
   `isStaticToken` is true (`mcp-transport.service.ts:268-272`). Static tokens resolve
   to **full access** (`scopes = null`) but work **only on `/mcp`**, never on `/api/*`.

> **Wiring a real client up is where the time goes — read
> [`references/mcp-client-setup.md`](references/mcp-client-setup.md) first.** It has
> the verified config, and the three traps that cost the most: `allowed_scopes` is a
> hard ceiling (`oauth.service.ts:651`) so a read-only preset can never be talked into
> writing; the requested scope must be pinned with
> `--static-oauth-client-metadata` or the client asks for more than it may have and
> gets a 400; and TREK matches the redirect **path** exactly, so the presets'
> `http://localhost` needs `--callback-path /` to work with `mcp-remote`.

MCP write scopes for plan building: `trips:write` (trip, days, members, guests),
`places:write` (places + day assignments), `reservations:write` (bookings,
transports, accommodations), `budget:write`, `packing:write`; `trips:delete` is
separate (`server/src/mcp/scopes.ts:92-108`). `write` implies that group's reads
(`nest-mcp-policy.ts:29-33`), so don't also request the `:read` pairs.

**The tool list is scoped.** A full-access static-token session listed **248** tools; a
scoped OAuth session listed **247**. Treat the count as a property of the session, not
a constant.

#### Verified MCP handshake

✅ Executed end-to-end. The transport answers as SSE, so extract the `data:` line:

```bash
# 1. initialize — read the session id off the response HEADER
curl -sS -D - -X POST "$TREK_URL/mcp" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"cli","version":"1.0"}}}'
# -> 200 text/event-stream, mcp-session-id: <uuid>
#    serverInfo {"name":"TREK MCP","version":"1.0.0"}

# 2. notifications/initialized — no id, no body, but the session header is required
curl -sS -X POST "$TREK_URL/mcp" -H "Authorization: Bearer $TOKEN" \
  -H "Mcp-Session-Id: $SID" -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3. call a tool
curl -sS -X POST "$TREK_URL/mcp" -H "Authorization: Bearer $TOKEN" \
  -H "Mcp-Session-Id: $SID" -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"create_trip","arguments":{"title":"…","start_date":"2027-03-01","end_date":"2027-03-03"}}}' \
  | sed -n 's/^data: //p'
```

**Read the `instructions` field that `initialize` returns.** TREK sends ~5.5k
characters of authoritative reference — Data model, Key workflows, Access rules,
Dates and times, Add-on features, Behavioral rules. That is the vendor's own
statement of the model: treat it as the first source and this skill as the second.

Tool results are also the one place TREK injects a notice it wants surfaced
(see the deprecation above), because `instructions` is only background context.
Relay such notices to the user rather than silently acting on them.


## 2. Preflight

Run these before building anything; each one has a specific failure it prevents.

```bash
# 1. auth posture (public, no auth needed)
GET /api/auth/app-config        # -> has_users, setup_complete, require_mfa, password_login, demo_mode
                                # 📖 auth-public.controller.ts:38-43
# 2. are you actually authenticated?
GET /api/trips                  # ✅ 200 {"trips":[…]} ; 401 => login failed or no token
# 3. (MCP path only) is the addon on?
GET /api/admin/addons           # ✅ 200 {"addons":[…]} — find id "mcp"; needs enabled truthy
```

`must_change_password` is surfaced in the user payload but **not enforced server-side**
— no guard blocks API calls while it is set (`server/src/nest/auth/auth.helpers.ts:66`).

## 3. The golden path

Every step below was executed against a live instance; the status code and the
top-level response key are the observed values.

```bash
# 1. create the trip — days are generated for you from the date range
POST /api/trips
  {"title":"Australia East Coast Road Trip",
   "start_date":"2026-11-01","end_date":"2026-11-05","currency":"AUD"}
# ✅ 201 {"trip":{…}}
# Give only one of start_date/end_date and the other is inferred as ±6 days
# (shared/src/trip/trip.schema.ts:91-97). end_date < start_date => 400.

# 2. read the generated days to get their ids
GET /api/trips/:tripId/days
# ✅ 200 {"days":[{id,trip_id,day_number,date,notes,title,default_transport_mode,
#                 assignments:[…],notes_items:[…]}, …]}

# 3. add a place to the trip's pool (NOT to a day — see §5)
POST /api/trips/:tripId/places
  {"name":"Bondi Beach","address":"Bondi Beach NSW, Australia",
   "lat":-33.8915,"lng":151.2767}
# ✅ 201 {"place":{…}}       only `name` is required

# 4. put that place on a day — this is what the UI's drag-and-drop does
POST /api/trips/:tripId/days/:dayId/assignments
  {"place_id":<place id>}
# ✅ 201 {"assignment":{…}}   appends at order_index = MAX+1 for that day

# 5. give the stop a time window (assignment-level, not place-level)
PUT /api/trips/:tripId/assignments/:assignmentId/time
  {"place_time":"09:30","end_time":"12:00"}
# ✅ 200 {"assignment":{…}}

# 6. a transport leg — this is a RESERVATION of a transport type, not its own resource
POST /api/trips/:tripId/reservations
  {"title":"SYD -> MEL","type":"flight","day_id":<day id>}
# ✅ 201 {"reservation":{…}}

# 7. a cost
POST /api/trips/:tripId/budget
  {"name":"Flights","total_price":420,"category":"transport"}
# ✅ 201 {"item":{…}}

# 8. a packing item
POST /api/trips/:tripId/packing
  {"name":"Sunscreen","category":"Toiletries"}
# ✅ 201 {"item":{…}}

# 9. a note on a day
POST /api/trips/:tripId/days/:dayId/notes   {"text":"Pick up rental car"}
# ✅ 201 {"note":{…}}

# 10. read the whole plan back in one call
GET /api/trips/:tripId/bundle
# ✅ 200 {"trip","days","places","packingItems","todoItems",
#         "budgetItems","reservations","files","accommodations","members"}
```

`GET /api/trips/:id/bundle` is the cheapest way to verify a plan and the best
starting point for reasoning about one — use it instead of N per-feature GETs.

To tear down a scratch trip: `DELETE /api/trips/:tripId` → ✅ 200 `{"success":…}`.

## 4. Operation catalogue

The full categorised list — every route, its required fields, and the equivalent MCP
tool — is in **[`references/routes.md`](references/routes.md)**. Read it when you
need a route outside the golden path above (day reordering, bulk place edits, booking
imports, budget settlements, packing bags, file links, collaborators, categories).

Categories covered there: trips · days · day notes · places · day assignments ·
accommodations · reservations/bookings · transports · packing lists · to-do ·
costs/budget · files · collaborators & invites · categories.

## 5. The rules that actually bite

Full detail in **[`references/data-model.md`](references/data-model.md)**. The ones
that cause silent wrong results:

- **A place belongs to the trip, not to a day.** `places` has no `day_id` column
  (`server/src/db/schema.ts:124-150`). The place↔day link is a separate
  `day_assignments` row. Creating a place does **not** schedule it.
- **The "unplanned pool" has no flag.** A place is unplanned exactly when it has no
  `day_assignments` row (`server/src/nest/public-api/public-api.service.ts:231-245`).
  There is nothing to set to move a place back to the pool except deleting the
  assignment.
- **Ordering is `order_index` on the assignment**, 0-based, listed
  `ORDER BY order_index ASC, created_at ASC` (`assignments.service.ts:141`). Because
  the move endpoint sets `order_index = order_index ?? 0` without renumbering the
  target day, **duplicate `order_index` values are legitimate** and `created_at`
  breaks the tie. Don't treat `order_index` as unique.
- **Deleting a day does not delete its places.** It cascades `day_assignments` and
  `day_notes` (`ON DELETE CASCADE`) but the places fall back into the pool
  (`days.service.ts:252-254`, `schema.ts:169`). Day numbers are *not* renumbered
  afterwards, so gaps are normal.
- **`PUT /days/reorder` requires the complete id set.** A partial list is a 400
  (`days.service.ts:404-410`) — send every day id, in the order you want.
- **Places use open-record schemas.** Create/update validate only `name` and pass
  unknown keys through (`shared/src/place/place.schema.ts:155`) — under the global
  Zod pipe there is no `forbidNonWhitelisted` (`server/src/nest/app.module.ts:113`).
  A misspelled field name is **silently accepted and ignored**. Verify with a
  read-back; don't assume a 201 means your field landed.
- **Permission gates are per-domain, and `admin` bypasses all of them**
  (`server/src/nest/permissions/permissions.service.ts:173`). Writes need the
  matching trip permission: `day_edit`, `place_edit`, `reservation_edit`,
  `budget_edit`, `packing_edit`, `file_edit`, `member_manage`, `share_manage`. A 403
  on a write usually means the trip role, not the route.
- **`PUT /api/trips/:id` gates per FIELD GROUP, not per route.** `trip_edit` is only
  checked when the body carries one of `title`, `description`, `start_date`,
  `end_date`, `currency`, `reminder_days`, `day_count`; `trip_archive` and
  `trip_cover_upload` are checked separately, for `is_archived` and `cover_image`
  (`trips.controller.ts:135-160`). An empty `{}` body skips every check and returns
  200 — that looks like a permission bypass but is not one. Send the field you are
  actually testing. (This also means you can rename a trip by accident: never fire a
  `PUT` with a speculative body at a trip you care about.)
- **Trip visibility is ownership OR membership.** `GET /api/trips` selects
  `WHERE (t.user_id = :userId OR m.user_id IS NOT NULL)`
  (`trips.service.ts:295-310`), so a trip only appears for someone once they own it or
  are a member. Verified against a live instance: a member sees the owner's trip and
  can do member-level writes, while `trip_edit`, `member_manage` and `trip_delete`
  still return 403.
- **Test permissions with a non-admin account.** Because `admin` passes every check,
  an admin-driven walkthrough proves nothing about the gates. Log in as a plain member
  and re-run — that is the only way the 403s above become visible.

## 6. Traps found the hard way

- **Geocoding dies without server egress.** `POST /api/maps/search` proxies Nominatim
  and returns **500 `{"error":"fetch failed"}`** when the *server process* has no
  outbound network — while the browser may still load map tiles fine, so the UI looks
  half-alive. Symptom in the UI: the "Search places…" box returns nothing forever.
  Fall back to creating places with explicit `name` + `address` + `lat`/`lng`.
- **There is no Transports API.** The `Transports` tab is a client-side filter over
  reservations (`client/src/components/Planner/ReservationsPanel.tsx:171`,
  `client/src/utils/dayMerge.ts:6`). A "transport" is a reservation whose `type` is
  one of `flight, train, bus, car, taxi, bicycle, cruise, ferry, transit,
  transport_other`. Query `GET /api/trips/:id/reservations` and filter, or use the MCP
  `create_transport` tool.
- **Cost categories have no API.** The list is fixed in the client
  (`client/src/components/Budget/costsCategories.tsx:6`). Only per-trip ordering is
  server state.
- **Trip settings have no dedicated route.** Everything — title, dates, currency,
  reminder, archive — goes through `PUT /api/trips/:id`. Archiving is
  `{"is_archived":true}`, and archived trips are listed via `GET /api/trips?archived=1`.
- **Changing trip dates moves day content.** `PUT /api/trips/:id` takes
  `date_shift_mode` (`keep_bookings` | `shift_all`) to decide whether bookings follow
  the shift (`trips.controller.ts:135`).
- **One client route is dead on the server.** `PUT
  /api/trips/:tripId/days/:dayId/assignments/:id` exists in the client
  (`client/src/api/client.ts:483`) but no server controller registers it. Use
  `PUT /api/trips/:tripId/assignments/:id/{time,notes,transport,participants}` or the
  `move`/`reorder` routes instead.

## 7. Rate limiting (read this before blaming the server)

The limits are **hardcoded in the source — there is no config file**. The
HTTP-facing ones all funnel through one service, `RateLimitService.check()`
(`server/src/nest/common/rate-limit.service.ts`), shared by the auth, passkey,
transit, trip-invite and public-api controllers. Each bucket carries its own
15-minute window and a ceiling passed as a literal at every call site.

The trap is the key: `req.ip`. On a local instance the browser, your CLI and any
test script all arrive from `127.0.0.1`, so they **share one attempt budget** —
ceilings meant for strangers end up punishing the single operator.

Worse, several unrelated routes share a bucket literally named `login` with
**different ceilings**:

| Route | Bucket | Ceiling |
|---|---|---|
| `POST /api/auth/login`, register | `login` | 10 |
| `POST /api/auth/mcp-tokens` | `login` | **5** |
| `POST /api/auth/api-tokens` | `login` | **5** |
| `POST /api/auth/forgot-password` | `forgot` | 3 |
| `POST /api/auth/reset-password` | `reset` | 5 |

The OAuth endpoints are separate, and on a **60 s** window rather than 15 min
(`oauth-public.controller.ts:40,158`, `oauth-api.controller.ts:37`):

| Route | Bucket | Key | Ceiling |
|---|---|---|---|
| `POST /oauth/token` | `oauth_token` | `${req.ip}\|${client_id}` | **30 / 60 s** |
| `POST /oauth/revoke` | `oauth_revoke` | `req.ip` | 10 / 60 s |
| `GET /oauth/authorize/validate` | `oauth_validate` | `req.ip` | 30 / 60 s |

⚠️ `oauth_token` is keyed by **IP *and* `client_id`**, so it is not the `login` bucket
and minting a token does not spend login budget. What actually starves is a script that
re-mints per tool call: 30 successful mints in one minute, then a wall of 429s that
clears on its own a minute later. Cache the token instead.

So minting a **static** MCP token (`/api/auth/mcp-tokens`) spends your *login* budget at a
*lower* ceiling — that route, not `/oauth/token`. The only
feedback is a bare `429 {"error":"Too many attempts. Please try again later."}`. A
rejected request does not increment the counter, so polling is safe; the window resets
15 minutes after the **first** attempt in it.

Two ways out, neither of which edits the literals:

- **Restart the server.** The buckets are in-memory and per-process, so a restart
  clears all of them (`server/src/nest/common/rate-limit.module.ts`).
- **`RATE_LIMIT_MAX_OVERRIDE`** raises every ceiling through that one service
  (`app-config/derive.ts`, consumed in `check()`). It is a development escape hatch,
  not a tuning knob — leave it unset in any deployment others can reach, where those
  ceilings are the brute-force protection on the auth routes. Put it in the
  gitignored `server/.env`, never a higher value in tracked source:

  ```
  RATE_LIMIT_MAX_OVERRIDE=999999
  MCP_RATE_LIMIT=999999        # this one is a real knob and already existed
  ```

The server runs built output (`node dist/index.js`), so a source edit or a new env var
needs **a rebuild and a restart** to take effect — `npm run build` inside `server/`,
then restart. `MCP_RATE_LIMIT` (default 300 req/min per user) is the only genuinely
configurable limiter (`app-config/derive.ts:194`, `mcp/index.ts:23-24`).

Verify an override actually took (a restart alone clears the buckets and would fool
you): hit a low-ceiling route past its limit and confirm no 429 —
`POST /api/auth/reset-password` with a bogus token is stateless, harmless, and its
ceiling is 5, so 9 calls prove it.

Other limiters are separate and are safety valves rather than user quotas: the
websocket flood guard (`realtime/trek-ws.adapter.ts`, 10s), backups
(`backup/backup.impl.ts`, 1h), the plugin host and supervisor, collab, place
enrichment, OAuth. Don't raise those to unblock a test — they are not what blocks you.

## 8. Bundled script

`scripts/trek-api.sh` is a thin authenticated `curl` wrapper that removes the login
and header boilerplate. Both its paths are ✅ verified end-to-end against a live
instance.

**It defaults to `TREK_URL=http://localhost:9999` — the local dev instance.** Set
`TREK_URL` to the instance you confirmed in §0 before using it, or you get the worst
split available: the MCP tools writing to the live instance while this script reads and
writes the local one, with both reporting success.

```bash
export TREK_EMAIL=you@example.com TREK_PASSWORD=…      # or TREK_JWT=<jwt>
.agents/skills/trek-trip-planner/scripts/trek-api.sh GET /api/trips
.agents/skills/trek-trip-planner/scripts/trek-api.sh POST /api/trips \
  '{"title":"Iceland","start_date":"2026-10-01","end_date":"2026-10-07"}'
```

Behaviour worth knowing:

- The status line goes to **stderr** and the body to **stdout**, so
  `body=$(trek-api.sh GET /api/trips)` captures only the body.
- It logs in on first use and caches the JWT at
  `${TMPDIR:-/tmp}/trek-jwt.$(id -u)`, mode 0600. Override with `TREK_TOKEN_CACHE`.
- A **401 clears the cache** so the next run logs in again, instead of failing
  forever on a stale token (a password reset bumps `password_version` and invalidates
  every issued JWT).
- Passwords containing control characters aren't supported by its minimal JSON
  escaping — use `TREK_JWT` for those.
- It does **not** retry on 429. If you hit the rate limit, see §7.

If a plan build has more than a handful of steps, don't loop this script — write a
real script that logs in once and reuses the token.

