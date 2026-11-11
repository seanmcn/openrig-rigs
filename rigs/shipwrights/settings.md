# Team settings

These settings shape how the team works. Every seat reads this file at start and at
refocus, so a change reaches a seat at its next start or refocus. To change one, edit its
default here, or ship your own copy of this file in its place.

| Setting | Default | Read by |
| --- | --- | --- |
| Disagreement rounds before the person is asked | 2 | judge, lead |
| Confirm each triage result with the person | off | planner |
| Slice time limit | 4 working hours | clerk, lead |
| One-runtime review pairs while a runtime is out | off | clerk |
| Risky slices | `risky: true` in the spec | planner, lead, judge |

- **Disagreement rounds before the person is asked.** How many fix rounds a disagreement
  between the builder and a reviewer or QA may go before the lead takes it to the person,
  with both sides' evidence. The judge settles the first round, and passes a disagreement
  still not settled after it to the lead.
- **Confirm each triage result with the person.** When on, the planner asks the person to
  confirm each triage result before it becomes a slice. When off, the result becomes a
  slice straight away.
- **Slice time limit.** How long a slice's build may run before the lead looks at it. The
  clerk creates each build row with the queue tier whose deadline is closest to this limit
  without going over it (OpenRig's `routine` tier is 4 hours, `deep` is 24), and checks
  `rig queue overdue` each time its reminder wakes it. Queue deadlines count clock hours,
  so the clerk counts working hours itself, and passes the lead only a build past the limit.
- **One-runtime review pairs while a runtime is out.** When on, the clerk may pair two code
  reviewers on one runtime while every reviewer on the other runtime has reached its usage
  limit, so slices keep moving when one runtime's accounts have run out. The two must run
  different models, at least one of them a model tier above the builder's, and the pull request
  says so. The clerk checks at every new pairing, so pairs go back to one of each by
  themselves once the other runtime has room. When off, a slice with no pair on
  different runtimes waits, as "No free pair" in "This team's shape" says. With the
  suggested models, two reviewers on one runtime share a model, so to use this, give one
  of them another model in your copy of `rig.yaml`.
- **Risky slices.** How a slice is marked risky, so the judge passes it to the lead
  whatever its proof shows. By default the planner adds `risky: true` to the frontmatter
  of a slice's `SPEC.md` when the slice changes authentication, permissions, secrets,
  payments, personal data, a data migration or deletion, or a deploy or CI workflow, and
  the lead checks it when it locks the spec. To mark risky slices another way, such as a
  label on the slice's issue or a risk label the repository defines, say so here.
