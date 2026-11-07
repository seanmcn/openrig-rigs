# Shipwrights

An engineering crew for [OpenRig](https://github.com/mvschwarz/openrig), built on OpenRig's
[Workshop](https://github.com/mvschwarz/openrig-world/tree/d544888b4c9973164e7986d7e0344a7ceca89a8c/rigs/workshop-review-pair)
team. You bring a goal; the planner cuts it into missions and slices, each one pull request, the lead hands them to
the builders and judges the proof that QA and two independent reviewers record, and the release manager publishes
each pull request and keeps it mergeable. You decide what is merged.

It works in a clone of one repository, or in a folder that holds clones of several: the seats read each repository's
own `AGENTS.md` before they start a slice there, and run every command from inside the slice's worktree.

| Seat | Runtime | Does |
|---|---|---|
| `orch-lead` | Codex | Starts from your goal, has it cut into slices, locks their specs, hands them on, judges their proof and owns each PR description. Talk to this seat. |
| `orch-peer` | Claude Code | Runs the lead's guidance on the other runtime and follows its work. Takes over, and tells you, only when the lead's seat has been down for 10 minutes; hands back with a recap. |
| `plan-planner` | Claude Code | Turns goals and issues into missions and slices, with triage, specs, dependencies and a build order. |
| `dev-backend` | Claude Code | Builds a backend slice in its own worktree, reviews its own diff and runs the repository's checks. |
| `dev-frontend` | Claude Code | Builds on the backend builder's guidance for slices tagged UI or both: checks them in a real browser and runs impeccable's reviews and detector. |
| `check-qa` | Claude Code | Runs the checks a slice calls for and records what each one proved. |
| `review-r1` | Claude Code | Reviews the handed-off commit with the named review skills, and runs the tests that bear on it. |
| `review-r2` | Codex | Reviews the same commit the same way, independently of `review-r1`. |
| `release-manager` | Codex | Publishes each judged slice's pull request with its merge gate, watches CI, rebases with lease and closes the slice after the merge. |

These are the recommended runtimes; `configurations.yaml` lets each seat use the other one. Keep the lead and its peer
on different runtimes. More builders join the `dev` pod with the builder-backend or builder-frontend profile.

## How the work moves

1. The planner records your goal or issues as missions in OpenRig's work tree (`rig scope`), with one slice per pull
   request and the dependencies between them. Each slice's `SPEC.md` lists the repositories it touches in merge order
   (`repos:` in its frontmatter), and says what a user gets, when it's done, what's out of scope, what to reuse, what
   it depends on and whether it is UI, backend or both, and ends with a proof contract. The lead locks each spec.
2. The lead hands each slice to a builder as a queue row whose tier matches the slice time limit: UI work to the
   frontend builder, backend work to the backend builder.
3. The builder builds and hands each commit to QA and both reviewers at once. They record their verdicts at that
   commit with `rig proof add`.
4. The lead compares the reviews and judges the proof with `rig proof judge` at that commit, again after any rebase or
   fix, then hands the slice to the release manager.
5. The release manager publishes only proof judged at the commit it pushes. It opens the pull request with a merge
   gate filled from the proof, watches CI, sends failures back
   to the builder and keeps the branch mergeable. A slice you gave the team is your word to open its pull request;
   merging, tagging and releasing still need yours, unless your settings for that repository allow them and the gate
   is all green. After you merge, it closes the slice.
6. Before closing its row, every seat writes a short retrospective note in the slice's PROGRESS. When a mission closes,
   the lead offers you the lessons as proposed changes to the guidance.

Waits are queue blocks with a wake, never polling. A reminder wakes the lead to check `rig queue overdue` for builds
past the time limit, and another wakes the peer to check that the lead's seat is up. Stop and pause hold the work and
keep every seat's session.

## Settings

`settings.md` holds the team settings, delivered to every seat at start:

| Setting | Default |
| --- | --- |
| Disagreement rounds before the person is asked | 2 |
| Confirm each triage result with the person | off |
| Slice time limit | 4 working hours |

To change one, edit `settings.md`, or ship your own copy of it in place of this one (below).

## Skills

Every seat gets OpenRig's `openrig-core` plugin and Workshop's `using-the-tui-together`, which this team ships. The
other skills its guidance names, such as `implement`, `tdd`, `code-review` and `impeccable`, it doesn't ship: you
install them at user level (`~/.claude/skills` and `~/.codex/skills`), where every seat finds them, or supply your own
versions under the same names. [`skills.md`](skills.md) lists each one with its source, a suggested commit, its
licence, the seats that use it and whether the guidance requires it, and `install-skills.sh` installs them from that
table. It never replaces a skill you already have.

## Before you start

- OpenRig 0.7.1 or later (`rig --version`), Node 22 or 24, and tmux.
- Claude Code and Codex installed and logged in, for the recommended runtimes.
- A clone of each repository you want to work on, set up the way its README says, and a GitHub login on this machine
  that can push to it and open pull requests.

Install the skills the guidance names, from a clone of the repository you got this team from, at the commit you
install. Preview first; `--dry-run` changes nothing:

```sh
rigs/shipwrights/install-skills.sh --dry-run
rigs/shipwrights/install-skills.sh
```

Keep OpenRig's files out of your commits. From the root of each clone:

```sh
printf '%s\n' CLAUDE.local.md AGENTS.md /.openrig/ .claude/settings.local.json /.worktrees/ >> .git/info/exclude
```

If you skip this, the lead adds any missing entries when it starts. An exclude line can't hide a file the repository
already tracks: if yours tracks `AGENTS.md` or `CLAUDE.local.md`, OpenRig's block shows up as a change to it, and the
seats keep that file out of their commits.

Optionally add OpenRig's public context pack, so the seats load it at start:

```sh
rig context add --git https://github.com/mvschwarz/openrig-world
```

## Install

From the folder the seats should work in, install the team from the GitHub link to this folder at a full commit
ID, previewing it first. `<link>` below is `https://github.com/<owner>/<repository>/tree/<commit>/rigs/shipwrights`
for the repository you got this team from:

```sh
rig bundle install <link> --preset recommended --target ~/rigs/shipwrights --cwd . --plan
rig bundle install <link> --preset recommended --target ~/rigs/shipwrights --cwd .
```

`--cwd .` sets where the seats work. A branch or tag in the link also works: OpenRig resolves it once and prints the
commit-pinned link to keep. Then tell the lead what you want:

```sh
rig send orch-lead@shipwrights "Please take issue #<number>: <one line on what you want>"
```

`rig capture orch-lead@shipwrights` reads its screen, `tmux attach -t orch-lead@shipwrights` puts a terminal on it,
and `rig` opens OpenRig's TUI. Stop the team with `rig down shipwrights`; the seats' worktrees under `.worktrees/`
stay until you remove them with `git worktree remove`.

## Building your own layer on top

The team is meant to be used as it is, or under a layer of your own that changes only what is yours: your settings
copy, your own skills in place of some of these, and startup files for your own rules. Keep a copy of this folder
pinned to a commit (OpenRig resolves agent specs only from disk), then in your own rig spec:

- deliver your own `settings.md` in place of this one;
- point the profiles' skill IDs at your own skills where you swap one;
- add or replace startup files for your own rules, and keep the role files as they are, so this team's improvements
  keep reaching you.

## Permissions

Every seat starts with permission prompts off: `rig.yaml` sets `permission_policy: builtin:yolo` and
`non_interruptive: true`. Claude Code seats launch with `--dangerously-skip-permissions`, and Codex seats with full
access and no approval prompts, so they can reach the local OpenRig daemon. Each seat can run any command on this
machine as you: install it where you are comfortable with that. Install and run it as your normal user, not root.

The team still asks for your word before it merges, tags or releases, and before it publishes anything you didn't
give it (CULTURE.md, "Lines we keep"). With prompts off, that rests on the seats following their instructions.

To go back to OpenRig's default posture, remove those two lines from `rig.yaml` before you launch. Claude Code seats
then ask before commands, and Codex seats run in `-s workspace-write`, which blocks the network, the local daemon
included.

### Codex seats and the sandbox

In the default posture, a Codex seat can't run `rig` commands, `git fetch`, `gh` or tests that need a local server. It
says so on its screen, and someone with daemon access reaches it with `rig send` and `rig capture`. To give the Codex
seats network access while keeping approvals, create a Codex profile with `sandbox_mode = "workspace-write"`,
`approval_policy = "on-request"` and `[sandbox_workspace_write] network_access = true`, and set
`codex_config_profile: <its name>` on `orch.lead`, `review.r2` and `release.manager` in `rig.yaml` (OpenRig's
`docs/reference/getting-started.md`, "Codex: select sandbox and approvals together").

## Limits

- **Nine seats run at once,** so expect nine seats' worth of provider usage. The peer and the planner are idle much of
  the time.
- **The peer's takeover is a check, not an alarm.** OpenRig has no watchdog that fires when a seat goes down, so the
  peer looks every five minutes and takes over after two looks ten minutes apart.
- **Each building seat uses its own worktree** and installs the repository's dependencies there, which costs disk and
  time.
- **The time limit counts clock hours in the queue.** The lead counts working hours itself before it acts on an
  overdue build.
- **Every map here is incomplete.** These files and the repository's own maps can be stale. The code and its behaviour
  decide.

## Credits

Shipwrights is a modified version of Workshop with a review pair, from
[mvschwarz/openrig-world](https://github.com/mvschwarz/openrig-world) at `d544888`, licensed under Apache-2.0
(`LICENSE`). `NOTICE.md` says what changed.
