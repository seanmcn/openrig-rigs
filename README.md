# openrig-rigs

Teams for [OpenRig](https://github.com/mvschwarz/openrig), each a folder under `rigs/` that installs as a bundle. The
words these docs use, such as team, rig, seat and slice, are in the [glossary](GLOSSARY.md).

| Team | What it is |
|---|---|
| [`rigs/shipwrights`](rigs/shipwrights) | An engineering team built on OpenRig's Workshop. Its twelve seats (a lead, its peer, a clerk, a planner, a backend and a frontend builder, a QA seat for each builder, a pair of reviewers, a judge and a release manager) take a goal to judged pull requests that are ready to merge, and a rig grows the roles it needs. |

Each team's README says how to install it.

## Working on a team

A team is a folder of files, and one command turns it into a running rig: `rig bundle install` starts its seats from
`rig.yaml`, `agent.yaml`, its start files and its skills.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/team-to-rig-dark.svg">
  <img alt="From a team to a running rig: a team folder's rig.yaml, agent.yaml, start files and skills go into rig bundle install, which starts the running rig with a session per seat." src="docs/diagrams/team-to-rig.svg">
</picture>

A team ships every skill its guidance names as a team skill. Its `skills.md` lists them, each with its source, the
commit the team pins and its licence, and the team carries a copy of each, unchanged, that its profiles select per
role ([why](docs/adr/0001-teams-vendor-their-skills.md)). `scripts/sync-skills.py rigs/<team>` writes the copies and
`agent.yaml`'s skill lines from the table, and a weekly workflow moves the pins to each source's newest release, which
comes out as the team's next version.

Each team has a version, in its `agent.yaml`, and a tag `<team>-v<version>` marks each team version; install a team
from its tag to pin it. The team's README says when each part of the version moves.

`scripts/check-team.py rigs/<team>` checks a team against what its README promises; the script's docstring lists every
check. Set `TEAM_BLOCKLIST` to a comma-separated list of words the team must never contain, such as names from the
setup it was first built for. `python3 -m unittest discover -s scripts/tests` tests both scripts, and the `check`
workflow runs all of this on every pull request.

`docs/diagrams/build.py` generates the diagrams, here and in each team's folder. To change one, edit its geometry
there and run the script; an SVG edited by hand is overwritten on the next run.
