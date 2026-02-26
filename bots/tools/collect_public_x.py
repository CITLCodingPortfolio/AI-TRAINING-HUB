#!/usr/bin/env python3
"""
Collect PUBLIC posts from X search results into local JSONL using Playwright.

Rules:
- No API keys.
- No bypass of login/CAPTCHA/anti-bot.
- If X requires login or blocks automation, this tool fails gracefully.

Use only where you have the right to collect/store the data and respect site terms.
"""
import argparse, datetime as dt, json, os, re, sys
from urllib.parse import quote_plus

def now_utc():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def safe_filename(s: str) -> str:
    s = re.sub(r"\s+", "_", (s or "").strip().lower())
    s = re.sub(r"[^a-z0-9_\-\.]+", "", s)
    return (s[:80] or "query")

def extract_status_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out-dir", default=os.path.expanduser("~/.local/share/citl/online/x"))
    ap.add_argument("--headful", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except Exception as e:
        print(f"[fail] playwright not available: {e}", file=sys.stderr)
        sys.exit(2)

    os.makedirs(args.out_dir, exist_ok=True)
    q = quote_plus(args.keyword)
    url = f"https://x.com/search?q={q}&src=typed_query&f=live"

    stamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(args.out_dir, f"x_{safe_filename(args.keyword)}_{stamp}.jsonl")

    items = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=(not args.headful))
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(20000)

        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        html = page.content().lower()
        if "x.com/i/flow/login" in html or ("log in" in html and "password" in html):
            raise RuntimeError("X requires login for this view. Not bypassing.")
        if "something went wrong" in html:
            raise RuntimeError("X returned an error page. Try later.")

        try:
            page.wait_for_selector("article", timeout=20000)
        except PWTimeout:
            raise RuntimeError("No articles found (blocked/layout change/network).")

        def grab():
            for a in page.query_selector_all("article"):
                try:
                    link = a.query_selector('a[href*="/status/"]')
                    href = link.get_attribute("href") if link else None
                    full = f"https://x.com{href}" if href and href.startswith("/") else (href or "")
                    tid = extract_status_id(full)
                    if not tid or tid in seen:
                        continue

                    txt_el = a.query_selector('div[data-testid="tweetText"]')
                    text = (txt_el.inner_text().strip() if txt_el else "").strip()

                    t_el = a.query_selector("time")
                    timestamp = t_el.get_attribute("datetime") if t_el else ""

                    handle = ""
                    user_a = a.query_selector('a[href^="/"][role="link"]')
                    if user_a:
                        h = user_a.get_attribute("href") or ""
                        if h.startswith("/") and "/status/" not in h and len(h) > 1:
                            handle = h[1:].split("/")[0]

                    items.append({
                        "source": "x_public_playwright",
                        "keyword": args.keyword,
                        "collected_at": now_utc(),
                        "tweet_id": tid,
                        "url": full,
                        "author": handle,
                        "timestamp": timestamp,
                        "text": text,
                    })
                    seen.add(tid)
                except Exception:
                    continue

        scrolls = 0
        while len(items) < args.limit and scrolls < 80:
            grab()
            if len(items) >= args.limit:
                break
            page.mouse.wheel(0, 2200)
            page.wait_for_timeout(900)
            scrolls += 1

        browser.close()

    with open(out_path, "w", encoding="utf-8") as f:
        for it in items[:args.limit]:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"[ok] wrote {min(len(items), args.limit)} items -> {out_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[fail] {e}", file=sys.stderr)
        sys.exit(2)
