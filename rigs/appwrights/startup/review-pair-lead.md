# Your team reviews in pairs

Where your role file says "the code reviewers", this team uses a review pair: `reviewer-claude` and
`reviewer-codex`, one on each runtime, which the clerk names for each slice when QA first passes it. The builder hands
each commit to QA first, and to both reviewers once QA passes it, all but a docs-only fix ("A docs-only fix" in "This
team's shape"). They review independently, and the judge compares their reviews.

- **Both reviews in the pull request:** the judge reports them in the description, with what each reviewer ran and at
  which commit, and how the disagreements were settled.
- **While a runtime is out:** both reviewers may run on one runtime until its plan resets ("While a runtime is out"
  in "This team's shape"). The pull request says so. Nothing is yours to decide there unless the clerk asks.
