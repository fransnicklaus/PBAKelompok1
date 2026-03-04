import feedparser
from newspaper import Article
import pandas as pd
import time

def scrape_indo_news(topic, limit=500): 
    # 'id' for Indonesian language, 'ID' for Indonesia region
    rss_url = f"https://news.google.com/rss/search?q={topic}&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(rss_url)
    
    results = []
    print(f"Ditemukan {len(feed.entries)} artikel. Mulai mengambil data...")

    for entry in feed.entries[:limit]:
        try:
            # Set language to 'id' for better parsing of Indonesian sites
            article = Article(entry.link, language='id') 
            article.download()
            article.parse()
            
            results.append({
                'judul': article.title,
                'tanggal': article.publish_date,
                'sumber': entry.source.get('title', 'N/A'),
                'url': entry.link,
                'konten': article.text
            })
            print(f"Berhasil: {article.title[:50]}...")
            time.sleep(1.5) # Slightly longer delay for Indo servers
            
        except Exception as e:
            print(f"Gagal di {entry.link}: {e}")

    df = pd.DataFrame(results)
    df.to_csv(f"berita_{topic}.csv", index=False)
    print(f"Selesai! {len(results)} artikel disimpan.")

# Contoh: Mencari tentang 'Ekonomi Digital'
scrape_indo_news("program_makan_gratis_pemerintah", limit=500)