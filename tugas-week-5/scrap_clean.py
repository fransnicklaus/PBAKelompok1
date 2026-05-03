#!/usr/bin/env python3
"""Create a cleaned CSV with only successful scrapes.

The script reads a scraping results CSV, removes failed rows, and writes a
new CSV containing only the article title and link.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def is_successful_scrape(row: dict[str, str]) -> bool:
    """Return True when the row looks like a successful scrape."""

    error = row.get("error", "").strip()
    content = row.get("content", "").strip()
    return not error and bool(content) and len(content) >= 50


def clean_scraping_csv(input_csv: str, output_csv: str) -> int:
    """Write a cleaned CSV with title and link columns only."""

    input_path = Path(input_csv)
    if not input_path.exists():
        print(f"Error: File not found: {input_csv}")
        sys.exit(1)

    output_path = Path(output_csv)
    kept_rows: list[dict[str, str]] = []

    with input_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            if not is_successful_scrape(row):
                continue

            title = row.get("title", "").strip()
            link = row.get("url", "").strip() or row.get("link", "").strip()
            if not title or not link:
                continue

            kept_rows.append({"title": title, "link": link})

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["title", "link"])
        writer.writeheader()
        writer.writerows(kept_rows)

    return len(kept_rows)


if __name__ == "__main__":
    default_input = Path(__file__).with_name("scraped_articles.csv")
    default_output = Path(__file__).with_name("scrap_clean.csv")

    input_csv = sys.argv[1] if len(sys.argv) > 1 else str(default_input)
    output_csv = sys.argv[2] if len(sys.argv) > 2 else str(default_output)

    kept = clean_scraping_csv(input_csv, output_csv)
    print(f"Saved {kept} cleaned rows to {output_csv}")