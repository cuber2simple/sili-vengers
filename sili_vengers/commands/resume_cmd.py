"""sili-vengers resume"""

import click
from rich.console import Console
from rich.prompt import Prompt
from sili_vengers.core.state import (
    load_toml, get_sleeping_features, update_feature_status,
    load_task_json, is_initialized
)

console = Console()


@click.command()
@click.argument("feature", required=False)
def resume(feature: str):
    """Resume a stopped feature process.

    Example: sili-vengers resume migrate_auth
    """
    if not is_initialized():
        console.print("[red]✗ Not initialized. Run: sili-vengers init[/red]")
        raise click.Abort()

    toml_data = load_toml()
    sleeping = get_sleeping_features(toml_data)

    if not sleeping:
        console.print("[yellow]No sleeping processes found.[/yellow]")
        return

    if not feature:
        console.print("[bold]Sleeping processes:[/bold]")
        for i, f in enumerate(sleeping):
            console.print(f"  [{i}] [cyan]{f['feature']}[/cyan] ({f['date']}) — {f['prompt_summary'][:60]}")
        idx = Prompt.ask("Select", default="0")
        selected = sleeping[int(idx)]
    else:
        selected = next((f for f in sleeping if f["feature"] == feature), None)
        if not selected:
            console.print(f"[red]Feature '{feature}' not found in sleeping processes.[/red]")
            return

    # Restore status
    update_feature_status(selected["feature"], selected["date"], "active")
    console.print(f"[green]✓[/green] Resumed [cyan]{selected['feature']}[/cyan]")

    # Show pending tasks
    task_data = load_task_json(selected["feature"], selected["date"])
    pending = [t for t in task_data.get("tasks", []) if t.get("status") == "pending"]
    console.print(f"\n[yellow]{len(pending)} pending tasks[/yellow]")
    for t in pending:
        console.print(f"  [dim]{t['id']}[/dim] {t['description'][:70]}")

    console.print(f"\n  Continue with: [cyan]sili-vengers run {selected['feature']}[/cyan]")
