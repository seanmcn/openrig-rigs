# Notice

Shipwrights is built on Workshop with a review pair (`rigs/workshop-review-pair`) from
[mvschwarz/openrig-world](https://github.com/mvschwarz/openrig-world) at commit
`d544888b4c9973164e7986d7e0344a7ceca89a8c`, Copyright the OpenRig authors, licensed under the Apache License 2.0. The
licence is in `LICENSE`. These files are modified versions of Workshop's:

| File here | Workshop's file | What changed |
|---|---|---|
| `rig.yaml` | `rig.yaml` | Named `shipwrights`; the builder becomes `dev.backend` with the `builder-backend` profile; adds a peer beside the lead, a `plan` pod, a second backend builder, a frontend builder, a QA seat for each builder, a second review pair and a `release` pod; the lead is every seat's orchestrator, its only `delegates_to` source, so stuck rows escalate to it; the team settings and the team's shape are startup files for every seat. |
| `bundle.yaml` | `bundle.yaml` | Minimum OpenRig 0.7.1; preconditions for a folder of several clones. |
| `configurations.yaml` | `configurations.yaml` | No Pi runtimes; runtimes for the new seats, with the code reviewers half on each runtime. |
| `CULTURE.md` | `CULTURE.md` | QA passes a commit before review starts; adds each repository's own rules first, retrospective notes, skills a person types, publishing a judged slice through the release manager, merging only as the repository's `AGENTS.md` allows, and reporting a leaked credential. |
| `startup/context.md` | `startup/context.md` | Works in a folder of several clones; reads each repository's `AGENTS.md` first; loads every registered context pack; reads the team settings; with no goal, the lead waits. |
| `startup/lead-first-move.md` | `startup/lead-first-move.md` | The planner cuts every goal into slices, one pull request per repository each, with dependencies; points stop and pause to the role file. |
| `startup/review-pair-*.md` | `startup/review-pair-*.md` | The lead pairs two reviewers on different runtimes for each slice, in place of a fixed pair; reviewers keep apart from each other's proof as well as findings; the builder hands a commit to them once QA passes it. |
| `agents/shipwrights/agent.yaml` | `agents/workshop/agent.yaml` | Profiles select only OpenRig's plugin and `using-the-tui-together`; the builder profile renamed `builder-backend`; peer, planner, builder-frontend and release-manager profiles; no Pi profiles or generated skill snapshots. |
| `agents/shipwrights/skills/using-the-tui-together/SKILL.md` | `agents/workshop/bundle-skills/using-the-tui-together/SKILL.md` | Its examples name this team's seats and rig; no notes for OpenRig versions older than this team needs. |
| `agents/shipwrights/guidance/lead.md` | `agents/workshop/guidance/lead.md` | The planner scopes every slice, and the lead reviews and locks its spec; the lead assigns each slice a free builder and QA seat, then a review pair, and relaunches each worker fresh when its part is done; slices go to builders as queue rows with a tier; the lead judges recorded proof; waits, the slice time limit, stop and pause; judged slices go to a release manager, and CI failures and conflicts come back through the lead to a builder; the lead marks each mission active and closes it once its last slice is delivered; it finds work only when asked, offering three options; the roster describes each seat by its role; retrospectives. |
| `agents/shipwrights/guidance/builder-backend.md` | `agents/workshop/guidance/builder.md` | Renamed for the backend builder, whose guidance the frontend builder builds on; reads the repository's `AGENTS.md` first in every slice and runs commands from inside the worktree; `implement` and `tdd`; self-review with `ponytail-review`; QA passes each commit before review, and what each of its verdicts asks; rebasing, after the pull request is open only when the lead asks; the release manager pushes; a retrospective note. |
| `agents/shipwrights/guidance/qa.md` | `agents/workshop/guidance/qa.md` | Checks each commit before the reviewers see it; the same first steps; generic test layers in place of OpenRig's own; records its result with `rig proof add`, choosing the verdict by what the builder should do next; checks several pull requests together when the lead asks; a retrospective note when something cost time. |
| `agents/shipwrights/guidance/code-reviewer.md` | `agents/workshop/guidance/code-reviewer.md` | The lead names it for a slice as one of a review pair; the same first steps; three review skills on every change and the others only when the change calls for them; records its verdict with `rig proof add`, as `rev1-` and its member id; a retrospective note. |
| `agents/shipwrights/guidance/peer.md`, `planner.md`, `builder-frontend.md`, `release-manager.md` | none | New: this team's own seats. |
| `agents/shipwrights/runtime/claude-activity-hooks.json` | `agents/workshop/runtime/claude-activity-hooks.json` | Unchanged. |
| `README.md` | `README.md` | Rewritten for this team. |

`skills.md`, `install-skills.sh`, `settings.md`, `startup/slice-spec.md` and `startup/team-shape.md` are this team's
own. The team ships no third-party skills: `skills.md` names the ones its guidance uses, with each one's source and
licence, and `install-skills.sh` fetches them from their sources onto the person's machine.
