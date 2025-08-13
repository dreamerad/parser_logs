import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tabulate import tabulate


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process log files and generate reports"
    )

    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="Path to log file (can be specified multiple times)"
    )

    parser.add_argument(
        "--report",
        required=True,
        help="Type of report to generate (average)"
    )

    parser.add_argument(
        "--date",
        help="Filter logs by date (format: YYYY-MM-DD)"
    )

    return parser.parse_args()


def read_log_files(file_paths: List[str]) -> List[Dict]:
    entries = []

    for file_path in file_paths:
        path = Path(file_path)

        if not path.exists():
            print(f"Warning: File {file_path} does not exist, skipping...")
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON in {file_path} at line {line_num}: {e}")

        except (IOError, OSError) as e:
            print(f"Error reading file {file_path}: {e}")

    return entries


def filter_by_date(entries: List[Dict], date_filter: str) -> List[Dict]:
    filtered = []

    for entry in entries:
        timestamp = entry.get("@timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                entry_date = dt.strftime("%Y-%m-%d")
                if entry_date == date_filter:
                    filtered.append(entry)
            except (ValueError, AttributeError):
                continue

    return filtered


def generate_average_report(entries: List[Dict]) -> str:
    if not entries:
        return "No log entries found"

    stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})

    for entry in entries:
        url = entry.get("url", "")
        if url:
            endpoint = url.split("?")[0]
            response_time = entry.get("response_time", 0.0)

            stats[endpoint]["count"] += 1
            stats[endpoint]["total_time"] += response_time

    if not stats:
        return "No valid endpoints found"

    table_data = []
    for endpoint, data in stats.items():
        avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
        table_data.append([
            endpoint,
            data["count"],
            f"{avg_time:.3f}"
        ])

    table_data.sort(key=lambda x: x[1], reverse=True)

    table_data = [[i] + row for i, row in enumerate(table_data)]

    headers = ["", "handler", "total", "avg_response_time"]

    return tabulate(
        table_data,
        headers=headers,
        tablefmt="plain",
        colalign=("left", "left", "right", "right")
    )


def main():
    args = parse_arguments()

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            sys.exit(1)

    entries = read_log_files(args.file)

    if not entries:
        print("Error: No valid log entries found in the specified files.")
        sys.exit(1)

    if args.date:
        entries = filter_by_date(entries, args.date)
        if not entries:
            print(f"No log entries found for date {args.date}")
            sys.exit(0)

    if args.report == "average":
        report = generate_average_report(entries)
        print(report)
    # elif args.report == "user-agent": # Пример добавления нового фильтра
    #     report = generate_user_agent_report(entries)
    #     print(report)
    else:
        print(f"Error: Unknown report type '{args.report}'. Supported: average")
        sys.exit(1)


if __name__ == "__main__":
    main()
