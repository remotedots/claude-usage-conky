# Claude Usage Conky

A Conky desktop overlay that mimics Claude Code's `/usage` output: session and weekly usage bars with exact reset times.

## What it shows

![Two progress bars: current session % and current week % with reset times](screenshot.png)

## How it works

The script calls `https://api.anthropic.com/api/oauth/usage` (the same endpoint Claude Code's `/usage` command uses) with the OAuth token stored in `~/.claude/.credentials.json`. No tokens are consumed and it doesn't affect your usage limit.

Results are cached in `/tmp/claude_usage_conky_cache.json` so the API is only hit once per Conky refresh cycle. The config calls the script 6 times per update (4 values × 2 sections, with `session_pct` called twice — once for the label, once for the bar), but only the first call fetches; the rest read from cache.

## Requirements

- [Conky](https://github.com/brndnmtthws/conky) (`apt install conky`)
- A Claude Code installation with a logged-in account (`~/.claude/.credentials.json`)
- JetBrains Mono font (or edit `font` in `claude_usage_conky.conf`)

## Installation

```bash
cp claude_usage_conky.py claude_usage_conky.conf ~/.config/conky/
conky -c ~/.config/conky/claude_usage_conky.conf &
```

To start automatically on login, create `~/.config/autostart/claude-usage-conky.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Claude Usage Conky
Exec=conky -c /home/YOUR_USER/.config/conky/claude_usage_conky.conf
StartupNotify=false
Terminal=false
X-GNOME-Autostart-enabled=true
```

### Already using Conky?

**Option A: Run as a second instance** (simplest, no conflicts):

```bash
# start both independently
conky -c ~/.config/conky/existing.conf &
conky -c ~/.config/conky/claude_usage_conky.conf &
```

Each instance has its own position, font, and update interval.

**Option B: Merge into your existing config**:

1. Copy `claude_usage_conky.py` to `~/.config/conky/`
2. Add to your existing `conky.config` block (if not already present):
   ```lua
   default_bar_height = 4,
   default_bar_width  = 0,
   ```
3. Append to your existing `conky.text`:
   ```
   ${color #FFFFFF}Current session${alignr}${color #AAAAAA}${exec python3 ~/.config/conky/claude_usage_conky.py session_pct}% used
   ${color #4EC9B0}${execbar python3 ~/.config/conky/claude_usage_conky.py session_pct}
   ${color #666666}Resets ${exec python3 ~/.config/conky/claude_usage_conky.py session_reset}

   ${color #FFFFFF}Current week (all models)${alignr}${color #AAAAAA}${exec python3 ~/.config/conky/claude_usage_conky.py week_pct}% used
   ${color #4EC9B0}${execbar python3 ~/.config/conky/claude_usage_conky.py week_pct}
   ${color #666666}Resets ${exec python3 ~/.config/conky/claude_usage_conky.py week_reset}
   ```

## Configuration

| File | What to change |
|------|---------------|
| `claude_usage_conky.conf` | Position (`alignment`, `gap_x`, `gap_y`), font, bar height, refresh interval |
| `claude_usage_conky.py` | Timezone (`TZ`), cache TTL (`TTL`) |

**Position options** (`alignment` in `claude_usage_conky.conf`): `top_right`, `top_left`, `bottom_right`, `bottom_left`, `top_middle`, etc.

**Refresh interval**: currently 600 seconds (10 min). The endpoint is lightweight metadata, not inference, but Anthropic rate-limits it — don't go below 300s.
