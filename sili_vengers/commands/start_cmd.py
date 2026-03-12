"""sili-vengers start"""

import click
from rich.console import Console
from rich.panel import Panel
from sili_vengers.core.state import (
    is_initialized, register_feature, get_feature_dir, save_task_json
)
from sili_vengers.core.discussion import run_discussion

console = Console()


@click.command()
@click.argument("requirement")
def start(requirement: str):
    """Start a new feature. Launches architect discussion to build task plan.

    Example: sili-vengers start "migrate auth system to JWT"
    """

    if not is_initialized():
        console.print("[red]✗ Not initialized. Run: sili-vengers init[/red]")
        raise click.Abort()

    # Extract short feature name from requirement
    feature = _slugify(requirement)

    console.print(Panel(
        f"[bold]New feature:[/bold] [cyan]{feature}[/cyan]\n\n"
        f"[dim]{requirement}[/dim]",
        title="⚡ Sili-vengers start",
        border_style="bright_blue",
    ))

    # Register in .vengers.toml
    date = register_feature(feature, requirement[:100])
    feature_dir = get_feature_dir(feature, date)
    feature_dir.mkdir(parents=True, exist_ok=True)

    # Write requirements.md
    req_file = feature_dir / "requirements.md"
    req_file.write_text(f"# Requirements\n\n{requirement}\n")
    console.print(f"[green]✓[/green] Created [dim]{req_file}[/dim]")

    # Run architect discussion → get task.json
    task_json = run_discussion(feature, date, requirement)

    # Save task.json
    save_task_json(feature, date, task_json)
    console.print(f"\n[green]✓[/green] Task plan saved to [dim]{feature_dir}/task.json[/dim]")

    # Create git worktree for feature
    _create_git_worktree(feature, date)

    console.print(f"\n[bold green]✓ Feature ready![/bold green]")
    console.print(f"\n  Run tasks: [cyan]sili-vengers status[/cyan]")
    console.print(f"  Execute:   [cyan]sili-vengers run {feature}[/cyan]")


def _slugify(text: str) -> str:
    import re
    # Take first ~5 words as feature name
    words = re.sub(r"[^\w\s]", "", text.lower()).split()[:5]
    return "_".join(words)


def _create_git_worktree(feature: str, date: str):
    import subprocess
    branch = f"feature/{feature}_{date}"
    try:
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, f".worktrees/{branch}"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            console.print(f"[green]✓[/green] Git worktree created: [dim]{branch}[/dim]")
        else:
            console.print(f"[yellow]![/yellow] Git worktree skipped: {result.stderr.strip()}")
    except FileNotFoundError:
        console.print("[dim]  (git not available, skipping worktree)[/dim]")
