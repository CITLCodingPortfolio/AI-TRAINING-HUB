import os
import requests
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")  # change to your custom model name
def generate(prompt: str) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=60)
    r.raise_for_status()
    return r.json().get("response", "")
if __name__ == "__main__":
    print("CLI Chat (Ctrl+C to quit)")
    while True:
        msg = input("\nYou: ").strip()
        if not msg:
            continue
        try:
            out = generate(msg)
            print("\nBot:", out)
        except Exception as e:
            print("\nERROR:", e)
