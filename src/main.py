import asyncio
import os
from typing import Optional

import pandas as pd
from tqdm import tqdm

from article_parser import parse_article
from rss_fetcher import fetch_rss_feed, read_keywords
from url_resolver import URLResolver


async def scrape_news_pipeline(
    keywords: list[str],
    output_file: str,
    limit_per_keyword: Optional[int] = None,
    max_concurrent: int = 5,
    show_progress: bool = True,
) -> pd.DataFrame:
    # Step 1: Fetch RSS feeds
    all_entries = []
    for keyword in tqdm(keywords, desc="Fetching RSS feeds", disable=not show_progress):
        entries = fetch_rss_feed(keyword, limit=limit_per_keyword)
        for entry in entries:
            entry["keyword"] = keyword
        all_entries.extend(entries)

    print(f"\nTotal entries fetched: {len(all_entries)}")

    # Deduplicate by Google redirect URL
    seen_links = set()
    unique_entries = []
    for entry in all_entries:
        if entry["link"] not in seen_links:
            seen_links.add(entry["link"])
            unique_entries.append(entry)

    print(f"Unique entries after dedup: {len(unique_entries)}")

    # Step 2: Resolve redirect URLs with Playwright
    redirect_urls = [e["link"] for e in unique_entries]
    resolved: list[tuple[str, Optional[str]]] = []

    with tqdm(
        total=len(redirect_urls), desc="Resolving URLs", disable=not show_progress
    ) as pbar:

        async def progress_callback(total, completed, current_url):
            pbar.n = completed
            pbar.set_postfix_str(current_url[:50])
            pbar.refresh()

        async with URLResolver(max_concurrent=max_concurrent) as resolver:
            resolved = await resolver.resolve_batch(redirect_urls, progress_callback)

    # Step 3: Parse article content with newspaper4k
    rows = []
    parse_iter = tqdm(
        zip(unique_entries, resolved),
        total=len(unique_entries),
        desc="Parsing articles",
        disable=not show_progress,
    )
    for entry, (final_url, html_content) in parse_iter:
        resolution_status = "success"
        if final_url == entry["link"] and html_content is None:
            resolution_status = "failed: url_resolution_error"

        try:
            parsed = parse_article(html_content, final_url)
            parse_status = "success"
        except Exception as e:
            parsed = {
                "title": "",
                "text": "FAILED_TO_PARSE",
                "authors": [],
                "publish_date": None,
                "top_image": "",
                "images": [],
                "keywords": [],
                "summary": "",
            }
            parse_status = f"failed: {e}"

        rows.append(
            {
                "keyword": entry["keyword"],
                "judul": entry["title"],
                "tanggal": parsed["publish_date"],
                "sumber": entry["source"],
                "source_url": entry["source_url"],
                "url_google": entry["link"],
                "url_resolved": final_url,
                "konten": parsed["text"],
                "authors": ", ".join(parsed["authors"]),
                "tags": ", ".join(parsed["keywords"]),
                "top_image": parsed["top_image"],
                "resolution_status": resolution_status,
                "parse_status": parse_status,
            }
        )

    # Step 4: Save to CSV
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["url_resolved"])

    os.makedirs(os.path.dirname(output_file), exist_ok=True) if os.path.dirname(
        output_file
    ) else None
    df.to_csv(output_file, index=False)
    print(f"\nDone! {len(df)} unique articles saved to {output_file}")
    return df


def run_scraper(
    keyword_file: str,
    output_file: str,
    limit_per_keyword: Optional[int] = None,
    max_concurrent: int = 5,
    headless: bool = True,
    show_progress: bool = True,
):
    keywords = read_keywords(keyword_file)
    print(f"Found {len(keywords)} keywords.")
    asyncio.run(
        scrape_news_pipeline(
            keywords=keywords,
            output_file=output_file,
            limit_per_keyword=limit_per_keyword,
            max_concurrent=max_concurrent,
            show_progress=show_progress,
        )
    )


if __name__ == "__main__":
    run_scraper(
        keyword_file="src/keyword.txt",
        output_file="berita_all_keywords.csv",
        limit_per_keyword=None,
        max_concurrent=5,
    )
