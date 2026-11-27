# Skills

The team's guidance names skills by name, such as "follow the `implement` skill", and the team ships every one of
them as a team skill. Each is a copy of its source's skill at the commit in the table below, in
`agents/appwrights/vendor/<skill>`: unchanged, except that the source's hidden files are left out, and its licence is
added when the skill has none of its own. Each profile in `agents/appwrights/agent.yaml` selects the skills whose row
lists its role, so a seat gets those and no others, wherever it runs.

OpenRig provides its `openrig-core` plugin and its skills, and the team ships its own skills in
`agents/appwrights/skills`, which every seat gets: Workshop's `using-the-tui-together`, and `page-proof`, which
captures a page at a laptop and a phone width as proof.

## The skills

**Required** skills are named in a step of the guidance; a seat without one can't do that step as written.
**Optional** ones help the seats listed but no step names them. **Seats** are the roles in
`agents/appwrights/agent.yaml`; `all` is every seat. **Commit** is the one the team's copy matches, one per source.
This table is the only list: `scripts/sync-skills.py` copies the skills and writes `agent.yaml`'s skill declarations
and each profile's skills from it.

| Skill | Source | Path | Commit | Licence | Seats | Need |
| --- | --- | --- | --- | --- | --- | --- |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | all | required |
| `ponytail-review` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `skills/ponytail-review` | `7801d061243d7b753bad0e0b3c057cd250b11755` | MIT | builder, code-reviewer | required |
| `pr` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/pr` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | judge | required |
| `retro` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/retro` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | required |
| `triage` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/triage` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | required |
| `wayfinder` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/wayfinder` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | required |
| `to-spec` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/to-spec` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | required |
| `implement` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/implement` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder | required |
| `tdd` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/tdd` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder | required |
| `diagnosing-bugs` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/diagnosing-bugs` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder, qa | required |
| `code-review` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/code-review` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | code-reviewer | required |
| `differential-review` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/differential-review/skills/differential-review` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `sharp-edges` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/sharp-edges/skills/sharp-edges` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `supply-chain-risk-auditor` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `agentic-actions-auditor` | [trailofbits/skills](https://github.com/trailofbits/skills) | `plugins/agentic-actions-auditor/skills/agentic-actions-auditor` | `e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff` | CC-BY-SA-4.0 | code-reviewer | required |
| `eas-simulator` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/eas-simulator` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | qa | required |
| `eas-update` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/eas-update` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | qa | required |
| `agent-device` | [callstack/agent-device](https://github.com/callstack/agent-device) | `skills/agent-device` | `d2426fffdf7829f58458ec1631bd117e6cd8cf94` | MIT | qa | required |
| `react-native-testing` | [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | `plugins/vendored/.agents/skills/react-native-testing` | `59e9d17446a248b21d86f078fcd0bd2d36db1ca4` | MIT | qa | required |
| `react-native-best-practices` | [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | `skills/react-native-best-practices` | `59e9d17446a248b21d86f078fcd0bd2d36db1ca4` | MIT | builder, code-reviewer | required |
| `expo-overview` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-overview` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | lead, builder | optional |
| `expo-router` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-router` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | builder | optional |
| `expo-native-ui` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-native-ui` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | builder | optional |
| `expo-data-fetching` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-data-fetching` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | builder | optional |
| `expo-design-system` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-design-system` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | builder | optional |
| `expo-upgrade` | [expo/skills](https://github.com/expo/skills) | `plugins/expo/skills/expo-upgrade` | `acc0b21ce09be356b5cf0323482bdfe7db0b7a1e` | MIT | builder | optional |
| `grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/productivity/grilling` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead | optional |
| `domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/domain-modeling` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, builder | optional |
| `research` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/research` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, builder | optional |
| `writing-for-agents` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/productivity/writing-for-agents` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | lead, builder, code-reviewer | optional |
| `codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/codebase-design` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder | optional |
| `wizard` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/wizard` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder | optional |
| `prototype` | [mattpocock/skills](https://github.com/mattpocock/skills) | `skills/engineering/prototype` | `d1478fcb140db0b93c0c8df17bcfd311844749d0` | MIT | builder | optional |
| `humanizer` | [blader/humanizer](https://github.com/blader/humanizer) | `.` | `b48c832f0f809c1b5658edbb838c2521b72f2413` | MIT | lead, builder, judge | optional |
| `diagram-design` | [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | `skills/diagram-design` | `f6db0decea96de66b901331a0f79a8d4b147ebae` | MIT | lead, builder | optional |

**Path** is where the skill sits in its source; `.` means the repository is the skill. Each skill keeps its own
licence, beside it in its folder: the Trail of Bits skills are CC-BY-SA-4.0, so a changed copy you share must keep that
licence and its attribution. `agent-device` follows the CLI's own releases, so the skill matches the `agent-device`
version QA runs.

## Sources

| Source | Follows | Release |
| --- | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `v<version>` tags | v1.3.2 |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | `v<version>` tags | v5.3.3 |
| [trailofbits/skills](https://github.com/trailofbits/skills) | `main` | none |
| [expo/skills](https://github.com/expo/skills) | `main` | none |
| [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | `main` | none |
| [callstack/agent-device](https://github.com/callstack/agent-device) | `v<version>` tags | v0.21.37 |
| [blader/humanizer](https://github.com/blader/humanizer) | `v<version>` tags | v4.0.0 |
| [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | `main` | none |

## Keeping them current

To move the pins by hand, from a clone of this repository:

```sh
scripts/sync-skills.py rigs/appwrights --update        # or name sources: --update expo/skills
scripts/sync-skills.py rigs/appwrights --check
```

To add or remove a skill, change a skill's seats, or pin a source to another commit, edit the table (a source's rows
share one commit), then run `scripts/sync-skills.py rigs/appwrights`.
