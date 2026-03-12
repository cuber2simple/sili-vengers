"""sili-vengers init"""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from sili_vengers.core.state import (
    get_vengers_dir, get_toml_path, get_agents_dir, get_hooks_dir,
    load_toml, get_sleeping_features, is_initialized
)
from sili_vengers.agents.definitions import create_all_agents
from sili_vengers.hooks.definitions import create_all_hooks

console = Console()

VENGERS_CODE_MD = "vengers-code.md"


@click.command()
def init():
    """Initialize Sili-vengers in current project"""

    console.print(Panel(
        "[bold magenta]⚡ Sili-vengers[/bold magenta] [dim]initializing...[/dim]",
        border_style="bright_blue"
    ))

    vengers_code = Path(VENGERS_CODE_MD)

    if vengers_code.exists():
        console.print(f"[green]✓[/green] Found [cyan]{VENGERS_CODE_MD}[/cyan]")
        _check_and_patch_agents()
        _check_and_patch_hooks()
        _show_sleeping_features()
    else:
        console.print(f"[yellow]![/yellow] [cyan]{VENGERS_CODE_MD}[/cyan] not found, creating...")
        _create_vengers_code(vengers_code)
        _create_directory_structure()
        _create_toml()
        create_all_agents(get_agents_dir())
        create_all_hooks(get_hooks_dir())
        console.print("\n[bold green]✓ Sili-vengers initialized![/bold green]")
        console.print("\nNext steps:")
        console.print("  [cyan]sili-vengers start \"your feature description\"[/cyan]")


def _create_vengers_code(path: Path):
    content = """# Sili-vengers Code

This project uses Sili-vengers for multi-agent orchestration.

## Active Agents
- visionary (The Visionary - tech aesthetics & intuition)
- architect (The Architect - deep technical expertise)
- scout (The Scout - research & industry patterns)
- mediator (Mediator - synthesizes architect discussions)
- decomposer (Requirement decomposition)
- craftsman (Code implementation)
- reviewer (Code review)
- qa_sentinel (QA & testing)
- archaeologist (Legacy code analysis)
- scribe (Documentation)

## Hooks
- post-write: triggers reviewer after code changes
- post-review: triggers qa_sentinel if review passes
- post-task: triggers scribe for documentation
- post-scribe: commits to git worktree
- pre-start: checks task dependencies

## Workflow
1. `sili-vengers start "description"` - Start new feature
2. Architects discuss and generate task.json
3. Tasks execute in parallel groups
4. Results written to .vengers/{feature}_{date}/
"""
    path.write_text(content)
    console.print(f"[green]✓[/green] Created [cyan]{VENGERS_CODE_MD}[/cyan]")


def _create_directory_structure():
    dirs = [
        get_vengers_dir(),
        get_agents_dir(),
        get_hooks_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created [dim]{d}[/dim]")


def _create_toml():
    toml_path = get_toml_path()
    if not toml_path.exists():
        import tomli_w
        with open(toml_path, "wb") as f:
            tomli_w.dump({"vengers": {}}, f)
        console.print(f"[green]✓[/green] Created [dim]{toml_path}[/dim]")


def _check_and_patch_agents():
    agents_dir = get_agents_dir()
    from sili_vengers.agents.definitions import AGENT_NAMES, create_all_agents
    missing = []
    for name in AGENT_NAMES:
        if not (agents_dir / f"{name}.md").exists():
            missing.append(name)

    if missing:
        console.print(f"[yellow]![/yellow] Missing agents: {', '.join(missing)} — creating...")
        create_all_agents(agents_dir, only=missing)
    else:
        console.print(f"[green]✓[/green] All agents present")


def _check_and_patch_hooks():
    hooks_dir = get_hooks_dir()
    from sili_vengers.hooks.definitions import HOOK_NAMES, create_all_hooks
    missing = []
    for name in HOOK_NAMES:
        if not (hooks_dir / f"{name}.sh").exists():
            missing.append(name)

    if missing:
        console.print(f"[yellow]![/yellow] Missing hooks: {', '.join(missing)} — creating...")
        create_all_hooks(hooks_dir, only=missing)
    else:
        console.print(f"[green]✓[/green] All hooks present")


def _show_sleeping_features():
    toml_data = load_toml()
    sleeping = get_sleeping_features(toml_data)
    if sleeping:
        console.print(f"\n[yellow]💤 Sleeping processes ({len(sleeping)}):[/yellow]")
        for f in sleeping:
            console.print(f"  [cyan]{f['feature']}[/cyan] [dim]({f['date']})[/dim] — {f['prompt_summary'][:60]}...")
        console.print("\n  Resume with: [cyan]sili-vengers resume <feature>[/cyan]")
    else:
        console.print("\n[dim]No sleeping processes.[/dim]")
