from __future__ import annotations

from datetime import datetime
from typing import Optional


def _fmt_duration(seconds: int) -> str:
    m = max(0, seconds) // 60
    h = m // 60
    if h > 0:
        return f"{h}h{m % 60:02d}m"
    return f"{m}m"


def render_panel(
    players: list[tuple[str, Optional[str]]],
    states: dict[str, object],
) -> str:
    now = datetime.now()
    now_ts = int(now.timestamp())
    updated_hm = now.strftime("%H:%M")

    playing: list[str] = []
    idle: list[str] = []

    for steam_id, name in players:
        label = (name or steam_id).strip()
        st = states.get(steam_id)

        is_playing = bool(st and getattr(st, "was_playing_bf6", 0))
        if is_playing:
            since_ts = int(getattr(st, "since_ts", None) or now_ts)
            since_hm = datetime.fromtimestamp(since_ts).strftime("%H:%M")
            dur = _fmt_duration(now_ts - since_ts)
            playing.append(f"🟢 {label} {since_hm} ({dur})")
        else:
            idle.append(f"⚪ {label}")

    lines: list[str] = []

    # Заголовок
    lines.append("🎮 BF6")

    # Online
    lines.append("Players online:")
    if playing:
        lines.extend(playing)
    else:
        lines.append("—")

    # Offline
    lines.append("Offline:")
    if idle:
        lines.extend(idle)
    else:
        lines.append("—")

    # Footer
    lines.append(f"Upd: {updated_hm}")

    text = "\n".join(lines)

    # Telegram limit safety
    if len(text) > 3900:
        text = text[:3900] + "\n…"

    return text
