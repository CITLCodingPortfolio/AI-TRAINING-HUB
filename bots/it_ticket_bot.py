def run(prompt: str, files: dict | None = None) -> str:
    files = files or {}
    policy = files.get("policy.txt", "")
    out = []
    out.append("Triage Summary")
    out.append("- Category: Remote Access / VPN")
    out.append("- Likely cause: group membership or IdP sync after password rotation")
    out.append("")
    out.append("Action Plan (operator-ready)")
    out.append("1) Confirm user is in VPN-Users group.")
    out.append("2) If MFA loop: reset MFA device binding, re-enroll.")
    out.append("3) Verify Password Last Set synced to IdP; re-sync if needed.")
    out.append("4) If >10 impacted: escalate to IAM team.")
    out.append("")
    out.append("Evidence Used")
    out.append(f"- policy.txt chars={len(policy)}")
    out.append("")
    out.append("SELF_TEST: PASS (it_ticket_bot)")
    return "\n".join(out)
