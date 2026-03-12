"""Hook definitions - creates shell scripts in hooks directory"""

import stat
from pathlib import Path

HOOK_NAMES = ["post-write", "post-review", "post-task", "post-scribe", "pre-start"]

HOOK_SCRIPTS = {
    "post-write": """\
#!/bin/bash
# post-write hook: triggers reviewer after code changes
# Usage: called automatically after craftsman writes code
# Args: $1=feature $2=date $3=task_id

FEATURE=$1
DATE=$2
TASK_ID=$3

echo "[hook:post-write] Triggering reviewer for $TASK_ID..."

RESULT_FILE=".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_result.md"

if [ ! -f "$RESULT_FILE" ]; then
    echo "[hook:post-write] No result file found, skipping"
    exit 0
fi

SYSTEM_PROMPT=$(cat ".vengers/agents/reviewer.md")
TASK_CONTENT=$(cat "$RESULT_FILE")

claude --print \
    --system-prompt "$SYSTEM_PROMPT" \
    "Review this code:\n\n$TASK_CONTENT" \
    > ".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_review.md"

echo "[hook:post-write] Review saved to ${TASK_ID}_review.md"
""",
    "post-review": """\
#!/bin/bash
# post-review hook: triggers QA sentinel if review passes
# Args: $1=feature $2=date $3=task_id $4=verdict (APPROVE|REQUEST_CHANGES)

FEATURE=$1
DATE=$2
TASK_ID=$3
VERDICT=$4

if [ "$VERDICT" != "APPROVE" ]; then
    echo "[hook:post-review] Verdict is $VERDICT, skipping QA"
    exit 0
fi

echo "[hook:post-review] Review passed, triggering QA Sentinel..."

SYSTEM_PROMPT=$(cat ".vengers/agents/qa_sentinel.md")
RESULT_FILE=".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_result.md"

claude --print \
    --system-prompt "$SYSTEM_PROMPT" \
    "Run QA on this implementation:\n\n$(cat $RESULT_FILE)" \
    > ".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_qa.md"

echo "[hook:post-review] QA report saved to ${TASK_ID}_qa.md"
""",
    "post-task": """\
#!/bin/bash
# post-task hook: triggers scribe to write documentation
# Args: $1=feature $2=date $3=task_id

FEATURE=$1
DATE=$2
TASK_ID=$3

echo "[hook:post-task] Triggering Scribe for $TASK_ID..."

SYSTEM_PROMPT=$(cat ".vengers/agents/scribe.md")
RESULT_FILE=".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_result.md"

claude --print \
    --system-prompt "$SYSTEM_PROMPT" \
    "Document this completed task:\n\nTask: $TASK_ID\n\nResult:\n$(cat $RESULT_FILE)" \
    > ".vengers/${FEATURE}_${DATE}/tasks/${TASK_ID}_docs.md"

echo "[hook:post-task] Docs saved to ${TASK_ID}_docs.md"
""",
    "post-scribe": """\
#!/bin/bash
# post-scribe hook: commits completed task to git worktree
# Args: $1=feature $2=date $3=task_id

FEATURE=$1
DATE=$2
TASK_ID=$3

WORKTREE_PATH=".worktrees/feature/${FEATURE}_${DATE}"
BRANCH="feature/${FEATURE}_${DATE}"

if [ ! -d "$WORKTREE_PATH" ]; then
    echo "[hook:post-scribe] Worktree not found at $WORKTREE_PATH, skipping"
    exit 0
fi

echo "[hook:post-scribe] Committing $TASK_ID to worktree..."

# Copy task results to worktree
TASK_DIR=".vengers/${FEATURE}_${DATE}/tasks"
cp -r "$TASK_DIR" "$WORKTREE_PATH/.vengers-tasks/" 2>/dev/null || true

cd "$WORKTREE_PATH"
git add -A
git commit -m "feat($FEATURE): complete $TASK_ID

Task: $TASK_ID
Feature: $FEATURE
Auto-committed by sili-vengers post-scribe hook"

echo "[hook:post-scribe] Committed $TASK_ID to $BRANCH"
""",
    "pre-start": """\
#!/bin/bash
# pre-start hook: checks task dependencies before executing
# Args: $1=feature $2=date $3=task_id
# Exits 1 if dependencies not met (blocks task execution)

FEATURE=$1
DATE=$2
TASK_ID=$3

TASK_JSON=".vengers/${FEATURE}_${DATE}/task.json"

if [ ! -f "$TASK_JSON" ]; then
    echo "[hook:pre-start] No task.json found"
    exit 1
fi

# Use python to check deps (jq might not be available)
python3 - <<EOF
import json, sys

with open("$TASK_JSON") as f:
    data = json.load(f)

tasks = {t["id"]: t for t in data.get("tasks", [])}
task = tasks.get("$TASK_ID")

if not task:
    print(f"[hook:pre-start] Task $TASK_ID not found")
    sys.exit(1)

deps = task.get("depends_on", [])
for dep in deps:
    dep_task = tasks.get(dep)
    if not dep_task or dep_task.get("status") != "done":
        print(f"[hook:pre-start] BLOCKED: dependency {dep} not done (status: {dep_task.get('status', 'unknown') if dep_task else 'missing'})")
        sys.exit(1)

print(f"[hook:pre-start] All dependencies met for $TASK_ID")
sys.exit(0)
EOF
""",
}


def create_all_hooks(hooks_dir: Path, only: list = None):
    """Create hook shell scripts, make them executable"""
    hooks_dir.mkdir(parents=True, exist_ok=True)
    names = only or HOOK_NAMES
    for name in names:
        script = HOOK_SCRIPTS.get(
            name, f"#!/bin/bash\n# {name} hook\necho '[{name}] triggered'\n"
        )
        path = hooks_dir / f"{name}.sh"
        path.write_text(script)
        path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
