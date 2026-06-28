"""
Web Scraper Tool — requests + BeautifulSoup
Features: proxy support, smart rate limiting, retry with backoff
Output: CSV
"""

import csv
import time
import random
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, fields, asdict
from typing import Optional


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Status codes that warrant a retry
RETRYABLE_CODES = {429, 500, 502, 503, 504}


@dataclass
class ScrapedItem:
    url: str
    title: str
    text_preview: str
    links_found: int


class RateLimiter:
    """Token-bucket rate limiter — enforces min delay with optional jitter."""

    def __init__(self, min_delay: float = 1.0, max_jitter: float = 0.5):
        self.min_delay = min_delay
        self.max_jitter = max_jitter
        self._last_request: float = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        jitter = random.uniform(0, self.max_jitter)
        wait_for = max(0.0, self.min_delay + jitter - elapsed)
        if wait_for > 0:
            print(f"  [RATE] Waiting {wait_for:.2f}s ...")
            time.sleep(wait_for)
        self._last_request = time.monotonic()


class ProxyManager:
    """Round-robin proxy rotation from a list."""

    def __init__(self, proxies: list[str]):
        self._proxies = proxies
        self._index = 0

    @classmethod
    def from_file(cls, path: str) -> "ProxyManager":
        with open(path, encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        print(f"[PROXY] Loaded {len(proxies)} proxies from {path}")
        return cls(proxies)

    def next(self) -> Optional[dict]:
        if not self._proxies:
            return None
        proxy = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        return {"http": proxy, "https": proxy}

    def remove_current(self) -> None:
        """Drop the last-used proxy (e.g. on 407 / connection error)."""
        bad = (self._index - 1) % len(self._proxies)
        removed = self._proxies.pop(bad)
        self._index = max(0, self._index - 1)
        print(f"  [PROXY] Removed bad proxy: {removed} ({len(self._proxies)} left)")


def fetch_page(
    url: str,
    rate_limiter: RateLimiter,
    proxy_manager: Optional[ProxyManager] = None,
    timeout: int = 10,
    max_retries: int = 3,
) -> Optional[BeautifulSoup]:
    backoff = 2.0

    for attempt in range(1, max_retries + 1):
        proxies = proxy_manager.next() if proxy_manager else None
        proxy_label = list(proxies.values())[0] if proxies else "direct"

        rate_limiter.wait()

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                proxies=proxies,
            )

            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", backoff))
                print(f"  [429] Rate-limited. Backing off {retry_after:.1f}s ...")
                time.sleep(retry_after)
                backoff *= 2
                continue

            if response.status_code in RETRYABLE_CODES:
                print(f"  [{response.status_code}] Retrying in {backoff:.1f}s (attempt {attempt}/{max_retries}) ...")
                time.sleep(backoff)
                backoff *= 2
                continue

            response.raise_for_status()
            print(f"  [OK] via {proxy_label}")
            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.ProxyError:
            print(f"  [PROXY ERROR] {proxy_label}")
            if proxy_manager:
                proxy_manager.remove_current()
        except requests.RequestException as e:
            print(f"  [ERROR] Attempt {attempt}/{max_retries}: {e}")
            time.sleep(backoff)
            backoff *= 2

    print(f"[FAIL] Gave up on {url} after {max_retries} attempts")
    return None


def parse_page(url: str, soup: BeautifulSoup) -> ScrapedItem:
    title = soup.title.string.strip() if soup.title else "N/A"
    body_text = soup.get_text(separator=" ", strip=True)
    text_preview = " ".join(body_text.split())[:300]

    links = soup.find_all("a", href=True)
    absolute_links = [
        urljoin(url, a["href"])
        for a in links
        if urlparse(urljoin(url, a["href"])).scheme in ("http", "https")
    ]

    return ScrapedItem(
        url=url,
        title=title,
        text_preview=text_preview,
        links_found=len(absolute_links),
    )


def collect_internal_links(
    base_url: str, soup: BeautifulSoup, max_links: int = 20
) -> list[str]:
    base_domain = urlparse(base_url).netloc
    seen: set[str] = set()
    result: list[str] = []

    for a in soup.find_all("a", href=True):
        full_url = urljoin(base_url, a["href"])
        parsed = urlparse(full_url)
        if (
            parsed.netloc == base_domain
            and parsed.scheme in ("http", "https")
            and full_url not in seen
            and not parsed.fragment
        ):
            seen.add(full_url)
            result.append(full_url)
            if len(result) >= max_links:
                break

    return result


def save_to_csv(items: list[ScrapedItem], output_file: str) -> None:
    if not items:
        print("[WARN] No data to save.")
        return

    fieldnames = [f.name for f in fields(ScrapedItem)]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))

    print(f"[OK] Saved {len(items)} rows to {output_file}")


def scrape(
    start_url: str,
    max_pages: int = 10,
    delay: float = 1.0,
    jitter: float = 0.5,
    output_file: str = "output.csv",
    crawl: bool = False,
    proxy_file: Optional[str] = None,
    max_retries: int = 3,
) -> None:
    rate_limiter = RateLimiter(min_delay=delay, max_jitter=jitter)
    proxy_manager = ProxyManager.from_file(proxy_file) if proxy_file else None

    visited: set[str] = set()
    queue = [start_url]
    results: list[ScrapedItem] = []

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue

        print(f"[FETCH] ({len(visited)+1}/{max_pages}) {url}")
        soup = fetch_page(url, rate_limiter, proxy_manager, max_retries=max_retries)
        if soup is None:
            visited.add(url)
            continue

        item = parse_page(url, soup)
        results.append(item)
        visited.add(url)
        print(f"  Title : {item.title}")
        print(f"  Links : {item.links_found}")

        if crawl:
            for link in collect_internal_links(url, soup, max_links=max_pages):
                if link not in visited:
                    queue.append(link)

    save_to_csv(results, output_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Web scraper with proxy & rate limiting → CSV")
    parser.add_argument("url", help="Starting URL to scrape")
    parser.add_argument(
        "--max-pages", type=int, default=10,
        help="Maximum pages to scrape (default: 10)"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Minimum delay in seconds between requests (default: 1.0)"
    )
    parser.add_argument(
        "--jitter", type=float, default=0.5,
        help="Max random jitter added to delay in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--output", default="output.csv",
        help="Output CSV file name (default: output.csv)"
    )
    parser.add_argument(
        "--crawl", action="store_true",
        help="Follow internal links and scrape multiple pages"
    )
    parser.add_argument(
        "--proxy-file",
        help="Path to a .txt file with one proxy per line (e.g. http://ip:port)"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3,
        help="Max retry attempts per page on failure (default: 3)"
    )
    args = parser.parse_args()

    scrape(
        start_url=args.url,
        max_pages=args.max_pages,
        delay=args.delay,
        jitter=args.jitter,
        output_file=args.output,
        crawl=args.crawl,
        proxy_file=args.proxy_file,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
