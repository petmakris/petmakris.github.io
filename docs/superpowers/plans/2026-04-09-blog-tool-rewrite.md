# Blog Tool Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the `bin/blog` bash script as a single Python script with safe frontmatter handling and auto-calc after editing.

**Architecture:** Single `bin/blog` Python script. Uses `python-frontmatter` for YAML frontmatter read/write, `yaml.safe_load()` for parsing Claude output, `subprocess` for calling `dialog`, `claude`, and `$EDITOR`. Config read from `_config.yml`.

**Tech Stack:** Python 3, python-frontmatter, pyyaml, dialog (external binary), claude CLI

---

### Task 1: Install dependency and scaffold the script

**Files:**
- Replace: `bin/blog`

- [ ] **Step 1: Install python-frontmatter**

Run: `pip install python-frontmatter`
Expected: Successfully installed python-frontmatter and pyyaml

- [ ] **Step 2: Write the scaffold with imports, config loader, and argparse**

Replace `bin/blog` entirely with:

```python
#!/usr/bin/env python3
"""blog — daily nutrition journal tool."""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import frontmatter
import yaml
from zoneinfo import ZoneInfo

# ── config ──────────────────────────────────────────────────

BLOG_HOME = Path(__file__).resolve().parent.parent
POSTS_DIR = BLOG_HOME / "_posts"
PICS_DIR = BLOG_HOME / "pics"
TEMPLATES_DIR = BLOG_HOME / "templates"
CONFIG_PATH = BLOG_HOME / "_config.yml"
EDITOR = os.environ.get("EDITOR", "vim")


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return {
        "rmr": cfg["rmr"],
        "tz": ZoneInfo(cfg.get("timezone", "Europe/Athens")),
    }


# ── commands (implemented in subsequent tasks) ──────────────


def main():
    parser = argparse.ArgumentParser(prog="blog", description="Daily nutrition journal tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("new", help="Create today's post and update symlinks")

    edit_p = sub.add_parser("edit", help="Pick a recent post to edit")
    edit_p.add_argument("target", nargs="?", help="today, yesterday, or omit for picker")

    calc_p = sub.add_parser("calc", help="Calculate calories for a post")
    calc_p.add_argument("target", nargs="?", default="today", help="today or yesterday")

    sub.add_parser("foods", help="Edit the food catalog")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "new":
        cmd_new()
    elif args.command == "edit":
        cmd_edit(args.target)
    elif args.command == "calc":
        cmd_calc(args.target)
    elif args.command == "foods":
        cmd_foods()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Make executable and verify scaffold runs**

Run: `chmod +x bin/blog && bin/blog --help`
Expected: Shows usage with new, edit, calc, foods subcommands

- [ ] **Step 4: Verify config loading**

Run: `python3 -c "exec(open('bin/blog').read()); cfg = load_config(); print(cfg)"`
Expected: `{'rmr': 1900, 'tz': ZoneInfo(key='Europe/Athens')}`

- [ ] **Step 5: Commit**

```bash
git add bin/blog
git commit -m "refactor: scaffold blog tool as Python script with argparse and config loader"
```

---

### Task 2: Implement `cmd_new`

**Files:**
- Modify: `bin/blog`

- [ ] **Step 1: Add cmd_new function**

Add before the `main()` function in `bin/blog`:

```python
# ── new ─────────────────────────────────────────────────────


def cmd_new():
    cfg = load_config()
    tz = cfg["tz"]
    today = datetime.now(tz).date()
    yesterday = today - timedelta(days=1)

    today_str = today.isoformat()
    yday_str = yesterday.isoformat()

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    (PICS_DIR / today_str).mkdir(parents=True, exist_ok=True)

    today_file = POSTS_DIR / f"{today_str}-notes.md"
    yday_file = POSTS_DIR / f"{yday_str}-notes.md"

    if not today_file.exists():
        post = frontmatter.Post(
            f"\n### Διατροφή\n\n- γιαούρτι\n\n<!---  ![pic](/pics/{today_str}/yogurt.jpg)<br> -->\n",
            layout="post",
            title=f"Notes {today_str}",
            date=today_str,
            cal={"deficit": None, "intake": None, "tdee": None, "active": 0, "weight": None},
        )
        today_file.write_text(frontmatter.dumps(post) + "\n")
        print(f"Created {today_file}")

    # Update symlinks
    today_link = POSTS_DIR / "today.md"
    today_link.unlink(missing_ok=True)
    today_link.symlink_to(today_file)

    yday_link = POSTS_DIR / "yesterday.md"
    if yday_file.exists():
        yday_link.unlink(missing_ok=True)
        yday_link.symlink_to(yday_file)
```

- [ ] **Step 2: Test cmd_new**

Run: `bin/blog new`
Expected: Creates today's post file (or says nothing if it already exists). Symlinks updated.

Run: `ls -la _posts/today.md _posts/yesterday.md`
Expected: Both symlinks point to the correct date files.

Run: `head -15 _posts/$(date +%F)-notes.md`
Expected: Shows frontmatter with `cal:` block and markdown body.

- [ ] **Step 3: Commit**

```bash
git add bin/blog
git commit -m "feat: implement cmd_new — post creation with symlinks"
```

---

### Task 3: Implement `cmd_calc`

**Files:**
- Modify: `bin/blog`

- [ ] **Step 1: Add cmd_calc function**

Add after `cmd_new` in `bin/blog`:

```python
# ── calc ────────────────────────────────────────────────────


def resolve_post(target):
    """Resolve a target ('today', 'yesterday') to a real post file path."""
    post_file = POSTS_DIR / f"{target}.md"
    if post_file.is_symlink():
        post_file = post_file.resolve()
    if not post_file.exists():
        print(f"Error: File not found -> {post_file}", file=sys.stderr)
        sys.exit(1)
    return post_file


def cmd_calc(target="today"):
    cfg = load_config()
    post_file = resolve_post(target)

    prompt_template = (TEMPLATES_DIR / "prompt.txt").read_text()
    food_index = (TEMPLATES_DIR / "food_index.txt").read_text()
    summary = (TEMPLATES_DIR / "summary.txt").read_text()
    user_input = post_file.read_text()

    prompt = (
        prompt_template
        .replace("{rmr}", str(cfg["rmr"]))
        .replace("{food_index}", food_index)
        .replace("{user_input}", user_input)
        .replace("{summary}", summary)
    )

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error: claude failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    print(output)

    # Parse the cal block from Claude's output
    try:
        parsed = yaml.safe_load(output)
    except yaml.YAMLError:
        print("Error: Could not parse Claude's output as YAML", file=sys.stderr)
        sys.exit(1)

    cal = parsed.get("cal") if isinstance(parsed, dict) else None
    if cal is None or not isinstance(cal.get("intake"), (int, float)):
        print("Error: Claude output missing valid 'intake' value", file=sys.stderr)
        sys.exit(1)

    # Patch frontmatter
    post = frontmatter.load(str(post_file))
    post["cal"] = {
        "deficit": cal.get("deficit"),
        "intake": cal.get("intake"),
        "tdee": cal.get("tdee"),
        "active": cal.get("active"),
        "weight": cal.get("weight"),
    }
    post_file.write_text(frontmatter.dumps(post) + "\n")
    print(f"Updated {post_file.name}")
```

- [ ] **Step 2: Test cmd_calc on an existing post**

First ensure today's post exists and has some food entries:
Run: `bin/blog new`

Run: `bin/blog calc`
Expected:
- Claude's YAML output printed to stdout
- "Updated YYYY-MM-DD-notes.md" message
- The post file's frontmatter `cal:` block is now filled in

Verify: `head -12 _posts/$(date +%F)-notes.md`
Expected: `cal:` block has numeric values for deficit, intake, tdee.

- [ ] **Step 3: Test cmd_calc for yesterday**

Run: `bin/blog calc yesterday`
Expected: Either calculates and updates, or prints "File not found" if no yesterday post.

- [ ] **Step 4: Commit**

```bash
git add bin/blog
git commit -m "feat: implement cmd_calc — Claude calorie calculation with frontmatter patching"
```

---

### Task 4: Implement `cmd_edit`

**Files:**
- Modify: `bin/blog`

- [ ] **Step 1: Add cmd_edit function**

Add after `cmd_calc` in `bin/blog`:

```python
# ── edit ────────────────────────────────────────────────────


def pick_post_with_dialog():
    """Show a dialog menu to pick from the last 10 posts, sorted date descending."""
    posts = sorted(POSTS_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-notes.md"), reverse=True)[:10]

    if not posts:
        print("No posts found", file=sys.stderr)
        sys.exit(1)

    menu_args = []
    for i, p in enumerate(posts, 1):
        menu_args += [str(i), p.name]

    result = subprocess.run(
        [
            "dialog", "--clear", "--no-tags",
            "--menu", "Select a post to edit", "15", "70", "10",
            *menu_args,
        ],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        sys.exit(0)  # user cancelled

    choice_idx = int(result.stderr.strip()) - 1
    return posts[choice_idx]


def cmd_edit(target=None):
    cmd_new()  # ensure today's post exists

    if target in ("today", "yesterday"):
        post_file = resolve_post(target)
    elif target is None:
        post_file = pick_post_with_dialog()
    else:
        print(f"Error: Unknown target '{target}'. Use 'today', 'yesterday', or omit.", file=sys.stderr)
        sys.exit(1)

    subprocess.run([EDITOR, str(post_file)])

    # Auto-calc after editing
    print("Calculating calories...")
    # Determine the symlink target name for calc
    today_link = POSTS_DIR / "today.md"
    yday_link = POSTS_DIR / "yesterday.md"

    if today_link.resolve() == post_file.resolve():
        cmd_calc("today")
    elif yday_link.exists() and yday_link.resolve() == post_file.resolve():
        cmd_calc("yesterday")
    else:
        # Direct calc on the file — temporarily symlink it
        # Simpler: just call calc logic directly with the resolved path
        cmd_calc_file(post_file)
```

- [ ] **Step 2: Refactor cmd_calc to accept a file path directly**

Replace the existing `cmd_calc` function with a version that accepts either a target name or a path. Change the function to split the logic:

```python
def cmd_calc(target="today"):
    post_file = resolve_post(target)
    cmd_calc_file(post_file)


def cmd_calc_file(post_file):
    """Run calorie calculation on a specific post file."""
    cfg = load_config()

    prompt_template = (TEMPLATES_DIR / "prompt.txt").read_text()
    food_index = (TEMPLATES_DIR / "food_index.txt").read_text()
    summary = (TEMPLATES_DIR / "summary.txt").read_text()
    user_input = post_file.read_text()

    prompt = (
        prompt_template
        .replace("{rmr}", str(cfg["rmr"]))
        .replace("{food_index}", food_index)
        .replace("{user_input}", user_input)
        .replace("{summary}", summary)
    )

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error: claude failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    print(output)

    try:
        parsed = yaml.safe_load(output)
    except yaml.YAMLError:
        print("Error: Could not parse Claude's output as YAML", file=sys.stderr)
        sys.exit(1)

    cal = parsed.get("cal") if isinstance(parsed, dict) else None
    if cal is None or not isinstance(cal.get("intake"), (int, float)):
        print("Error: Claude output missing valid 'intake' value", file=sys.stderr)
        sys.exit(1)

    post = frontmatter.load(str(post_file))
    post["cal"] = {
        "deficit": cal.get("deficit"),
        "intake": cal.get("intake"),
        "tdee": cal.get("tdee"),
        "active": cal.get("active"),
        "weight": cal.get("weight"),
    }
    post_file.write_text(frontmatter.dumps(post) + "\n")
    print(f"Updated {post_file.name}")
```

And simplify `cmd_edit` to always use `cmd_calc_file`:

```python
def cmd_edit(target=None):
    cmd_new()

    if target in ("today", "yesterday"):
        post_file = resolve_post(target)
    elif target is None:
        post_file = pick_post_with_dialog()
    else:
        print(f"Error: Unknown target '{target}'. Use 'today', 'yesterday', or omit.", file=sys.stderr)
        sys.exit(1)

    subprocess.run([EDITOR, str(post_file)])

    print("Calculating calories...")
    cmd_calc_file(post_file)
```

- [ ] **Step 3: Test cmd_edit with today shortcut**

Run: `bin/blog edit today`
Expected: Opens today's post in vim. After saving and quitting, auto-calculates and patches frontmatter.

- [ ] **Step 4: Test cmd_edit with dialog picker**

Run: `bin/blog edit`
Expected: Shows dialog picker with last 10 posts sorted date descending. After selecting and editing, auto-calculates.

- [ ] **Step 5: Commit**

```bash
git add bin/blog
git commit -m "feat: implement cmd_edit — editor with auto-calc on save"
```

---

### Task 5: Implement `cmd_foods` and finalize

**Files:**
- Modify: `bin/blog`

- [ ] **Step 1: Add cmd_foods function**

Add after `cmd_edit` in `bin/blog`:

```python
# ── foods ───────────────────────────────────────────────────


def cmd_foods():
    subprocess.run([EDITOR, str(TEMPLATES_DIR / "food_index.txt")])
```

- [ ] **Step 2: Verify all commands work end-to-end**

Run each command and verify:

```bash
bin/blog --help        # shows usage
bin/blog new           # creates post + symlinks
bin/blog edit today    # opens editor, auto-calcs on quit
bin/blog calc          # standalone calc for today
bin/blog calc yesterday  # calc for yesterday (if exists)
bin/blog foods         # opens food catalog in editor
```

- [ ] **Step 3: Clean up old bash artifacts**

The old bash script is already replaced. Check if there are leftover scripts in `bin/`:

Run: `ls bin/`
Expected: Only `blog` (the Python script)

- [ ] **Step 4: Final commit**

```bash
git add bin/blog
git commit -m "feat: implement cmd_foods, complete blog tool Python rewrite"
```
