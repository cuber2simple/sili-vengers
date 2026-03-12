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
from rich.prompt import Prompt
from sili_vengers.core.runner import run_agents_parallel, run_agent

console = Console()

ARCHITECTS = ["visionary", "architect", "scout"]

ARCHITECT_LABELS = {
    "visionary": ("🔮 The Visionary", "magenta"),
    "architect": ("⚙️  The Architect", "cyan"),
    "scout":     ("🔭 The Scout", "green"),
    "mediator":  ("⚖️  Mediator", "yellow"),
}


def run_discussion(feature: str, date: str, requirement: str, extra_context: str = "") -> dict:
    """
    Full multi-round architect discussion.
    Returns confirmed task.json dict.
    """
    console.print()
    console.print(Panel(
        f"[bold]Assembling the crew for:[/bold]\n\n{requirement}",
        title="⚡ Sili-vengers",
        border_style="bright_blue",
    ))

    round_num = 1
    history = []

    while True:
        console.print(f"\n[bold yellow]── Round {round_num} ──[/bold yellow]")

        context = _build_context(requirement, history, extra_context)

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

        _display_architect_outputs(architect_outputs, round_num)

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

        history.append({
            "round": round_num,
            "architect_outputs": architect_outputs,
            "mediator_summary": mediator_output,
        })

        console.print()
        action = Prompt.ask(
            "[bold]Next?[/bold]  [dim]next=another round  proceed=build tasks  edit=change requirement[/dim]",
            choices=["next", "edit", "proceed"],
            default="next" if round_num < 2 else "proceed",
        )

        if action == "next":
            round_num += 1
        elif action == "edit":
            new_req = click.edit(requirement)
            if new_req and new_req.strip():
                requirement = new_req.strip()
                console.print("[green]Requirement updated.[/green]")
            round_num += 1
        else:
            break

    return _generate_and_confirm_tasks(feature, date, requirement, history)


def run_quick_discussion(feature: str, date: str, requirement: str, extra_context: str = "") -> dict:
    """
    Quick mode: one round, architects review only, Mediator goes straight to task.json.
    """
    console.print()
    console.print(Panel(
        f"[bold yellow]⚡ Quick mode[/bold yellow]\n\n{requirement}",
        title="Sili-vengers",
        border_style="yellow",
    ))

    context = _build_context(requirement, [], extra_context)
    agent_prompt = (
        f"Quick review of this requirement:\n\n{requirement}\n\n"
        "Give your top 2-3 concerns or recommendations. Be brief and direct."
    )

    console.print("[dim]Quick architect review...[/dim]")
    with console.status("[bold green]Reviewing...[/bold green]"):
        architect_outputs = run_agents_parallel(
            agents=[
                {"agent_name": a, "prompt": agent_prompt, "extra_context": context}
                for a in ARCHITECTS
            ],
            feature=feature,
            date=date,
        )

    _display_architect_outputs(architect_outputs, round_num=1)

    # Mediator goes straight to task.json
    full_history_text = _format_quick_history(requirement, architect_outputs)
    with console.status("[bold yellow]Building task plan...[/bold yellow]"):
        task_json_output = run_agent(
            agent_name="mediator",
            prompt=_build_taskjson_prompt(requirement, full_history_text),
            feature=feature,
            date=date,
            task_id="quick_taskjson",
        )

    task_json = _parse_task_json(task_json_output)
    return _user_confirm_tasks(task_json, requirement)


def _generate_and_confirm_tasks(feature: str, date: str, requirement: str, history: list) -> dict:
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
    return _user_confirm_tasks(task_json, requirement)


def _display_architect_outputs(outputs: dict, round_num: int):
    panels = []
    for agent_name in ARCHITECTS:
        label, color = ARCHITECT_LABELS[agent_name]
        output = outputs.get(agent_name, "[no output]")
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


def _build_context(requirement: str, history: list, extra_context: str = "") -> str:
    lines = [f"Original requirement:\n{requirement}"]
    if extra_context:
        lines.append(f"\nAdditional context:\n{extra_context}")
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
1. Identify key agreements
2. Surface 2-3 main disagreements/tensions
3. Propose a synthesis position
4. List open questions or flag if ready to proceed
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

Output ONLY valid JSON in this exact format, no markdown fences:
{{
  "feature": "<feature name>",
  "requirement_summary": "<one sentence>",
  "tasks": [
    {{
      "id": "task_01",
      "description": "<specific, actionable description>",
      "agent": "<craftsman|reviewer|qa_sentinel|scribe|decomposer|archaeologist>",
      "depends_on": [],
      "status": "pending",
      "parallel_group": 1
    }}
  ]
}}

Rules:
- Tasks in same parallel_group run simultaneously
- depends_on lists task ids that must complete first
- Be specific in descriptions
- Output ONLY the JSON
"""


def _parse_task_json(raw: str) -> dict:
    import json, re
    cleaned = re.sub(r"```json\s*|```\s*", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        console.print("[red]Warning: Could not parse task JSON[/red]")
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


def _format_quick_history(requirement: str, outputs: dict) -> str:
    lines = [f"Requirement:\n{requirement}\n\nQuick review:\n"]
    for agent_name in ARCHITECTS:
        label, _ = ARCHITECT_LABELS[agent_name]
        lines.append(f"### {label}\n{outputs.get(agent_name, '')}\n")
    return "\n".join(lines)


def _user_confirm_tasks(task_json: dict, requirement: str) -> dict:
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
            "\n[bold]Confirm plan?[/bold]",
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
