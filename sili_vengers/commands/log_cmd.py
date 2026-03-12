"""sili-vengers log"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from sili_vengers.core.state import load_toml, get_active_features, get_feature_dir, is_initialized

console = Console()


@click.command()
@click.argument("feature", required=False)
@click.option("--task", "-t", default=None, help="Show log for specific task only")
@click.option("--raw", "-r", is_flag=True, help="Show raw log output")
def log(feature: str, task: str, raw: bool):
    """Show execution logs for a feature.

    \b
    Examples:
      sili-vengers log
      sili-vengers log migrate_auth
      sili-vengers log migrate_auth --task task_02
    """
    if not is_initialized():
        console.print("[red]✗ Not initialized.[/red]")
        raise click.Abort()

    toml_data = load_toml()
    active = get_active_features(toml_data)

    if not active:
        console.print("[yellow]No active features.[/yellow]")
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

    feat = selected["feature"]
    date = selected["date"]
    feature_dir = get_feature_dir(feat, date)
    log_dir = feature_dir / "logs"

    if not log_dir.exists():
        console.print("[yellow]No logs found yet.[/yellow]")
        return

    log_files = sorted(log_dir.glob("*.log"))

    if not log_files:
        console.print("[yellow]No log files found.[/yellow]")
        return

    # Filter by task if specified
    if task:
        log_files = [f for f in log_files if task in f.name]
        if not log_files:
            console.print(f"[yellow]No logs for task '{task}'.[/yellow]")
            return

    console.print(Panel(
        f"[bold]Logs for:[/bold] [cyan]{feat}[/cyan] [dim]({date})[/dim]",
        border_style="bright_blue",
    ))

    for log_file in log_files:
        agent_name = log_file.stem
        content = log_file.read_text()

        if not content.strip():
            continue

        console.print(f"\n[bold cyan]── {agent_name} ──[/bold cyan]")

        if raw:
            console.print(content)
        else:
            # Truncate long logs
            if len(content) > 2000:
                content = content[:2000] + f"\n\n[dim]... ({len(content) - 2000} more chars, use --raw to see all)[/dim]"
            console.print(Markdown(content))
