# Notice

Shipwrights is built on Workshop with a review pair (`rigs/workshop-review-pair`) from
[mvschwarz/openrig-world](https://github.com/mvschwarz/openrig-world) at commit
`d544888b4c9973164e7986d7e0344a7ceca89a8c`, Copyright the OpenRig authors, licensed under the Apache License 2.0. The
licence is in `LICENSE`. These files are modified versions of Workshop's:

| File here | Workshop's file | What changed |
|---|---|---|
| `rig.yaml` | `rig.yaml` | Named `shipwrights`; the builder becomes `dev.backend` with the `builder-backend` profile; adds a peer beside the lead, a `plan` pod, a frontend builder and a `release` pod; the team settings are a startup file for every seat. |
| `bundle.yaml` | `bundle.yaml` | Minimum OpenRig 0.7.1; preconditions for a folder of several clones. |
| `configurations.yaml` | `configurations.yaml` | No Pi runtimes; runtimes for the new seats. |
| `CULTURE.md` | `CULTURE.md` | Adds each repository's own rules first, retrospective notes, skills a person types, publishing a judged slice through the release manager, merging only as the repository's `AGENTS.md` allows, and reporting a leaked credential. |
| `startup/context.md` | `startup/context.md` | Works in a folder of several clones; reads each repository's `AGENTS.md` first; loads every registered context pack; reads the team settings. |
| `startup/lead-first-move.md` | `startup/lead-first-move.md` | A mission is cut into slices, one pull request per repository each, with dependencies, by the planner when it needs more than one; points stop and pause to the role file. |
| `startup/review-pair-*.md` | `startup/review-pair-*.md` | Reviewers keep apart from each other's proof as well as findings; the builder hands a commit to them once QA passes it. |
| `agents/shipwrights/agent.yaml` | `agents/workshop/agent.yaml` | Profiles select only OpenRig's plugin and `using-the-tui-together`; the builder profile renamed `builder-backend`; peer, planner, builder-frontend and release-manager profiles; no Pi profiles or generated skill snapshots. |
| `agents/shipwrights/skills/using-the-tui-together/SKILL.md` | `agents/workshop/bundle-skills/using-the-tui-together/SKILL.md` | Its examples name this team's seats and rig. |
| `agents/shipwrights/guidance/lead.md` | `agents/workshop/guidance/lead.md` | Briefs name what to reuse and the patterns to follow, and end in a proof contract; slices go to builders as queue rows with a tier; the lead judges recorded proof; waits, the slice time limit, stop and pause; the planner cuts the work and the lead locks its specs; judged slices go to the release manager; retrospectives. |
| `agents/shipwrights/guidance/builder-backend.md` | `agents/workshop/guidance/builder.md` | Renamed for the backend builder, whose guidance the frontend builder builds on; reads the repository's `AGENTS.md` first in every slice and runs commands from inside the worktree; `implement` and `tdd`; self-review with `ponytail-review`; QA passes each commit before review; rebasing; the release manager pushes; a retrospective note. |
| `agents/shipwrights/guidance/qa.md` | `agents/workshop/guidance/qa.md` | The same first steps; generic test layers in place of OpenRig's own; records its result with `rig proof add`; a retrospective note. |
| `agents/shipwrights/guidance/code-reviewer.md` | `agents/workshop/guidance/code-reviewer.md` | The same first steps; the named review skills; records its verdict with `rig proof add`; a retrospective note. |
| `agents/shipwrights/guidance/peer.md`, `planner.md`, `builder-frontend.md`, `release-manager.md` | none | New: this team's own seats. |
| `agents/shipwrights/runtime/claude-activity-hooks.json` | `agents/workshop/runtime/claude-activity-hooks.json` | Unchanged. |
| `README.md` | `README.md` | Rewritten for this team. |

`skills.md`, `install-skills.sh` and `settings.md` are this team's own. The team ships no third-party skills:
`skills.md` names the ones its guidance uses, with each one's source and licence, and `install-skills.sh` fetches
them from their sources onto the person's machine.
