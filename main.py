from rich.console import Console
from rich.prompt import Prompt
from brain import handle, patch_weak_tools, jarvis_memory
from memory_store import save_memory

console = Console()
console.print("\n[bold cyan]J.A.R.V.I.S[/bold cyan] — type anything or 'quit' to exit\n")
patch_weak_tools()

while True:
    try:
        user_input = Prompt.ask("[bold green]You[/bold green]")
        if user_input.lower() in ["quit", "exit", "bye"]:
            save_memory(jarvis_memory)
            console.print("[cyan]JARVIS shutting down. Memory saved.[/cyan]")
            break
        result = handle(user_input)
        console.print(f"\n[bold cyan]JARVIS:[/bold cyan] {result}\n")
    except KeyboardInterrupt:
        save_memory(jarvis_memory)
        console.print("\n[cyan]JARVIS shutting down. Memory saved.[/cyan]")
        break