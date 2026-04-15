#!/usr/bin/env python3
"""
Preprocessing script for scraped MBG articles.
Input:  tugas-week-5/scraped_articles.csv
Output: tugas-week-7/preprocessed_articles.csv

Output columns:
  judul              - article title
  link               - article URL
  portal_berita      - news source extracted from URL domain
  text_berita        - raw article content
  text_berita_clean  - cleaned and stemmed text
"""

import csv
import re
import unicodedata
from pathlib import Path

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

stemmer = StemmerFactory().create_stemmer()
stopword_remover = StopWordRemoverFactory().create_stop_word_remover()

# Boilerplate phrases common in Indonesian scraped news
NOISE_PATTERNS = [
    r"\biklan\b",
    r"\bgabung\s+tempo\s+circle\b",
    r"\bdengarkan\s+artikel\b",
    r"^\s*bagikan\s*$",           # only when the entire line is "Bagikan"
    r"\bberita\s+tempo\s+plus\b",
    r"\bbaca\s+juga\s*:?",
    r"\blihat\s+juga\s*:?",
    r"\bbaca\s+selengkapnya\s*:?",
    r"\bartikel\s+terkait\s*:?",
    r"^\s*editor\s*:.*",
    r"^\s*reporter\s*:.*",
    r"^\s*penulis\s*:.*",
    r"copyright\s*©.*",
    r"\ball\s+rights\s+reserved\b",
    r"\bfollow\s+kami\s+di\b",
    r"\bsubscribe\s+sekarang\b",
    r"\bdapatkan\s+update\b",
    r"\bpodcast\s+rekomendasi\b",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)

# Domain → readable portal name
PORTAL_MAP = {
    "tempo.co": "Tempo",
    "kompas.com": "Kompas",
    "tribunnews.com": "Tribun",
    "tribratanews.polri.go.id": "Tribrata",
    "sindonews.com": "Sindonews",
    "liputan6.com": "Liputan6",
    "detik.com": "Detik",
    "cnnindonesia.com": "CNN Indonesia",
    "antaranews.com": "Antara",
    "republika.co.id": "Republika",
    "jpnn.com": "JPNN",
    "okezone.com": "Okezone",
    "merdeka.com": "Merdeka",
    "suara.com": "Suara",
    "medcom.id": "Medcom",
    "wartaekonomi.co.id": "Warta Ekonomi",
    "bisnis.com": "Bisnis",
    "cnbcindonesia.com": "CNBC Indonesia",
    "bbc.com": "BBC",
    "beritajatim.com": "Berita Jatim",
    "hukumonline.com": "Hukumonline",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_portal(url: str) -> str:
    """Extract readable portal name from URL domain."""
    try:
        domain = url.split("://", 1)[1].split("/")[0].lstrip("www.")
    except IndexError:
        return ""
    for key, name in PORTAL_MAP.items():
        if key in domain:
            return name
    # Fallback: return domain without www./TLD
    parts = domain.split(".")
    return parts[0].capitalize() if parts else domain


def remove_noise(text: str) -> str:
    """Remove boilerplate lines from scraped content."""
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if NOISE_RE.search(line):
            continue
        if len(line) < 20:  # skip very short fragments (nav items, etc.)
            continue
        clean_lines.append(line)
    return " ".join(clean_lines)


def normalize(text: str) -> str:
    """Lowercase, normalize unicode, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"https?://\S+", "", text)          # remove URLs
    text = re.sub(r"\S+@\S+\.\S+", "", text)          # remove emails
    text = re.sub(r"&[a-z]+;", " ", text)             # HTML entities
    text = re.sub(r"[^\w\s]", " ", text)              # punctuation
    text = re.sub(r"\d+", "", text)                   # numbers
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_text(text: str) -> str:
    """Full preprocessing pipeline."""
    text = remove_noise(text)
    text = normalize(text)
    text = stopword_remover.remove(text)
    text = stemmer.stem(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    input_path = Path(__file__).parent.parent / "out" / "scraped_articles.csv"
    output_path = Path(__file__).parent / "preprocessed_articles.csv"

    rows_out = []
    skipped = 0

    with open(input_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} articles...")

    for i, row in enumerate(rows, 1):
        if i % 50 == 0:
            print(f"  {i}/{len(rows)}")

        error = row.get("error", "").strip()
        content = row.get("content", "").strip()

        # Skip failed / empty scrapes
        if error or not content or len(content) < 50:
            skipped += 1
            continue

        url = row.get("url", "").strip()
        title = row.get("title", "").strip()

        rows_out.append({
            "judul": title,
            "link": url,
            "portal_berita": extract_portal(url),
            "text_berita": content,
            "text_berita_clean": clean_text(content),
        })

    fieldnames = ["judul", "link", "portal_berita", "text_berita", "text_berita_clean"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"\nDone.")
    print(f"  Output:  {output_path}")
    print(f"  Written: {len(rows_out)} articles")
    print(f"  Skipped: {skipped} (failed/empty scrapes)")


if __name__ == "__main__":
    main()
