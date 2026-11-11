# This team's shape

Every seat reads this. It names the team's roles, which of them can have more than one seat, and how to find a role's
seats. Seats are found by role, never by a name you remember: the team may have grown since this file was written.

| Role | Profiles | Pod | Seats in the default team | Can grow |
| --- | --- | --- | --- | --- |
| Lead | `lead-claude`, `lead-codex` | `orch` | `lead` | No |
| Peer | `peer-claude`, `peer-codex` | `orch` | `peer`, on either runtime | No |
| Clerk | `clerk-claude`, `clerk-codex` | `orch` | `clerk-1` | Yes, rarely needed |
| Planner | `planner-claude`, `planner-codex` | `orch` | `planner-1` | Yes, rarely needed |
| Backend builder | `builder-backend-claude`, `builder-backend-codex` | `dev` | `backend-1` | Yes |
| Frontend builder | `builder-frontend-claude`, `builder-frontend-codex` | `dev` | `frontend-1` | Yes |
| QA | `qa-claude`, `qa-codex` | `quality` | `qa-1`, `qa-2`, one for each builder | Yes, with the builders |
| Code reviewer | `code-reviewer-claude`, `code-reviewer-codex` | `review` | `reviewer-1`, `reviewer-2`, one on each runtime | Yes, keeping both runtimes |
| Release manager | `release-manager-claude`, `release-manager-codex` | `release` | `manager-1` | Yes, rarely needed |

Each role has one profile per runtime: the `-claude` one for a seat on Claude Code, the `-codex` one for a seat on
Codex. Both carry the same guidance; they differ only in the model and effort they suggest. The default team has
enough seats for two slices at once. A rig grows the roles its work needs.

## Find a role's seats

```sh
rig ps --nodes --rig <rig> --json --fields canonicalSessionName,profile,runtime
```

lists every seat with its profile and runtime. A role's seats are the ones with either of its profiles; use the
addresses it gives (`canonicalSessionName`).

## Add a seat

Only a role marked "Yes" above grows. A grown seat takes the next number in its role's pod, such as `backend-2` in
`dev` after `backend-1`, the same profile and start files as the role's other seats on its runtime, and the role's
edges:

- a `delegates_to` edge from `orch.lead`, so its stuck rows escalate to the lead;
- a line for it in `configurations.yaml`, mapping each runtime to the role's profile there, as the role's other seats
  do;
- for a builder, the `startup/review-pair-builder.md` start file, and for a code reviewer,
  `startup/review-pair-reviewer.md`.

Add a QA seat with each builder, so every builder can build at once. Keep code reviewers on at least two runtimes, so
every review pair can have one of each.

To grow a team you haven't launched, add the member to its pod in `rig.yaml`. To grow a running rig, use OpenRig's
`rig add`, which adds a member to an existing pod, or `rig expand`, which adds a new pod; both take the full member
definition, as `rig.yaml` writes it. Don't use `rig grow`: `rig grow` adds only OpenRig's default agent, so the new
seat would lose its role's profile, model and runtime choices. Put the same member in your copy of `rig.yaml` too, so the
seat comes back the next time the rig starts.

## Which seats a slice holds

The clerk is the only role that assigns seats, by the rules below, so two slices never take the same seat. The lead
decides what is built and when; the clerk decides which free seat does it. Anything these rules don't settle goes to
the lead.

- **Free:** a seat is free when it holds no open row on another slice
  (`rig queue list --destination <seat> --state pending,in-progress,blocked`).
- **Builder and QA:** once the lead has locked a slice's spec and the slice is ready, the clerk names one free builder
  of the slice's kind and one free QA seat, and sends each a row for the slice. Both hold the slice until the lead has
  judged it, QA parking its row between commits.
- **Review pair:** when QA first records PASS on the slice, the builder asks the clerk, which names two free code
  reviewers on different runtimes and sends each a row for the slice. They hold it, parked between commits, through
  every fix round, until both have recorded PASS at the same commit and the lead has compared their reviews.
  When the team setting "One-runtime review pairs while a runtime is out" is on and one runtime's accounts have run
  out, the clerk may pair two reviewers on the other runtime instead: two different models, one a tier above the
  builder's. New pairs go back to one of each once the other runtime has room, and the slice progress records each
  pair's models and why it shared a runtime.
- **After publishing:** a failing CI run or a conflict goes to the lead, which decides the fix or when to rebase and
  sends it to the clerk. The clerk gives it to a free builder of the slice's kind and a free QA seat, the same ones
  when they are free, and to a free review pair again when the slice's own diff changes.
- **Planner:** the lead sends the clerk each goal, slice to re-cut, survey for work and question that needs reading
  code, and the clerk hands it to a free planner.
- **Release manager:** the lead gives each judged slice to the release manager that already holds its mission's other
  slices, or else to the one with the fewest open rows, so one release manager sees each mission's merge order.

A seat closes its row on a slice when the clerk tells it the lead has released it.

## Fresh seats and long-lived seats

**Builders, QA seats, code reviewers and planners start fresh for each piece of work.** Once such a seat has closed its
rows on a slice (a planner: its row on the work it took) and holds no other claimed row, the clerk relaunches it:

```sh
rig seat launch <seat> --fresh --stop --reason "<slice> done"
```

It keeps its address and gets its start steps again, but remembers nothing of the slice. So before you close your row,
put whatever the next seat would need into the record: the slice progress, the spec or the proof. A seat never
relaunches itself.

**The lead, its peer, the clerk and the release manager are long-lived:** they hold work across slices. Each registers
one reminder on its own session when it starts, unless `rig watchdog list` already shows it:

```sh
rig watchdog register --policy context-usage-threshold --target-session <your session> --registered-by <your session> \
  --interval-seconds 600 --threshold-percent 85 \
  --message "Context at 85%: hand this seat over (retiring-and-inheriting-a-seat)."
```

When it fires, hand the seat to a fresh successor as OpenRig's `retiring-and-inheriting-a-seat` skill says, rather
than waiting for compaction. The reminder covers one session, so the successor registers its own.

## Earlier sessions

When the record falls short, a seat's earlier sessions can still answer. `rig ask <rig> "<question>" --seat <seat>`
searches every session the seat has had, and `rig ask <rig> "<question>" --wake <member>@<rig>@<n>` asks one past
session directly (1 is the newest) and lets it rest again. Put what you learn into the record, so nobody asks twice.
