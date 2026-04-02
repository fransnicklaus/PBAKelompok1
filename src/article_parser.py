from typing import Callable, Optional

from newspaper import Article


class ArticleParseError(Exception):
    pass


def parse_article(
    html_content: Optional[str],
    url: str,
    language: str = "id",
) -> dict:
    if not html_content:
        return {
            "title": "",
            "text": "NO_CONTENT_EXTRACTED",
            "authors": [],
            "publish_date": None,
            "top_image": "",
            "images": [],
            "keywords": [],
            "summary": "",
        }

    try:
        article = Article(url, language=language)
        article.set_html(html_content)
        article.parse()
        article.nlp()
    except Exception as e:
        raise ArticleParseError(f"Failed to parse article at {url}: {e}") from e

    return {
        "title": article.title or "",
        "text": article.text or "",
        "authors": article.authors or [],
        "publish_date": article.publish_date,
        "top_image": article.top_image or "",
        "images": list(article.images) if article.images else [],
        "keywords": article.keywords or [],
        "summary": article.summary or "",
    }


def parse_batch(
    articles: list[dict],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[dict]:
    results = []
    total = len(articles)
    for i, item in enumerate(articles):
        try:
            parsed = parse_article(item.get("html_content"), item["url"])
        except ArticleParseError as e:
            print(f"[article_parser] Error: {e}")
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
        results.append(parsed)
        if progress_callback:
            progress_callback(i + 1, total)
    return results
