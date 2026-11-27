# Notice

Appwrights is derived from this repository's Shipwrights team (`rigs/shipwrights`, version 2.8.0), which is built on
Workshop with a review pair (`rigs/workshop-review-pair`) from
[mvschwarz/openrig-world](https://github.com/mvschwarz/openrig-world) at commit
`d544888b4c9973164e7986d7e0344a7ceca89a8c`, Copyright the OpenRig authors, licensed under the Apache License 2.0. The
licence is in `LICENSE`. Shipwrights' `NOTICE.md` lists what it changed from Workshop; these files change Shipwrights':

| File here | Shipwrights' file | What changed |
|---|---|---|
| `rig.yaml` | `rig.yaml` | Named `appwrights`; seven seats that don't grow: `orch.lead` and `orch.clerk`, `dev.builder`, `quality.qa`, and `review.reviewer-claude`, `review.reviewer-codex` and `review.judge`. No peer, planner, frontend builder, second QA seat or release manager. The clerk observes the lead. |
| `configurations.yaml` | `configurations.yaml` | The seven seats; the recommended preset puts the lead, clerk, builder and `reviewer-claude` on Claude Code, and QA, `reviewer-codex` and the judge on Codex. |
| `settings.md` | `settings.md` | Adds "Slices in flight" (2); one-runtime review pairs are on; the lead marks risky slices, and native dependencies, app build configuration and skipped iOS proof are risky too. |
| `CULTURE.md` | `CULTURE.md` | The judge, not a release manager, opens a judged slice's pull request. |
| `startup/context.md` | `startup/context.md` | The clerk hands the person's goal to the lead, which cuts it. |
| `startup/team-shape.md` | `startup/team-shape.md` | Seven fixed seats; slices in flight; the earlier slice comes first; the fixed review pair; what a pair does while a runtime's plan is out; the judge publishes. |
| `startup/lead-first-move.md` | `startup/lead-first-move.md` | The lead sorts and cuts each goal itself. |
| `startup/slice-spec.md` | `startup/slice-spec.md` | No slice kind; the proof contract opens with a **Platforms** line (`web`, or `web + iOS` with a reason) and names its seed. |
| `startup/review-pair-*.md` | `startup/review-pair-*.md` | The pair is `reviewer-claude` and `reviewer-codex`; the judge reports both reviews in the pull request. |
| `agents/appwrights/agent.yaml` | `agents/shipwrights/agent.yaml` | Roles `lead`, `clerk`, `builder`, `qa`, `code-reviewer` and `judge`, one profile per runtime each; version 0.1.0. |
| `agents/appwrights/guidance/lead.md` | `lead.md` and `planner.md` | The lead does the planner's job: triage, `wayfinder`, cutting slices and writing specs with `to-spec`, reading through a subagent. |
| `agents/appwrights/guidance/clerk.md` | `clerk.md` and `peer.md` | The clerk hands goals to the lead, keeps to the slices in flight, names the fixed review pair, and watches the lead, relaunching it after 10 minutes down and telling the person if it is still down 10 minutes later. |
| `agents/appwrights/guidance/builder.md` | `builder-backend.md` and `builder-frontend.md` | One full-stack builder; the Expo and React Native skills; the web export at phone width for UI changes; says when a change needs a new app build. No impeccable. |
| `agents/appwrights/guidance/qa.md` | `qa.md` | Web first, and iOS on Expo's simulators when the spec's Platforms line asks for it. |
| `agents/appwrights/guidance/judge.md` | `judge.md` and `release-manager.md` | The judge publishes each slice it judges ready and carries its pull request to delivery. |
| `agents/appwrights/guidance/code-reviewer.md` | `code-reviewer.md` | Unchanged. |
| `README.md` | `README.md` | Rewritten for this team. |

`skills.md` is this team's own. `agents/appwrights/vendor/` holds copies of other people's skills, each unchanged from
the source and commit its row in `skills.md` names. Each keeps its own licence, which sits beside it in its folder, and
none of this team's Apache-2.0 licence applies to them. The Trail of Bits skills are CC-BY-SA-4.0: their copies, and any
changed copy you share, keep that licence and its attribution.
