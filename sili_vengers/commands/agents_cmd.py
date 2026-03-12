"""sili-vengers agents"""

import click
from rich.console import Console
from rich.table import Table
from sili_vengers.core.state import get_agents_dir, is_initialized
from sili_vengers.agents.definitions import AGENT_REGISTRY

console = Console()


@click.command()
def agents():
    """List all available agents and their roles."""

    table = Table(title="⚡ Sili-vengers Agents", border_style="bright_blue")
    table.add_column("Agent", style="cyan")
    table.add_column("Role", style="white")
    table.add_column("Trigger", style="dim")
    table.add_column("File", style="dim")

    agents_dir = get_agents_dir()

    for name, info in AGENT_REGISTRY.items():
        exists = (agents_dir / f"{name}.md").exists()
        file_status = f"[green]{name}.md[/green]" if exists else f"[red]{name}.md (missing)[/red]"
        table.add_row(
            name,
            info["role"],
            info.get("trigger", "manual"),
            file_status,
        )

    console.print(table)
