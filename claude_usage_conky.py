#!/usr/bin/env python3
# Usage: claude_usage.py [header|pct|footer] [session|week]
# Called multiple times per Conky refresh; uses a 60s file cache.
import json, sys, time
from datetime import datetime
from pathlib import Path
import urllib.request
import zoneinfo

CREDS  = Path.home() / ".claude" / ".credentials.json"
CACHE  = Path("/tmp/claude_usage_conky_cache.json")
LOCK   = Path("/tmp/claude_usage_conky_cache.lock")
API    = "https://api.anthropic.com/api/oauth/usage"
TZ     = zoneinfo.ZoneInfo("Europe/Amsterdam")
TTL    = 290  # seconds — just under the 300s Conky refresh interval


def load_data():
    import fcntl
    now = time.time()
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if now - cached.get("_ts", 0) < TTL:
            return cached
    # Only one process fetches; others wait and read the result
    with open(LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        # Re-check after acquiring lock — another process may have fetched
        if CACHE.exists():
            cached = json.loads(CACHE.read_text())
            if time.time() - cached.get("_ts", 0) < TTL:
                return cached
        token = json.loads(CREDS.read_text())["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(API, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        data["_ts"] = time.time()
        CACHE.write_text(json.dumps(data))
        return data


def fmt_reset(iso_str):
    if not iso_str:
        return "—"
    dt = datetime.fromisoformat(iso_str).astimezone(TZ)
    now = datetime.now(TZ)
    if dt.date() == now.date():
        return dt.strftime("%-I:%M%p").lower() + f" ({TZ.key})"
    return dt.strftime("%b %-d, %-I%p").lower().replace(":00", "") + f" ({TZ.key})"


def c(color, text):
    return f"${{color {color}}}{text}${{color}}"


C_TITLE = "#FFFFFF"
C_PCT   = "#AAAAAA"
C_RESET = "#666666"
C_ERR   = "#E06C75"

mode   = sys.argv[1] if len(sys.argv) > 1 else "header"
target = sys.argv[2] if len(sys.argv) > 2 else "session"

try:
    data = load_data()
except Exception as e:
    if mode == "pct":
        print(0)
    else:
        print(c(C_ERR, f"error: {e}"))
    sys.exit(0)

if target == "session":
    block = data.get("five_hour") or {}
    title = "Current session"
else:
    block = data.get("seven_day") or {}
    title = "Current week (all models)"

pct       = round(block.get("utilization", 0))
reset_str = fmt_reset(block.get("resets_at"))

if mode == "header":
    print(c(C_TITLE, title) + "${alignr}" + c(C_PCT, f"{pct}% used"))
elif mode == "pct":
    print(pct)
elif mode == "footer":
    print(c(C_RESET, f"Resets {reset_str}"))
