"""
Core executor - runs all tasks for a feature.
Handles parallel groups, git merges, conflict detection, and feature completion.
"""

import subprocess
import threading
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from sili_vengers.core.state import (
    load_task_json, save_task_json, update_task_status,
    get_feature_dir, update_feature_status
)
from sili_vengers.core.runner import run_task_agent

console = Console()


def run_all_tasks(feature: str, date: str):
    """
    Full execution pipeline:
    1. Run tasks in parallel groups respecting dependencies
    2. After each task: commit to task branch, merge to feature branch
    3. On merge conflict: mark task as merge_conflict, pause dependents
    4. When all done: generate result.md, merge feature → main
    """
    task_data = load_task_json(feature, date)
    tasks = task_data.get("tasks", [])
    feature_dir = get_feature_dir(feature, date)

    req_file = feature_dir / "requirements.md"
    requirements = req_file.read_text() if req_file.exists() else ""

    # Group by parallel_group
    groups = {}
    for t in tasks:
        g = t.get("parallel_group", 1)
        groups.setdefault(g, []).append(t)

    all_success = True

    for group_id in sorted(groups.keys()):
        group_tasks = groups[group_id]
        runnable = [
            t for t in group_tasks
            if t.get("status") == "pending" and _deps_met(t, tasks)
        ]
        blocked = [
            t for t in group_tasks
            if t.get("status") == "pending" and not _deps_met(t, tasks)
        ]

        if blocked:
            for t in blocked:
                console.print(f"  [magenta]⊘[/magenta] {t['id']} blocked (dependency not met)")

        if not runnable:
            continue

        console.print(f"\n[bold yellow]── Group {group_id} · {len(runnable)} tasks parallel ──[/bold yellow]")

        results = {}
        lock = threading.Lock()

        def execute_task(task):
            tid = task["id"]
            console.print(f"  [cyan]→[/cyan] {tid}: {task['description'][:60]}")

            # Update status to running
            _update_task(feature, date, tid, "running")

            try:
                output = run_task_agent(
                    agent_name=task.get("agent", "craftsman"),
                    task=task,
                    feature=feature,
                    date=date,
                    requirements=requirements,
                )

                # Save result file
                result_dir = feature_dir / "tasks"
                result_dir.mkdir(parents=True, exist_ok=True)
                result_file = result_dir / f"{tid}_result.md"
                result_file.write_text(output)

                # Commit to task branch
                merge_ok = _commit_and_merge_task(feature, date, tid, task)

                with lock:
                    if merge_ok:
                        results[tid] = "done"
                        console.print(f"  [green]✓[/green] {tid} done")
                    else:
                        results[tid] = "merge_conflict"
                        console.print(f"  [red]⚡[/red] {tid} merge conflict")

            except Exception as e:
                with lock:
                    results[tid] = "failed"
                console.print(f"  [red]✗[/red] {tid} failed: {e}")

        threads = [threading.Thread(target=execute_task, args=(t,)) for t in runnable]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Update statuses and reload task list
        task_data = load_task_json(feature, date)
        tasks = task_data.get("tasks", [])
        for tid, status in results.items():
            _update_task(feature, date, tid, status)
            if status in ("failed", "merge_conflict"):
                all_success = False

        # Reload for next group
        task_data = load_task_json(feature, date)
        tasks = task_data.get("tasks", [])

    # Check for any conflicts
    task_data = load_task_json(feature, date)
    tasks = task_data.get("tasks", [])
    conflicts = [t for t in tasks if t.get("status") == "merge_conflict"]
    failed = [t for t in tasks if t.get("status") == "failed"]

    if conflicts or failed:
        _show_intervention_needed(feature, date, conflicts, failed)
        return

    # All done — finalize
    _finalize_feature(feature, date, tasks, requirements)


def _commit_and_merge_task(feature: str, date: str, task_id: str, task: dict) -> bool:
    """
    Commit task results to task branch, then merge into feature branch.
    Returns True if merge succeeded, False on conflict.
    """
    feature_branch = f"feature/{feature}_{date}"
    task_branch = f"task/{task_id}_{date}"
    worktree = Path(f".worktrees/{feature_branch}")

    if not worktree.exists():
        # No git setup, skip
        return True

    try:
        # Create task branch from feature branch
        subprocess.run(
            ["git", "worktree", "add", "-b", task_branch,
             f".worktrees/{task_branch}", feature_branch],
            capture_output=True, check=True
        )

        # Copy result files into task worktree
        task_worktree = Path(f".worktrees/{task_branch}")
        result_src = Path(f".vengers/{feature}_{date}/tasks/{task_id}_result.md")
        if result_src.exists():
            dest_dir = task_worktree / ".vengers-results"
            dest_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(result_src, dest_dir / f"{task_id}_result.md")

        # Commit in task worktree
        subprocess.run(["git", "add", "-A"], cwd=task_worktree, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"task({task_id}): {task['description'][:60]}"],
            cwd=task_worktree, capture_output=True
        )

        # Merge task branch into feature worktree
        merge_result = subprocess.run(
            ["git", "merge", "--no-ff", task_branch,
             "-m", f"merge: {task_id} into {feature_branch}"],
            cwd=worktree, capture_output=True, text=True
        )

        # Clean up task worktree
        subprocess.run(
            ["git", "worktree", "remove", str(task_worktree), "--force"],
            capture_output=True
        )

        return merge_result.returncode == 0

    except subprocess.CalledProcessError:
        return True  # Git not available, treat as success


def _finalize_feature(feature: str, date: str, tasks: list, requirements: str):
    """Generate result.md and merge feature branch to main."""
    console.print(f"\n[bold green]── Finalizing feature ──[/bold green]")

    feature_dir = get_feature_dir(feature, date)

    # Collect all task results
    task_results = []
    for t in tasks:
        result_file = feature_dir / "tasks" / f"{t['id']}_result.md"
        if result_file.exists():
            task_results.append(f"## {t['id']}: {t['description']}\n\n{result_file.read_text()}")

    # Generate result.md via Scribe
    console.print("[dim]Scribe generating result.md...[/dim]")
    from sili_vengers.core.runner import run_agent
    scribe_prompt = f"""
Summarize this completed feature for the team.

Requirements:
{requirements}

Task Results:
{"---".join(task_results)}

Write a clear result.md covering:
- What was built
- Key decisions made
- How to use/test it
- Any known limitations
"""
    result_content = run_agent(
        agent_name="scribe",
        prompt=scribe_prompt,
        feature=feature,
        date=date,
        task_id="final_result",
    )

    result_file = feature_dir / "result.md"
    result_file.write_text(result_content)
    console.print(f"[green]✓[/green] result.md written")

    # Merge feature → main
    feature_branch = f"feature/{feature}_{date}"
    worktree = Path(f".worktrees/{feature_branch}")

    if worktree.exists():
        merge = subprocess.run(
            ["git", "merge", "--no-ff", feature_branch,
             "-m", f"feat({feature}): complete feature {date}"],
            capture_output=True, text=True
        )
        if merge.returncode == 0:
            console.print(f"[green]✓[/green] Merged [cyan]{feature_branch}[/cyan] → main")
        else:
            console.print(f"[yellow]![/yellow] Merge to main failed, resolve manually:")
            console.print(f"  git merge {feature_branch}")
    else:
        console.print("[dim]  (no worktree, skipping merge)[/dim]")

    update_feature_status(feature, date, "done")

    console.print(Panel(
        f"[bold green]✓ Feature complete![/bold green]\n\n"
        f"[cyan]{feature}[/cyan]\n"
        f"[dim]{feature_dir}/result.md[/dim]",
        border_style="green",
    ))


def _show_intervention_needed(feature: str, date: str, conflicts: list, failed: list):
    """Show clear instructions when human intervention is needed."""
    feature_branch = f"feature/{feature}_{date}"

    console.print(Panel(
        "[bold yellow]⚠️  Human intervention needed[/bold yellow]",
        border_style="yellow"
    ))

    if conflicts:
        console.print("\n[yellow]Merge conflicts:[/yellow]")
        for t in conflicts:
            console.print(f"\n  [cyan]{t['id']}[/cyan]: {t['description'][:60]}")
            console.print(f"    1. cd .worktrees/{feature_branch}")
            console.print(f"    2. git merge task/{t['id']}_{date}")
            console.print(f"    3. Resolve conflicts")
            console.print(f"    4. git add . && git commit")
            console.print(f"    5. sili-vengers task retry {t['id']}")

    if failed:
        console.print("\n[red]Failed tasks:[/red]")
        for t in failed:
            console.print(f"\n  [cyan]{t['id']}[/cyan]: {t['description'][:60]}")
            console.print(f"    sili-vengers task retry {t['id']}")
            console.print(f"    sili-vengers task retry {t['id']} --agent craftsman  # change agent")

    console.print(f"\n  After fixing: [cyan]sili-vengers task run {feature}[/cyan]")


def _deps_met(task: dict, all_tasks: list) -> bool:
    deps = task.get("depends_on", [])
    if not deps:
        return True
    done_ids = {t["id"] for t in all_tasks if t.get("status") == "done"}
    return all(dep in done_ids for dep in deps)


def _update_task(feature: str, date: str, task_id: str, status: str):
    task_data = load_task_json(feature, date)
    for t in task_data.get("tasks", []):
        if t["id"] == task_id:
            t["status"] = status
            t["updated_at"] = datetime.now().isoformat()
    save_task_json(feature, date, task_data)
