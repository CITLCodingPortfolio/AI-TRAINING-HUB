from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from bots.registry import get_registry
console = Console()
def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")
def run_fallback(text: str, input_file: Optional[str], files: List[str]) -> Dict[str, Any]:
    out = {"bot": "fallback_bot", "ok": True}
    if text:
        out["text"] = text
    if input_file:
        t = _read_text(input_file)
        out["input_file"] = input_file
        out["input_len"] = len(t)
        out["input_lines"] = t.count("\n") + 1
    if files:
        stats = []
        for f in files:
            t = _read_text(f)
            stats.append({"file": f, "len": len(t), "lines": t.count("\n") + 1})
        out["files"] = stats
    return out
def run_it_ticket(input_text: str, policy_text: str, mode: str) -> Dict[str, Any]:
    # deterministic demo logic (LLM optional later)
    steps = []
    if "AUTH_FAILED" in input_text.upper():
        steps += [
            "Verify account is enabled",
            "Reset password (if needed) and re-test login",
            "Confirm MFA enrollment",
            "Ensure user is in VPN_Users group",
            "Re-test VPN connection",
        ]
    if "new hire" in input_text.lower():
        steps.append("Confirm manager approval + ticket number for onboarding access")
    if policy_text:
        steps.append("Cross-check against policy excerpt and document actions in ticket")
    if mode == "escalate":
        result = {
            "summary": "Escalation requested: VPN AUTH_FAILED for onboarding user. See checklist + policy alignment.",
            "next_actions": steps[:3],
            "escalation": "If unresolved after MFA/group checks, escalate to IAM/network team with logs.",
        }
    elif mode == "checklist":
        result = {"checklist": steps}
    else:
        result = {"triage_plan": steps, "notes": "Record steps + outcomes in the ticket. Confirm access deadline."}
    return {"bot": "it_ticket_bot", "ok": True, "result": result}
def run_deploy_ops(files: List[str], target: str) -> Dict[str, Any]:
    checks = []
    cmds = []
    for f in files:
        p = Path(f)
        name = p.name.lower()
        text = p.read_text(encoding="utf-8", errors="replace")
        if "docker" in target or target == "all":
            if "compose" in name or "docker-compose" in name:
                checks += [f"[docker] Found compose file: {p.name}", "[docker] Validate ports/env, run: docker compose up -d", "[docker] Rollback: docker compose down"]
                cmds += ["docker compose config", "docker compose up -d", "docker compose logs -f --tail 200"]
        if "kubernetes" in target or target == "all":
            if name.endswith(".yaml") or name.endswith(".yml"):
                if "kind: Job" in text:
                    checks += [f"[k8s] Found Job manifest: {p.name}", "[k8s] Validate namespace + image tags", "[k8s] Run: kubectl apply -f <file>"]
                    cmds += [f"kubectl apply -f {p.name}", "kubectl get jobs -w", "kubectl logs -l job-name=<name> --tail=200"]
        if "slurm" in target or target == "all":
            if name.endswith(".sh") and "#SBATCH" in text:
                checks += [f"[slurm] Found SLURM script: {p.name}", "[slurm] Validate partition/gres/time", "[slurm] Run: sbatch <file>"]
                cmds += [f"sbatch {p.name}", "squeue -u $USER", "sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS"]
    return {"bot": "deploy_ops_bot", "ok": True, "checks": checks, "suggested_cmds": cmds}
def main():
    reg = get_registry()
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True, help="bot id (see registry)")
    ap.add_argument("--text", default="", help="inline text input")
    ap.add_argument("--input-file", default="", help="path to primary input file")
    ap.add_argument("--file", action="append", default=[], help="extra file(s)")
    ap.add_argument("--mode", default="triage")
    ap.add_argument("--target", default="all")
    ap.add_argument("--json", action="store_true", help="output raw json only")
    args = ap.parse_args()
    bot_id = args.bot.strip()
    if bot_id not in reg:
        raise SystemExit(f"Unknown bot: {bot_id}. Known: {', '.join(sorted(reg.keys()))}")
    input_text = args.text
    if args.input_file:
        input_text = (Path(args.input_file).read_text(encoding="utf-8", errors="replace"))
    files = list(args.file or [])
    if bot_id == "fallback_bot":
        out = run_fallback(args.text, args.input_file or None, files)
    elif bot_id == "it_ticket_bot":
        policy = ""
        if files:
            policy = Path(files[0]).read_text(encoding="utf-8", errors="replace")
        out = run_it_ticket(input_text=input_text or "", policy_text=policy, mode=args.mode)
    elif bot_id == "deploy_ops_bot":
        use_files = files[:] or ([args.input_file] if args.input_file else [])
        out = run_deploy_ops(use_files, target=args.target)
    elif bot_id == "api_server_bot":
        # This bot is for API demos; CLI just echoes
        out = {"bot": "api_server_bot", "ok": True, "hint": "Use scripts/windows/start_api.ps1 then open /health and /bots."}
    else:
        out = {"bot": bot_id, "ok": True, "note": "Bot exists in registry but no implementation yet."}
    if args.json:
        print(json.dumps(out, indent=2))
        return
    meta = reg[bot_id]
    console.print(Panel.fit(f"[bold]{meta.name}[/bold] ([{meta.color}]{meta.bot_id}[/{meta.color}])", border_style=meta.color))
    console.print(json.dumps(out, indent=2))
if __name__ == "__main__":
    main()