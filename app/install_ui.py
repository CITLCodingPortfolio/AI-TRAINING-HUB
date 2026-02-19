import streamlit as st
def summarize_pip_log(log_text: str, max_lines: int = 25) -> dict:
    lines = (log_text or "").splitlines()
    filtered = []
    skipped = 0
    for ln in lines:
        if "Requirement already satisfied:" in ln:
            skipped += 1
            continue
        filtered.append(ln)
    tail_lines = filtered[-max_lines:] if len(filtered) > max_lines else filtered
    status = "success"
    if any(("ERROR:" in ln) or ("Traceback" in ln) for ln in lines):
        status = "error"
    elif any(("WARNING:" in ln) or ("warning" in ln.lower()) for ln in lines):
        status = "warning"
    return {"status": status, "skipped": skipped, "tail": "\n".join(tail_lines), "full": "\n".join(lines)}
def render_install_log(out_all: list[str]) -> None:
    joined = "\n\n".join([x for x in out_all if x])
    info = summarize_pip_log(joined, max_lines=25)
    if info["status"] == "success":
        st.success("✅ Install completed (no fatal errors detected).")
    elif info["status"] == "warning":
        st.warning("⚠️ Install completed with warnings.")
    else:
        st.error("❌ Install encountered errors. Expand details below.")
    st.caption(f"Filtered {info['skipped']} 'already satisfied' lines.")
    st.text_area("Log (last 25 meaningful lines)", value=info["tail"], height=180)
    with st.expander("Show full install log (IT/instructor)", expanded=False):
        st.text_area("Full pip output", value=info["full"], height=320)

