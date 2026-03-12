"""
Architect discussion engine.
Three architects discuss in parallel, Mediator synthesizes,
multiple rounds until consensus, then user confirms.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from sili_vengers.core.runner import run_agents_parallel, run_agent

console = Console()

ARCHITECTS = ["visionary", "architect", "scout"]

ARCHITECT_LABELS = {
    "visionary": ("🔮 The Visionary", "magenta"),
    "architect": ("⚙️  The Architect", "cyan"),
    "scout":     ("🔭 The Scout", "green"),
    "mediator":  ("⚖️  Mediator", "yellow"),
}


def run_discussion(feature: str, date: str, requirement: str) -> dict:
    """
    Full architect discussion flow.
    Returns final agreed task.json dict.
    """
    console.print()
    console.print(Panel(
        f"[bold]Assembling the crew for:[/bold]\n\n{requirement}",
        title="⚡ Sili-vengers",
        border_style="bright_blue",
    ))

    round_num = 1
    history = []  # accumulate discussion history
    task_json = None

    while True:
        console.print(f"\n[bold yellow]── Round {round_num} ──[/bold yellow]")

        # Build context from previous rounds
        context = _build_context(requirement, history)

        # Round prompt varies by round number
        if round_num == 1:
            agent_prompt = (
                f"Analyze this requirement and share your perspective:\n\n{requirement}\n\n"
                "Focus on your unique angle. Be concrete and opinionated. "
                "End with your top 3 concerns or recommendations."
            )
        else:
            prev_summary = history[-1].get("mediator_summary", "")
            agent_prompt = (
                f"Previous discussion summary:\n{prev_summary}\n\n"
                f"Original requirement:\n{requirement}\n\n"
                "Respond to the other architects' points. "
                "Where do you agree? Where do you push back? "
                "Refine your position. Be specific."
            )

        # Run 3 architects in parallel
        console.print("[dim]Architects thinking in parallel...[/dim]")
        with console.status("[bold green]Deliberating...[/bold green]"):
            architect_outputs = run_agents_parallel(
                agents=[
                    {"agent_name": a, "prompt": agent_prompt, "extra_context": context}
                    for a in ARCHITECTS
                ],
                feature=feature,
                date=date,
            )

        # Display architect outputs
        _display_architect_outputs(architect_outputs, round_num)

        # Mediator synthesizes
        console.print("\n[dim]Mediator synthesizing...[/dim]")
        mediator_input = _build_mediator_prompt(requirement, architect_outputs, round_num)
        with console.status("[bold yellow]Synthesizing...[/bold yellow]"):
            mediator_output = run_agent(
                agent_name="mediator",
                prompt=mediator_input,
                feature=feature,
                date=date,
                task_id=f"round_{round_num}",
            )

        _display_mediator(mediator_output)

        # Save round to history
        history.append({
            "round": round_num,
            "architect_outputs": architect_outputs,
            "mediator_summary": mediator_output,
        })

        # Ask user: continue discussion or proceed?
        console.print()
        action = Prompt.ask(
            "[bold]What next?[/bold]",
            choices=["next", "edit", "proceed"],
            default="next" if round_num < 2 else "proceed",
        )

        if action == "next":
            round_num += 1
            continue
        elif action == "edit":
            requirement = click.edit(requirement)
            if not requirement:
                console.print("[yellow]No changes made, continuing.[/yellow]")
            round_num += 1
            continue
        elif action == "proceed":
            break

    # Generate final task.json
    console.print("\n[bold green]Generating task plan...[/bold green]")
    full_history_text = _format_full_history(history)
    with console.status("[bold green]Building task.json...[/bold green]"):
        task_json_output = run_agent(
            agent_name="mediator",
            prompt=_build_taskjson_prompt(requirement, full_history_text),
            feature=feature,
            date=date,
            task_id="final_taskjson",
        )

    task_json = _parse_task_json(task_json_output)

    # User final confirm
    task_json = _user_confirm_tasks(task_json, requirement)

    return task_json


def _display_architect_outputs(outputs: dict, round_num: int):
    panels = []
    for agent_name in ARCHITECTS:
        label, color = ARCHITECT_LABELS[agent_name]
        output = outputs.get(agent_name, "[no output]")
        # Trim for display
        display = output[:1200] + "..." if len(output) > 1200 else output
        panels.append(Panel(
            Markdown(display),
            title=f"[bold {color}]{label}[/bold {color}]",
            border_style=color,
            width=60,
        ))
    console.print(Columns(panels))


def _display_mediator(output: str):
    label, color = ARCHITECT_LABELS["mediator"]
    console.print(Panel(
        Markdown(output),
        title=f"[bold {color}]{label} — Synthesis[/bold {color}]",
        border_style=color,
    ))


def _build_context(requirement: str, history: list) -> str:
    if not history:
        return f"Original requirement:\n{requirement}"
    lines = [f"Original requirement:\n{requirement}\n"]
    for h in history:
        lines.append(f"\n## Round {h['round']} Summary\n{h['mediator_summary']}")
    return "\n".join(lines)


def _build_mediator_prompt(requirement: str, outputs: dict, round_num: int) -> str:
    parts = [f"Original requirement:\n{requirement}\n\nRound {round_num} architect inputs:\n"]
    for agent_name in ARCHITECTS:
        label, _ = ARCHITECT_LABELS[agent_name]
        parts.append(f"\n### {label}\n{outputs.get(agent_name, '')}")

    parts.append("""
---
Your job as Mediator:
1. Identify key agreements between architects
2. Surface the 2-3 main disagreements/tensions
3. Propose a synthesis position
4. List open questions that need another round OR flag if ready to proceed
Keep it concise. Use markdown headers.
""")
    return "\n".join(parts)


def _build_taskjson_prompt(requirement: str, history: str) -> str:
    return f"""
Based on this requirement and architect discussion, generate a task.json.

Requirement:
{requirement}

Discussion:
{history}

Output ONLY valid JSON in this exact format:
{{
  "feature": "<feature name>",
  "requirement_summary": "<one sentence>",
  "tasks": [
    {{
      "id": "task_01",
      "description": "<clear task description>",
      "agent": "<craftsman|reviewer|qa_sentinel|scribe|decomposer|archaeologist>",
      "depends_on": [],
      "status": "pending",
      "parallel_group": 1
    }}
  ]
}}

Rules:
- Tasks in the same parallel_group run at the same time
- depends_on lists task ids that must complete first
- Choose the most appropriate agent for each task
- Be specific in descriptions
- Output ONLY the JSON, no markdown fences, no explanation
"""


def _parse_task_json(raw: str) -> dict:
    import json
    import re
    # Strip markdown fences if present
    cleaned = re.sub(r"```json\s*|```\s*", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        console.print("[red]Warning: Could not parse task JSON, returning raw[/red]")
        return {"tasks": [], "raw": raw}


def _format_full_history(history: list) -> str:
    lines = []
    for h in history:
        lines.append(f"\n## Round {h['round']}\n")
        for agent_name in ARCHITECTS:
            label, _ = ARCHITECT_LABELS[agent_name]
            lines.append(f"### {label}\n{h['architect_outputs'].get(agent_name, '')}\n")
        lines.append(f"### Mediator\n{h['mediator_summary']}\n")
    return "\n".join(lines)


def _user_confirm_tasks(task_json: dict, requirement: str) -> dict:
    """Show tasks to user, allow edits before final confirm"""
    import json

    console.print()
    console.print(Panel(
        Markdown(f"## Proposed Task Plan\n\n**{task_json.get('requirement_summary', requirement)}**"),
        title="📋 Final Plan",
        border_style="bright_green",
    ))

    tasks = task_json.get("tasks", [])
    for t in tasks:
        deps = ", ".join(t.get("depends_on", [])) or "none"
        group = t.get("parallel_group", "?")
        console.print(
            f"  [cyan]{t['id']}[/cyan] [dim](group {group}, deps: {deps})[/dim]\n"
            f"    Agent: [green]{t.get('agent', '?')}[/green]\n"
            f"    {t['description']}\n"
        )

    while True:
        action = Prompt.ask(
            "\n[bold]Confirm this plan?[/bold]",
            choices=["yes", "edit", "abort"],
            default="yes",
        )

        if action == "yes":
            return task_json
        elif action == "edit":
            edited = click.edit(json.dumps(task_json, indent=2, ensure_ascii=False))
            if edited:
                try:
                    task_json = json.loads(edited)
                    console.print("[green]Plan updated.[/green]")
                except json.JSONDecodeError:
                    console.print("[red]Invalid JSON. Keeping original.[/red]")
        elif action == "abort":
            raise click.Abort()
