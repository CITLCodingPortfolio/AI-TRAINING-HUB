#!/usr/bin/env python3
import argparse, collections, datetime as dt, glob, json, os, re, sys

def parse_iso(ts: str):
    if not ts: return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return dt.datetime.fromisoformat(ts)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True)
    ap.add_argument("--dir", default=os.path.expanduser("~/.local/share/citl/online/x"))
    ap.add_argument("--days", type=int, default=3650)
    args = ap.parse_args()

    kw = args.keyword.strip()
    rx = re.compile(re.escape(kw), re.IGNORECASE)
    paths = sorted(glob.glob(os.path.join(args.dir, "*.jsonl")))
    if not paths:
        print(f"No cache files in: {args.dir}")
        return

    cutoff = dt.datetime.utcnow() - dt.timedelta(days=args.days)
    total = 0
    by_author = collections.Counter()
    by_day = collections.Counter()
    samples = []

    for p in paths:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    it = json.loads(line)
                except Exception:
                    continue
                text = (it.get("text") or "")
                if not (rx.search(text) or kw.lower() in (it.get("keyword","").lower())):
                    continue
                ts = parse_iso(it.get("timestamp","")) or parse_iso(it.get("collected_at",""))
                if ts and ts < cutoff:
                    continue

                total += 1
                by_author[it.get("author","") or "unknown"] += 1
                daykey = (ts.date().isoformat() if ts else "unknown_date")
                by_day[daykey] += 1
                if len(samples) < 12 and text:
                    samples.append((it.get("url",""), text[:280].replace("\n"," ")))

    print("\n=== Local Cached Post Assessment ===")
    print(f"keyword: {kw}")
    print(f"cache_dir: {args.dir}")
    print(f"matched_posts: {total}")

    print("\nTop authors:")
    for a,c in by_author.most_common(10):
        print(f"  {a:20} {c}")

    print("\nActivity by day (top 10):")
    for d,c in by_day.most_common(10):
        print(f"  {d} {c}")

    print("\nSamples:")
    for url, txt in samples:
        print(f"- {txt}")
        if url: print(f"  {url}")

if __name__ == "__main__":
    main()
