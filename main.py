from rich.console import Console
from rich.prompt import Prompt
from brain import handle, patch_weak_tools, echo_memory
from memory_store import save_memory

console = Console()
console.print("\n[bold cyan]E.C.H.O[/bold cyan] — type anything or 'quit' to exit\n")
patch_weak_tools()

while True:
    try:
        user_input = Prompt.ask("[bold green]You[/bold green]")
        if user_input.lower() in ["quit", "exit", "bye"]:
            save_memory(echo_memory)
            console.print("[cyan]echo shutting down. Memory saved.[/cyan]")
            break
        result = handle(user_input)
        console.print(f"\n[bold cyan]echo:[/bold cyan] {result}\n")
    except KeyboardInterrupt:
        save_memory(echo_memory)
        console.print("\n[cyan]echo shutting down. Memory saved.[/cyan]")
        break
