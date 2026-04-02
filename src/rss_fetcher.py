import urllib.parse

import feedparser


class RSSFetchError(Exception):
    pass


def read_keywords(filepath: str) -> list[str]:
    keywords = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and line.lower() not in ["gemini said", "keyword"]:
                    keywords.append(line)
        return keywords
    except Exception as e:
        raise RSSFetchError(f"Failed to read keywords from {filepath}: {e}") from e


def fetch_rss_feed(
    keyword: str,
    region: str = "ID",
    language: str = "id",
    limit: int | None = None,
) -> list[dict]:
    safe_keyword = urllib.parse.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={safe_keyword}&hl={language}&gl={region}&ceid={region}:{language}"

    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        raise RSSFetchError(f"Failed to fetch RSS for '{keyword}': {e}") from e

    entries = feed.entries if limit is None else feed.entries[:limit]
    results = []
    for entry in entries:
        source_title = ""
        source_href = ""
        if hasattr(entry, "source"):
            source_title = entry.source.get("title", "")
            source_href = entry.source.get("href", "")

        results.append(
            {
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "source": source_title,
                "source_url": source_href,
                "pub_date": getattr(entry, "published", ""),
            }
        )

    return results


def fetch_all_feeds(
    keywords: list[str],
    limit_per_keyword: int | None = None,
    region: str = "ID",
    language: str = "id",
    progress_callback=None,
) -> list[dict]:
    all_entries = []
    for i, keyword in enumerate(keywords):
        if progress_callback:
            progress_callback(i, len(keywords), keyword)
        try:
            entries = fetch_rss_feed(
                keyword, region=region, language=language, limit=limit_per_keyword
            )
            for entry in entries:
                entry["keyword"] = keyword
            all_entries.extend(entries)
        except RSSFetchError as e:
            print(f"[rss_fetcher] Error for '{keyword}': {e}")
    return all_entries
