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
from sili_vengers.claude_commands.definitions import create_claude_commands, COMMAND_NAMES

console = Console()

VENGERS_CODE_MD = "vengers-code.md"


@click.command()
def init():
    """Initialize Sili-vengers in current project."""

    console.print(Panel(
        "[bold magenta]⚡ Sili-vengers[/bold magenta] [dim]initializing...[/dim]",
        border_style="bright_blue"
    ))

    vengers_code = Path(VENGERS_CODE_MD)

    if vengers_code.exists():
        console.print(f"[green]✓[/green] Found [cyan]{VENGERS_CODE_MD}[/cyan]")
        _check_and_patch_agents()
        _check_and_patch_hooks()
        _check_and_patch_claude_commands()
        _show_sleeping_features()
    else:
        console.print(f"[yellow]![/yellow] [cyan]{VENGERS_CODE_MD}[/cyan] not found, creating...")
        _create_vengers_code(vengers_code)
        _create_directory_structure()
        _create_toml()
        create_all_agents(get_agents_dir())
        create_all_hooks(get_hooks_dir())
        _install_claude_commands()
        console.print("\n[bold green]✓ Sili-vengers initialized![/bold green]")
        _print_next_steps()


def _print_next_steps():
    console.print("\nNext steps:")
    console.print("  [cyan]sili-vengers start \"your feature description\"[/cyan]")
    console.print("\nOr in Claude Code:")
    console.print("  [cyan]/sv-start your feature description[/cyan]")
    console.print("  [cyan]/sv-quick small bug fix[/cyan]")
    console.print("  [cyan]/sv-status[/cyan]")


def _create_vengers_code(path: Path):
    content = """\
# Sili-vengers

This project uses Sili-vengers for multi-agent orchestration.

## Agents
- visionary: Tech aesthetics, intuition & system elegance
- architect: Performance, correctness & resilience
- scout: Research, industry patterns & OSS landscape
- mediator: Synthesizes architect discussions into decisions
- decomposer: Breaks requirements into atomic tasks
- craftsman: Code implementation
- reviewer: Code review
- qa_sentinel: Testing & quality assurance
- archaeologist: Legacy code analysis
- scribe: Documentation

## Hooks
- post-write: triggers reviewer after code changes
- post-review: triggers qa_sentinel if review passes
- post-task: triggers scribe for documentation
- post-scribe: commits to git worktree
- pre-start: checks task dependencies

## Claude Code Commands
- /sv-start: start a new feature
- /sv-quick: quick mode for small tasks
- /sv-status: check task progress
- /sv-crew: list active features
- /sv-retry: retry a failed task
- /sv-log: view execution logs
- /sv-stop: pause current feature
- /sv-resume: resume a stopped feature
- /sv-agents: list all agents
"""
    path.write_text(content)
    console.print(f"[green]✓[/green] Created [cyan]{VENGERS_CODE_MD}[/cyan]")


def _create_directory_structure():
    dirs = [get_vengers_dir(), get_agents_dir(), get_hooks_dir()]
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


def _install_claude_commands():
    project_dir = Path.cwd()
    created = create_claude_commands(project_dir)
    console.print(f"[green]✓[/green] Installed [bold]{len(created)}[/bold] Claude Code commands:")
    for name in created:
        console.print(f"  [dim]/{name}[/dim]")


def _check_and_patch_agents():
    agents_dir = get_agents_dir()
    from sili_vengers.agents.definitions import AGENT_NAMES, create_all_agents
    missing = [n for n in AGENT_NAMES if not (agents_dir / f"{n}.md").exists()]
    if missing:
        console.print(f"[yellow]![/yellow] Missing agents: {', '.join(missing)} — creating...")
        create_all_agents(agents_dir, only=missing)
    else:
        console.print(f"[green]✓[/green] All agents present")


def _check_and_patch_hooks():
    hooks_dir = get_hooks_dir()
    from sili_vengers.hooks.definitions import HOOK_NAMES, create_all_hooks
    missing = [n for n in HOOK_NAMES if not (hooks_dir / f"{n}.sh").exists()]
    if missing:
        console.print(f"[yellow]![/yellow] Missing hooks: {', '.join(missing)} — creating...")
        create_all_hooks(hooks_dir, only=missing)
    else:
        console.print(f"[green]✓[/green] All hooks present")


def _check_and_patch_claude_commands():
    commands_dir = Path.cwd() / ".claude" / "commands"
    missing = [n for n in COMMAND_NAMES if not (commands_dir / f"{n}.md").exists()]
    if missing:
        console.print(f"[yellow]![/yellow] Missing Claude commands: {', '.join(missing)} — creating...")
        create_claude_commands(Path.cwd())
    else:
        console.print(f"[green]✓[/green] All Claude Code commands present")


def _show_sleeping_features():
    toml_data = load_toml()
    sleeping = get_sleeping_features(toml_data)
    if sleeping:
        console.print(f"\n[yellow]💤 Sleeping processes ({len(sleeping)}):[/yellow]")
        for f in sleeping:
            console.print(f"  [cyan]{f['feature']}[/cyan] [dim]({f['date']})[/dim] — {f['prompt_summary'][:60]}")
        console.print("\n  Resume with: [cyan]sili-vengers resume[/cyan]  or  [cyan]/sv-resume[/cyan]")
    else:
        console.print("\n[dim]No sleeping processes.[/dim]")
