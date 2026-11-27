# Team settings

These settings shape how the team works. Every seat reads this file at start and at
refocus, so a change reaches a seat at its next start or refocus. To change one, edit its
default here, or ship your own copy of this file in its place.

| Setting | Default | Read by |
| --- | --- | --- |
| Slices in flight | 2 | clerk |
| Disagreement rounds before the person is asked | 2 | judge, lead |
| Confirm each triage result with the person | off | lead |
| Slice time limit | 4 working hours | clerk, lead |
| One-runtime review pairs while a runtime is out | on | clerk |
| Risky slices | `risky: true` in the spec | lead, judge |

- **Slices in flight.** How many slices may be handed on at once. With the default, one slice is
  being built while another is in QA, review or judging; the clerk holds the rest in the queue
  until one is published. A slice is in flight from its build row until the judge publishes it.
- **Disagreement rounds before the person is asked.** How many fix rounds a disagreement
  between the builder and a reviewer or QA may go before the lead takes it to the person,
  with both sides' case. The judge settles the first round, and passes a disagreement
  still not settled after it to the lead.
- **Confirm each triage result with the person.** When on, the lead asks the person to
  confirm each triage result before it becomes a slice. When off, the result becomes a
  slice straight away.
- **Slice time limit.** How long a slice's build may run before the lead looks at it,
  counted in working hours from when the clerk created the build row. Each time its
  reminder wakes it, the clerk counts the working hours of every open build row, and passes
  the lead only a build past the limit.
- **One-runtime review pairs while a runtime is out.** When on, while one runtime's plan has
  reached its usage limit, its reviewer runs on the other runtime with that runtime's profile
  ("While a runtime is out" in "This team's shape"), so the pair shares a runtime and slices keep
  moving. The two reviewers then run different models, and the pull request says so. Pairs go
  back to one of each by themselves once the plan resets. When off, a slice waits for both
  runtimes.
- **Risky slices.** How a slice is marked risky, so the judge passes it to the lead whatever
  its proof shows. The lead adds `risky: true` to the frontmatter of a slice's `SPEC.md` when
  the slice changes authentication or sign-in, permissions, secrets, payments, personal data,
  a database migration or deletion, a native dependency or anything that needs a new app
  build, the app's build or EAS configuration, or a deploy or CI workflow, or when its iOS
  proof was skipped or failed. A rig may name more in its own copy of this file.
