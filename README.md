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
# 1. 在你的项目里初始化
cd your-project
sili-vengers init

# 2. 开始一个新 feature（标准模式：多轮讨论）
sili-vengers start "migrate auth system to JWT"

# 2b. 快速模式（小需求/bug fix，一轮审核直接跑）
sili-vengers start --quick "fix login button color"

# 2c. 干跑模式（只生成计划，不执行）
sili-vengers start --dry-run "big refactor"

# 2d. 带额外上下文（给架构师喂文档）
sili-vengers start --context ./docs/spec.md "new payment flow"

# 3. confirm task.json 后自动执行，全程无需干预
# 如果有失败或冲突，按提示处理后：
sili-vengers task retry task_03
sili-vengers task retry task_03 --agent craftsman  # 换 agent 重跑
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | 初始化，创建 agents & hooks |
| `start "description"` | 新 feature：讨论 → 确认 → 自动执行 |
| `start --quick` | 快速模式：一轮审核直接跑 |
| `start --dry-run` | 只生成 task.json，不执行 |
| `start --context file` | 给架构师注入额外上下文文件 |
| `resume [feature]` | 恢复暂停的 feature |
| `stop [feature]` | 保存并暂停当前 feature |
| `crew` | 查看所有进行中的 feature |
| `status [feature]` | 查看 task 进度 |
| `log [feature]` | 查看执行日志 |
| `log --task task_02` | 查看指定 task 的日志 |
| `agents` | 列出所有 agent |
| `task run [feature]` | 手动触发执行所有 pending tasks |
| `task done <id>` | 手动标记 task 完成 |
| `task retry <id>` | 重置失败的 task 并重跑 |
| `task retry <id> --agent` | 换 agent 重跑 |

## The Crew

| Agent | Role |
|-------|------|
| 🔮 **Visionary** | 技术美学、直觉与系统优雅性 |
| ⚙️ **Architect** | 深度技术、性能与可靠性 |
| 🔭 **Scout** | 研究、业界模式与开源方案 |
| ⚖️ **Mediator** | 汇总讨论，驱动决策 |
| 🔬 **Decomposer** | 需求拆解 |
| 🔨 **Craftsman** | 代码实现 |
| 👁️ **Reviewer** | 代码审核 |
| 🛡️ **QA Sentinel** | 测试与质量保证 |
| 🏛️ **Archaeologist** | 老代码分析 |
| 📜 **Scribe** | 文档编写 |

## The Flow

```
sili-vengers start "description"
         │
         ▼
  [标准] 三架构师并行讨论（多轮）    [quick] 一轮快速审核
         │
         ▼
  Mediator 汇总 → 生成 task.json
         │
         ▼
  用户 confirm（可编辑）
         │
         ▼
  自动按 parallel_group 并行执行 tasks
  每个 task = 独立 claude 进程
         │
         ├── task 完成 → commit task 分支 → merge 到 feature 分支
         │
         ├── merge 冲突 → 状态标记 merge_conflict
         │   └── 手动解决 → sili-vengers task retry
         │
         └── 全部完成 → Scribe 生成 result.md → merge feature → main
```

## Task 状态

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `running` | 执行中 |
| `done` | 完成 |
| `failed` | 执行失败，需 retry |
| `merge_conflict` | 代码合并冲突，需手动解决 |

## 处理 merge conflict

```bash
# 系统会提示：
⚠️  task_03 merge conflict
    1. cd .worktrees/feature/migrate_auth_20250312
    2. git merge task/task_03_20250312
    3. 解决冲突
    4. git add . && git commit
    5. sili-vengers task retry task_03
```

## File Structure

```
your-project/
├── vengers-code.md                    # 项目配置（Claude 读取）
├── .vengers/
│   ├── .vengers.toml                  # 总状态
│   ├── agents/                        # Agent system prompts
│   │   ├── visionary.md
│   │   ├── architect.md
│   │   └── ...
│   ├── hooks/                         # Hook 脚本
│   │   ├── post-write.sh
│   │   └── ...
│   └── {feature}_{date}/              # 每个 feature 的工作目录
│       ├── requirements.md
│       ├── task.json
│       ├── logs/                      # 各 agent 执行日志
│       ├── tasks/
│       │   ├── task_01_result.md
│       │   ├── task_01_review.md
│       │   └── task_01_docs.md
│       └── result.md                  # 最终汇总
└── .worktrees/
    └── feature/{feature}_{date}/      # Git worktree
        └── task/{task_id}_{date}/     # 每个 task 的临时分支
```

## Why Independent Processes?

每个 task 是独立的 `claude --print` 子进程：

- `/clear` 永远不会中断正在运行的 tasks
- Tasks 真正并行执行
- 所有状态持久化到文件，随时可以 resume
- 进程崩溃不影响其他 tasks
