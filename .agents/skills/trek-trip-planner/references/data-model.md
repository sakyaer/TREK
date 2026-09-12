# TREK data model, as it affects writing data

Read this before a multi-step build. Each rule here has bitten at least one
implementation, and most of them fail silently rather than erroring.

Schema: `server/src/db/schema.ts` (base) plus `server/src/db/migrations.ts` (every
later `ALTER TABLE`). FK enforcement is on: `PRAGMA foreign_keys = ON`
(`server/src/db/database.ts:47`).

## Shape of a plan

```
trip
├── days                     day_number (1-based, UNIQUE(trip_id, day_number))
│   ├── day_assignments ──►  place          the schedule; ordering lives HERE
│   ├── day_notes
│   └── day_accommodations ──► place
├── places                   the pool; belongs to the trip, never to a day
├── reservations             bookings AND transports
├── budget_items             expenses
├── packing_items / bags / todo_items
└── files                    attach to place / reservation / assignment
```

## The place ↔ day relationship

The single most important thing to get right:

- `places.trip_id` is `NOT NULL`; there is **no `day_id` column on `places`**
  (`schema.ts:124-150`; no migration adds one either).
- The link is a `day_assignments` row: `day_id NOT NULL`, `place_id NOT NULL`,
  ordering column `order_index INTEGER DEFAULT 0` (`schema.ts:167-177`).
- **No UNIQUE constraint** on `(day_id, place_id)` — the same place may legitimately
  appear on several days.
- **The "unplanned pool" is the absence of an assignment row.** There is no boolean
  or status field. The server's own definition also excludes places referenced by
  `day_accommodations` (`public-api.service.ts:231-245`); the client derives it the
  same way (`client/src/utils/plannedPlaces.ts:8-15`).
- So: to schedule a place, `POST` an assignment; to unschedule, `DELETE` that
  assignment. Creating or updating a place never changes its schedule.

## Ordering

- Within a day: `ORDER BY da.order_index ASC, da.created_at ASC`
  (`assignments.service.ts:141`).
- Creating an assignment **appends**: `order_index = MAX(order_index) + 1` for that
  day, `0` for an empty day — i.e. **0-based** (`assignments.service.ts:163-175`).
- Reorder writes `order_index = arrayIndex`, scoped `WHERE id = ? AND day_id = ?`, so
  ids belonging to another day are **silently ignored** (`assignments.service.ts:188-195`).
- `move` writes `day_id = new_day_id, order_index = order_index ?? 0` and does **not
  renumber the target day** (`assignments.service.ts:205-214`). Consequence:
  **duplicate `order_index` values inside one day are normal**, and `created_at`
  decides the order. Never assume `order_index` is unique, and never use it as a key.
- Days: ordering is `day_number` (1-based, `UNIQUE(trip_id, day_number)`).
  `PUT /days/reorder` rewrites `day_number` only, keeping rows stable so assignments
  and notes ride along — which is why it must receive the **complete** id set; a
  partial set raises `DayReorderError` → 400 (`days.service.ts:256-267,404-410`).

## Cascades — what deleting takes with it

| Delete | Effect |
|---|---|
| day | cascades its `day_assignments`, `day_notes`, `day_accommodations`. **Places survive** and return to the pool. `reservations.day_id` is `ON DELETE SET NULL`, so bookings survive unassigned. Day numbers are **not** renumbered — gaps stay. |
| place | cascades its `day_assignments`, `place_ratings`, `place_tags`. |
| trip | cascades days, places, notes, assignments. |
| reservation | cascades its linked accommodation and its linked budget item. |
| accommodation | cascades linked reservations and budget items. |

Evidence: `days.service.ts:252-254`, `schema.ts:83,99,126,153-170,219,246,484-485`.

The practical trap: **deleting a day is not a way to delete its places.** If you want
them gone, delete the places explicitly (or `bulk-delete`).

## Validation

- Global pipe is `ZodValidationPipe` (`server/src/nest/app.module.ts:113`, impl
  `server/src/nest/common/zod-validation.pipe.ts:33`). It calls Zod `parse`, so:
  **no `whitelist`, no `forbidNonWhitelisted`.**
- For ordinary object schemas, unknown keys are **stripped**. For places, create and
  update use an **open record** (`z.record(...).and(z.object({name}))`,
  `shared/src/place/place.schema.ts:155,158`) — unknown keys **pass through**.
- Therefore a misspelled field name is accepted with a 201 and simply ignored.
  **Read back and verify** anything load-bearing; a success status is not proof.
- Failures are HTTP 400 with `{ error: "field: message; …" }`.

Extra hand-written guards on places, outside the DTO
(`places.controller.ts:46-85`): string length caps, a hex check on `route_color`, URL
checks on `image_url`/`website`.

## Optimistic concurrency

`PUT` on places, packing items, and budget items accepts an optional
`x-base-updated-at` header. If the row moved on since that timestamp the write is
rejected with **409 `{"error":"conflict","server":{…}}`**. Omit the header and you get
last-write-wins.

## Idempotency

Write requests may carry `X-Idempotency-Key`; it is applied by a global interceptor
(`server/src/nest/common/idempotency.interceptor.ts`, wired at `app.module.ts:102`)
and is **optional**. The SPA sends it on writes
(`client/src/api/client.ts:609`).

## Permissions

- `GlobalAuthGuard` is registered as `APP_GUARD` and is **default-deny**
  (`app.module.ts:84`, `server/src/nest/auth/global-auth.guard.ts:9`); `@Public()`
  opts out.
- Trip-scoped writes name a permission via `@RequirePermission`, checked by
  `checkPermission` (`server/src/nest/permissions/permissions.service.ts:165-189`).
- **`role === 'admin'` passes every check** (`permissions.service.ts:173`). An admin
  will therefore never see a permission 403, which makes this class of bug invisible
  until a non-admin runs the same script — test with a member account when the plan
  depends on permissions.
- Levels are global settings, changed via `GET/PUT /api/admin/permissions`; there is
  no per-trip override API.
- Ownership-only routes deliberately bypass the matrix: trip transfer and guest CRUD
  (`server/src/nest/permissions/trip-owner.guard.ts:37-41`).

Permissions seen on planning routes: `day_edit` (days, notes, assignments,
accommodations), `place_edit` (places), `reservation_edit` (reservations, imports),
`budget_edit`, `packing_edit` (packing **and** to-do), `file_upload`/`file_edit`/
`file_delete`, `member_manage`, `share_manage`.

## Dates

- `POST /api/trips` with only one of `start_date`/`end_date` infers the other as
  ±6 days (`shared/src/trip/trip.schema.ts:91-97`); `end_date < start_date` → 400.
- The date range generates the days, so create the trip before adding days.
- Changing dates later goes through `PUT /api/trips/:id` with `date_shift_mode`
  (`keep_bookings` | `shift_all`) deciding whether bookings follow the shift.
