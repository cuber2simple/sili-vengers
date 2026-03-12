# ⚡ Sili-vengers

> Multi-agent Claude Code orchestration. Your AI crew, assembled and ready.

## Install

```bash
# 推荐：pipx 全局安装
brew install pipx
pipx install git+ssh://git@github.com/cuber2simple/sili-vengers.git

# 或者 clone 后本地安装
git clone git@github.com:cuber2simple/sili-vengers.git
cd sili-vengers
pipx install .
```

## Quick Start

```bash
# Initialize in your project
sili-vengers init

# Start a new feature (launches architect discussion)
sili-vengers start "migrate auth system to JWT"

# Check your crew's active work
sili-vengers crew

# See task progress
sili-vengers status

# Run the tasks
sili-vengers task run

# Stop and save (safe to /clear after this)
sili-vengers stop

# Resume later
sili-vengers resume
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize Sili-vengers, create agents & hooks |
| `start "description"` | New feature: architect discussion → task.json |
| `resume [feature]` | Resume a stopped feature |
| `stop [feature]` | Save and pause current feature |
| `crew` | List all active features |
| `status [feature]` | Task progress for a feature |
| `agents` | List all agents |
| `task run [feature]` | Execute pending tasks (parallel) |
| `task done <id>` | Manually mark task done |
| `task retry <id>` | Reset failed task to pending |

## How It Works

### The Crew

| Agent | Role |
|-------|------|
| 🔮 **Visionary** | Tech aesthetics, elegance & intuition |
| ⚙️ **Architect** | Performance, correctness & resilience |
| 🔭 **Scout** | Research, industry patterns & OSS landscape |
| ⚖️ **Mediator** | Synthesizes architect discussion → decisions |
| 🔬 **Decomposer** | Breaks requirements into atomic tasks |
| 🔨 **Craftsman** | Code implementation |
| 👁️ **Reviewer** | Code review |
| 🛡️ **QA Sentinel** | Testing & quality assurance |
| 🏛️ **Archaeologist** | Legacy code analysis |
| 📜 **Scribe** | Documentation |

### The Flow

```
sili-vengers start "description"
         ↓
  3 architects discuss (parallel, multi-round)
         ↓
  Mediator synthesizes
         ↓
  User confirms task.json
         ↓
  sili-vengers task run
         ↓
  Tasks execute in parallel groups
  (each task = independent claude process)
         ↓
  Hooks: post-write → reviewer → QA → scribe → git worktree commit
```

### Why Independent Processes?

Each task runs as a separate `claude --print` subprocess. This means:
- `/clear` never kills your tasks
- Tasks run truly in parallel
- State lives in files, not context
- Resume anytime with `sili-vengers resume`

## File Structure

```
your-project/
├── vengers-code.md              # Project config (read by Claude)
├── .vengers/
│   ├── .vengers.toml            # Master state
│   ├── agents/                  # Agent system prompts
│   │   ├── visionary.md
│   │   ├── architect.md
│   │   └── ...
│   ├── hooks/                   # Hook scripts
│   │   ├── post-write.sh
│   │   └── ...
│   └── {feature}_{date}/        # Per-feature workspace
│       ├── requirements.md
│       ├── task.json
│       ├── tasks/
│       │   ├── task_01_result.md
│       │   ├── task_01_review.md
│       │   └── task_01_docs.md
│       └── result.md
└── .worktrees/
    └── feature/{feature}_{date}/ # Git worktrees per feature
```
