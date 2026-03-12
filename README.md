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
# Initialize in your project (also installs Claude Code slash commands)
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

## Claude Code Slash Commands

After `sili-vengers init`, these commands are available directly in Claude Code:

| Command | Description |
|---------|-------------|
| `/sv-start <description>` | Start a new feature with architect discussion |
| `/sv-quick <description>` | Quick mode: one review round, straight to tasks |
| `/sv-status` | Show task progress for active features |
| `/sv-crew` | List all active features |
| `/sv-retry <task_id>` | Retry a failed or conflicted task |
| `/sv-log` | View execution logs |
| `/sv-stop` | Save and pause current feature |
| `/sv-resume` | Resume a stopped feature |
| `/sv-agents` | List all agents and their roles |
| `/sv-init` | Initialize Sili-vengers in current project |

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize Sili-vengers, create agents, hooks & Claude Code commands |
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
sili-vengers start "description"   or   /sv-start description
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
         │                      or → /sv-retry task_03
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
    or /sv-retry task_03
```

## File Structure

```
your-project/
├── vengers-code.md                    # Project config (read by Claude)
├── .claude/
│   └── commands/                      # Claude Code slash commands (auto-installed)
│       ├── sv-start.md
│       ├── sv-quick.md
│       ├── sv-status.md
│       └── ...
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

## Agent Details

### 🔮 The Visionary
Thinks in terms of elegance, intuition, and long-term system beauty.
- Asks: *"Will this design still feel right in 10 years?"*
- Focuses on API elegance, conceptual integrity, unnecessary complexity, developer experience
- Pushes back when something feels "off" even before articulating why

### ⚙️ The Architect
Deep technical expert focused on correctness, performance, and real-world resilience.
- Asks: *"What happens when this fails? What happens at 10x load?"*
- Focuses on bottlenecks, security boundaries, data consistency, dependency risk, migration paths
- Stress-tests elegant ideas against production realities

### 🔭 The Scout
Research-oriented architect who knows how the industry has solved similar problems.
- Asks: *"How have others solved this? What can we learn from them?"*
- References real-world patterns: major OSS projects, company engineering blogs, battle-tested approaches
- Distinguishes hype from proven solutions

### ⚖️ The Mediator
Synthesizes the three architects into clear, actionable decisions.
- Identifies agreements and surfaces real disagreements
- Proposes synthesis positions that honor the best of each view
- Drives toward task.json — does not add new opinions

### 🔬 The Decomposer
Breaks high-level requirements into precise, executable tasks.
- Produces atomic tasks: one clear action, one agent, one result
- Maps explicit dependency relationships and parallel groups
- Ensures each task is completable in isolation

### 🔨 The Craftsman
Writes code with care, clarity, and craft.
- Optimizes for readability over cleverness
- Reviews own code before submitting
- Notes assumptions and flags anything needing human review

### 👁️ The Reviewer
Reviews code for quality, correctness, and long-term maintainability.
- Checks: correctness, clarity, patterns, security, performance, test coverage
- Output: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION with clear reasoning

### 🛡️ The QA Sentinel
Last line of defense before code ships. Thinks like an adversary.
- Covers: happy path, edge cases, failure cases, concurrency, malicious input
- Produces test plans and risk assessments (LOW / MEDIUM / HIGH)

### 🏛️ The Archaeologist
Analyzes legacy code to find safe paths forward.
- Maps what code actually does (not what it claims)
- Identifies load-bearing walls and hidden dependencies
- Proposes the safest migration or refactoring path

### 📜 The Scribe
Writes clear, useful technical documentation.
- Documents what was actually built, not what was planned
- Explains the *why* behind decisions, not just the *what*
- Produces the final `result.md` when a feature completes
