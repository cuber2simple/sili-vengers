"""sili-vengers status"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sili_vengers.core.state import (
    load_toml, get_active_features, load_task_json, is_initialized
)
from rich.prompt import Prompt

console = Console()

STATUS_COLORS = {
    "pending": "dim",
    "running": "yellow",
    "done": "green",
    "failed": "red",
    "blocked": "magenta",
}


@click.command()
@click.argument("feature", required=False)
def status(feature: str):
    """Show task progress for a feature.

    Example: sili-vengers status migrate_auth
    """
    if not is_initialized():
        console.print("[red]✗ Not initialized.[/red]")
        raise click.Abort()

    toml_data = load_toml()
    active = get_active_features(toml_data)

    if not active:
        console.print("[yellow]No active processes.[/yellow]")
        return

    if not feature:
        if len(active) == 1:
            selected = active[0]
        else:
            console.print("[bold]Active:[/bold]")
            for i, f in enumerate(active):
                console.print(f"  [{i}] [cyan]{f['feature']}[/cyan]")
            idx = Prompt.ask("Select", default="0")
            selected = active[int(idx)]
    else:
        selected = next((f for f in active if f["feature"] == feature), None)
        if not selected:
            console.print(f"[red]Feature '{feature}' not found.[/red]")
            return

    task_data = load_task_json(selected["feature"], selected["date"])
    tasks = task_data.get("tasks", [])

    done = sum(1 for t in tasks if t.get("status") == "done")
    total = len(tasks)

    console.print(Panel(
        f"[bold cyan]{selected['feature']}[/bold cyan]\n"
        f"[dim]{selected['prompt_summary']}[/dim]\n\n"
        f"Progress: [bold]{done}/{total}[/bold] tasks complete",
        title="📋 Status",
        border_style="bright_blue",
    ))

    table = Table(border_style="dim")
    table.add_column("ID", style="dim")
    table.add_column("Agent", style="cyan")
    table.add_column("Status")
    table.add_column("Description")
    table.add_column("Deps", style="dim")

    for t in tasks:
        s = t.get("status", "pending")
        color = STATUS_COLORS.get(s, "white")
        table.add_row(
            t["id"],
            t.get("agent", "?"),
            f"[{color}]{s}[/{color}]",
            t["description"][:55],
            ", ".join(t.get("depends_on", [])) or "—",
        )

    console.print(table)
