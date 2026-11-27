# Appwrights

An engineering team for one person's React Native and Expo app, on [OpenRig](https://github.com/mvschwarz/openrig).
You give it a goal; it cuts the goal into slices, builds each one, proves it on the web and, when the slice says so, on
iOS, has it reviewed by a pair on different runtimes, and opens a pull request for you to merge.

It is [Shipwrights](../shipwrights) cut down to seven seats for a single stream of work. `NOTICE.md` lists every change.

## Seats

| Seat | Role | Runtime | Model tier | Also does |
| --- | --- | --- | --- | --- |
| `orch.lead` | lead | Claude Code | upper | the planner's job: triage, `wayfinder`, cutting slices and writing their specs |
| `orch.clerk` | clerk | Claude Code | budget | watches the lead and relaunches it if its seat stays down |
| `dev.builder` | builder | Claude Code | workhorse | every slice, end to end: API, database, policy and the app |
| `quality.qa` | qa | Codex | workhorse | web proof, and iOS proof on Expo's simulators |
| `review.reviewer-claude` | code-reviewer | Claude Code | upper | |
| `review.reviewer-codex` | code-reviewer | Codex | workhorse | |
| `review.judge` | judge | Codex | workhorse | publishing: the pull request, its description, CI and keeping it mergeable |

Up to two slices are in flight: one being built while the one before it is in QA, review or judging.

## How the work moves

1. Your goal reaches the clerk, through OpenRig's kernel operator or as a queue row, and the clerk hands it to the lead.
2. The lead reads the code, cuts the goal into missions and slices, writes each slice's spec with a proof contract and
   a **Platforms** line, and locks it.
3. The clerk hands each ready slice to the builder and QA. QA checks every commit first; once it passes, the two
   reviewers review it independently.
4. The judge compares the reviews and judges the proof against the locked spec. A routine slice it publishes; a hard
   or risky one goes to the lead first.
5. You merge. The judge closes the slice, and the clerk tells the lead when the mission is complete.

## Models

Each role has two profiles in `agents/appwrights/agent.yaml`, `<role>-claude` and `<role>-codex`, with the same
guidance. `configurations.yaml` gives each seat its role's profile for its runtime, so a seat moved to the other
runtime while its plan is out keeps its job.

| Model tier | Claude Code | Codex |
| --- | --- | --- |
| top | — | GPT-6 Astra (`gpt-6-astra`) |
| upper | Opus 5.5 (`claude-opus-5-5`) | — |
| workhorse | Sonnet 5.5 (`claude-sonnet-5-5`) | GPT-6.1 Sol (`gpt-6.1-sol`) |
| budget | Haiku 5.5 (`claude-haiku-5-5`) | GPT-6 Luna (`gpt-6-luna`) |

A rig may override any seat's model: set `model` (and `effort`) on the member in your copy of `rig.yaml`.

## Permissions

Every seat launches with permission prompts off (`permission_policy: builtin:yolo`): Claude Code bypasses permissions
and Codex runs unsandboxed. Run it on a machine that holds only what the team should reach.

## Skills

`skills.md` lists every skill the team ships, its source, its pinned commit and the roles that use it, including the
Expo and Callstack skills for the builder, QA and the reviewers. `scripts/sync-skills.py rigs/appwrights` vendors them.

## Versions

The team starts at 0.1.0, in `agents/appwrights/agent.yaml`, and a tag `appwrights-v<version>` marks each release.
