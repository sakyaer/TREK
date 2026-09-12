#!/usr/bin/env python3
"""Minimal MCP StreamableHTTP client for the local TREK instance.

Usage:
  python3 mcp.py <tool> '<json-args>'
  python3 mcp.py --batch '<json-array-of-[tool,args]>'
"""
import json
import os
import sys
import urllib.request

BASE = os.environ.get("TREK_URL", "http://localhost:9999")
TOKEN = os.environ["TREK_TOKEN"]
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session-id")


def _post(payload, sid=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if sid:
        headers["Mcp-Session-Id"] = sid
    req = urllib.request.Request(
        f"{BASE}/mcp", data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        new_sid = resp.headers.get("mcp-session-id")
        body = resp.read().decode()
    # SSE framing: pick out the data: lines
    out = None
    for line in body.splitlines():
        if line.startswith("data: "):
            out = json.loads(line[6:])
    if out is None and body.strip():
        out = json.loads(body)
    return new_sid, out


def session():
    if os.path.exists(SESSION_FILE):
        return open(SESSION_FILE).read().strip()
    sid, _ = _post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "build-script", "version": "1.0"},
            },
        }
    )
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    open(SESSION_FILE, "w").write(sid)
    return sid


def call(tool, args, sid=None, rid=2):
    for attempt in (1, 2):
        s = sid or session()
        try:
            new_sid, out = _post(
                {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "method": "tools/call",
                    "params": {"name": tool, "arguments": args},
                },
                s,
            )
        except urllib.error.HTTPError as e:
            if attempt == 2 or e.code not in (404, 400):
                raise
            os.remove(SESSION_FILE)  # stale session -> re-initialize
            sid = None
            continue
        if out is None:
            raise RuntimeError("empty MCP response")
        if "error" in out:
            raise RuntimeError(json.dumps(out["error"], ensure_ascii=False))
        result = out.get("result", {})
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError"):
            raise RuntimeError(text)
        try:
            return json.loads(text)
        except Exception:
            return text
    raise RuntimeError("unreachable")


if __name__ == "__main__":
    if sys.argv[1] == "--batch":
        items = json.load(open(sys.argv[2]))
        s = session()
        for i, (tool, args) in enumerate(items):
            print(f"### {i} {tool}", file=sys.stderr)
            print(json.dumps(call(tool, args, sid=s, rid=100 + i), ensure_ascii=False))
    else:
        print(json.dumps(call(sys.argv[1], json.loads(sys.argv[2])), ensure_ascii=False, indent=2))
