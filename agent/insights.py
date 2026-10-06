"""
Session Insights Engine for Hermes Agent.

Analyzes historical session data from the SQLite state database to produce
comprehensive usage insights — token consumption, cost estimates, tool usage
patterns, activity trends, model/platform breakdowns, and session metrics.

Inspired by Claude Code's /insights command, adapted for Hermes Agent's
multi-platform architecture with additional cost estimation and platform
breakdown capabilities.

Usage:
    from agent.insights import InsightsEngine
    engine = InsightsEngine(db)
    report = engine.generate(days=30)
    print(engine.format_terminal(report))
"""

import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.usage_pricing import (
    CanonicalUsage,
    estimate_usage_cost,
    format_duration_compact,
    has_known_pricing,
)




def _estimate_cost(
    session_or_model: Dict[str, Any] | str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    *,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> tuple[float, str]:
    """Estimate the USD cost for a session row or a model/token tuple."""
    if isinstance(session_or_model, dict):
        session = session_or_model
        model = session.get("model") or ""
        usage = CanonicalUsage(
            input_tokens=session.get("input_tokens") or 0,
            output_tokens=session.get("output_tokens") or 0,
            cache_read_tokens=session.get("cache_read_tokens") or 0,
            cache_write_tokens=session.get("cache_write_tokens") or 0,
        )
        provider = session.get("billing_provider")
        base_url = session.get("billing_base_url")
    else:
        model = session_or_model or ""
        usage = CanonicalUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        )
    result = estimate_usage_cost(
        model,
        usage,
        provider=provider,
        base_url=base_url,
    )
    return float(result.amount_usd or 0.0), result.status




def _bar_chart(values: List[int], max_width: int = 20) -> List[str]:
    """Create simple horizontal bar chart strings from values."""
    peak = max(values) if values else 1
    if peak == 0:
        return ["" for _ in values]
    return ["█" * max(1, int(v / peak * max_width)) if v > 0 else "" for v in values]


def _fmt_num(n) -> str:
    """Humanize large numbers: 7.44B / 505.25M / 36.1K / 942."""
    n = float(n or 0)
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:.2f}".rstrip("0").rstrip(".") + suffix
    return str(int(n)) if n == int(n) else f"{n:.1f}"


def _share_bar(pct: float, width: int = 10) -> str:
    """Block-character share bar: ▓▓▓▓▓░░░░░."""
    pct = max(0.0, min(100.0, pct or 0.0))
    filled = round(pct / 100 * width)
    if pct > 0 and filled == 0:
        filled = 1
    return "▓" * filled + "░" * (width - filled)


def _disp_width(s: str) -> int:
    """Terminal display width: CJK/fullwidth chars and emoji count as 2 columns."""
    import unicodedata
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in "WF" or ord(ch) >= 0x1F300:
            w += 2
        else:
            w += 1
    return w


def _pad_to(s: str, width: int) -> str:
    return s + " " * max(0, width - _disp_width(s))


def _fmt_num(n) -> str:
    """Humanize large numbers: 7.44B / 505.25M / 36.1K / 942."""
    n = float(n or 0)
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            return f"{n / div:.2f}".rstrip("0").rstrip(".") + suffix
    return str(int(n)) if n == int(n) else f"{n:.1f}"


def _sparkline(values) -> str:
    """Mini histogram: ▁▂▃▄▅▆▇█ (for 24h activity)."""
    values = list(values or [])
    if not values or max(values) <= 0:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    peak = max(values)
    return "".join(blocks[min(7, int(v / peak * 7.999))] for v in values)


class InsightsEngine:
    """
    Analyzes session history and produces usage insights.

    Works directly with a SessionDB instance (or raw sqlite3 connection)
    to query session and message data.
    """

    def __init__(self, db):
        """
        Initialize with a SessionDB instance.

        Args:
            db: A SessionDB instance (from hermes_state.py)
        """
        self.db = db
        self._conn = db._conn

    def generate(self, days: int = 30, source: str = None) -> Dict[str, Any]:
        """
        Generate a complete insights report.

        Args:
            days: Number of days to look back (default: 30)
            source: Optional filter by source platform

        Returns:
            Dict with all computed insights
        """
        cutoff = time.time() - (days * 86400)

        # Gather raw data
        sessions = self._get_sessions(cutoff, source)
        tool_usage = self._get_tool_usage(cutoff, source)
        skill_usage = self._get_skill_usage(cutoff, source)
        message_stats = self._get_message_stats(cutoff, source)

        if not sessions:
            return {
                "days": days,
                "source_filter": source,
                "empty": True,
                "overview": {},
                "models": [],
                "platforms": [],
                "tools": [],
                "skills": {
                    "summary": {
                        "total_skill_loads": 0,
                        "total_skill_edits": 0,
                        "total_skill_actions": 0,
                        "distinct_skills_used": 0,
                    },
                    "top_skills": [],
                },
                "activity": {},
                "top_sessions": [],
            }

        # Compute insights
        overview = self._compute_overview(sessions, message_stats)
        models = self._compute_model_breakdown(sessions)
        platforms = self._compute_platform_breakdown(sessions)
        tools = self._compute_tool_breakdown(tool_usage)
        skills = self._compute_skill_breakdown(skill_usage)
        activity = self._compute_activity_patterns(sessions)
        top_sessions = self._compute_top_sessions(sessions)

        return {
            "days": days,
            "source_filter": source,
            "empty": False,
            "generated_at": time.time(),
            "overview": overview,
            "models": models,
            "platforms": platforms,
            "tools": tools,
            "skills": skills,
            "activity": activity,
            "top_sessions": top_sessions,
        }

    # =========================================================================
    # Data gathering (SQL queries)
    # =========================================================================

    # Columns we actually need (skip system_prompt, model_config blobs)
    _SESSION_COLS = ("id, source, model, started_at, ended_at, "
                     "message_count, tool_call_count, input_tokens, output_tokens, "
                     "cache_read_tokens, cache_write_tokens, billing_provider, "
                     "billing_base_url, billing_mode, estimated_cost_usd, "
                     "actual_cost_usd, cost_status, cost_source")

    # Pre-computed query strings — f-string evaluated once at class definition,
    # not at runtime, so no user-controlled value can alter the query structure.
    _GET_SESSIONS_WITH_SOURCE = (
        f"SELECT {_SESSION_COLS} FROM sessions"
        " WHERE started_at >= ? AND source = ?"
        " ORDER BY started_at DESC"
    )
    _GET_SESSIONS_ALL = (
        f"SELECT {_SESSION_COLS} FROM sessions"
        " WHERE started_at >= ?"
        " ORDER BY started_at DESC"
    )

    def _get_sessions(self, cutoff: float, source: str = None) -> List[Dict]:
        """Fetch sessions within the time window."""
        if source:
            cursor = self._conn.execute(self._GET_SESSIONS_WITH_SOURCE, (cutoff, source))
        else:
            cursor = self._conn.execute(self._GET_SESSIONS_ALL, (cutoff,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_tool_usage(self, cutoff: float, source: str = None) -> List[Dict]:
        """Get tool call counts from messages.

        Uses two sources:
        1. tool_name column on 'tool' role messages (set by gateway)
        2. tool_calls JSON on 'assistant' role messages (covers CLI where
           tool_name is not populated on tool responses)
        """
        tool_counts = Counter()

        # Source 1: explicit tool_name on tool response messages
        if source:
            cursor = self._conn.execute(
                """SELECT m.tool_name, COUNT(*) as count
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ? AND s.source = ?
                     AND m.role = 'tool' AND m.tool_name IS NOT NULL
                   GROUP BY m.tool_name
                   ORDER BY count DESC""",
                (cutoff, source),
            )
        else:
            cursor = self._conn.execute(
                """SELECT m.tool_name, COUNT(*) as count
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ?
                     AND m.role = 'tool' AND m.tool_name IS NOT NULL
                   GROUP BY m.tool_name
                   ORDER BY count DESC""",
                (cutoff,),
            )
        for row in cursor.fetchall():
            tool_counts[row["tool_name"]] += row["count"]

        # Source 2: extract from tool_calls JSON on assistant messages
        # (covers CLI sessions where tool_name is NULL on tool responses)
        if source:
            cursor2 = self._conn.execute(
                """SELECT m.tool_calls
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ? AND s.source = ?
                     AND m.role = 'assistant' AND m.tool_calls IS NOT NULL""",
                (cutoff, source),
            )
        else:
            cursor2 = self._conn.execute(
                """SELECT m.tool_calls
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ?
                     AND m.role = 'assistant' AND m.tool_calls IS NOT NULL""",
                (cutoff,),
            )

        tool_calls_counts = Counter()
        for row in cursor2.fetchall():
            try:
                calls = row["tool_calls"]
                if isinstance(calls, str):
                    calls = json.loads(calls)
                if isinstance(calls, list):
                    for call in calls:
                        func = call.get("function", {}) if isinstance(call, dict) else {}
                        name = func.get("name")
                        if name:
                            tool_calls_counts[name] += 1
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

        # Merge: prefer tool_name source, supplement with tool_calls source
        # for tools not already counted
        if not tool_counts and tool_calls_counts:
            # No tool_name data at all — use tool_calls exclusively
            tool_counts = tool_calls_counts
        elif tool_counts and tool_calls_counts:
            # Both sources have data — use whichever has the higher count per tool
            # (they may overlap, so take the max to avoid double-counting)
            all_tools = set(tool_counts) | set(tool_calls_counts)
            merged = Counter()
            for tool in all_tools:
                merged[tool] = max(tool_counts.get(tool, 0), tool_calls_counts.get(tool, 0))
            tool_counts = merged

        # Convert to the expected format
        return [
            {"tool_name": name, "count": count}
            for name, count in tool_counts.most_common()
        ]

    def _get_skill_usage(self, cutoff: float, source: str = None) -> List[Dict]:
        """Extract per-skill usage from assistant tool calls."""
        skill_counts: Dict[str, Dict[str, Any]] = {}

        if source:
            cursor = self._conn.execute(
                """SELECT m.tool_calls, m.timestamp
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ? AND s.source = ?
                     AND m.role = 'assistant' AND m.tool_calls IS NOT NULL""",
                (cutoff, source),
            )
        else:
            cursor = self._conn.execute(
                """SELECT m.tool_calls, m.timestamp
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ?
                     AND m.role = 'assistant' AND m.tool_calls IS NOT NULL""",
                (cutoff,),
            )

        for row in cursor.fetchall():
            try:
                calls = row["tool_calls"]
                if isinstance(calls, str):
                    calls = json.loads(calls)
                if not isinstance(calls, list):
                    continue
            except (json.JSONDecodeError, TypeError):
                continue

            timestamp = row["timestamp"]
            for call in calls:
                if not isinstance(call, dict):
                    continue
                func = call.get("function", {})
                tool_name = func.get("name")
                if tool_name not in {"skill_view", "skill_manage"}:
                    continue

                args = func.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except (json.JSONDecodeError, TypeError):
                        continue
                if not isinstance(args, dict):
                    continue

                skill_name = args.get("name")
                if not isinstance(skill_name, str) or not skill_name.strip():
                    continue

                entry = skill_counts.setdefault(
                    skill_name,
                    {
                        "skill": skill_name,
                        "view_count": 0,
                        "manage_count": 0,
                        "last_used_at": None,
                    },
                )
                if tool_name == "skill_view":
                    entry["view_count"] += 1
                else:
                    entry["manage_count"] += 1

                if timestamp is not None and (
                    entry["last_used_at"] is None or timestamp > entry["last_used_at"]
                ):
                    entry["last_used_at"] = timestamp

        return list(skill_counts.values())

    def _get_message_stats(self, cutoff: float, source: str = None) -> Dict:
        """Get aggregate message statistics."""
        if source:
            cursor = self._conn.execute(
                """SELECT
                     COUNT(*) as total_messages,
                     SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) as user_messages,
                     SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
                     SUM(CASE WHEN m.role = 'tool' THEN 1 ELSE 0 END) as tool_messages
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ? AND s.source = ?""",
                (cutoff, source),
            )
        else:
            cursor = self._conn.execute(
                """SELECT
                     COUNT(*) as total_messages,
                     SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) as user_messages,
                     SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
                     SUM(CASE WHEN m.role = 'tool' THEN 1 ELSE 0 END) as tool_messages
                   FROM messages m
                   JOIN sessions s ON s.id = m.session_id
                   WHERE s.started_at >= ?""",
                (cutoff,),
            )
        row = cursor.fetchone()
        return dict(row) if row else {
            "total_messages": 0, "user_messages": 0,
            "assistant_messages": 0, "tool_messages": 0,
        }

    # =========================================================================
    # Computation
    # =========================================================================

    def _compute_overview(self, sessions: List[Dict], message_stats: Dict) -> Dict:
        """Compute high-level overview statistics."""
        total_input = sum(s.get("input_tokens") or 0 for s in sessions)
        total_output = sum(s.get("output_tokens") or 0 for s in sessions)
        total_cache_read = sum(s.get("cache_read_tokens") or 0 for s in sessions)
        total_cache_write = sum(s.get("cache_write_tokens") or 0 for s in sessions)
        total_tokens = total_input + total_output + total_cache_read + total_cache_write
        total_tool_calls = sum(s.get("tool_call_count") or 0 for s in sessions)
        total_messages = sum(s.get("message_count") or 0 for s in sessions)

        # Cost estimation (weighted by model)
        total_cost = 0.0
        actual_cost = 0.0
        models_with_pricing = set()
        models_without_pricing = set()
        unknown_cost_sessions = 0
        included_cost_sessions = 0
        for s in sessions:
            model = s.get("model") or ""
            estimated, status = _estimate_cost(s)
            total_cost += estimated
            actual_cost += s.get("actual_cost_usd") or 0.0
            display = model.split("/")[-1] if "/" in model else (model or "unknown")
            if status == "included":
                included_cost_sessions += 1
            elif status == "unknown":
                unknown_cost_sessions += 1
            if has_known_pricing(model, s.get("billing_provider"), s.get("billing_base_url")):
                models_with_pricing.add(display)
            else:
                models_without_pricing.add(display)

        # Session duration stats (guard against negative durations from clock drift)
        durations = []
        for s in sessions:
            start = s.get("started_at")
            end = s.get("ended_at")
            if start and end and end > start:
                durations.append(end - start)

        total_hours = sum(durations) / 3600 if durations else 0
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Earliest and latest session
        started_timestamps = [s["started_at"] for s in sessions if s.get("started_at")]
        date_range_start = min(started_timestamps) if started_timestamps else None
        date_range_end = max(started_timestamps) if started_timestamps else None

        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cache_read_tokens": total_cache_read,
            "total_cache_write_tokens": total_cache_write,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost,
            "actual_cost": actual_cost,
            "total_hours": total_hours,
            "avg_session_duration": avg_duration,
            "avg_messages_per_session": total_messages / len(sessions) if sessions else 0,
            "avg_tokens_per_session": total_tokens / len(sessions) if sessions else 0,
            "user_messages": message_stats.get("user_messages") or 0,
            "assistant_messages": message_stats.get("assistant_messages") or 0,
            "tool_messages": message_stats.get("tool_messages") or 0,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
            "models_with_pricing": sorted(models_with_pricing),
            "models_without_pricing": sorted(models_without_pricing),
            "unknown_cost_sessions": unknown_cost_sessions,
            "included_cost_sessions": included_cost_sessions,
        }

    def _compute_model_breakdown(self, sessions: List[Dict]) -> List[Dict]:
        """Break down usage by model."""
        model_data = defaultdict(lambda: {
            "sessions": 0, "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "total_tokens": 0, "tool_calls": 0, "cost": 0.0,
        })

        for s in sessions:
            model = s.get("model") or "unknown"
            # Normalize: strip provider prefix for display
            display_model = model.split("/")[-1] if "/" in model else model
            d = model_data[display_model]
            d["sessions"] += 1
            inp = s.get("input_tokens") or 0
            out = s.get("output_tokens") or 0
            cache_read = s.get("cache_read_tokens") or 0
            cache_write = s.get("cache_write_tokens") or 0
            d["input_tokens"] += inp
            d["output_tokens"] += out
            d["cache_read_tokens"] += cache_read
            d["cache_write_tokens"] += cache_write
            d["total_tokens"] += inp + out + cache_read + cache_write
            d["tool_calls"] += s.get("tool_call_count") or 0
            estimate, status = _estimate_cost(s)
            d["cost"] += estimate
            d["has_pricing"] = has_known_pricing(model, s.get("billing_provider"), s.get("billing_base_url"))
            d["cost_status"] = status

        result = [
            {"model": model, **data}
            for model, data in model_data.items()
        ]
        # Sort by tokens first, fall back to session count when tokens are 0
        result.sort(key=lambda x: (x["total_tokens"], x["sessions"]), reverse=True)
        return result

    def _compute_platform_breakdown(self, sessions: List[Dict]) -> List[Dict]:
        """Break down usage by platform/source."""
        platform_data = defaultdict(lambda: {
            "sessions": 0, "messages": 0, "input_tokens": 0,
            "output_tokens": 0, "cache_read_tokens": 0,
            "cache_write_tokens": 0, "total_tokens": 0, "tool_calls": 0,
        })

        for s in sessions:
            source = s.get("source") or "unknown"
            d = platform_data[source]
            d["sessions"] += 1
            d["messages"] += s.get("message_count") or 0
            inp = s.get("input_tokens") or 0
            out = s.get("output_tokens") or 0
            cache_read = s.get("cache_read_tokens") or 0
            cache_write = s.get("cache_write_tokens") or 0
            d["input_tokens"] += inp
            d["output_tokens"] += out
            d["cache_read_tokens"] += cache_read
            d["cache_write_tokens"] += cache_write
            d["total_tokens"] += inp + out + cache_read + cache_write
            d["tool_calls"] += s.get("tool_call_count") or 0

        result = [
            {"platform": platform, **data}
            for platform, data in platform_data.items()
        ]
        result.sort(key=lambda x: x["sessions"], reverse=True)
        return result

    def _compute_tool_breakdown(self, tool_usage: List[Dict]) -> List[Dict]:
        """Process tool usage data into a ranked list with percentages."""
        total_calls = sum(t["count"] for t in tool_usage) if tool_usage else 0
        result = []
        for t in tool_usage:
            pct = (t["count"] / total_calls * 100) if total_calls else 0
            result.append({
                "tool": t["tool_name"],
                "count": t["count"],
                "percentage": pct,
            })
        return result

    def _compute_skill_breakdown(self, skill_usage: List[Dict]) -> Dict[str, Any]:
        """Process per-skill usage into summary + ranked list."""
        total_skill_loads = sum(s["view_count"] for s in skill_usage) if skill_usage else 0
        total_skill_edits = sum(s["manage_count"] for s in skill_usage) if skill_usage else 0
        total_skill_actions = total_skill_loads + total_skill_edits

        top_skills = []
        for skill in skill_usage:
            total_count = skill["view_count"] + skill["manage_count"]
            percentage = (total_count / total_skill_actions * 100) if total_skill_actions else 0
            top_skills.append({
                "skill": skill["skill"],
                "view_count": skill["view_count"],
                "manage_count": skill["manage_count"],
                "total_count": total_count,
                "percentage": percentage,
                "last_used_at": skill.get("last_used_at"),
            })

        top_skills.sort(
            key=lambda s: (
                s["total_count"],
                s["view_count"],
                s["manage_count"],
                s["last_used_at"] or 0,
                s["skill"],
            ),
            reverse=True,
        )

        return {
            "summary": {
                "total_skill_loads": total_skill_loads,
                "total_skill_edits": total_skill_edits,
                "total_skill_actions": total_skill_actions,
                "distinct_skills_used": len(skill_usage),
            },
            "top_skills": top_skills,
        }

    def _compute_activity_patterns(self, sessions: List[Dict]) -> Dict:
        """Analyze activity patterns by day of week and hour."""
        day_counts = Counter()  # 0=Monday ... 6=Sunday
        hour_counts = Counter()
        daily_counts = Counter()  # date string -> count

        for s in sessions:
            ts = s.get("started_at")
            if not ts:
                continue
            dt = datetime.fromtimestamp(ts)
            day_counts[dt.weekday()] += 1
            hour_counts[dt.hour] += 1
            daily_counts[dt.strftime("%Y-%m-%d")] += 1

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_breakdown = [
            {"day": day_names[i], "count": day_counts.get(i, 0)}
            for i in range(7)
        ]

        hour_breakdown = [
            {"hour": i, "count": hour_counts.get(i, 0)}
            for i in range(24)
        ]

        # Busiest day and hour
        busiest_day = max(day_breakdown, key=lambda x: x["count"]) if day_breakdown else None
        busiest_hour = max(hour_breakdown, key=lambda x: x["count"]) if hour_breakdown else None

        # Active days (days with at least one session)
        active_days = len(daily_counts)

        # Streak calculation
        if daily_counts:
            all_dates = sorted(daily_counts.keys())
            current_streak = 1
            max_streak = 1
            for i in range(1, len(all_dates)):
                d1 = datetime.strptime(all_dates[i - 1], "%Y-%m-%d")
                d2 = datetime.strptime(all_dates[i], "%Y-%m-%d")
                if (d2 - d1).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1
        else:
            max_streak = 0

        return {
            "by_day": day_breakdown,
            "by_hour": hour_breakdown,
            "busiest_day": busiest_day,
            "busiest_hour": busiest_hour,
            "active_days": active_days,
            "max_streak": max_streak,
        }

    def _compute_top_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """Find notable sessions (longest, most messages, most tokens)."""
        top = []

        # Longest by duration
        sessions_with_duration = [
            s for s in sessions
            if s.get("started_at") and s.get("ended_at")
        ]
        if sessions_with_duration:
            longest = max(
                sessions_with_duration,
                key=lambda s: (s["ended_at"] - s["started_at"]),
            )
            dur = longest["ended_at"] - longest["started_at"]
            top.append({
                "label": "Longest session",
                "session_id": longest["id"][:16],
                "value": format_duration_compact(dur),
                "date": datetime.fromtimestamp(longest["started_at"]).strftime("%b %d"),
            })

        # Most messages
        most_msgs = max(sessions, key=lambda s: s.get("message_count") or 0)
        if (most_msgs.get("message_count") or 0) > 0:
            top.append({
                "label": "Most messages",
                "session_id": most_msgs["id"][:16],
                "value": f"{most_msgs['message_count']} msgs",
                "date": datetime.fromtimestamp(most_msgs["started_at"]).strftime("%b %d") if most_msgs.get("started_at") else "?",
            })

        # Most tokens
        most_tokens = max(
            sessions,
            key=lambda s: (s.get("input_tokens") or 0) + (s.get("output_tokens") or 0),
        )
        token_total = (most_tokens.get("input_tokens") or 0) + (most_tokens.get("output_tokens") or 0)
        if token_total > 0:
            top.append({
                "label": "Most tokens",
                "session_id": most_tokens["id"][:16],
                "value": f"{token_total:,} tokens",
                "date": datetime.fromtimestamp(most_tokens["started_at"]).strftime("%b %d") if most_tokens.get("started_at") else "?",
            })

        # Most tool calls
        most_tools = max(sessions, key=lambda s: s.get("tool_call_count") or 0)
        if (most_tools.get("tool_call_count") or 0) > 0:
            top.append({
                "label": "Most tool calls",
                "session_id": most_tools["id"][:16],
                "value": f"{most_tools['tool_call_count']} calls",
                "date": datetime.fromtimestamp(most_tools["started_at"]).strftime("%b %d") if most_tools.get("started_at") else "?",
            })

        return top

    # =========================================================================
    # Formatting
    # =========================================================================

    def format_terminal(self, report: Dict) -> str:
        """Format the insights report for terminal display (CLI).

        Pretty variant: box title, dim rules, colored section headers and
        share bars when stdout is a TTY; graceful plain-text fallback when
        piped (hermes insights | grep ... keeps working).
        """
        if report.get("empty"):
            days = report.get("days", 30)
            src = f" (source: {report['source_filter']})" if report.get("source_filter") else ""
            return f"  No sessions found in the last {days} days{src}."

        # ── Color plumbing (TTY-only; plain fallback when piped) ──
        try:
            import sys as _sys
            import shutil as _shutil
            use_color = _sys.stdout.isatty()
            term_width = _shutil.get_terminal_size().columns if use_color else 80
        except Exception:
            use_color, term_width = False, 80

        def c(code: str, text: str) -> str:
            return f"\033[{code}m{text}\033[0m" if use_color else text

        dim = lambda s: c("2", s)           # noqa: E731
        bold = lambda s: c("1", s)          # noqa: E731
        cyan = lambda s: c("36", s)         # noqa: E731
        green = lambda s: c("32", s)        # noqa: E731
        yellow = lambda s: c("33", s)       # noqa: E731
        magenta = lambda s: c("35", s)      # noqa: E731
        blue = lambda s: c("34", s)         # noqa: E731

        def rule(label: str) -> str:
            inner = f" {label} "
            pad = max(2, 56 - len(inner))
            return "  " + dim("─" * 2) + dim(inner) + dim("─" * pad)

        def bar_row(name: str, count: int, peak: int, total: int, width: int) -> str:
            pct = count / total * 100 if total else 0
            filled = round(count / peak * width) if peak else 0
            filled = max(1, min(width, filled)) if count > 0 else 0
            bar = "█" * filled + dim("░" * (width - filled))
            bar_color = green if pct >= 20 else (cyan if pct >= 5 else blue)
            return f"  {name:<24} {bar_color(bar)} {count:>8,} {dim(f'{pct:>5.1f}%')}"

        lines = []
        o = report["overview"]
        days = report["days"]
        src_filter = report.get("source_filter")

        # Header (display-width aware centering for CJK)
        lines.append("")
        period_label = f"近 {days} 天"
        if src_filter:
            period_label += f" · {src_filter}"
        inner_w = 56
        title = "📊 Hermes 用量洞察"
        t_pad = max(0, (inner_w - _disp_width(title)) // 2)
        p_pad = max(0, (inner_w - _disp_width(period_label)) // 2)
        lines.append("  ╭" + "─" * inner_w + "╮")
        lines.append("  │" + " " * t_pad + title + " " * (inner_w - t_pad - _disp_width(title)) + "│")
        lines.append("  │" + " " * p_pad + dim(period_label) + " " * (inner_w - p_pad - _disp_width(period_label)) + "│")
        lines.append("  ╰" + "─" * inner_w + "╯")

        # Date range
        if o.get("date_range_start") and o.get("date_range_end"):
            start_str = datetime.fromtimestamp(o["date_range_start"]).strftime("%m-%d")
            end_str = datetime.fromtimestamp(o["date_range_end"]).strftime("%m-%d")
            lines.append("")
            lines.append(f"  {dim('统计周期:')} {start_str} → {end_str}")

        # Overview — compact 2-column key figures
        lines.append("")
        lines.append(bold("  📋 总览"))
        lines.append(rule("概览"))
        v_sess, v_msg, v_calls, v_user = (
            f"{o['total_sessions']:,}", f"{o['total_messages']:,}",
            f"{o['total_tool_calls']:,}", f"{o['user_messages']:,}",
        )
        lines.append(
            f"  会话 {bold(v_sess)}   消息 {bold(v_msg)}   "
            f"工具调用 {bold(v_calls)}   用户消息 {bold(v_user)}"
        )
        v_tok = _fmt_num(o["total_tokens"])
        v_in = _fmt_num(o["total_input_tokens"])
        v_out = _fmt_num(o["total_output_tokens"])
        lines.append(
            f"  Tokens {bold(v_tok)} {dim('(' + format(o['total_tokens'], ',') + ')')}   "
            f"输入 {bold(v_in)}   输出 {bold(v_out)}"
        )
        if o.get("total_cache_read_tokens"):
            cache_pct = o["total_cache_read_tokens"] / o["total_tokens"] * 100 if o["total_tokens"] else 0
            lines.append(
                f"  缓存读取 {bold(_fmt_num(o['total_cache_read_tokens']))} {dim(f'{cache_pct:.0f}%')}"
            )
        if o["total_hours"] > 0:
            lines.append(
                f"  活跃时长 ~{bold(format_duration_compact(o['total_hours'] * 3600))}   "
                f"平均会话 ~{bold(format_duration_compact(o['avg_session_duration']))}   "
                f"均 {o['avg_messages_per_session']:.1f} 条/会话"
            )
        lines.append("")

        # Model breakdown
        if report["models"]:
            lines.append(bold("  🤖 模型分布"))
            lines.append(rule("模型"))
            total_m = sum(m["total_tokens"] for m in report["models"]) or 1
            for m in report["models"]:
                pct = m["total_tokens"] / total_m * 100
                marker = green("●") if m.get("has_pricing") else yellow("○")
                cost_str = ""
                if m.get("has_pricing") and m.get("cost"):
                    cost_str = "  " + dim("~$" + format(m["cost"], ".2f"))
                tok_disp = _fmt_num(m["total_tokens"])
                lines.append(
                    f"  {marker} {m['model'][:28]:<28} {m['sessions']:>5} 会话  "
                    f"{tok_disp:>9} tok {dim(f'{pct:.0f}%')}{cost_str}"
                )
            lines.append("")

        # Platform breakdown
        if len(report["platforms"]) > 1 or (report["platforms"] and report["platforms"][0]["platform"] != "cli"):
            lines.append(bold("  📱 平台分布"))
            lines.append(rule("平台"))
            plat_total = sum(p["total_tokens"] for p in report["platforms"]) or 1
            plat_peak = max(p["total_tokens"] for p in report["platforms"]) or 1
            plat_width = min(24, max(10, term_width - 66))
            for p in report["platforms"]:
                row = bar_row(p["platform"][:24], p["total_tokens"], plat_peak, plat_total, plat_width)
                tok_human = _fmt_num(p["total_tokens"]).rjust(8)
                # swap the raw comma count from bar_row for the humanized form
                raw = f"{p['total_tokens']:>8,}"
                row = row.replace(raw, tok_human) if raw in row else row
                lines.append(row + dim(f"  {p['sessions']} 会话 · {p['messages']:,} 消息"))
            lines.append("")

        # Tool usage
        if report["tools"]:
            lines.append(bold("  🔧 高频工具"))
            lines.append(rule("工具"))
            tools = report["tools"][:12]
            peak = max(t["count"] for t in tools) or 1
            for t in tools:
                lines.append(bar_row(t["tool"][:24], t["count"], peak, o["total_tool_calls"] or 1, 16))
            if len(report["tools"]) > 12:
                lines.append(dim(f"  … 另有 {len(report['tools']) - 12} 个工具"))
            lines.append("")

        # Skill usage
        skills = report.get("skills", {})
        top_skills = skills.get("top_skills", [])
        if top_skills:
            lines.append(bold("  🧠 高频技能"))
            lines.append(rule("技能"))
            for skill in top_skills[:10]:
                last_used = "—"
                if skill.get("last_used_at"):
                    last_used = datetime.fromtimestamp(skill["last_used_at"]).strftime("%m-%d")
                loads_disp = format(skill["view_count"], ",")
                edits_disp = format(skill["manage_count"], ",")
                lines.append(
                    f"  {skill['skill'][:30]:<30} {cyan(loads_disp.rjust(5))} 加载  "
                    f"{magenta(edits_disp.rjust(4))} 编辑  {dim(last_used)}"
                )
            summary = skills.get("summary", {})
            lines.append(
                dim(
                    f"  去重 {summary.get('distinct_skills_used', 0)} 个 · "
                    f"加载 {summary.get('total_skill_loads', 0):,} · 编辑 {summary.get('total_skill_edits', 0):,}"
                )
            )
            lines.append("")

        # Activity patterns
        act = report.get("activity", {})
        if act.get("by_day"):
            lines.append(bold("  📅 活动规律"))
            lines.append(rule("活动"))
            day_values = [d["count"] for d in act["by_day"]]
            bars = _bar_chart(day_values, max_width=15)
            day_peak = max(day_values) or 1
            for i, d in enumerate(act["by_day"]):
                bar = bars[i]
                color = green if d["count"] >= day_peak * 0.8 else (blue if d["count"] > 0 else dim)
                lines.append(f"  {d['day']}  {color(bar):<15} {d['count']}")
            lines.append("")

            # 24h sparkline
            hour_counts = [h["count"] for h in act["by_hour"]]
            spark = _sparkline(hour_counts)
            if spark:
                busiest = act.get("busiest_hour")
                peak_hr = f"峰值 {busiest['hour']:02d}:00 ({busiest['count']})" if busiest else ""
                lines.append(f"  24h {spark}  {dim(peak_hr)}")
                lines.append("")

            if act.get("active_days"):
                streak = f" · 连续 {act['max_streak']} 天" if act.get("max_streak", 0) > 1 else ""
                lines.append(f"  活跃天数 {act['active_days']}{streak}")
            lines.append("")

        # Notable sessions
        if report.get("top_sessions"):
            lines.append(bold("  🏆 重点会话"))
            lines.append(rule("会话"))
            label_map = {
                "Longest session": "最长会话", "Most messages": "消息最多",
                "Most tokens": "Tokens 最多", "Most tool calls": "工具调用最多",
            }
            for ts in report["top_sessions"]:
                zh_label = label_map.get(ts["label"], ts["label"])
                meta = f"({ts['date']}, {ts['session_id']})"
                lines.append(f"  {_pad_to(zh_label, 16)} {cyan(ts['value']):<18} {dim(meta)}")
            lines.append("")

        return "\n".join(lines)

    def format_gateway(self, report: Dict) -> str:
        """Format the insights report for gateway/messaging (Telegram Markdown).

        Pretty variant: table rows, share bars, humanized token counts,
        Chinese labels; degrades to plain text on non-Telegram gateways
        (markdown tables degrade to readable bullet groups).
        """
        if report.get("empty"):
            days = report.get("days", 30)
            return f"近 {days} 天没有会话记录。"

        lines = []
        o = report["overview"]
        days = report["days"]
        src_filter = report.get("source_filter")

        period = f"近 {days} 天"
        if src_filter:
            period += f" · {src_filter}"
        lines.append(f"📊 **Hermes 用量洞察** — {period}\n")

        # Overview key figures
        period_span = ""
        if o.get("date_range_start") and o.get("date_range_end"):
            s = datetime.fromtimestamp(o["date_range_start"]).strftime("%m-%d")
            e = datetime.fromtimestamp(o["date_range_end"]).strftime("%m-%d")
            period_span = f"（{s} → {e}）"
        lines.append(
            f"**会话** {o['total_sessions']:,} ｜ **消息** {o['total_messages']:,} ｜ "
            f"**工具调用** {o['total_tool_calls']:,} ｜ **用户消息** {o['user_messages']:,}"
        )
        tok_line = f"**Tokens** {_fmt_num(o['total_tokens'])}（{o['total_tokens']:,}）｜ 输入 {_fmt_num(o['total_input_tokens'])} ｜ 输出 {_fmt_num(o['total_output_tokens'])}"
        if o.get("total_cache_read_tokens"):
            cache_pct = o["total_cache_read_tokens"] / o["total_tokens"] * 100 if o["total_tokens"] else 0
            tok_line += f" ｜ 缓存读取 {_fmt_num(o['total_cache_read_tokens'])}（{cache_pct:.0f}%）"
        lines.append(tok_line)
        if o["total_hours"] > 0:
            lines.append(
                f"**活跃时长** ~{format_duration_compact(o['total_hours'] * 3600)} ｜ "
                f"**平均会话** ~{format_duration_compact(o['avg_session_duration'])} ｜ "
                f"均 {o['avg_messages_per_session']:.1f} 条/会话"
            )
        if period_span:
            lines.append(f"*统计周期* {period_span}")
        lines.append("")

        # Models table
        if report["models"]:
            lines.append("**🤖 模型分布**\n")
            lines.append("| 模型 | 会话 | Tokens |")
            lines.append("|---|---:|---:|")
            for m in report["models"][:5]:
                lines.append(f"| {m['model'][:26]} | {m['sessions']} | {_fmt_num(m['total_tokens'])} |")
            lines.append("")

        # Platforms with share bars
        if len(report["platforms"]) > 1 or (report["platforms"] and report["platforms"][0]["platform"] != "cli"):
            lines.append("**📱 平台分布**\n")
            lines.append("| 平台 | 占比 | Tokens | 会话 |")
            lines.append("|---|---|---:|---:|")
            plat_total = sum(p["total_tokens"] for p in report["platforms"]) or 1
            for p in report["platforms"]:
                pct = p["total_tokens"] / plat_total * 100
                lines.append(
                    f"| {p['platform']} | `{_share_bar(pct)}` {pct:.0f}% | {_fmt_num(p['total_tokens'])} | {p['sessions']:,} |"
                )
            lines.append("")

        # Tools with share bars
        if report["tools"]:
            lines.append("**🔧 高频工具**\n")
            lines.append("| 工具 | 占比 | 调用 |")
            lines.append("|---|---|---:|")
            total_calls = sum(t["count"] for t in report["tools"]) or 1
            for t in report["tools"][:10]:
                pct = t["count"] / total_calls * 100
                lines.append(f"| `{t['tool']}` | `{_share_bar(pct)}` {pct:.1f}% | {t['count']:,} |")
            if len(report["tools"]) > 10:
                lines.append(f"\n*… 另有 {len(report['tools']) - 10} 个工具*")
            lines.append("")

        # Skills table
        skills = report.get("skills", {})
        if skills.get("top_skills"):
            lines.append("**🧠 高频技能**\n")
            lines.append("| 技能 | 加载 | 编辑 | 最近 |")
            lines.append("|---|---:|---:|---|")
            for skill in skills["top_skills"][:8]:
                last_used = "—"
                if skill.get("last_used_at"):
                    last_used = datetime.fromtimestamp(skill["last_used_at"]).strftime("%m-%d")
                lines.append(
                    f"| {skill['skill'][:24]} | {skill['view_count']:,} | {skill['manage_count']:,} | {last_used} |"
                )
            summary = skills.get("summary", {})
            lines.append(
                f"\n*去重 {summary.get('distinct_skills_used', 0)} 个 · 加载 {summary.get('total_skill_loads', 0):,} · 编辑 {summary.get('total_skill_edits', 0):,}*"
            )
            lines.append("")

        # Activity
        act = report.get("activity", {})
        if act.get("by_day"):
            day_values = [d["count"] for d in act["by_day"]]
            day_peak = max(day_values) or 1
            lines.append("**📅 活动规律**\n")
            lines.append("| 星期 | 会话 | 峰值 |")
            lines.append("|---|---:|---|")
            day_names_zh = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            peak_val = day_peak
            for i, d in enumerate(act["by_day"]):
                mark = " 🔥" if d["count"] == peak_val and peak_val > 0 else ""
                lines.append(f"| {day_names_zh[i]} | {d['count']} | `{_share_bar(d['count'] / day_peak * 100)}`{mark} |")
            lines.append("")
            hour_counts = [h["count"] for h in act.get("by_hour", [])]
            spark = _sparkline(hour_counts)
            extra = []
            busiest = act.get("busiest_hour")
            if busiest and busiest.get("count"):
                extra.append(f"峰值 {busiest['hour']:02d}:00（{busiest['count']} 会话）")
            if act.get("active_days"):
                extra.append(f"活跃 {act['active_days']} 天")
            if act.get("max_streak", 0) > 1:
                extra.append(f"连续 {act['max_streak']} 天")
            if spark:
                lines.append(f"`{spark}`" + (f" ｜ {' · '.join(extra)}" if extra else ""))
                lines.append("")

        # Notable sessions
        if report.get("top_sessions"):
            lines.append("**🏆 重点会话**\n")
            label_map = {
                "Longest session": "最长会话", "Most messages": "消息最多",
                "Most tokens": "Tokens 最多", "Most tool calls": "工具调用最多",
            }
            for ts in report["top_sessions"]:
                zh_label = label_map.get(ts["label"], ts["label"])
                lines.append(f"- **{zh_label}** {ts['value']}（{ts['date']}）")
            lines.append("")

        return "\n".join(lines)
