"""sili-vengers task"""

import click
from rich.console import Console
from rich.prompt import Prompt
from sili_vengers.core.state import (
    load_toml, get_active_features, load_task_json,
    save_task_json, update_task_status, is_initialized, get_feature_dir
)
from pathlib import Path

console = Console()

TASK_STATUSES = ["pending", "running", "done", "failed", "merge_conflict"]


@click.group()
def task():
    """Manage individual tasks."""
    pass


@task.command()
@click.argument("task_id")
@click.argument("feature", required=False)
def done(task_id: str, feature: str):
    """Manually mark a task as done."""
    selected = _get_feature(feature)
    if not selected:
        return
    update_task_status(selected["feature"], selected["date"], task_id, "done")
    console.print(f"[green]✓[/green] Task [cyan]{task_id}[/cyan] marked done")


@task.command()
@click.argument("task_id")
@click.argument("feature", required=False)
@click.option("--agent", "-a", default=None, help="Override agent for this retry")
def retry(task_id: str, feature: str, agent: str):
    """Reset a failed/conflict task and re-run it.

    \b
    Examples:
      sili-vengers task retry task_03
      sili-vengers task retry task_03 --agent craftsman
    """
    selected = _get_feature(feature)
    if not selected:
        return

    feat = selected["feature"]
    date = selected["date"]

    # Override agent if specified
    if agent:
        task_data = load_task_json(feat, date)
        for t in task_data.get("tasks", []):
            if t["id"] == task_id:
                t["agent"] = agent
                console.print(f"[yellow]![/yellow] Agent overridden → [cyan]{agent}[/cyan]")
        save_task_json(feat, date, task_data)

    update_task_status(feat, date, task_id, "pending")
    console.print(f"[yellow]↺[/yellow] Task [cyan]{task_id}[/cyan] reset to pending")

    # Re-run just this task
    from sili_vengers.core.executor import run_all_tasks
    console.print(f"[dim]Re-running {task_id}...[/dim]")
    run_all_tasks(feat, date)


@task.command("run")
@click.argument("feature", required=False)
def run_tasks(feature: str):
    """Execute all pending tasks for a feature."""
    if not is_initialized():
        console.print("[red]✗ Not initialized.[/red]")
        raise click.Abort()

    selected = _get_feature(feature)
    if not selected:
        return

    from sili_vengers.core.executor import run_all_tasks
    run_all_tasks(selected["feature"], selected["date"])


def _get_feature(feature: str) -> dict | None:
    toml_data = load_toml()
    active = get_active_features(toml_data)
    if not active:
        console.print("[yellow]No active features.[/yellow]")
        return None
    if not feature:
        if len(active) == 1:
            return active[0]
        console.print("[bold]Active:[/bold]")
        for i, f in enumerate(active):
            console.print(f"  [{i}] [cyan]{f['feature']}[/cyan]")
        idx = Prompt.ask("Select", default="0")
        return active[int(idx)]
    return next((f for f in active if f["feature"] == feature), None)
