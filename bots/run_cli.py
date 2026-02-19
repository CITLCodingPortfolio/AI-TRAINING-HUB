import argparse
from pathlib import Path
from typing import Dict
from bots.registry import list_bots, load_bot_callable
def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")
def main():
    ap = argparse.ArgumentParser(description="AI-Training-Hub Bot CLI Runner")
    ap.add_argument("--bot", required=True, help="bot_id (see --list)")
    ap.add_argument("--input-file", default="", help="Primary input text file")
    ap.add_argument("--file", action="append", default=[], help="Extra file paths (repeatable)")
    ap.add_argument("--list", action="store_true", help="List bots and exit")
    args = ap.parse_args()
    if args.list:
        for b in list_bots():
            print(f'{b["bot_id"]}\t{b["title"]}')
        return
    files: Dict[str, str] = {}
    if args.input_file:
        p = Path(args.input_file)
        files[p.name] = read_text(p)
        prompt = files[p.name]
    else:
        prompt = ""
    for fp in args.file:
        p = Path(fp)
        files[p.name] = read_text(p)
    fn = load_bot_callable(args.bot)
    out = fn(prompt, files)
    print(out)
if __name__ == "__main__":
    main()
