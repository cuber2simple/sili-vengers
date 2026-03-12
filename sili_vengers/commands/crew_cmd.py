"""sili-vengers crew"""

import click
from rich.console import Console
from rich.panel import Panel
from sili_vengers.core.state import (
    load_toml, get_active_features, get_sleeping_features,
    load_task_json, is_initialized
)

console = Console()

STATUS_ICON = {
    "pending":        "○",
    "running":        "→",
    "done":           "✓",
    "failed":         "✗",
    "merge_conflict": "⚡",
    "blocked":        "⊘",
}

STATUS_COLOR = {
    "pending":        "dim",
    "running":        "yellow",
    "done":           "green",
    "failed":         "red",
    "merge_conflict": "magenta",
    "blocked":        "blue",
}


@click.command()
@click.option("--all", "-a", "show_all", is_flag=True, help="Include stopped/sleeping features")
def crew(show_all: bool):
    """Show all active features and their task progress."""

    if not is_initialized():
        console.print("[red]✗ Not initialized. Run: sili-vengers init[/red]")
        raise click.Abort()

    toml_data = load_toml()
    active = get_active_features(toml_data)
    sleeping = get_sleeping_features(toml_data) if show_all else []

    if not active and not sleeping:
        console.print("[yellow]No active features.[/yellow]")
        console.print("  Start one: [cyan]sili-vengers start \"your feature\"[/cyan]")
        console.print("  or:        [cyan]/sv-start your feature[/cyan]")
        return

    console.print()

    if active:
        console.print(f"[bold]⚡ Active ({len(active)})[/bold]")
        for f in active:
            _print_feature(f, "active")

    if sleeping:
        console.print(f"\n[bold dim]💤 Sleeping ({len(sleeping)})[/bold dim]")
        for f in sleeping:
            _print_feature(f, "stopped")

    if not show_all and get_sleeping_features(toml_data):
        n = len(get_sleeping_features(toml_data))
        console.print(f"\n[dim]  + {n} sleeping. Use --all to show.[/dim]")


def _print_feature(f: dict, feature_status: str):
    feat = f["feature"]
    date = f["date"]

    task_data = load_task_json(feat, date)
    tasks = task_data.get("tasks", [])

    total = len(tasks)
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    running = [t for t in tasks if t.get("status") == "running"]
    conflicts = [t for t in tasks if t.get("status") == "merge_conflict"]
    failed = [t for t in tasks if t.get("status") == "failed"]
    pending = [t for t in tasks if t.get("status") == "pending"]

    # Status label
    if feature_status == "stopped":
        status_label = "[dim]paused[/dim]"
    elif conflicts or failed:
        status_label = "[magenta]needs attention[/magenta]"
    elif running:
        status_label = "[yellow]running[/yellow]"
    elif done_count == total and total > 0:
        status_label = "[green]complete[/green]"
    else:
        status_label = "[cyan]active[/cyan]"

    progress = f"[dim]{done_count}/{total} tasks[/dim]" if total > 0 else "[dim]no tasks yet[/dim]"

    console.print(
        f"\n  [bold cyan]{feat}[/bold cyan]  [dim]{date}[/dim]  "
        f"{status_label}  {progress}"
    )

    if f.get("prompt_summary"):
        console.print(f"  [dim italic]{f['prompt_summary'][:70]}[/dim italic]")

    # Show tasks
    show_tasks = []
    shown_ids = set()

    # Running first
    for t in running:
        show_tasks.append(t)
        shown_ids.add(t["id"])

    # Conflicts and failed
    for t in conflicts + failed:
        if t["id"] not in shown_ids:
            show_tasks.append(t)
            shown_ids.add(t["id"])

    # Last done for context
    done_tasks = [t for t in tasks if t.get("status") == "done"]
    if done_tasks:
        last_done = done_tasks[-1]
        if last_done["id"] not in shown_ids:
            show_tasks = [last_done] + show_tasks
            shown_ids.add(last_done["id"])

    # Next 2 pending
    for t in pending:
        if t["id"] not in shown_ids and len(show_tasks) < 5:
            show_tasks.append(t)
            shown_ids.add(t["id"])

    for t in show_tasks:
        s = t.get("status", "pending")
        icon = STATUS_ICON.get(s, "?")
        color = STATUS_COLOR.get(s, "white")
        agent = t.get("agent", "?")
        desc = t["description"][:52]
        console.print(
            f"    [{color}]{icon}[/{color}] [dim]{t['id']}[/dim] "
            f"[{color}]{desc}[/{color}]  [dim]{agent}[/dim]"
        )

    remaining = [t for t in tasks if t["id"] not in shown_ids and t.get("status") != "done"]
    if remaining:
        console.print(f"    [dim]... and {len(remaining)} more[/dim]")

    # Commands for this feature
    console.print(f"\n  [dim]Commands:[/dim]")
    console.print(f"    [dim]sili-vengers status {feat}[/dim]   [dim]or[/dim]  [cyan]/sv-status {feat}[/cyan]")

    if conflicts:
        for t in conflicts:
            console.print(f"    [dim]sili-vengers task retry {t['id']}[/dim]  [dim]or[/dim]  [cyan]/sv-retry {t['id']}[/cyan]")
    if failed:
        for t in failed:
            console.print(f"    [dim]sili-vengers task retry {t['id']}[/dim]  [dim]or[/dim]  [cyan]/sv-retry {t['id']}[/cyan]")
    if feature_status == "stopped":
        console.print(f"    [dim]sili-vengers resume {feat}[/dim]  [dim]or[/dim]  [cyan]/sv-resume {feat}[/cyan]")
    elif running or pending:
        console.print(f"    [dim]sili-vengers log {feat}[/dim]    [dim]or[/dim]  [cyan]/sv-log {feat}[/cyan]")
        console.print(f"    [dim]sili-vengers stop {feat}[/dim]   [dim]or[/dim]  [cyan]/sv-stop {feat}[/cyan]")
