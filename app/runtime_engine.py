from __future__ import annotations
from typing import Dict, Any, List, Optional
import requests
def ollama_chat(base_url: str, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> str:
    payload = {"model": model, "messages": messages, "stream": False, "options": options or {}}
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["message"]["content"]
def build_context_with_rag(rag_hits: List[Dict[str, Any]], citations: bool = True) -> str:
    if not rag_hits:
        return ""
    parts = ["You may use the following sources:"]
    for i, h in enumerate(rag_hits, start=1):
        src = h.get("meta", {}).get("source", "source")
        parts.append(f"[{i}] ({src}) {h.get('text','')}")
    parts.append("If you use a source, cite it like: [1], [2].")
    return "\n".join(parts)
def run_bot(spec: Dict[str, Any], user_text: str, chat_history: List[Dict[str, str]], rag_context: str = "") -> str:
    base_url = spec["runtime"]["base_url"]
    model = spec["runtime"]["model"]
    sys_prompt = spec["system"]["prompt"]
    if rag_context:
        sys_prompt = sys_prompt + "\n\n" + rag_context
    framework = spec.get("agent", {}).get("framework", "none")
    mode = spec.get("agent", {}).get("mode", "single")
    options = {
        "temperature": spec["generation"]["temperature"],
        "top_p": spec["generation"]["top_p"],
        "num_ctx": spec["generation"]["num_ctx"],
        "num_predict": spec["generation"]["max_tokens"]
    }
    # Always enforce system message at beginning
    messages = [{"role": "system", "content": sys_prompt}] + [m for m in chat_history if m["role"] != "system"]
    messages.append({"role": "user", "content": user_text})
    # Starter “agentic” behaviors (teaching)
    if framework == "none":
        return ollama_chat(base_url, model, messages, options)
    if framework == "langgraph":
        # Simulate planner -> answer (simple)
        planner = "First, write a short plan. Then answer."
        messages2 = messages[:-1] + [{"role": "user", "content": planner + "\n\nUser question:\n" + user_text}]
        return ollama_chat(base_url, model, messages2, options)
    if framework == "crewai":
        # Simulate role/task prompting; real CrewAI projects happen in exported scaffold
        role = spec.get("identity", {}).get("role", "Assistant")
        goal = spec.get("identity", {}).get("goal", "")
        backstory = spec.get("identity", {}).get("backstory", "")
        crew_sys = f"You are acting as: {role}.\nGoal: {goal}\nBackstory: {backstory}\nComplete the task."
        messages2 = [{"role": "system", "content": crew_sys}] + messages[1:]
        return ollama_chat(base_url, model, messages2, options)
    if framework == "autogen":
        # Simulate 2-agent pattern: critic + assistant (simple)
        assistant = ollama_chat(base_url, model, messages, options)
        critic_prompt = "Critique the assistant answer for errors. Then provide a corrected final answer."
        critic_messages = [{"role": "system", "content": critic_prompt},
                           {"role": "user", "content": f"Question: {user_text}\n\nAssistant answer:\n{assistant}"}]
        return ollama_chat(base_url, model, critic_messages, options)
    return ollama_chat(base_url, model, messages, options)
