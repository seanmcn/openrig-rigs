# openrig-rigs

Teams for [OpenRig](https://github.com/mvschwarz/openrig), each a folder under `rigs/` that installs as a bundle.

| Team | What it is |
|---|---|
| [`rigs/shipwrights`](rigs/shipwrights) | An engineering crew built on OpenRig's Workshop: a lead, a builder, QA and two independent reviewers who take a goal to judged, mergeable pull requests. |

Install a team from its GitHub link at a full commit ID; each team's README has the commands.

## Working on a team

A team ships no third-party skills. Its `skills.md` lists the skills its guidance names, each with its source, a
suggested commit and its licence, and its `install-skills.sh` installs them at user level for Claude Code and Codex.

- `scripts/check-team.py rigs/<team>` checks the team: its settings, that every skill its guidance names is in
  `skills.md` with a source, commit and licence, that `install-skills.sh` reads that table, that its profiles select
  only skills inside the team folder, the rules its role guidance relies on, and `rig bundle check` when `rig` is
  installed. Set
  `TEAM_BLOCKLIST` to a comma-separated list of words the team must never contain, such as names from the setup it was
  first built for.
