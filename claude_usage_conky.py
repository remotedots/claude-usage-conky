#!/usr/bin/env python3
# Outputs a single plain value. Called from conky.text with one argument:
#   session_pct | session_reset | week_pct | week_reset
import json, sys, time, fcntl
from datetime import datetime
from pathlib import Path
import urllib.request
import zoneinfo

CREDS = Path.home() / ".claude" / ".credentials.json"
CACHE = Path("/tmp/claude_usage_conky_cache.json")
LOCK  = Path("/tmp/claude_usage_conky_cache.lock")
API   = "https://api.anthropic.com/api/oauth/usage"
TZ    = zoneinfo.ZoneInfo("Europe/Amsterdam")
TTL   = 590


def load_data():
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if time.time() - cached.get("_ts", 0) < TTL:
            return cached
    with open(LOCK, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
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


key = sys.argv[1] if len(sys.argv) > 1 else "session_pct"

try:
    data = load_data()
except Exception as e:
    print("0" if key.endswith("_pct") else f"error: {e}")
    sys.exit(0)

five = data.get("five_hour") or {}
week = data.get("seven_day") or {}

print({
    "session_pct":   str(round(five.get("utilization", 0))),
    "session_reset": fmt_reset(five.get("resets_at")),
    "week_pct":      str(round(week.get("utilization", 0))),
    "week_reset":    fmt_reset(week.get("resets_at")),
}.get(key, "?"))
