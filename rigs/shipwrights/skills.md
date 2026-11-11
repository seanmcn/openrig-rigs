# Skills

The team's guidance names skills by name, such as "follow the `implement` skill". Shipwrights doesn't ship them:
install them at user level, where every seat finds them, or supply your own versions under the same names. Claude
Code seats read skills from `~/.claude/skills`, and Codex seats from `~/.codex/skills`.

The rest come with the team: OpenRig provides its `openrig-core` plugin and its skills, and the team ships
Workshop's `using-the-tui-together`.

## Install them

From a clone of this repository, preview what would change, then install:

```sh
rigs/shipwrights/install-skills.sh --dry-run
rigs/shipwrights/install-skills.sh
```

It installs each skill in the table below into `~/.claude/skills/<skill>` and `~/.codex/skills/<skill>`, from its
source at the suggested commit, with the source's licence beside it when the skill has none of its own. It needs only
`curl` and `tar`. It never replaces a skill you already have under that name, so you can run it again at any
time, and a skill of your own under one of these names stays yours: the seats use it in place of this one. `--force`
replaces them with the versions below. Name skills to install only those, such as
`install-skills.sh impeccable tdd`. `CLAUDE_CONFIG_DIR` and `CODEX_HOME` move the two folders, as they do for Claude
Code and Codex.

## The skills

**Required** skills are named in a step of the guidance, `CULTURE.md` included, since every seat reads it; a seat
without one can't do that step as written. **Optional** ones help the seats listed but no step names them. **Seats** are
the roles in `agents/shipwrights/agent.yaml`, each meaning both of the role's profiles; `all` is every seat. The commit is the one this team was last checked
with; a newer one usually works. This table is the only list: the install script and `scripts/check-team.py` both read
it.

| Skill | Source | Path | Commit | Licence | Seats | Need |
| --- | --- | --- | --- | --- | --- | --- |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | all | required |
| `ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail-review` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | builder-backend, builder-frontend, code-reviewer | required |
| `pr` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/pr` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, release-manager | required |
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

The suggested commits are these releases where the source tags them: `mattpocock/skills` v1.3.2, `ponytail` v5.3.3,
`humanizer` v3.1.0 and `impeccable` skill-v4.8.0. `diagram-design` and Trail of Bits' skills have no tags.

**Path** is where the skill sits in its source; `.` means the repository is the skill. Each skill keeps its own
licence: the Trail of Bits skills are CC-BY-SA-4.0, so a changed copy you share must keep that licence and its
attribution.

`impeccable` includes a live mode that drives a browser and can start a CLI agent of its own. The frontend builder's
guidance never uses it, whichever version you install.

## Using your own

To use your own version of a skill, put it at `~/.claude/skills/<skill>` and `~/.codex/skills/<skill>` under the name
in the table, before or after running the script; the script leaves it alone. A required skill of your own should do
what the guidance asks of it: the step that names it says what that is.
