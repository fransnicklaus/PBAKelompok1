import feedparser
from newspaper import Article
import pandas as pd
import time
import os

def read_keywords(filepath):
    """Membaca keyword dari file teks, mengabaikan header dan baris kosong."""
    keywords = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Mengabaikan baris kosong dan header seperti 'Gemini said' atau 'Keyword'
                if line and line.lower() not in ['gemini said', 'keyword']:
                    keywords.append(line)
        return keywords
    except Exception as e:
        print(f"Gagal membaca file {filepath}: {e}")
        return []

def scrape_indo_news_batch(keywords, limit_per_keyword=500, output_file="berita_gabungan.csv"):
    all_results = []
    seen_urls = set()
    
    for topic in keywords:
        print(f"\n--- Mengambil berita untuk topik: '{topic}' ---")
        # Menggunakan format URL yang aman
        safe_topic = topic.replace(' ', '%20')
        # 'id' for Indonesian language, 'ID' for Indonesia region
        rss_url = f"https://news.google.com/rss/search?q={safe_topic}&hl=id&gl=ID&ceid=ID:id"
        feed = feedparser.parse(rss_url)
        
        print(f"Ditemukan {len(feed.entries)} artikel. Mulai mengambil data...")
        
        success_count = 0
        for entry in feed.entries[:limit_per_keyword]:
            # Hindari duplikat URL
            if entry.link in seen_urls:
                continue
                
            try:
                # Set language to 'id' for better parsing of Indonesian sites
                article = Article(entry.link, language='id') 
                article.download()
                article.parse()
                
                all_results.append({
                    'keyword': topic,
                    'judul': article.title,
                    'tanggal': article.publish_date,
                    'sumber': entry.source.get('title', 'N/A') if hasattr(entry, 'source') else 'N/A',
                    'url': entry.link,
                    'konten': article.text,
                    'tags': ', '.join(article.tags) if article.tags else ''
                })
                seen_urls.add(entry.link)
                success_count += 1
                print(f"Berhasil: {article.title[:50]}...")
                time.sleep(1.5) # Slightly longer delay for Indo servers
                
            except Exception as e:
                print(f"Gagal di {entry.link}: {e}")
                
        print(f"Selesai untuk '{topic}'. {success_count} artikel unik didapatkan.")
        time.sleep(3) # Jeda antar keyword agar tidak kena rate limit

    if all_results:
        df = pd.DataFrame(all_results)
        # Menghapus duplikat berdasarkan URL jika ada yang terlewat
        df = df.drop_duplicates(subset=['url'])
        df.to_csv(output_file, index=False)
        print(f"\nSelesai Keseluruhan! Total {len(df)} artikel unik disimpan di {output_file}.")
    else:
        print("\nTidak ada artikel yang berhasil diambil dari semua keyword.")

if __name__ == "__main__":
    keyword_file = "keyword.txt"
    if os.path.exists(keyword_file):
        keywords_to_scrape = read_keywords(keyword_file)
        if keywords_to_scrape:
            print(f"Ditemukan {len(keywords_to_scrape)} keyword untuk dicari.")
            # Batasi limit_per_keyword untuk testing jika perlu
            scrape_indo_news_batch(keywords_to_scrape, limit_per_keyword=500, output_file="berita_all_keywords.csv")
        else:
            print("Tidak ada keyword valid di dalam file.")
    else:
        print(f"File {keyword_file} tidak ditemukan di direktori ini.")
