"""sili-vengers crew"""

import click
from rich.console import Console
from rich.table import Table
from sili_vengers.core.state import load_toml, get_active_features, is_initialized

console = Console()


@click.command()
def crew():
    """Show all active feature processes."""

    if not is_initialized():
        console.print("[red]✗ Not initialized.[/red]")
        raise click.Abort()

    toml_data = load_toml()
    active = get_active_features(toml_data)

    if not active:
        console.print("[yellow]No active processes. Start one with:[/yellow]")
        console.print("  [cyan]sili-vengers start \"your feature\"[/cyan]")
        return

    table = Table(title="⚡ Active Crew", border_style="bright_blue")
    table.add_column("Feature", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Summary", style="white")

    for f in active:
        table.add_row(
            f["feature"],
            f["date"],
            f["status"],
            f["prompt_summary"][:60] + ("..." if len(f["prompt_summary"]) > 60 else ""),
        )

    console.print(table)
