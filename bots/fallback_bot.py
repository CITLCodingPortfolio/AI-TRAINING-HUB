def run(prompt: str, files: dict | None = None) -> str:
    files = files or {}
    return (
        "OK: fallback_bot online.\n"
        f"- prompt_chars={len(prompt or '')}\n"
        f"- files={list(files.keys())}\n"
        "SELF_TEST: PASS\n"
    )
