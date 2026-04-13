#!/usr/bin/env python3
"""
Scraping Result Analyzer
Analyzes the scraped_articles.csv file to provide statistics on:
- Total data entries
- Successful scrapes (with content)
- Failed scrapes (with error messages)
- Error type breakdown
"""

import csv
import sys
from collections import Counter
from pathlib import Path


def analyze_scraping_results(csv_path):
    """Analyze scraping results from CSV file."""

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    total = 0
    success = 0
    failed = 0
    error_messages = []
    success_domains = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            url = row.get("url", "").strip()
            title = row.get("title", "").strip()
            content = row.get("content", "").strip()
            error = row.get("error", "").strip()

            # Check if error field is populated
            if error:
                failed += 1
                # Clean up error message for counting
                error_clean = error.strip().replace('"', "")
                if error_clean:
                    error_messages.append(error_clean)
            elif not content or len(content) < 50:
                # Content is too short, consider as failed
                failed += 1
                error_messages.append("Empty or too short content")
            else:
                success += 1
                # Extract domain from URL
                if url:
                    domain = url.split("/")[2] if "://" in url else url.split("/")[0]
                    success_domains.append(domain)

    # Print analysis results
    print("=" * 60)
    print("SCRAPING RESULT ANALYSIS")
    print("=" * 60)
    print(f"\nFile: {csv_path}")
    print(f"\n{'METRIC':<30} {'COUNT':<10} {'PERCENTAGE'}")
    print("-" * 60)
    print(f"{'Total Entries':<30} {total:<10} {'100.0%'}")
    print(f"{'Successful Scrapes':<30} {success:<10} {success / total * 100:.1f}%")
    print(f"{'Failed Scrapes':<30} {failed:<10} {failed / total * 100:.1f}%")

    if success > 0:
        print("\n" + "=" * 60)
        print("SUCCESSFUL SCRAPES BY DOMAIN")
        print("=" * 60)
        domain_counts = Counter(success_domains)
        for domain, count in domain_counts.most_common():
            print(f"  {domain:<40} {count}")

    if error_messages:
        print("\n" + "=" * 60)
        print("TOP ERROR MESSAGES")
        print("=" * 60)
        error_counts = Counter(error_messages)
        for error, count in error_counts.most_common(15):
            # Truncate long error messages
            error_display = error[:60] + "..." if len(error) > 60 else error
            print(f"  {count:>4}x  {error_display}")

    # Content length statistics for successful scrapes
    if success > 0:
        print("\n" + "=" * 60)
        print("CONTENT STATISTICS (Successful Scrapes)")
        print("=" * 60)

        content_lengths = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                error = row.get("error", "").strip()
                content = row.get("content", "").strip()
                if not error and content and len(content) >= 50:
                    content_lengths.append(len(content))

        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            min_length = min(content_lengths)
            max_length = max(content_lengths)

            print(f"  Average content length: {avg_length:,.0f} characters")
            print(f"  Shortest content:       {min_length:,} characters")
            print(f"  Longest content:        {max_length:,} characters")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Out of {total:,} URLs attempted:")
    print(f"  ✓ {success:,} ({success / total * 100:.1f}%) successfully scraped")
    print(f"  ✗ {failed:,} ({failed / total * 100:.1f}%) failed")

    if success == 0:
        print("\n⚠️  Warning: No successful scrapes found!")
    elif success / total < 0.5:
        print("\n⚠️  Warning: Less than 50% success rate")
    else:
        print("\n✓ Good success rate!")

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "success_rate": success / total * 100 if total > 0 else 0,
    }


if __name__ == "__main__":
    csv_file = Path(__file__).parent / "scraped_articles.csv"

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]

    analyze_scraping_results(csv_file)
