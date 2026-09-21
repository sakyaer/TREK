# Connecting an MCP client to TREK

Getting an MCP client to authenticate against TREK is where most of the time goes.
This is the verified field guide — every command below was executed, and the failure
table is drawn from failures actually hit, not imagined ones.

**The URL in every example below is a placeholder, not a target.** `localhost:9999` is
the local dev instance; the live one is a different host, and which of them your client
is bound to decides which store your writes reach — settle that first, per §0 of the
skill, because getting it wrong is silent. Two consequences that follow from the host
choice:

- A remote instance must be reached over **`https`** — `mcp-remote` refuses to send a
  client secret to a non-HTTPS token endpoint, with `localhost` / `127.0.0.1` the only
  exemptions (§7). That is why the live binding is an `https://…` origin.
- `--callback-path /` and the redirect-path traps below are `localhost`-specific; they
  do not carry over to a remote host.

## 1. Pick the auth method for the client you have

| Client capability | Method | Works with `mcp-remote`? |
|---|---|---|
| Can call `/oauth/token` itself | **Machine client** (`client_credentials`) | Yes, with `--client-credentials` |
| Can open a browser once | **OAuth 2.1 browser client** (`authorization_code`) | Yes, natively |
| Can only send a static header | Static token (deprecated) | Yes, via `--header` |

TREK's own `wiki/MCP-Setup.md` says `mcp-remote` "implements the browser-based
`authorization_code` flow only — it does not support `client_credentials`". **That is
out of date.** `mcp-remote` ≥ 0.13 has `--client-credentials`:

```js
const useClientCredentials = args.includes("--client-credentials");
if (useClientCredentials) log("Using the OAuth client_credentials grant; no browser will be opened…");
grantTypes() { if (this.useClientCredentials) return ["client_credentials"]; … }
```

So a machine client **is** usable with `mcp-remote`, and it is the better choice for an
agent: no browser, no consent step, no refresh-token rotation.

## 2. Know which kind of OAuth client you have

Read it, don't guess — the Settings UI wording is easy to misread:

```sql
SELECT name, created_via, redirect_uris, allowed_scopes, is_public, allows_client_credentials
FROM oauth_clients WHERE client_id = '<id>';
```

| | Browser client | Machine client |
|---|---|---|
| `redirect_uris` | non-empty (e.g. `["http://localhost"]`) | **`[]`** |
| `allows_client_credentials` | `0` | **`1`** |
| Grant it can use | `authorization_code` | `client_credentials` |

A machine client has **no redirect URI at all** — the field disappears in the UI when
you tick "Machine client (no browser login)". If your client has an empty
`redirect_uris`, it cannot do the browser flow, and passing it to a browser-only client
setup fails at authorization.

### Client presets and their scopes

Presets live in `client/src/components/Settings/IntegrationsTab.tsx`; the scope sets in
`client/src/api/oauthScopes.ts`:

```js
PRESET_SCOPES_DEFAULT  = ALL_SCOPES.filter(s => !s.includes(':delete') && !PRESET_OPT_IN_ONLY.has(s))
PRESET_SCOPES_READONLY = ALL_SCOPES.filter(s => s.endsWith(':read') && !PRESET_OPT_IN_ONLY.has(s))
```

| Preset | Redirect URI | Scopes |
|---|---|---|
| claude-web | `https://claude.ai/api/mcp/auth_callback` | DEFAULT |
| claude-desktop, cursor, windsurf, zed | `http://localhost` | DEFAULT (**has writes**) |
| vscode | `http://localhost` | **READONLY** |

**The VS Code preset is the trap**: it is the only read-only one. Pick it by reflex and
you get a client that connects, reads trips, and silently cannot create anything.

## 3. Scope rules that will bite

- **`allowed_scopes` is a hard ceiling, not a default.** The consent step intersects
  what it asks for with what the client allows:
  `oauth.service.ts:651` — `requestedScopes.filter(s => allowedScopes.includes(s))`.
  A consent screen can therefore never grant more than the client already has. No
  checkbox can add a write to a read-only client.
- **`scopes_supported` ≠ `allowed_scopes`.** Discovery advertises 35 scopes; a
  DEFAULT-preset client allows 33 (it excludes `:delete` and opt-in scopes like
  `plugins:use`). A client that asks for the advertised set gets:
  ```
  400 {"error":"invalid_scope","error_description":"Scopes not allowed for this client: trips:delete, plugins:use"}
  ```
- **`write` implies that group's reads.** The policy is `read ⇒ group:read OR
  group:write` (`server/src/mcp/nest-mcp-policy.ts:29-33`), so requesting
  `places:write` is enough to list places too. Don't request the `:read` pair as well
  unless you want it.
- **There is no update route for a client.** Only `POST /api/oauth/clients`,
  `POST /api/oauth/clients/:id/rotate` and `DELETE /api/oauth/clients/:id`. To change
  scopes or the redirect URI, recreate the client (max 10 per user).
- **The tool list is scoped.** A full-access static-token session listed **248** tools;
  a scoped OAuth session listed **247**. Don't treat the tool count as a constant —
  it reflects what that session may call.

## 4. Verified recipes

### A. `mcp-remote` + machine client (no browser) — the one that works for agents

```json
{
  "mcpServers": {
    "trek": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:9999/mcp",
        "--static-oauth-client-info",
        "{\"client_id\": \"<id>\", \"client_secret\": \"<trekcs_…>\"}",
        "--client-credentials",
        "--static-oauth-client-metadata",
        "{\"scope\": \"trips:write places:write reservations:write budget:write packing:write\"}"
      ]
    }
  }
}
```

Three flags are load-bearing:

- `-y` — without it `npx` prints "Ok to proceed?" on first run, and a stdio server has
  no terminal to answer, so the connection just hangs.
- `--client-credentials` — selects the grant. Without it `mcp-remote` attempts the
  browser flow and fails, because a machine client has no redirect URI.
- `--static-oauth-client-metadata '{"scope": …}'` — **pins the requested scope.**
  Without it, `mcp-remote`'s `requestedScope()` falls through to the protected
  resource's `scopes_supported` (all 35) and TREK answers 400. This is the single
  least obvious requirement in the whole setup.

Verified result: `initialize` → `TREK MCP 1.0.0`, `tools/list` → 247 tools,
`create_trip` → created a trip. The token is a `trekoa_…` bearer, valid 1 hour;
`mcp-remote` renews it silently.

### B. `mcp-remote` + browser client (needs one consent click)

Same as A minus `--client-credentials`, **plus** the path fix below. `mcp-remote`
opens a browser for consent on first connect, so give the client a longer startup
timeout (30s default is not enough for a human to finish).

### C. Static token (deprecated)

```json
{"command": "npx", "args": ["-y", "mcp-remote", "http://localhost:9999/mcp",
 "--header", "Authorization: Bearer trek_…"]}
```

Full access, no scopes. TREK injects a deprecation notice into the result of the first
`list_trips`/`get_trip_summary` in the session — see §5.

## 5. Trap: the redirect path must match exactly

TREK compares redirect URIs **byte-exactly except for the port**
(`server/src/nest/oauth/oauth.helpers.ts:126-147`, RFC 8252 §7.3 — `a.pathname ===
r.pathname`). But `mcp-remote`'s default callback path is `/oauth/callback`
(`DEFAULT_CALLBACK_PATH`), while every loopback preset registers a bare
`http://localhost`.

Measured against a live instance:

| `redirect_uri` sent | Result |
|---|---|
| `http://localhost:45321/oauth/callback` | **400 `Unregistered redirect_uri`** |
| `http://localhost:45321/` | 302 → consent ✓ |
| `http://localhost` | 302 → consent ✓ |

Two ways out, pick one and be consistent:

- Add `--callback-path /` to `mcp-remote` (its parser accepts `/`; only
  `/wait-for-auth` is reserved).
- Or register `http://localhost/oauth/callback` on the client and add nothing.

Mixing them breaks it: the flag is wrong once the client registers the full path.

So **TREK's `wiki/MCP-Setup.md` documents a combination that cannot complete** — it
pairs the `http://localhost` presets with `mcp-remote`, without mentioning
`--callback-path`. Worth reporting upstream.

## 6. ZCode-specific notes

- Servers go in `~/.zcode/cli/config.json` under **`mcp.servers`** (nested). The
  top-level `mcpServers` shape belongs in `~/.agents/mcp.json`, the same-scope
  fallback — and that fallback is ignored entirely once `.zcode` defines any MCP
  server. Pasting a `{"mcpServers": …}` snippet into the `.zcode` file is silently
  dropped.
- The server schema is **strict**: an unknown key drops the whole server.
- Canonical fields: `type` (`stdio`|`http`|`sse`), `command`, `args[]`, `env`,
  `headers`, `timeoutMs`, `enabled`.
- Restart the session after editing, then check **Settings → MCP**.
- To see a stdio server's real error, run its `command` + `args` in a terminal — the
  client only surfaces a truncated status line.

## 7. Failure → cause

| Symptom | Cause |
|---|---|
| `Scopes not allowed for this client: …` on the token request | Client asks for the advertised `scopes_supported`; pin it with `--static-oauth-client-metadata`. |
| `unauthorized_client … not authorized for the client_credentials grant` | Doing `client_credentials` against a browser client (`allows_client_credentials=0`). |
| `400 Unregistered redirect_uri` | Path mismatch — see §5. |
| Connects, reads work, every write fails | Read-only preset (`PRESET_SCOPES_READONLY`). Recreate with a DEFAULT preset. |
| `403` on every `/mcp` call | The `mcp` addon is disabled (`server/src/db/seeds.ts:120`). |
| `401` with `WWW-Authenticate: Bearer realm="TREK MCP"` | Addon is on; the credential is missing or bad. |
| Hangs on first run, no output | `npx` waiting on its install prompt — add `-y`. |
| `spawn npx ENOENT` | The client's `PATH` lacks npx (a GUI app often gets a minimal `PATH`). Use an absolute path such as `/opt/homebrew/bin/npx`. |
| `Refusing to send the client secret … needs an https token endpoint` | Always `https`, except `localhost` / `127.0.0.1`, which are exempt. |
| Worked, then died an hour later | A static bearer token was pasted into `headers`; machine-client tokens last 3600s. Let the client renew them. |
| `429 Too Many Requests` on `/oauth/token` mid-run | You re-mint per request. `/oauth/token` has **its own bucket** — `oauth_token`, **30 per 60 s**, keyed `${req.ip}\|${client_id}` (`oauth-public.controller.ts:40`), not the `login` bucket. Mint once, cache the `trekoa_…` for its `expires_in` (3600s), reuse it for every tool call. |

## 8. Verify before blaming the client

Two checks that separate "TREK is fine" from "the client is misconfigured":

```bash
# addon on? 401 (on) vs 403 (off)
curl -sS -o /dev/null -w '%{http_code}\n' -X POST http://localhost:9999/mcp \
  -H 'Content-Type: application/json' -d '{}'

# does this client actually authenticate? (machine clients only)
curl -sS -X POST http://localhost:9999/oauth/token \
  -d grant_type=client_credentials -d client_id=<id> -d client_secret=<secret>
# -> {"access_token":"trekoa_…","expires_in":3600, …}  or a specific error_description
```

Feeding a handshake straight into `mcp-remote`'s stdio is the closest thing to a real
client, and needs no extra tooling — but **keep stdin open** while it works. Closing it
right after writing (`communicate()`) kills the process mid-handshake and yields empty
stdout, which looks like a protocol failure and is not one.
