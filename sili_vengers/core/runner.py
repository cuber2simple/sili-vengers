"""Agent runner - spawns independent claude subprocesses"""

import subprocess
import threading
import os
from pathlib import Path
from typing import Optional
from sili_vengers.core.state import get_agents_dir, get_feature_dir


def get_agent_prompt(agent_name: str) -> str:
    """Load agent system prompt from agents directory"""
    agents_dir = get_agents_dir()
    agent_file = agents_dir / f"{agent_name}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent definition not found: {agent_file}")
    return agent_file.read_text()


def run_agent(
    agent_name: str,
    prompt: str,
    feature: str,
    date: str,
    task_id: Optional[str] = None,
    extra_context: str = "",
) -> str:
    """
    Spawn an independent claude process for a single agent.
    Returns the output as a string.
    This is blocking - call from a thread for parallel execution.
    """
    system_prompt = get_agent_prompt(agent_name)

    if extra_context:
        full_prompt = f"{extra_context}\n\n---\n\n{prompt}"
    else:
        full_prompt = prompt

    cmd = [
        "claude",
        "--print",
        "--system-prompt", system_prompt,
        full_prompt,
    ]

    feature_dir = get_feature_dir(feature, date)
    log_dir = feature_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_name = f"{agent_name}_{task_id}.log" if task_id else f"{agent_name}.log"
    log_path = log_dir / log_name

    with open(log_path, "w") as log_file:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        output = result.stdout
        log_file.write(output)
        if result.stderr:
            log_file.write("\n--- STDERR ---\n")
            log_file.write(result.stderr)

    return output


def run_agents_parallel(
    agents: list[dict],
    feature: str,
    date: str,
) -> dict[str, str]:
    """
    Run multiple agents in parallel threads.
    agents: list of {agent_name, prompt, task_id (optional), extra_context (optional)}
    Returns: {agent_name: output}
    """
    results = {}
    threads = []
    lock = threading.Lock()

    def worker(agent_config: dict):
        name = agent_config["agent_name"]
        try:
            output = run_agent(
                agent_name=name,
                prompt=agent_config["prompt"],
                feature=feature,
                date=date,
                task_id=agent_config.get("task_id"),
                extra_context=agent_config.get("extra_context", ""),
            )
            with lock:
                results[name] = output
        except Exception as e:
            with lock:
                results[name] = f"[ERROR] {str(e)}"

    for agent_config in agents:
        t = threading.Thread(target=worker, args=(agent_config,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results


def run_task_agent(
    agent_name: str,
    task: dict,
    feature: str,
    date: str,
    requirements: str,
) -> str:
    """
    Run a single task with specified agent.
    Loads task context from task.json and requirements.md
    """
    task_context = f"""
# Requirements
{requirements}

# Current Task
ID: {task['id']}
Description: {task['description']}
Agent: {task.get('agent', agent_name)}

# Dependencies (already completed)
{_format_dependencies(task)}
"""
    return run_agent(
        agent_name=agent_name,
        prompt=f"Execute this task and write your result in markdown format:\n\n{task['description']}",
        feature=feature,
        date=date,
        task_id=task["id"],
        extra_context=task_context,
    )


def _format_dependencies(task: dict) -> str:
    deps = task.get("depends_on", [])
    if not deps:
        return "None"
    return "\n".join(f"- {dep}" for dep in deps)
