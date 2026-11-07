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
  <img alt="Shipwrights' seats in five pods, with the lead (Codex) as the hub and its peer (Claude Code) standing in while it is down. Your goal goes to the lead, which hands it to the planner; the planner sends slices back; the lead hands each locked slice, and any fix, to one of two backend builders or the frontend builder, with one of three QA seats, and the builders and QA report results back. Once QA passes a commit, the lead names a review pair, one of two Claude Code reviewers and one of two Codex reviewers, whose findings go straight to the builders and verdicts to the lead. The lead hands judged slices to the release manager (Codex), which reports CI failures and each delivery." src="diagrams/seats.svg">
</picture>

| Seat | Runtime | Does |
|---|---|---|
| `orch-lead` | Codex | Starts from your goal, has it cut into slices, locks their specs, hands them on, judges their proof and owns each PR description. Talk to this seat. |
| `orch-peer` | Claude Code | Runs the lead's guidance on the other runtime and follows its work. Takes over, and tells you, only when the lead's seat has been down for 10 minutes; hands back with a recap. |
| `plan-planner` | Claude Code | Turns goals and issues into missions and slices, with triage, specs, dependencies and a build order. |
| `dev-backend`, `dev-backend2` | Claude Code | Each builds a backend slice in its own worktree, reviews its own diff and runs the repository's checks. |
| `dev-frontend` | Claude Code | Builds on the backend builder's guidance for slices tagged UI or both: checks them in a real browser and runs impeccable's reviews and detector. |
| `dev-qa`, `dev-qa2`, `dev-qa3` | Claude Code | One per builder: each runs the checks a slice calls for and records what each one proved. |
| `review-r1`, `review-r3` | Claude Code | Each reviews the handed-off commit with the named review skills, and runs the tests that bear on it. |
| `review-r2`, `review-r4` | Codex | The same, on the other runtime: the lead pairs one reviewer from each runtime for each slice, and they review independently. |
| `release-manager` | Codex | Publishes each judged slice's pull requests with their merge gate, watches CI, pushes rebased commits with lease and approves each merged slice for delivery. |

These are the runtimes of the `recommended` preset; [`configurations.yaml`](configurations.yaml) lets each seat use the
other one. Keep the lead and its peer on different runtimes, and the code reviewers on at least two.

### Growing the team

[`startup/team-shape.md`](startup/team-shape.md) is the one place that says which roles can have more seats and what a
new seat needs. Builders, QA seats and code reviewers grow with the work you run at once, a QA seat for each builder.
A second planner or release manager is rarely needed. Every seat reads that file at start, and finds the others by
role, so a seat you add is used without changing any guidance.

## How the work moves

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/how-the-work-moves-dark.svg">
  <img alt="How the work moves: your goal goes to the lead and planner, who cut and lock it; a builder builds a commit and QA checks it, back and forth until QA passes; both reviewers then review that commit, and any findings go back to the builder and through QA again; the lead judges the proof; the release manager opens the pull requests, and a failing CI run or a rebase goes back to the builder; you merge; the release manager approves delivery and tells the lead." src="diagrams/how-the-work-moves.svg">
</picture>

1. The planner records your goal or issues as a mission in OpenRig's work tree (`rig scope`), with its slices and the
   dependencies between them. Each slice's `SPEC.md` lists the repositories it touches in merge order and ends with a
   proof contract ([`slice-spec.md`](startup/slice-spec.md)). The lead locks each spec.
2. The lead hands each slice to a free builder as a queue row, with a free QA seat: slices tagged UI or both to a
   frontend builder, backend slices to a backend builder ([`team-shape.md`](startup/team-shape.md), "Which seats a
   slice holds").
3. The builder hands each commit to the slice's QA seat, and they go back and forth until QA passes one. Then the lead
   pairs two free reviewers on different runtimes, and both review that commit. A fix for their findings goes through QA
   again before they look again. QA and the reviewers each record their proof at the commit they checked.
4. The lead compares the reviews and judges the proof at that commit, again after any rebase or fix, then hands the
   slice to the release manager.
5. The release manager publishes only proof judged at the commit it pushes, one pull request per repository, each
   opened with a merge gate. It watches CI, and tells the lead when CI fails or a branch conflicts with its base; the
   lead gives the fix or the rebase to a builder, and the new commit goes through QA and is judged again. A slice you
   gave the team is your word to open its pull requests. Merging, tagging and releasing still need yours, unless the
   repository's `AGENTS.md` allows an agent to merge in its `### Merging` section and the merge gate is all green
   ([`release-manager.md`](agents/shipwrights/guidance/release-manager.md)). After you merge, it approves the slice for
   delivery.
6. When something on a slice cost a seat time, it adds a short retrospective note to the slice's progress, naming its
   seat, runtime and model. Every ten delivered slices, the lead offers you, as proposed changes to the guidance, only
   the problems that came up more than once.

Builders, QA seats, code reviewers and planners start fresh for each slice: the lead relaunches each one once its
part is done, so what lasts is the record (the spec, the slice progress and the proof), not a seat's memory. The lead,
its peer and the release manager are long-lived, and hand over to a fresh session near a full context
([`team-shape.md`](startup/team-shape.md)).

Waits are queue rows blocked with a wake, never polling. An OpenRig watchdog wakes the lead on a timer to check for
builds past the slice time limit, and another wakes the peer to check that the lead's seat is up.

To drop a slice, tell the lead to stop it: its queue rows and the slice are closed. To hold a slice or a mission, tell
the lead to pause it: its rows are blocked until you resume it. Neither stops a seat's session.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="diagrams/slice-lifecycle-dark.svg">
  <img alt="A slice's lifecycle: spec locked, building with QA until QA passes, in review, judged and published, with reviewers' findings, a failing CI run and a rebase looping back to building; from any phase it can be paused and resumed, or stopped; once you merge, it is delivered." src="diagrams/slice-lifecycle.svg">
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

OpenRig writes its own files (`CLAUDE.local.md`, a block in `AGENTS.md`, `/.openrig/` and others) into the folder the
seats work in. The seats commit only in each slice's worktree, which never sees them, so they can't reach a commit. To
keep them out of `git status` in each clone as well, run from its root:

```sh
printf '%s\n' CLAUDE.local.md AGENTS.md /.openrig/ .claude/settings.local.json /.worktrees/ >> .git/info/exclude
```

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
starts from that row; with no goal, it waits. Ask it to find work, and it offers you three options from your
repositories' roadmaps, issues and CI; ask it to keep finding work, and it offers three more each time a piece you
picked is delivered, until you say stop.

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
`codex_config_profile: <its name>` on each seat that runs on Codex in `rig.yaml`: `orch.lead`, `review.r2`,
`review.r4` and `release.manager` in the recommended preset (OpenRig's `docs/reference/getting-started.md`, "Codex:
select sandbox and approvals together").

## Limits

- **Fourteen seats run at once,** so expect up to fourteen seats' worth of provider usage. The peer, the planner and any
  seat without a slice are idle much of the time. To run fewer, remove seats in an overlay
  ([`team-shape.md`](startup/team-shape.md) says which roles can shrink): one builder and one QA seat still work, but
  a review needs two code reviewers on different runtimes.
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
