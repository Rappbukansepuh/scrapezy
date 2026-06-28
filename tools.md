install library
pip install -r requirements.txt

# tools by @rapzding

contoh penggunaan 
# Scrape 1 halaman saja
  python scraper.py https://example.com

# Crawl seluruh internal link (maks 20 halaman)
  python scraper.py https://example.com --crawl --max-pages 20

# Custom output file dan delay
  python scraper.py https://example.com --crawl --output hasil.csv --delay 2.0

# python scraper.py https://www.tokopedia.com/ --crawl --proxy-file proxies.txt --delay 2.1 --jitter 1.0 --max-retries 4

Fitur yang tersedia:
  - --crawl — ikuti link internal otomatis
  - --max-pages — batas jumlah halaman (default: 10)
  - --delay — jeda antar request agar tidak di-ban (default: 1 detik)
  - --output — nama file CSV output
  - --jitter — tambahan random delay agar pola tidak terlalu predictable
  - Auto backoff saat kena HTTP 429 (Too Many Requests), baca header Retry-After
  - Retry otomatis untuk error 500/502/503/504 dengan exponential backoff

    Output CSV berisi kolom: url, title, text_preview, links_found.