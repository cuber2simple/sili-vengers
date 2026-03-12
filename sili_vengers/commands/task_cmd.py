"""sili-vengers task"""

import click
from rich.console import Console
from rich.prompt import Prompt
from sili_vengers.core.state import (
    load_toml, get_active_features, load_task_json,
    save_task_json, update_task_status, is_initialized
)
from sili_vengers.core.runner import run_task_agent
from pathlib import Path

console = Console()


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
    console.print(f"[green]✓[/green] Task [cyan]{task_id}[/cyan] marked as done")


@task.command()
@click.argument("task_id")
@click.argument("feature", required=False)
def retry(task_id: str, feature: str):
    """Reset a failed task to pending for re-execution."""
    selected = _get_feature(feature)
    if not selected:
        return
    update_task_status(selected["feature"], selected["date"], task_id, "pending")
    console.print(f"[yellow]↺[/yellow] Task [cyan]{task_id}[/cyan] reset to pending")


@task.command("run")
@click.argument("feature", required=False)
def run_tasks(feature: str):
    """Execute pending tasks for a feature (respects parallel groups and deps)."""
    if not is_initialized():
        console.print("[red]✗ Not initialized.[/red]")
        raise click.Abort()

    selected = _get_feature(feature)
    if not selected:
        return

    feat = selected["feature"]
    date = selected["date"]
    task_data = load_task_json(feat, date)
    tasks = task_data.get("tasks", [])

    req_file = Path(".vengers") / f"{feat}_{date}" / "requirements.md"
    requirements = req_file.read_text() if req_file.exists() else ""

    # Group tasks by parallel_group, execute groups in order
    groups = {}
    for t in tasks:
        g = t.get("parallel_group", 1)
        groups.setdefault(g, []).append(t)

    import threading
    for group_id in sorted(groups.keys()):
        group_tasks = groups[group_id]
        pending = [t for t in group_tasks if t.get("status") == "pending" and _deps_met(t, tasks)]

        if not pending:
            continue

        console.print(f"\n[bold yellow]── Parallel Group {group_id} ({len(pending)} tasks) ──[/bold yellow]")

        threads = []
        for t in pending:
            console.print(f"  [cyan]→[/cyan] {t['id']}: {t['description'][:60]}")
            update_task_status(feat, date, t["id"], "running")

            def run_one(task=t):
                try:
                    result = run_task_agent(
                        agent_name=task.get("agent", "craftsman"),
                        task=task,
                        feature=feat,
                        date=date,
                        requirements=requirements,
                    )
                    # Save result
                    result_dir = Path(".vengers") / f"{feat}_{date}" / "tasks"
                    result_dir.mkdir(parents=True, exist_ok=True)
                    result_file = result_dir / f"{task['id']}_result.md"
                    result_file.write_text(result)
                    update_task_status(feat, date, task["id"], "done", str(result_file))
                    console.print(f"  [green]✓[/green] {task['id']} done")
                except Exception as e:
                    update_task_status(feat, date, task["id"], "failed")
                    console.print(f"  [red]✗[/red] {task['id']} failed: {e}")

            thread = threading.Thread(target=run_one)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    console.print("\n[bold green]✓ All runnable tasks complete[/bold green]")
    console.print(f"  Check: [cyan]sili-vengers status {feat}[/cyan]")


def _deps_met(task: dict, all_tasks: list) -> bool:
    deps = task.get("depends_on", [])
    if not deps:
        return True
    done_ids = {t["id"] for t in all_tasks if t.get("status") == "done"}
    return all(dep in done_ids for dep in deps)


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
