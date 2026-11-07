# Team settings

These settings shape how the team works. Every seat reads this file at start and at
refocus, so a change reaches a seat at its next start or refocus. To change one, edit its
default here, or ship your own copy of this file in its place.

| Setting | Default | Read by |
| --- | --- | --- |
| Disagreement rounds before the person is asked | 2 | lead |
| Confirm each triage result with the person | off | planner |
| Slice time limit | 4 working hours | lead |

- **Disagreement rounds before the person is asked.** How many fix rounds a disagreement
  between the builder and a reviewer or QA may go before the lead takes it to the person,
  with both sides' evidence.
- **Confirm each triage result with the person.** When on, the planner asks the person to
  confirm each triage result before it becomes a slice. When off, the result becomes a
  slice straight away.
- **Slice time limit.** How long a slice's build may run before the lead looks at it. The
  lead creates each build row with the queue tier whose deadline is closest to this limit
  without going over it (OpenRig's `routine` tier is 4 hours, `deep` is 24), and checks
  `rig queue overdue` each time its reminder wakes it. Queue deadlines count clock hours,
  so the lead counts working hours itself before it acts on an overdue row.
