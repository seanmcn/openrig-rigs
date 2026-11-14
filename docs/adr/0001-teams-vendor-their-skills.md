# Teams vendor their skills

A team ships every skill its guidance names as a team skill: a copy, unchanged from its source at a pinned commit,
declared in its `agent.yaml` and selected per profile. A weekly workflow moves the pins, and each move comes out as a
new team version. This reverses the first rule, that a team shipped no third-party skills and a script installed them
in the person's home folder. Copies installed there never updated. They sat outside the bundle's checksums, so a team
pinned to a commit still ran whatever skills the host had. And they reached every seat, and every other session the
person ran. OpenRig copies a declared skill into each seat's own storage at launch, so vendoring gives each seat
exactly its role's skills, from one install.

## Considered options

- **Install at user level** (the old rule): rejected for the reasons above.
- **A `skills/` folder beside `rig.yaml`, found by name at launch:** an overlay whose rig spec lives elsewhere stops
  finding it, and OpenRig can't restore a discovered skill from its source.
- **A local plugin holding the skills:** an overlay could swap one skill only through a Git-backed OpenRig skill
  catalog on the person's machine.

## Consequences

- An overlay swaps a skill in an `agent.yaml` of its own that imports the team's spec and selects its own skill in
  the team's place. A user-level copy of the same name no longer replaces the team's, but Claude Code and Codex still
  load it beside it.
- Each skill is declared `on_restore: follow_source`: with OpenRig's default, a seat restored after an update loses
  the changed skill until it is launched fresh.
- The weekly update merges its own pull request when the team's checks pass, the one exception to a person merging
  every pull request. It holds for a person when a skill is gone or renamed upstream or its licence changed.
- A team has a version, which a tag `<team>-v<version>` marks, since OpenRig records no version for an installed team.
- `skills.md`'s table stays the only list of a team's skills: `scripts/sync-skills.py` writes the copies and
  `agent.yaml`'s skill lines from it.
