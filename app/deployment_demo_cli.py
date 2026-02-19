from __future__ import annotations
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
app = typer.Typer(add_completion=False)
console = Console()
@app.command()
def run(
    bot: str = typer.Option(..., "--bot", help="Bot name from registry"),
    text: str = typer.Option("", "--text", help="Input text"),
    file: Path = typer.Option(None, "--file", exists=True, help="Input file path"),
):
    from bots.registry import get_registry
    reg = get_registry()
    if bot not in reg:
        console.print(Panel(f"Unknown bot: {bot}\nAvailable: {', '.join(sorted(reg.keys()))}",
                            title="ERROR", style="bold red"))
        raise typer.Exit(code=2)
    user_input = text
    if file is not None:
        user_input = file.read_text(encoding="utf-8", errors="ignore")
    console.print(Panel(user_input or "(empty input)", title="USER", style="bold cyan"))
    impl = reg[bot]
    # Support function-bots or class-bots with .run/.invoke
    if callable(impl) and not hasattr(impl, "run") and not hasattr(impl, "invoke"):
        result = impl(user_input)
    else:
        obj = impl() if callable(impl) else impl
        if hasattr(obj, "run"):
            result = obj.run(user_input)
        elif hasattr(obj, "invoke"):
            result = obj.invoke(user_input)
        else:
            result = str(obj)
    # Alternate color for bot output (readable)
    if isinstance(result, (dict, list)):
        result = json.dumps(result, indent=2)
    console.print(Panel(str(result), title=f"BOT: {bot}", style="bold magenta"))
if __name__ == "__main__":
    app()
