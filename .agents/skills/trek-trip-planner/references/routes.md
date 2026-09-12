# TREK route catalogue

Every route for building and maintaining a trip plan, grouped by feature. Paths are
literal — there is no global prefix (`server/src/bootstrap.ts` sets none); the
`@Controller('…')` prefix is already baked into each path below.

**Required fields** are marked `req`. Everything else is optional. All routes need a
session JWT (§1 of the skill). `:tripId`, `:dayId`, `:id` etc. name the entity whose
id belongs there — they are **not** interchangeable.

MCP tool names are given where a tool exists; MCP tools call the same domain service
as the REST route.

Legend: ✅ executed against a live instance · 📖 read from source only.

---

## Trips

`@Controller('api/trips')` — `server/src/nest/trips/trips.controller.ts:65`

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips` | list trips; `?archived=1` for archived | — |
| `GET /api/trips/active` | the trip to open on launch | — |
| `GET /api/trips/:id` | one trip | — |
| `POST /api/trips` ✅ | create; generates days from the date range | `title` |
| `PUT /api/trips/:id` | update settings, dates, archive (no separate settings route) | — |
| `POST /api/trips/:id/cover` | upload cover image (multipart field `cover`, ≤20 MB) | `cover` |
| `POST /api/trips/:id/copy` | duplicate (deep-copies days, places, tags, assignments) | — |
| `DELETE /api/trips/:id` ✅ | delete (cascades days, places, notes, assignments) | — |
| `GET /api/trips/:id/bundle` ✅ | everything at once — best verification call | — |
| `GET /api/trips/:id/export.ics` | iCalendar export | — |
| `GET /api/trips/cover-images/search` | Unsplash cover search; `?query=` | — |

`PUT /api/trips/:id` accepts `title`, `description`, `start_date`, `end_date`,
`date_shift_mode` (`keep_bookings`\|`shift_all`), `currency`, `reminder_days`,
`day_count`, `is_archived`, `cover_image` — all optional
(`shared/src/trip/trip.schema.ts:86-103`).

Creating with only one of `start_date`/`end_date` infers the other as ±6 days;
`end_date < start_date` → 400 (`trips.controller.ts:112-118`).

- MCP: `create_trip`, `update_trip`, `list_trips`, `get_trip_summary`, `delete_trip`,
  `copy_trip`, `search_cover_images`, `export_trip_ics`
  (`server/src/nest/trips/trips.mcp.ts`)

## Days

`@Controller('api/trips/:tripId/days')` — `server/src/nest/days/days.controller.ts:28`.
All mutations require `day_edit`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/days` ✅ | list days, each with `assignments` and `notes_items` | — |
| `POST /api/trips/:tripId/days` | create a day; with `position` inserts and re-pins dates | — |
| `PUT /api/trips/:tripId/days/reorder` | reorder all days | `orderedIds` (complete set) |
| `PUT /api/trips/:tripId/days/:dayId` | update day (`notes`, `title`) | — |
| `PUT /api/trips/:tripId/days/:dayId/transport` | default transport mode for the whole day | — |
| `DELETE /api/trips/:tripId/days/:dayId` | delete day; its places return to the pool | — |

There is no `GET /days/:id` — read the list. `PUT /days/reorder` with a partial id
set is a 400 (`days.service.ts:404-410`).

- MCP: `create_day`, `update_day`, `reorder_days`, `delete_day`,
  `set_day_default_transport_mode` (`server/src/nest/days/days.mcp.ts`)

## Day notes

`@Controller('api/trips/:tripId/days/:dayId/notes')` —
`server/src/nest/day-notes/day-notes.controller.ts:30`. Mutations require `day_edit`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/days/:dayId/notes` | list | — |
| `POST /api/trips/:tripId/days/:dayId/notes` ✅ | create | `text` (1–500) |
| `PUT /api/trips/:tripId/days/:dayId/notes/:id` | update | — |
| `DELETE /api/trips/:tripId/days/:dayId/notes/:id` | delete | — |

Optional: `time`, `icon`, `color`, `sort_order`
(`shared/src/day/day.schema.ts:88-106`).

## Places

`@Controller('api/trips/:tripId/places')` — `server/src/nest/places/places.controller.ts:111`.
Mutations require `place_edit` (the rating route deliberately does not).

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/places` | the trip's whole place pool; `?search=`, `?category=`, `?tag=` | — |
| `GET /api/trips/:tripId/places/:id` | one place | — |
| `POST /api/trips/:tripId/places` ✅ | create in the pool (does **not** schedule it) | `name` |
| `PUT /api/trips/:tripId/places/:id` | update; optional `x-base-updated-at` → 409 on stale write | — |
| `DELETE /api/trips/:tripId/places/:id` | delete (cascades its assignments and ratings) | — |
| `POST /api/trips/:tripId/places/bulk-delete` | bulk delete | `ids` |
| `POST /api/trips/:tripId/places/bulk-update` | bulk set category | `ids`, `category_id` (key must be present) |
| `POST /api/trips/:tripId/places/:id/image` | upload image (multipart `image`) | `image` |
| `PUT /api/trips/:tripId/places/:id/rating` | cast a 1–5 star vote; any member may | `rating` |
| `DELETE /api/trips/:tripId/places/:id/rating` | clear your vote | — |
| `POST /api/trips/:tripId/places/import/gpx` | GPX import (multipart `file`) | `file` |
| `POST /api/trips/:tripId/places/import/map` | KML/KMZ import (multipart `file`) | `file` |
| `POST /api/trips/:tripId/places/import/google-list` | import a Google Maps list | `url` |
| `POST /api/trips/:tripId/places/import/naver-list` | import a Naver list | `url` |
| `GET /api/trips/:tripId/places/export.gpx` | export trip as GPX | — |

Commonly used optional fields on create/update: `description`, `lat`, `lng`,
`address`, `category_id`, `price`, `currency`, `place_time`, `end_time`,
`duration_minutes`, `notes`, `image_url`, `website`, `phone`, `transport_mode`,
`route_color`, `route_geometry`, `google_place_id`, `osm_id`, `tags[]`
(`shared/src/place/place.schema.ts:155`).

**These schemas are open records** — unknown keys pass through and are ignored.
A 201 does not prove your field name was right.

- MCP: `create_place`, `create_and_assign_place` (atomic create + schedule),
  `update_place`, `delete_place`, `list_places`, `search_place`, `rate_place`,
  `bulk_delete_places`, `bulk_update_places`, `import_places_from_url`,
  `export_trip_gpx` (`server/src/nest/places/places.mcp.ts`)

**The geocoding search route is not here.** Place-name lookup lives at
`POST /api/maps/search` (`server/src/nest/maps/maps.controller.ts:71`), returns 500
`{"error":"fetch failed"}` when the server has no outbound network, and is a
different module from `places`.

## Day assignments — the place↔day link

This is the resource that schedules a place onto a day. It replaces the planner's
drag-and-drop. Mutations require `day_edit`.

**Day-scoped** — `@Controller('api/trips/:tripId/days/:dayId/assignments')`
(`server/src/nest/assignments/assignments.controller.ts:41`):

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/days/:dayId/assignments` | ordered plan for the day | — |
| `POST /api/trips/:tripId/days/:dayId/assignments` ✅ | schedule a place on this day | `place_id` |
| `PUT /api/trips/:tripId/days/:dayId/assignments/reorder` | reorder within the day | `orderedIds` (assignment ids) |
| `DELETE /api/trips/:tripId/days/:dayId/assignments/:id` | unschedule (returns place to pool) | — |

**Trip-scoped** — `@Controller('api/trips/:tripId/assignments')`
(`assignments.controller.ts:123`). Every `:id` here is an **assignment** id:

| Route | Purpose | Required |
|---|---|---|
| `PUT /api/trips/:tripId/assignments/:id/move` | move to another day | `new_day_id` |
| `PUT /api/trips/:tripId/assignments/:id/time` ✅ | set `place_time` / `end_time` | — |
| `PUT /api/trips/:tripId/assignments/:id/notes` | day-specific note (`null` clears) | `notes` |
| `PUT /api/trips/:tripId/assignments/:id/transport` | leg mode; `direction` = `outgoing`\|`incoming` | — |
| `GET /api/trips/:tripId/assignments/:id/participants` | who is on this stop | — |
| `PUT /api/trips/:tripId/assignments/:id/participants` | set participants | `user_ids` |

- MCP: `assign_place_to_day`, `create_and_assign_place`, `unassign_place`,
  `move_assignment`, `reorder_day_assignments`, `update_assignment_time`,
  `update_assignment_notes`, `set_leg_transport_mode`,
  `get_assignment_participants`, `set_assignment_participants`
  (`server/src/nest/assignments/assignments.mcp.ts`)

## Accommodations

`@Controller('api/trips/:tripId/accommodations')` —
`server/src/nest/accommodations/accommodations.controller.ts:41`. Mutations require
`day_edit` (not `reservation_edit`).

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/accommodations` | list | — |
| `POST /api/trips/:tripId/accommodations` | create | `place_id`, `start_day_id`, `end_day_id` |
| `PUT /api/trips/:tripId/accommodations/:id` | update; refs re-validated | — |
| `DELETE /api/trips/:tripId/accommodations/:id` | delete (cascades linked reservations and budget items) | — |

Optional: `check_in`, `check_in_end`, `check_out`, `confirmation`, `notes`.

- MCP: `create_accommodation`, `create_place_accommodation`,
  `update_accommodation`, `delete_accommodation`

## Reservations — bookings **and** transports

`@Controller('api/trips/:tripId/reservations')` —
`server/src/nest/reservations/reservations.controller.ts:43`. Mutations require
`reservation_edit`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/reservations` | list — **this is where transports live** | — |
| `POST /api/trips/:tripId/reservations` ✅ | create a booking or transport leg | `title` |
| `PUT /api/trips/:tripId/reservations/:id` | update | — |
| `PUT /api/trips/:tripId/reservations/positions` | reorder day positions | `positions` |
| `PUT /api/trips/:tripId/reservations/:id/travelers` | assign travellers | `user_ids` |
| `DELETE /api/trips/:tripId/reservations/:id` | delete (cascades linked accommodation + budget item) | — |
| `GET /api/reservations/upcoming` | cross-trip upcoming feed (dashboard) | — |

Optional create fields include `type`, `url`, `day_id`, `end_day_id`, `place_id`,
`assignment_id`, `accommodation_id`, `reservation_time`, `reservation_end_time`,
`location`, `confirmation_number`, `notes`, `status`, `metadata`, `endpoints[]`, plus
two conveniences worth knowing:

- `create_accommodation` `{place_id, start_day_id, end_day_id, …}` — creating a
  `type:'hotel'` reservation this way also inserts the accommodation row.
- `create_budget_entry` `{total_price, category}` — likewise creates the linked
  expense.

Both are documented at `shared/src/reservation/reservation.schema.ts:225-234` and
implemented at `reservations.service.ts:567-577` and `:866-874`.

Transport types (`server/src/nest/reservations/reservations.mcp.ts:22`): `flight,
train, bus, car, taxi, bicycle, cruise, ferry, transit, transport_other`. A transport
carries one flat `place_id` plus an `endpoints[]` array with roles `from|to|stop` and
`dep_day_id`/`arr_day_id` per leg (`shared/src/reservation/reservation.schema.ts:96-124`).

Import — `@Controller('api/trips/:tripId/reservations/import')`
(`server/src/nest/reservation-import/reservation-import.controller.ts:55`), guarded by
`AddonGuard`; the booking-file parser accepts `.eml .pdf .pkpass .html .htm .txt`:

| Route | Purpose | Required |
|---|---|---|
| `POST …/import/booking` | parse booking files → preview (multipart `files`, ≤5) | `files` |
| `POST …/import/booking/async` | same, returns a `jobId` | `files` |
| `GET …/import/jobs/:jobId` | poll the import job | — |
| `POST …/import/booking/confirm` | persist the confirmed items | `items` |
| `POST …/import/airtrail` | AirTrail flights (needs the addon) | `flightIds` |

- MCP: `create_reservation`, `create_transport`, `update_reservation`,
  `update_transport`, `delete_reservation`, `set_reservation_travelers`,
  `reorder_reservations`, `link_hotel_accommodation`, `list_upcoming_reservations`,
  and `create_transit_journey` for scheduled public transit
  (`server/src/nest/transit/transit.mcp.ts:159-172`)

## Packing lists

`@Controller('api/trips/:tripId/packing')` —
`server/src/nest/packing/packing.controller.ts:55`. Mutations require `packing_edit`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/packing` | list (viewer-scoped private items) | — |
| `POST /api/trips/:tripId/packing` ✅ | create item | `name` |
| `PUT /api/trips/:tripId/packing/:id` | update (`x-base-updated-at` → 409) | — |
| `POST /api/trips/:tripId/packing/import` | bulk import | `items` |
| `PUT /api/trips/:tripId/packing/reorder` | reorder items | `orderedIds` |
| `DELETE /api/trips/:tripId/packing/:id` | delete | — |
| `PUT /api/trips/:tripId/packing/:id/sharing` | sharing; owner only | `visibility` |
| `POST /api/trips/:tripId/packing/:id/clone` | clone | — |
| `POST/DELETE /api/trips/:tripId/packing/:id/contributors[/:userId]` | contributors | — |
| `GET/POST /api/trips/:tripId/packing/bags` | list / create bag | `name` |
| `PUT/DELETE /api/trips/:tripId/packing/bags/:bagId` | update / delete bag | — |
| `PUT /api/trips/:tripId/packing/bags/:bagId/members` | bag members | `user_ids` |
| `GET /api/trips/:tripId/packing/templates` | list templates | — |
| `POST /api/trips/:tripId/packing/apply-template/:templateId` | apply a template | — |
| `POST /api/trips/:tripId/packing/save-as-template` | **admin only** | `name` |
| `GET/PUT /api/trips/:tripId/packing/category-assignees[/:categoryName]` | per-category assignees | `user_ids` |

Admin templates live under a separate controller,
`api/admin/packing-templates` (`server/src/nest/packing/admin-packing-templates.controller.ts:33`),
guarded by `JwtAuthGuard, AdminGuard`: CRUD on templates, their categories, and their
items.

Item fields: `category`, `checked`, `weight_grams`, `bag_id`, `quantity`,
`is_private`, `visibility`, `recipient_ids`.

- MCP: `create_packing_item`, `toggle_packing_item`, `update_packing_item`,
  `delete_packing_item`, bags, `apply_packing_template`, `bulk_import_packing`,
  sharing and category assignees (`server/src/nest/packing/packing.mcp.ts`)

## To-do (the Lists tab's second sub-tab)

`@Controller('api/trips/:tripId/todo')` — `server/src/nest/todo/todo.controller.ts:31`.
Mutations require **`packing_edit`** (not a `todo_edit`).

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/todo` | list | — |
| `POST /api/trips/:tripId/todo` | create | `name` |
| `PUT /api/trips/:tripId/todo/reorder` | reorder | `orderedIds` |
| `PUT /api/trips/:tripId/todo/:id` | update | — |
| `DELETE /api/trips/:tripId/todo/:id` | delete | — |
| `GET/PUT /api/trips/:tripId/todo/category-assignees[/:categoryName]` | assignees | `user_ids` |

Optional: `category`, `due_date`, `description`, `assigned_user_id`, `priority`.

## Costs / Budget

`@Controller('api/trips/:tripId/budget')` — `server/src/nest/budget/budget.controller.ts:49`.
Mutations require `budget_edit`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/budget` | list items | — |
| `POST /api/trips/:tripId/budget` ✅ | create expense | `name` |
| `PUT /api/trips/:tripId/budget/:id` | update; `total_price` writes back to a linked reservation | — |
| `DELETE /api/trips/:tripId/budget/:id` | delete | — |
| `PUT /api/trips/:tripId/budget/:id/members` | split participants | `user_ids` |
| `PUT /api/trips/:tripId/budget/:id/payers` | set payers | `payers` |
| `PUT /api/trips/:tripId/budget/:id/members/:userId/paid` | toggle paid | `paid` |
| `PUT /api/trips/:tripId/budget/reorder/items` | reorder | `orderedIds` |
| `PUT /api/trips/:tripId/budget/reorder/categories` | reorder categories | `orderedCategories` |
| `GET /api/trips/:tripId/budget/summary/per-person` | per-person totals | — |
| `GET /api/trips/:tripId/budget/settlement` | computed settle-up; `?base=` | — |
| `GET/POST /api/trips/:tripId/budget/settlements` | list / record a settlement | `from_user_id`, `to_user_id`, `amount` |
| `PUT/DELETE /api/trips/:tripId/budget/settlements/:settlementId` | edit / undo | — |

Expense fields: `category`, `total_price`, `currency`, `exchange_rate`, `payers[]`,
`member_ids[]`, `members[]`, `persons`, `days`, `note`, `expense_date`,
`reservation_id`, `place_id` (`shared/src/budget/budget.schema.ts:143-166`).
An expense links to a **place or reservation, never a day**; `persons`/`days` are
counts, not ids.

- MCP: `create_budget_item`, `create_budget_item_with_members`,
  `set_budget_item_members`, `toggle_budget_member_paid`, `get_settlement_summary`,
  `list/create/update/delete_settlement` (`server/src/nest/budget/budget.mcp.ts`)

## Files

`@Controller('api/trips/:tripId/files')` — `server/src/nest/files/files.controller.ts:73`.
Rights: `file_upload`, `file_edit`, `file_delete`.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/trips/:tripId/files` | list; `?trash=true` for the bin | — |
| `POST /api/trips/:tripId/files` | upload (multipart `file`; ≤50 MB, ≤500 MB video) | `file` |
| `PUT /api/trips/:tripId/files/:id` | update metadata / targets | — |
| `PATCH /api/trips/:tripId/files/:id/star` | toggle star | — |
| `DELETE /api/trips/:tripId/files/:id` | soft delete | — |
| `POST /api/trips/:tripId/files/:id/restore` | restore | — |
| `DELETE /api/trips/:tripId/files/:id/permanent` | hard delete | — |
| `DELETE /api/trips/:tripId/files/trash/empty` | empty the bin | — |
| `GET /api/trips/:tripId/files/:id/links` | list links | — |
| `POST /api/trips/:tripId/files/:id/link` | add a link | — |
| `DELETE /api/trips/:tripId/files/:id/link/:linkId` | drop a link | — |
| `GET /api/trips/:tripId/files/:id/download` | download (`@Public`; cookie, Bearer, or `?token=`) | — |

A file attaches to a **place** and/or a **reservation** on upload/update; extra links
to a reservation, assignment, or place go through the link table. **There is no day
target** (`shared/src/file/file.schema.ts:21-40`). Foreign ids must belong to the same
trip or it is a 400. Demo-mode accounts get a 403 on upload.

## Collaborators and invites

`@Controller('api/trips')` — `server/src/nest/trip-members/trip-members.controller.ts:44`.
Note the param is `:id`, not `:tripId`.

| Route | Purpose | Gate |
|---|---|---|
| `GET /api/trips/:id/members` | owner, members, current user | trip access |
| `POST /api/trips/:id/members` | add by `identifier` (username or email) | `member_manage` |
| `DELETE /api/trips/:id/members/:userId` | remove (self-removal always allowed) | `member_manage` for others |
| `POST /api/trips/:id/transfer` | transfer ownership | owner only |
| `POST /api/trips/:id/guests` | create a guest (`name`, 1–50) | owner only |
| `PUT/DELETE /api/trips/:id/guests/:userId` | rename / remove guest | owner only |

Invite links — `server/src/nest/trip-invite/trip-invite.controller.ts`:

| Route | Purpose | Gate |
|---|---|---|
| `GET/POST/DELETE /api/trips/:tripId/invite-link` | read / create / revoke | `share_manage` |
| `GET /api/trip-invites/:token` | inspect an invite | rate-limited 30/15 min |
| `POST /api/trip-invites/:token/accept` | accept | rate-limited 20/15 min |

There is **no per-trip permission API.** Permission levels are global admin settings
(`GET/PUT /api/admin/permissions`, `server/src/nest/admin/admin.controller.ts:121-124`).
Transfer and guest management bypass the permission matrix entirely and require literal
ownership (`server/src/nest/permissions/trip-owner.guard.ts:37-41`).

## Categories (place palette)

`@Controller('api/categories')` — `server/src/nest/categories/categories.controller.ts:25`.
Writes are **admin only**.

| Route | Purpose | Required |
|---|---|---|
| `GET /api/categories` | list the palette | — |
| `POST /api/categories` | create | `name` |
| `PUT /api/categories/:id` | update (`name`, `color`, `icon`) | — |
| `DELETE /api/categories/:id` | delete | — |

Distinct from **cost** categories, which have no API at all (see the skill's traps).

## Collab tab

`@Controller('api/trips/:tripId/collab')` — `server/src/nest/collab/collab.controller.ts:68`.
Notes, polls, and chat; writes need `collab_edit`, note-file upload needs `file_upload`.

- Notes: `GET/POST notes`, `PUT/DELETE notes/:id`, `POST notes/:id/files`,
  `DELETE notes/:id/files/:fileId`
- Polls: `GET/POST polls`, `POST polls/:id/vote`, `PUT polls/:id/close`, `DELETE polls/:id`
- Messages: `GET/POST messages`, `POST messages/:id/react`, `DELETE messages/:id`
- `GET link-preview?url=` — `url` required

Bodies: `shared/src/collab/collab.schema.ts:14-59`. Member management is *not* here —
it is the Collaborators section above.

## Not available over HTTP

Things a caller may go looking for, that have no endpoint:

| Wanted | Reality |
|---|---|
| Transports tab | Filtered reservations. No `transports` module. |
| Cost categories | Fixed client list (`client/src/components/Budget/costsCategories.tsx:6`). |
| Trip settings | Folded into `PUT /api/trips/:id`. |
| Per-trip permissions | Only global admin settings. |
| Day-scoped file attachment | Files link to place / reservation / assignment, never a day. |
| `assignment=unassigned\|assigned` place filter | Implemented in `places.service.ts:188-194` but exposed by no controller. |
| Transports via `/api/v1` | `/api/v1` is read-only and rejects session JWTs. |
