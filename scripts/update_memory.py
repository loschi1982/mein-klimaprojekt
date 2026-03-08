#!/usr/bin/env python3
"""
update_memory.py – Aktualisiert project_memory.json nach Abschluss einer Aufgabe.

Verwendung:
  python scripts/update_memory.py --team data-ingestion --task "co2-download" --status done
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


MEMORY_FILE = Path(__file__).parent.parent / "project_memory.json"
LOG_DIR = Path(__file__).parent.parent / "memory" / "team_logs"


def main():
    parser = argparse.ArgumentParser(description="Projektgedächtnis aktualisieren")
    parser.add_argument("--team", required=True, help="Team-Name (z.B. data-ingestion)")
    parser.add_argument("--task", required=True, help="Aufgabenname")
    parser.add_argument("--status", choices=["done", "in-progress", "blocked"], default="done")
    parser.add_argument("--note", default="", help="Optionale Notiz")
    args = parser.parse_args()

    # project_memory.json laden
    if not MEMORY_FILE.exists():
        print(f"Fehler: {MEMORY_FILE} nicht gefunden.", file=sys.stderr)
        sys.exit(1)

    with open(MEMORY_FILE) as f:
        memory = json.load(f)

    now = datetime.now(timezone.utc).isoformat()

    # Team-Eintrag aktualisieren
    if args.team not in memory["teams"]:
        print(f"Fehler: Team '{args.team}' nicht in project_memory.json gefunden.", file=sys.stderr)
        sys.exit(1)

    team = memory["teams"][args.team]
    team["last_update"] = now

    if args.status == "done":
        if args.task not in team["completed_tasks"]:
            team["completed_tasks"].append(args.task)
        if args.task in team["open_tasks"]:
            team["open_tasks"].remove(args.task)
        team["status"] = "in-progress"
    elif args.status == "in-progress":
        if args.task not in team["open_tasks"]:
            team["open_tasks"].append(args.task)
        team["status"] = "in-progress"
    elif args.status == "blocked":
        if args.task not in team["blockers"]:
            team["blockers"].append(args.task)

    # Datei speichern
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

    # Team-Log schreiben
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{args.team}.log"
    with open(log_file, "a") as f:
        note = f" | {args.note}" if args.note else ""
        f.write(f"[{now}] {args.status.upper()}: {args.task}{note}\n")

    print(f"Gedächtnis aktualisiert: Team '{args.team}', Aufgabe '{args.task}' → {args.status}")


if __name__ == "__main__":
    main()
