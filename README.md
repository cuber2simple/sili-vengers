# ⚡ Sili-vengers

> Multi-agent Claude Code orchestration. Your AI crew, assembled and ready.

## Install

```bash
# Recommended: install globally via pipx
brew install pipx
pipx install git+ssh://git@github.com/cuber2simple/sili-vengers.git

# Or clone and install locally
git clone git@github.com:cuber2simple/sili-vengers.git
cd sili-vengers
pipx install .
```

## Quick Start

```bash
# Initialize in your project
cd your-project
sili-vengers init

# Start a new feature (standard: multi-round architect discussion)
sili-vengers start "migrate auth system to JWT"

# Quick mode (small tasks / bug fixes — one review round, straight to execution)
sili-vengers start --quick "fix login button color"

# Dry run (generate task plan only, do not execute)
sili-vengers start --dry-run "big refactor"

# With extra context files for the architects
sili-vengers start --context ./docs/spec.md "new payment flow"

# After confirming task.json, execution runs automatically.
# If a task fails or hits a merge conflict:
sili-vengers task retry task_03
sili-vengers task retry task_03 --agent craftsman  # retry with a different agent
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize Sili-vengers, create agents & hooks |
| `start "description"` | New feature: discuss → confirm → auto-execute |
| `start --quick` | Quick mode: one review round, skip discussion |
| `start --dry-run` | Generate task.json only, do not run tasks |
| `start --context file` | Inject extra context files for architects |
| `resume [feature]` | Resume a stopped feature |
| `stop [feature]` | Save and pause current feature |
| `crew` | List all active features |
| `status [feature]` | Show task progress for a feature |
| `log [feature]` | Show execution logs |
| `log --task task_02` | Show logs for a specific task |
| `agents` | List all agents |
| `task run [feature]` | Manually trigger execution of pending tasks |
| `task done <id>` | Manually mark a task as done |
| `task retry <id>` | Reset a failed task and re-run it |
| `task retry <id> --agent` | Retry with a different agent |

## The Crew

| Agent | Role |
|-------|------|
| 🔮 **Visionary** | Tech aesthetics, intuition & system elegance |
| ⚙️ **Architect** | Performance, correctness & resilience |
| 🔭 **Scout** | Research, industry patterns & OSS landscape |
| ⚖️ **Mediator** | Synthesizes discussion into decisions |
| 🔬 **Decomposer** | Breaks requirements into atomic tasks |
| 🔨 **Craftsman** | Code implementation |
| 👁️ **Reviewer** | Code review |
| 🛡️ **QA Sentinel** | Testing & quality assurance |
| 🏛️ **Archaeologist** | Legacy code analysis |
| 📜 **Scribe** | Documentation |

## The Flow

```
sili-vengers start "description"
         │
         ▼
  [standard] 3 architects discuss in parallel (multi-round)
  [quick]    1 round review, straight to tasks
         │
         ▼
  Mediator synthesizes → generates task.json
         │
         ▼
  User confirms (editable)
         │
         ▼
  Tasks execute automatically in parallel groups
  Each task = independent claude subprocess
         │
         ├── task done → commit task branch → merge into feature branch
         │
         ├── merge conflict → status: merge_conflict
         │   └── resolve manually → sili-vengers task retry
         │
         └── all done → Scribe writes result.md → merge feature → main
```

## Task Statuses

| Status | Description |
|--------|-------------|
| `pending` | Waiting to run |
| `running` | Currently executing |
| `done` | Completed successfully |
| `failed` | Execution error, needs retry |
| `merge_conflict` | Git merge conflict, needs manual resolution |

## Handling Merge Conflicts

When a task hits a merge conflict, Sili-vengers will guide you:

```
⚠️  task_03 merge conflict
    Branch: task/task_03_20250312

    To resolve:
    1. cd .worktrees/feature/migrate_auth_20250312
    2. git merge task/task_03_20250312
    3. Resolve conflicts
    4. git add . && git commit
    5. sili-vengers task retry task_03
```

## File Structure

```
your-project/
├── vengers-code.md                    # Project config (read by Claude)
├── .vengers/
│   ├── .vengers.toml                  # Master state
│   ├── agents/                        # Agent system prompts
│   │   ├── visionary.md
│   │   ├── architect.md
│   │   └── ...
│   ├── hooks/                         # Hook scripts
│   │   ├── post-write.sh
│   │   └── ...
│   └── {feature}_{date}/              # Per-feature workspace
│       ├── requirements.md
│       ├── task.json
│       ├── logs/                      # Per-agent execution logs
│       ├── tasks/
│       │   ├── task_01_result.md
│       │   ├── task_01_review.md
│       │   └── task_01_docs.md
│       └── result.md                  # Final summary
└── .worktrees/
    └── feature/{feature}_{date}/      # Git worktree per feature
        └── task/{task_id}_{date}/     # Temporary task branches
```

## Why Independent Processes?

Each task runs as a separate `claude --print` subprocess:

- `/clear` never kills running tasks
- Tasks run truly in parallel
- All state is persisted to files — resume anytime
- One process crashing does not affect others
