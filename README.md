# 🕷️ Scrapezy

> Simple yet powerful Python web scraper dengan fitur **proxy rotation** & **smart rate limiting**.
> Output langsung ke file **CSV** — siap dianalisis di Excel atau Google Sheets.

<br>

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

<br>

---

## 📋 Daftar Isi

- [Instalasi](#-instalasi)
- [Cara Pakai](#-cara-pakai)
- [Argumen](#️-argumen--options)
- [Output CSV](#-output-csv)
- [Fitur](#️-fitur)
- [Disclaimer](#️-disclaimer)

---

## 📦 Instalasi

```bash
# Clone repo
git clone https://github.com/Rappbukansepuh/scrapezy.git
cd scrapezy

# Install dependencies
pip install -r requirements.txt
```

> **Requirements:** `requests`, `beautifulsoup4`, `lxml`

<br>

---

## 🚀 Cara Pakai

### Scrape 1 halaman saja
```bash
python scraper.py https://example.com
```

### Crawl seluruh internal link (maks 20 halaman)
```bash
python scraper.py https://example.com --crawl --max-pages 20
```

### Custom output file & delay
```bash
python scraper.py https://example.com --crawl --output hasil.csv --delay 2.0
```

### Dengan proxy & rate limiting
```bash
python scraper.py https://www.tokopedia.com/ \
  --crawl \
  --proxy-file proxies.txt \
  --delay 2.1 \
  --jitter 1.0 \
  --max-retries 4
```

> **Format `proxies.txt`** — satu proxy per baris:
> ```
> http://123.45.67.89:8080
> http://user:pass@98.76.54.32:3128
> ```

<br>

---

## ⚙️ Argumen / Options

| Argumen | Default | Keterangan |
|---|---|---|
| `url` | *(wajib)* | URL pertama yang akan di-scrape |
| `--crawl` | `False` | Ikuti internal link otomatis |
| `--max-pages` | `10` | Batas maksimum halaman yang di-scrape |
| `--delay` | `1.0` | Jeda minimum antar request (detik) |
| `--jitter` | `0.5` | Tambahan delay random agar tidak terdeteksi bot |
| `--output` | `output.csv` | Nama file CSV hasil output |
| `--proxy-file` | *(opsional)* | Path ke file `.txt` berisi daftar proxy |
| `--max-retries` | `3` | Jumlah maksimum retry saat request gagal |

<br>

---

## 📊 Output CSV

File CSV hasil scraping berisi kolom berikut:

| Kolom | Keterangan |
|---|---|
| `url` | URL halaman yang di-scrape |
| `title` | Judul halaman (`<title>` tag) |
| `text_preview` | Cuplikan teks 300 karakter pertama |
| `links_found` | Jumlah link yang ditemukan di halaman |

<br>

---

## 🛡️ Fitur

- **Proxy Rotation** — Rotasi proxy otomatis (round-robin), proxy mati langsung dibuang
- **Smart Rate Limiting** — Delay + jitter acak agar tidak terdeteksi sebagai bot
- **Auto Retry** — Retry otomatis untuk error `500`, `502`, `503`, `504`
- **429 Handling** — Backoff otomatis saat kena *Too Many Requests*, baca header `Retry-After`
- **Exponential Backoff** — Setiap retry, waktu tunggu berlipat ganda

<br>

---

## 👤 Author

**@rapzding** — [GitHub](https://github.com/Rappbukansepuh)

<br>

---

## ⚠️ Disclaimer

> Tool ini dibuat untuk keperluan **edukasi dan riset**.
> Pastikan scraping dilakukan sesuai dengan **Terms of Service** website target
> dan tidak melanggar regulasi yang berlaku.
