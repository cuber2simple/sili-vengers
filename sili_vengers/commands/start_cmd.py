"""sili-vengers start"""

import click
from rich.console import Console
from rich.panel import Panel
from sili_vengers.core.state import (
    is_initialized, register_feature, get_feature_dir, save_task_json
)
from sili_vengers.core.discussion import run_discussion, run_quick_discussion

console = Console()


@click.command()
@click.argument("requirement")
@click.option("--quick", "-q", is_flag=True, help="Quick mode: architects review only, skip multi-round discussion")
@click.option("--dry-run", "-d", is_flag=True, help="Dry run: generate task.json only, do not execute tasks")
@click.option("--context", "-c", multiple=True, type=click.Path(exists=True), help="Extra context files for architects")
def start(requirement: str, quick: bool, dry_run: bool, context: tuple):
    """Start a new feature. Launches architect discussion to build task plan.

    \b
    Examples:
      sili-vengers start "migrate auth system to JWT"
      sili-vengers start --quick "fix login button color"
      sili-vengers start --dry-run "big refactor"
      sili-vengers start --context ./docs/spec.md "new payment flow"
    """

    if not is_initialized():
        console.print("[red]✗ Not initialized. Run: sili-vengers init[/red]")
        raise click.Abort()

    feature = _slugify(requirement)

    mode_parts = []
    if quick:
        mode_parts.append("[yellow]quick[/yellow]")
    if dry_run:
        mode_parts.append("[cyan]dry-run[/cyan]")
    mode_str = " · ".join(mode_parts) if mode_parts else "[green]standard[/green]"

    console.print(Panel(
        f"[bold]Feature:[/bold] [cyan]{feature}[/cyan]  {mode_str}\n\n[dim]{requirement}[/dim]",
        title="⚡ Sili-vengers start",
        border_style="bright_blue",
    ))

    extra_context = _load_context_files(context)

    date = register_feature(feature, requirement[:100])
    feature_dir = get_feature_dir(feature, date)
    feature_dir.mkdir(parents=True, exist_ok=True)

    req_file = feature_dir / "requirements.md"
    req_content = f"# Requirements\n\n{requirement}\n"
    if extra_context:
        req_content += f"\n## Additional Context\n\n{extra_context}\n"
    req_file.write_text(req_content)
    console.print(f"[green]✓[/green] Created [dim]{req_file}[/dim]")

    if quick:
        task_json = run_quick_discussion(feature, date, requirement, extra_context)
    else:
        task_json = run_discussion(feature, date, requirement, extra_context)

    save_task_json(feature, date, task_json)
    console.print(f"\n[green]✓[/green] Task plan saved → [dim]{feature_dir}/task.json[/dim]")

    if dry_run:
        console.print("\n[cyan]Dry-run mode: tasks not executed.[/cyan]")
        console.print(f"  When ready: [cyan]sili-vengers task run {feature}[/cyan]")
        return

    _create_git_worktree(feature, date)

    console.print("\n[bold green]Starting task execution...[/bold green]")
    from sili_vengers.core.executor import run_all_tasks
    run_all_tasks(feature, date)


def _load_context_files(paths: tuple) -> str:
    if not paths:
        return ""
    parts = []
    for path in paths:
        try:
            content = open(path).read()
            parts.append(f"### {path}\n{content}")
            console.print(f"[green]✓[/green] Loaded context: [dim]{path}[/dim]")
        except Exception as e:
            console.print(f"[yellow]![/yellow] Could not read {path}: {e}")
    return "\n\n".join(parts)


def _slugify(text: str) -> str:
    import re
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
            console.print(f"[green]✓[/green] Git worktree: [dim]{branch}[/dim]")
        else:
            console.print(f"[yellow]![/yellow] Worktree skipped: {result.stderr.strip()}")
    except FileNotFoundError:
        console.print("[dim]  (git not available, skipping worktree)[/dim]")
