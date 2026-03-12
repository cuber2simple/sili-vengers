"""sili-vengers stop"""

import click
from rich.console import Console
from sili_vengers.core.state import (
    load_toml, get_active_features, update_feature_status, is_initialized
)
from rich.prompt import Prompt

console = Console()


@click.command()
@click.argument("feature", required=False)
def stop(feature: str):
    """Stop and save current feature process.

    Example: sili-vengers stop migrate_auth
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
        console.print("[bold]Active processes:[/bold]")
        for i, f in enumerate(active):
            console.print(f"  [{i}] [cyan]{f['feature']}[/cyan] ({f['date']})")
        idx = Prompt.ask("Select to stop", default="0")
        selected = active[int(idx)]
    else:
        selected = next((f for f in active if f["feature"] == feature), None)
        if not selected:
            console.print(f"[red]Feature '{feature}' not found.[/red]")
            return

    update_feature_status(selected["feature"], selected["date"], "stopped")
    console.print(f"[green]✓[/green] Stopped [cyan]{selected['feature']}[/cyan] — saved state")
    console.print(f"  Resume with: [cyan]sili-vengers resume {selected['feature']}[/cyan]")
