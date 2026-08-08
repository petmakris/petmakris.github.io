# Blog Tool Rewrite: Bash to Python

## Problem

The `bin/blog` tool is a single bash script that has grown fragile:
- YAML frontmatter manipulation via grep/sed/awk is error-prone
- Calorie calculation output must be manually copied into posts
- Platform-specific `date` flags (BSD vs GNU) cause portability issues
- Hard to extend with new commands

## Goals

- Rewrite as a single Python script for maintainability
- Eliminate manual file editing after calorie calculation
- Auto-calculate calories after editing a post
- Safe frontmatter handling (never corrupt a post)

## Non-Goals

- Splitting into a Python package with multiple modules
- Replacing `dialog` for the TUI picker
- Changing the Claude prompt templates or food index format
- Changing the Jekyll site structure

## Architecture

Single file: `bin/blog` (`#!/usr/bin/env python3`)

### Dependencies

| Dependency | Purpose | Install |
|---|---|---|
| `python-frontmatter` | Read/write YAML frontmatter in markdown | `pip install python-frontmatter` |
| `pyyaml` | Parse Claude's YAML output (comes with python-frontmatter) | — |
| `dialog` | TUI post picker | Already installed (external binary) |
| `claude` | LLM calorie calculation | Already installed (external binary) |

### Config

Read from `_config.yml` at runtime (single source of truth):
- `rmr` — resting metabolic rate (currently 1900)
- `timezone` — for date calculations (Europe/Athens)

`$EDITOR` environment variable respected, defaults to `vim`.

`BLOG_HOME` resolved relative to the script's own location.

## Commands

### `blog new`

1. Compute today and yesterday dates using `datetime` + timezone from config
2. Create `_posts/YYYY-MM-DD-notes.md` with frontmatter template (skip if exists)
3. Create `pics/YYYY-MM-DD/` directory
4. Update symlinks: `_posts/today.md` -> today's post, `_posts/yesterday.md` -> yesterday's post (if exists)

### `blog edit [target]`

1. Run `new` first to ensure today's post exists
2. If target is `today` or `yesterday` -> resolve symlink, open directly
3. If no target -> show `dialog` picker with last 10 posts (sorted date descending)
3. Open selected post in `$EDITOR`
4. **After editor exits: automatically run `calc` on the edited file**
5. Print calculated values to stdout

Event chain:
```
blog edit -> vim -> save & quit -> calc(file) -> frontmatter patched -> done
```

### `blog calc [target]`

1. Target defaults to `today`, also accepts `yesterday`
2. Resolve symlink to real file path
3. Load templates: `templates/prompt.txt`, `templates/food_index.txt`, `templates/summary.txt`
4. Read `rmr` from `_config.yml`
5. Build prompt via string substitution, call `claude -p` via subprocess
6. Parse Claude's YAML output with `yaml.safe_load()`
7. Validate: `intake` must be present and numeric; if not, abort with error (leave file unchanged)
8. Patch the `cal` block in the post's frontmatter using `python-frontmatter`
9. Print result to stdout

### `blog foods`

Open `templates/food_index.txt` in `$EDITOR`.

## Frontmatter Handling

Read and write via `python-frontmatter`:

```python
post = frontmatter.load(path)
post["cal"]["intake"] = 1580
frontmatter.dump(post, path)
```

The markdown body is preserved untouched. No regex, no awk.

## Claude Output Parsing

Claude outputs a YAML block:
```yaml
cal:
  deficit: 320
  intake: 1580
  tdee: 1900
  active: 0
  weight:
```

Parsed with `yaml.safe_load()`. Validation before writing:
- `intake` must be present and numeric
- On parse failure: print error, leave file unchanged

## Error Handling

- Missing post file: clear error message, exit 1
- Claude output unparseable: print error, leave file unchanged (safe fallback)
- `dialog` cancelled: exit cleanly
- Missing `_config.yml` keys: clear error message

## File Layout (unchanged)

```
blog/
  bin/blog              <- the Python script (replaces bash)
  _posts/
    YYYY-MM-DD-notes.md
    today.md            <- symlink
    yesterday.md        <- symlink
  pics/
    YYYY-MM-DD/
  templates/
    prompt.txt
    food_index.txt
    summary.txt
  _config.yml           <- rmr, timezone
```
