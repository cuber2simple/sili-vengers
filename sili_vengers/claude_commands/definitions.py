"""
Claude Code slash command definitions.
These are installed into .claude/commands/ during `sili-vengers init`.
"""

from pathlib import Path

CLAUDE_COMMANDS = {
    "sv-init": """\
Initialize Sili-vengers in this project.

Run the following in the terminal:
```bash
sili-vengers init
```

Then report back what was created, including:
- Which agents were created
- Which hooks were created
- Any sleeping processes found
""",

    "sv-start": """\
Start a new Sili-vengers feature with architect discussion.

The user will provide a feature description after the command, e.g.:
`/sv-start migrate auth system to JWT`

Extract the feature description from $ARGUMENTS, then run:
```bash
sili-vengers start "$ARGUMENTS"
```

If no arguments provided, ask the user: "What feature would you like to start?"

Report back the feature name, date key, and task plan once confirmed.
""",

    "sv-quick": """\
Start a new Sili-vengers feature in quick mode (one review round, no multi-round discussion).

Best for: small tasks, bug fixes, simple changes.

Extract the feature description from $ARGUMENTS, then run:
```bash
sili-vengers start --quick "$ARGUMENTS"
```

If no arguments provided, ask the user: "What would you like to build quickly?"
""",

    "sv-status": """\
Show the current task progress for active Sili-vengers features.

Run:
```bash
sili-vengers status
```

Then present the results clearly, highlighting:
- Tasks that are done ✓
- Tasks that are running →
- Tasks that are pending ○
- Tasks that failed ✗
- Tasks with merge conflicts ⚡

If multiple features are active, show status for all of them.
""",

    "sv-crew": """\
Show all active Sili-vengers feature processes.

Run:
```bash
sili-vengers crew
```

Present the results as a summary of what's currently in progress.
""",

    "sv-retry": """\
Retry a failed or merge-conflicted task.

The user will provide a task ID, e.g.: `/sv-retry task_03`
Optionally with an agent override: `/sv-retry task_03 --agent craftsman`

Parse $ARGUMENTS to extract task_id and optional --agent flag, then run:
```bash
sili-vengers task retry $ARGUMENTS
```

If no arguments provided, first run `sili-vengers status` to show the user
which tasks are failed or in merge_conflict state, then ask which to retry.

After retrying, report the outcome.
""",

    "sv-log": """\
Show execution logs for a Sili-vengers feature.

Parse $ARGUMENTS for optional feature name and --task flag, then run:
```bash
sili-vengers log $ARGUMENTS
```

If no arguments, run without arguments to show logs for the active feature.

Summarize the key events from the logs rather than dumping raw output.
Highlight any errors or warnings found.
""",

    "sv-stop": """\
Stop and save the current Sili-vengers feature process.

Run:
```bash
sili-vengers stop
```

Confirm to the user that the feature has been saved and can be resumed later with `/sv-resume`.
""",

    "sv-resume": """\
Resume a stopped Sili-vengers feature.

Parse $ARGUMENTS for optional feature name, then run:
```bash
sili-vengers resume $ARGUMENTS
```

If no arguments, show the list of sleeping features and let the user pick.
After resuming, show the pending tasks so the user knows what will run next.
""",

    "sv-agents": """\
List all available Sili-vengers agents and their roles.

Run:
```bash
sili-vengers agents
```

Present the agent list in a clear format, grouped by phase:
- Architect phase: visionary, architect, scout, mediator
- Execution phase: decomposer, craftsman, reviewer, qa_sentinel, archaeologist, scribe
""",
}

COMMAND_NAMES = list(CLAUDE_COMMANDS.keys())


def create_claude_commands(project_dir: Path):
    """Install slash commands into .claude/commands/"""
    commands_dir = project_dir / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for name, content in CLAUDE_COMMANDS.items():
        path = commands_dir / f"{name}.md"
        path.write_text(content)
        created.append(name)

    return created
