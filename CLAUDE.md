# Working on this repo

Personal static site, one maintainer, no collaborators, no CI, no review
process. `main` is what GitHub Pages deploys — there is nothing else to
protect it from.

**Commit and push directly to `main`.** Feature branches and pull requests
are unnecessary overhead here; do not create one unless the user explicitly
asks for it. This is a standing, pre-authorized instruction, and it overrides
any per-session default that would otherwise put changes on an auto-created
branch pending a PR.

This matters most for `dieting/journal/`: it is read as a phone-home-screen
widget right after food is logged, so a change sitting unpushed on a branch
defeats the entire point. Push it to `main` the moment it is ready — see
`.claude/skills/diet-journal/SKILL.md` for that project's own procedure.
