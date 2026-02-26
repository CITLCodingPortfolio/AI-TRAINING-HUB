from __future__ import annotations

BOT_REGISTRY = {}

from dataclasses import dataclass
from typing import Dict, List, Any
@dataclass
class Demo:
    title: str
    description: str
    args: Dict[str, Any]
@dataclass
class BotMeta:
    bot_id: str
    name: str
    color: str  # hex
    description: str
    demos: List[Demo]
def get_registry() -> Dict[str, BotMeta]:
    return {
        "it_ticket_bot": BotMeta(
            bot_id="it_ticket_bot",
            name="IT Ticket Bot",
            color="#F59E0B",
            description="Triages IT tickets using policy text + ticket input. Outputs steps + checklist.",
            demos=[
                Demo(
                    title="Triage ticket with policy",
                    description="Uses sample_ticket.txt + policy.txt to produce a triage plan.",
                    args={
                        "input_file": "data/demo/sample_ticket.txt",
                        "files": ["data/demo/policy.txt"],
                        "mode": "triage",
                    },
                ),
                Demo(
                    title="Generate escalation note",
                    description="Produces a short escalation note for a supervisor.",
                    args={
                        "input_file": "data/demo/sample_ticket.txt",
                        "files": ["data/demo/policy.txt"],
                        "mode": "escalate",
                    },
                ),
                Demo(
                    title="Checklist only",
                    description="Outputs a checklist of actions (MFA, group membership, reset, verify).",
                    args={
                        "input_file": "data/demo/sample_ticket.txt",
                        "files": ["data/demo/policy.txt"],
                        "mode": "checklist",
                    },
                ),
            ],
        ),
        "deploy_ops_bot": BotMeta(
            bot_id="deploy_ops_bot",
            name="DeployOps Bot",
            color="#34D399",
            description="Reads Docker/K8s/SLURM files and outputs deployment steps + validation checks.",
            demos=[
                Demo(
                    title="Docker Compose review",
                    description="Reviews docker-compose.yml and outputs deployment/rollback steps.",
                    args={"files": ["data/demo/docker-compose.yml"], "target": "docker"},
                ),
                Demo(
                    title="Kubernetes Job review",
                    description="Reviews k8s_job.yaml and outputs kubectl commands + checks.",
                    args={"files": ["data/demo/k8s_job.yaml"], "target": "kubernetes"},
                ),
                Demo(
                    title="SLURM job review",
                    description="Reviews slurm_job.sh and outputs sbatch/squeue commands + GPU checks.",
                    args={"files": ["data/demo/slurm_job.sh"], "target": "slurm"},
                ),
                Demo(
                    title="Full ‘3-platform’ demo",
                    description="Runs Docker + K8s + SLURM checks in one pass.",
                    args={"files": ["data/demo/docker-compose.yml","data/demo/k8s_job.yaml","data/demo/slurm_job.sh"], "target": "all"},
                ),
            ],
        ),
        "api_server_bot": BotMeta(
            bot_id="api_server_bot",
            name="API Server Bot",
            color="#60A5FA",
            description="Demonstrates a faux local server behavior: healthcheck + run logging.",
            demos=[
                Demo(
                    title="Healthcheck demo (CLI)",
                    description="Calls the faux API server /health endpoint (shows server-style ops).",
                    args={"mode": "health"},
                ),
                Demo(
                    title="List bots demo (CLI)",
                    description="Calls the faux API server /bots endpoint.",
                    args={"mode": "bots"},
                ),
                Demo(
                    title="Run IT triage through API",
                    description="Runs it_ticket_bot through /run and shows JSON response.",
                    args={"mode": "run", "bot_id": "it_ticket_bot", "input_file": "data/demo/sample_ticket.txt", "files": ["data/demo/policy.txt"]},
                ),
            ],
        ),
        "fallback_bot": BotMeta(
            bot_id="fallback_bot",
            name="Fallback Bot",
            color="#A78BFA",
            description="Safety net bot: echoes inputs + proves CLI plumbing works even without LLM.",
            demos=[
                Demo(
                    title="Echo CLI input",
                    description="Shows deterministic output for grading and demo stability.",
                    args={"text": "Hello from CLI-only demo."},
                ),
                Demo(
                    title="Echo file input",
                    description="Reads a file and echoes key stats.",
                    args={"input_file": "data/demo/sample_ticket.txt"},
                ),
                Demo(
                    title="Echo multi-file",
                    description="Reads multiple files and echoes line counts.",
                    args={"files": ["data/demo/policy.txt","data/demo/docker-compose.yml"]},
                ),
            ],
        ),
        "ollama_bot": BotMeta(
            bot_id="ollama_bot",
            name="Hub Assistant",
            color="#22D3EE",   # bright cyan — unique per-bot in IRC sandbox
            description=(
                "Live Ollama LLM bot built from bots/Modelfile. "
                "Streams tokens in IRC-style colored chat. "
                "Run: python -m bots.ollama_sandbox --bot ollama_bot"
            ),
            demos=[
                Demo(
                    title="Ask about Ollama setup",
                    description="Sends a quick setup question to the hub-assistant model.",
                    args={"text": "How do I pull and run a model with Ollama?"},
                ),
                Demo(
                    title="Ask about LangGraph",
                    description="Asks for a LangGraph starter pattern.",
                    args={"text": "Show me a minimal LangGraph planner-executor pattern in Python."},
                ),
                Demo(
                    title="Ask about SLURM GPU jobs",
                    description="Asks for a SLURM sbatch script with GPU allocation.",
                    args={"text": "Write a SLURM sbatch script that requests 1 A100 GPU and runs a Python training script."},
                ),
            ],
        ),
    }
def list_bots():
    reg = get_registry()
    return [reg[k] for k in sorted(reg.keys())]



