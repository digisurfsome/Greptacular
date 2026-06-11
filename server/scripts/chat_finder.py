#!/usr/bin/env python3
"""Chat Finder — search and read AutoForge workspace chats from the command line.

Designed for AI agents (and humans) to find old conversations the same way a
person would use the workspace search box, then read through the hits one by
one — just much faster.

The workspace database is SQLite at ~/.autoforge/workspace.db. This script
opens it READ-ONLY; it can never modify or delete chats.

Usage:
    python chat_finder.py search "deploy chain" [--limit 10] [--snippets 3]
    python chat_finder.py read 42 [--max-chars 2000]
    python chat_finder.py list [--days 14] [--limit 30]

Typical agent workflow:
    1. Run `search` with 3-5 keyword variations of what the user described.
    2. For each promising hit, run `read <id>` to read the conversation.
    3. Report back: chat title, category, how many days ago, and the
       relevant quote.

No third-party dependencies — stdlib only.
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / ".autoforge" / "workspace.db"


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"ERROR: workspace database not found at {db_path}")
    # Read-only URI so an agent can never corrupt the chat history.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def days_ago(iso_ts: str) -> str:
    if not iso_ts:
        return "unknown date"
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        if delta.days == 0:
            return "today"
        if delta.days == 1:
            return "yesterday"
        return f"{delta.days} days ago"
    except ValueError:
        return iso_ts


def excerpt(text: str, query: str, context: int = 90) -> str:
    """Return the first occurrence of query in text with surrounding context."""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[: context * 2].replace("\n", " ")
    start = max(0, idx - context)
    end = min(len(text), idx + len(query) + context)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + text[start:end].replace("\n", " ") + suffix


def cmd_search(conn: sqlite3.Connection, query: str, limit: int, snippets: int) -> None:
    like = f"%{query}%"
    # Conversations whose title OR any message content matches, ranked by match count.
    rows = conn.execute(
        """
        SELECT c.id, c.title, c.category, c.created_at, c.updated_at,
               COUNT(m.id) AS match_count
        FROM workspace_conversations c
        LEFT JOIN workspace_messages m
               ON m.conversation_id = c.id AND m.content LIKE ? COLLATE NOCASE
        WHERE c.title LIKE ? COLLATE NOCASE OR m.id IS NOT NULL
        GROUP BY c.id
        ORDER BY match_count DESC, c.updated_at DESC
        LIMIT ?
        """,
        (like, like, limit),
    ).fetchall()

    if not rows:
        print(f"No chats match '{query}'. Try different keywords or synonyms.")
        return

    print(f"{len(rows)} chat(s) match '{query}':\n")
    for r in rows:
        title = r["title"] or "(untitled)"
        print(f"[id {r['id']}] {title}")
        print(f"    folder: {r['category']} | last activity: {days_ago(r['updated_at'])} | message matches: {r['match_count']}")
        snips = conn.execute(
            """
            SELECT role, content, timestamp FROM workspace_messages
            WHERE conversation_id = ? AND content LIKE ? COLLATE NOCASE
            ORDER BY timestamp LIMIT ?
            """,
            (r["id"], like, snippets),
        ).fetchall()
        for s in snips:
            print(f"    {s['role']}: {excerpt(s['content'], query)}")
        print()
    print("Next step: read a promising chat in full with `read <id>`.")


def cmd_read(conn: sqlite3.Connection, conv_id: int, max_chars: int) -> None:
    conv = conn.execute(
        "SELECT * FROM workspace_conversations WHERE id = ?", (conv_id,)
    ).fetchone()
    if not conv:
        sys.exit(f"ERROR: no conversation with id {conv_id}")

    title = conv["title"] or "(untitled)"
    print(f"=== [id {conv['id']}] {title} ===")
    print(f"folder: {conv['category']} | model: {conv['model']} | created: {days_ago(conv['created_at'])} | last activity: {days_ago(conv['updated_at'])}")
    if conv["summary"]:
        print(f"summary: {conv['summary']}")
    print()

    msgs = conn.execute(
        "SELECT role, content, timestamp FROM workspace_messages WHERE conversation_id = ? ORDER BY timestamp",
        (conv_id,),
    ).fetchall()
    for m in msgs:
        content = m["content"]
        if max_chars and len(content) > max_chars:
            content = content[:max_chars] + f"... [truncated, {len(m['content'])} chars total]"
        print(f"--- {m['role']} ({m['timestamp']}) ---")
        print(content)
        print()
    print(f"({len(msgs)} messages total)")


def cmd_list(conn: sqlite3.Connection, days: int, limit: int) -> None:
    rows = conn.execute(
        """
        SELECT id, title, category, updated_at,
               (SELECT COUNT(*) FROM workspace_messages m WHERE m.conversation_id = c.id) AS msg_count
        FROM workspace_conversations c
        WHERE updated_at >= datetime('now', ?)
        ORDER BY updated_at DESC LIMIT ?
        """,
        (f"-{days} days", limit),
    ).fetchall()
    print(f"{len(rows)} chat(s) active in the last {days} days:\n")
    for r in rows:
        title = r["title"] or "(untitled)"
        print(f"[id {r['id']}] {title} — {r['category']} | {days_ago(r['updated_at'])} | {r['msg_count']} messages")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search and read AutoForge workspace chats.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to workspace.db (default: ~/.autoforge/workspace.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search chat titles and message content")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--snippets", type=int, default=3, help="Matching snippets to show per chat")

    p_read = sub.add_parser("read", help="Print a full conversation")
    p_read.add_argument("conversation_id", type=int)
    p_read.add_argument("--max-chars", type=int, default=2000, help="Truncate each message to this length (0 = no limit)")

    p_list = sub.add_parser("list", help="List recent chats")
    p_list.add_argument("--days", type=int, default=14)
    p_list.add_argument("--limit", type=int, default=30)

    args = parser.parse_args()
    conn = connect(args.db)
    try:
        if args.command == "search":
            cmd_search(conn, args.query, args.limit, args.snippets)
        elif args.command == "read":
            cmd_read(conn, args.conversation_id, args.max_chars)
        elif args.command == "list":
            cmd_list(conn, args.days, args.limit)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
