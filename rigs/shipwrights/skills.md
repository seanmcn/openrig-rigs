# Skills

The team's guidance names skills by name, such as "follow the `implement` skill", and the team ships every one of
them. Each is a copy of its source's skill, unchanged, at the commit in the table below, in
`agents/shipwrights/vendor/<skill>`. Each profile in `agents/shipwrights/agent.yaml` selects the skills its role's
row lists, so a seat gets those and no others, wherever it runs.

The rest come with the team too: OpenRig provides its `openrig-core` plugin and its skills, and the team ships
Workshop's `using-the-tui-together` in `agents/shipwrights/skills`.

## The skills

**Required** skills are named in a step of the guidance, `CULTURE.md` included, since every seat reads it; a seat
without one can't do that step as written. **Optional** ones help the seats listed but no step names them. **Seats** are
the roles in `agents/shipwrights/agent.yaml`, each meaning both of the role's profiles; `all` is every seat. A required
skill's seats are the roles whose guidance or start files name it. **Commit** is the one the team's copy matches. This
table is the only list: `scripts/sync-skills.py` copies the skills from it, and `scripts/check-team.py` checks the
copies and the profiles against it.

| Skill | Source | Path | Commit | Licence | Seats | Need |
| --- | --- | --- | --- | --- | --- | --- |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | all | required |
| `ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail-review` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | builder-backend, builder-frontend, code-reviewer | required |
| `pr` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/pr` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | release-manager | required |
| `retro` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/retro` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | required |
| `triage` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/triage` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | planner | required |
| `wayfinder` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/wayfinder` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | planner | required |
| `implement` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/implement` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-backend, builder-frontend | required |
| `tdd` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/tdd` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-backend, builder-frontend | required |
| `diagnosing-bugs` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/diagnosing-bugs` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-backend, builder-frontend, qa | required |
| `code-review` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/code-review` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | code-reviewer | required |
| `differential-review` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/differential-review/skills/differential-review` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `sharp-edges` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/sharp-edges/skills/sharp-edges` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `supply-chain-risk-auditor` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `agentic-actions-auditor` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/agentic-actions-auditor/skills/agentic-actions-auditor` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `impeccable` | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | `.agents/skills/impeccable` | `414603bf14c7a344edb466bb1f85690c77ce8b7d` | Apache-2.0 | builder-frontend | required |
| `grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/productivity/grilling` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, planner | optional |
| `domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/domain-modeling` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, planner, builder-backend, builder-frontend | optional |
| `research` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/research` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, planner, builder-backend, builder-frontend | optional |
| `writing-for-agents` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/productivity/writing-for-agents` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, builder-backend, builder-frontend, code-reviewer | optional |
| `to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/to-spec` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | planner | optional |
| `codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/codebase-design` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-backend, builder-frontend | optional |
| `wizard` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/wizard` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-backend, builder-frontend | optional |
| `prototype` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/prototype` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder-frontend | optional |
| `humanizer` | [blader/humanizer](https://github.com/blader/humanizer) | `.` | `225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8` | MIT | lead, builder-backend, builder-frontend | optional |
| `diagram-design` | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | `skills/diagram-design` | `e57eda6102a19444538ebd611d39534fad65b663` | MIT | lead, builder-backend, builder-frontend | optional |

**Path** is where the skill sits in its source; `.` means the repository is the skill. Each skill keeps its own
licence, beside it in its folder: the Trail of Bits skills are CC-BY-SA-4.0, so a changed copy you share must keep that
licence and its attribution.

`impeccable` includes a live mode that drives a browser and can start a CLI agent of its own. The frontend builder's
guidance never uses it.

## Sources

Each source's pin follows either its releases or a branch. Under **Follows**, a tag pattern such as `v<version>` tags
means the newest release among the tags it matches, and a branch such as `main` means that branch's head. **Release**
is the tag at the pin, or `none` for a branch.

| Source | Follows | Release |
| --- | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `v<version>` tags | v1.3.2 |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `v<version>` tags | v5.3.3 |
| [trailofbits/skills](https://github.com/trailofbits/skills) | `main` | none |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | `skill-v<version>` tags | skill-v4.8.0 |
| [blader/humanizer](https://github.com/blader/humanizer) | `v<version>` tags | v3.1.0 |
| [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | `main` | none |

## Keeping them current

Every week, a workflow in this repository moves each source to what it follows, and copies its skills again where any
of them changed. It releases the change as the team's next patch version, with notes naming each source's old and new
pin. It opens one pull request for the update and merges it itself when the team's checks pass. It leaves the pull
request open for a person instead when a check fails, when a skill is gone from its source or renamed there, or when a
skill's licence changed, and a later week's run replaces that pull request rather than opening another.

To do the same by hand, from a clone of this repository:

```sh
scripts/sync-skills.py rigs/shipwrights --update        # or name sources: --update mattpocock/skills
scripts/check-team.py rigs/shipwrights
```

To pin a skill to another commit, change its Commit cell, then run `scripts/sync-skills.py rigs/shipwrights` to copy it
again. `--check` says whether every copy matches its pin, and changes nothing.

## Using your own

A skill the team declares wins over one installed at user level, so a copy in `~/.claude/skills` or `~/.codex/skills`
doesn't replace the team's. The seat still sees both, though, since Claude Code and Codex load user-level skills
themselves. To use your own version of a skill, use an overlay, as the README's Overlays section says: an `agent.yaml`
of your own that imports this team's agent spec, declares your skill, and points the profiles at it in place of this
one. A required skill of your own should do what the guidance asks of it: the step that names it says what that is.
