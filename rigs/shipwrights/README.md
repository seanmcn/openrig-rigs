# Shipwrights

An engineering team for [OpenRig](https://github.com/mvschwarz/openrig), built on OpenRig's
[Workshop](https://github.com/mvschwarz/openrig-world/tree/d544888b4c9973164e7986d7e0344a7ceca89a8c/rigs/workshop-review-pair)
team. You bring a goal. The planner cuts it into a mission of slices, each one change with one pull request in every
repository it touches. The lead hands the slices to the builders and judges the proof that QA and two independent
reviewers record, and the release manager publishes each pull request and keeps it mergeable. You decide what is
merged.

It works in a clone of one repository, or in a folder that holds clones of several: the seats read each repository's
own `AGENTS.md` before they start a slice there, and run every command from inside the slice's worktree. The words
these docs use, such as seat, slice and proof, are in the repository's [glossary](../../GLOSSARY.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/seats-dark.svg">
  <img alt="Shipwrights' seats in five pods, with the lead (Codex) as the hub and its peer (Claude Code) standing in while it is down. Your goal goes to the lead, which hands it to the planner; the planner sends slices back; the lead hands each locked slice to a builder, and the builders and QA report results back. The builders hand each commit to QA, then once QA passes it to reviewers r1 (Claude Code) and r2 (Codex), whose findings go straight to the builders and verdicts to the lead. The lead hands judged slices to the release manager (Codex), which reports the pull request and its delivery." src="diagrams/seats.svg">
</picture>

| Seat | Runtime | Does |
|---|---|---|
| `orch-lead` | Codex | Starts from your goal, has it cut into slices, locks their specs, hands them on, judges their proof and owns each PR description. Talk to this seat. |
| `orch-peer` | Claude Code | Runs the lead's guidance on the other runtime and follows its work. Takes over, and tells you, only when the lead's seat has been down for 10 minutes; hands back with a recap. |
| `plan-planner` | Claude Code | Turns goals and issues into missions and slices, with triage, specs, dependencies and a build order. |
| `dev-backend` | Claude Code | Builds a backend slice in its own worktree, reviews its own diff and runs the repository's checks. |
| `dev-frontend` | Claude Code | Builds on the backend builder's guidance for slices tagged UI or both: checks them in a real browser and runs impeccable's reviews and detector. |
| `dev-qa` | Claude Code | Runs the checks a slice calls for and records what each one proved. |
| `review-r1` | Claude Code | Reviews the handed-off commit with the named review skills, and runs the tests that bear on it. |
| `review-r2` | Codex | Reviews the same commit the same way, independently of `review-r1`. |
| `release-manager` | Codex | Publishes each judged slice's pull requests with their merge gate, watches CI, rebases with lease and approves each merged slice for delivery. |

These are the runtimes of the `recommended` preset; [`configurations.yaml`](configurations.yaml) lets each seat use the
other one. Keep the lead and its peer on different runtimes. More builders join the `dev` pod with the builder-backend
or builder-frontend profile.

## How the work moves

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/how-the-work-moves-dark.svg">
  <img alt="How the work moves: your goal goes to the lead and planner, who cut and lock it; a builder builds a commit and QA checks it, back and forth until QA passes; both reviewers then review that commit, and any findings go back to the builder and through QA again; the lead judges the proof; the release manager opens the pull requests; you merge; the release manager approves delivery." src="diagrams/how-the-work-moves.svg">
</picture>

1. The planner records your goal or issues as a mission in OpenRig's work tree (`rig scope`), with its slices and the
   dependencies between them. Each slice's `SPEC.md` lists the repositories it touches in merge order and ends with a
   proof contract ([`slice-spec.md`](startup/slice-spec.md)). The lead locks each spec.
2. The lead hands each slice to a builder as a queue row: slices tagged UI or both to the frontend builder, backend
   slices to the backend builder ([`lead.md`](agents/shipwrights/guidance/lead.md), "Hand it on").
3. The builder hands each commit to QA, and they go back and forth until QA passes one. Then both reviewers review
   that commit. A fix for their findings goes through QA again before they look again. QA and the reviewers each
   record their proof at the commit they checked.
4. The lead compares the reviews and judges the proof at that commit, again after any rebase or fix, then hands the
   slice to the release manager.
5. The release manager publishes only proof judged at the commit it pushes, one pull request per repository, each
   opened with a merge gate. It watches CI, sends failures back to the builder and keeps the branches mergeable. A
   slice you gave the team is your word to open its pull requests. Merging, tagging and releasing still need yours,
   unless the repository's `AGENTS.md` allows an agent to merge in its `### Merging` section and the merge gate is all
   green ([`release-manager.md`](agents/shipwrights/guidance/release-manager.md)). After you merge, it approves the
   slice for delivery.
6. Before closing a queue row on a slice, each seat that worked on it adds a short retrospective note to its slice
   progress. When a mission closes, the lead offers you the lessons as proposed changes to the guidance.

Waits are queue rows blocked with a wake, never polling. An OpenRig watchdog wakes the lead on a timer to check for
builds past the slice time limit, and another wakes the peer to check that the lead's seat is up.

To drop a slice, tell the lead to stop it: its queue rows and the slice are closed. To hold a slice or a mission, tell
the lead to pause it: its rows are blocked until you resume it. Neither stops a seat's session.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/slice-lifecycle-dark.svg">
  <img alt="A slice's lifecycle: spec locked, building with QA until QA passes, in review, judged and published, with reviewers' findings and a failing CI run looping back to building and a rebase back to judged; from any phase it can be paused and resumed, or stopped; once you merge, it is delivered." src="diagrams/slice-lifecycle.svg">
</picture>

## Settings

[`settings.md`](settings.md) holds the team settings and their defaults. Every seat reads it at start and refocus. To
change one, edit it in your installed copy, or ship your own copy in an overlay (below).

## Skills

Every seat gets OpenRig's `openrig-core` plugin and Workshop's `using-the-tui-together`, which this team ships. The
other skills its guidance names, such as `implement`, `tdd`, `code-review` and `impeccable`, it doesn't ship: you
install them at user level (`~/.claude/skills` and `~/.codex/skills`), where every seat finds them, or supply your own
versions under the same names. [`skills.md`](skills.md) lists each one with its source, a suggested commit, its
licence, the seats that use it and whether the guidance requires it, and how to install them.

## Before you start

- OpenRig 0.7.1 or later (`rig --version`), with its kernel running, Node 22 or 24, and tmux.
- Claude Code and Codex installed and logged in, for the recommended runtimes.
- `gh` installed and logged in, with a GitHub account that can push to each repository and open pull requests.
- Your git identity set (`git config user.name` and `user.email`): the seats commit as you, and stop if it's empty.
- A clone of each repository you want to work on, set up the way its README says.
- A clone of this repository at the commit you install, for the skills installer and for editing the team.

Install the skills the guidance names from that clone, as [`skills.md`](skills.md) says ("Install them").

Keep OpenRig's files out of your commits. From the root of each clone:

```sh
printf '%s\n' CLAUDE.local.md AGENTS.md /.openrig/ .claude/settings.local.json /.worktrees/ >> .git/info/exclude
```

If you skip this, the lead adds the missing entries when it starts, along with one per skill OpenRig projects into the
clone ([`lead.md`](agents/shipwrights/guidance/lead.md), "First, keep OpenRig's files out of commits"). An exclude
line can't hide a file the repository already tracks: if yours tracks `AGENTS.md` or `CLAUDE.local.md`, OpenRig's
block shows up as a change to it, and the seats keep that file out of their commits.

Optionally add OpenRig's public context pack, so the seats load it at start:

```sh
rig context add --git https://github.com/mvschwarz/openrig-world
```

## Install

From the folder the seats should work in, install the team from the GitHub link to this folder, previewing it first.
`<link>` below is `https://github.com/seanmcn/openrig-rigs/tree/<commit>/rigs/shipwrights`. Pin a full commit ID; a
branch or tag also works, and OpenRig resolves it once and prints the commit-pinned link to keep.

```sh
rig bundle install <link> --preset recommended --target ~/rigs/shipwrights --cwd . --plan
rig bundle install <link> --preset recommended --target ~/rigs/shipwrights --cwd .
```

`--cwd .` sets where the seats work, and `--target` is your installed copy of the team. To put one seat on the other
runtime, add `--seat <pod.member>=<runtime>`, such as `--seat review.r1=codex`.

Then give your goal to OpenRig's kernel operator, the seat you talk to in OpenRig's view (`rig` opens it), such as
"Have shipwrights take issue #42: <one line on what you want>". It hands the goal to the lead as a queue row. The lead
starts from that row; with no goal, it proposes work from the repository and asks before starting it.

`rig capture orch-lead@shipwrights` reads the lead's screen and `tmux attach -t orch-lead@shipwrights` puts a terminal
on it. Watch for prompts: the seats never answer one for you, and tell you which seat is waiting.

## Stop, start again and remove

- **Stop:** `rig down shipwrights` ends every seat's session. `rig down shipwrights --snapshot` also saves their state.
- **Start again:** `rig up shipwrights --existing` brings the team back, resuming each seat's conversation where it
  can. Or ask the kernel operator.
- **Remove:** stop the team, then delete your installed copy (`~/rigs/shipwrights` above), the seats' worktrees with
  `git worktree remove` (they're under `.worktrees/` in each clone), and the skills `install-skills.sh` added, which
  [`skills.md`](skills.md) lists.

Outside your clones, the team writes to OpenRig's workspace (`rig config get workspace.root`): its missions and slices,
and the lead's roster of the team's seats in `rosters/shipwrights.json`. Delete those too if you want no trace.

## Changing the team

Edit your installed copy (`--target`), not the GitHub link, and start the team again. Two changes people make:

- **Settings:** edit `settings.md` there.
- **Permissions:** the two lines in `rig.yaml` below.

To change more and keep taking this team's improvements, use an overlay instead.

## Overlays

The team is meant to be used as it is, or under an overlay of your own that changes only what is yours: your settings
copy, your own skills in place of some of these, and startup files for your own rules. Keep a copy of this folder
pinned to a commit (OpenRig resolves agent specs only from disk), then in your own rig spec:

- deliver your own `settings.md` in place of this one;
- point the profiles' skill IDs at your own skills where you swap one;
- add or replace startup files for your own rules, and keep the role files as they are, so this team's improvements
  keep reaching you.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/seat-start-dark.svg">
  <img alt="What a seat starts with: every seat gets the culture, the start steps, the settings and the skills; each profile adds its role guidance, and each seat its own start files. In an overlay, the settings are your copy, any skill can be swapped for yours, the role guidance stays as it is, and you add start files for your own rules." src="diagrams/seat-start.svg">
</picture>

## Permissions

Every seat starts with permission prompts off: `rig.yaml` sets `permission_policy: builtin:yolo` and
`non_interruptive: true`. Claude Code seats launch with `--dangerously-skip-permissions`, and Codex seats with full
access and no approval prompts, so they can reach the local OpenRig daemon. Each seat can run any command on this
machine as you: install it where you are comfortable with that. Install and run it as your normal user, not root.

The team still asks for your word before it merges, tags or releases, and before it publishes anything you didn't
give it ([`CULTURE.md`](CULTURE.md), "Lines we keep"). With prompts off, that rests on the seats following their
instructions.

To go back to OpenRig's default posture, remove those two lines from `rig.yaml` before you launch. Claude Code seats
then ask before commands, and Codex seats run in `-s workspace-write`, which blocks the network, the local daemon
included.

### Codex seats and the sandbox

In the default posture, a Codex seat can't run `rig` commands, `git fetch`, `gh` or tests that need a local server. It
says so on its screen, and someone with daemon access reaches it with `rig send` and `rig capture`. To give the Codex
seats network access while keeping approvals, create a Codex profile with `sandbox_mode = "workspace-write"`,
`approval_policy = "on-request"` and `[sandbox_workspace_write] network_access = true`, and set
`codex_config_profile: <its name>` on each seat that runs on Codex in `rig.yaml`: `orch.lead`, `review.r2` and
`release.manager` in the recommended preset (OpenRig's `docs/reference/getting-started.md`, "Codex: select sandbox
and approvals together").

## Limits

- **Nine seats run at once,** so expect nine seats' worth of provider usage. The peer and the planner are idle much of
  the time.
- **The peer's takeover is a check, not an alarm.** OpenRig has no event that fires when a seat goes down, so a
  watchdog wakes the peer every five minutes to look, and it takes over only once the lead has been down for 10
  minutes without a break ([`peer.md`](agents/shipwrights/guidance/peer.md)).
- **Each building seat uses its own worktree** and installs the repository's dependencies there, which costs disk and
  time.
- **The time limit counts clock hours in the queue.** The lead counts working hours itself before it acts on an
  overdue build.
- **Every map here is incomplete.** These files and the repository's own maps can be stale. The code and its behaviour
  decide.

## Credits

Shipwrights is a modified version of Workshop with a review pair, from
[mvschwarz/openrig-world](https://github.com/mvschwarz/openrig-world) at `d544888`, licensed under Apache-2.0
([`LICENSE`](LICENSE)). [`NOTICE.md`](NOTICE.md) says what changed.
