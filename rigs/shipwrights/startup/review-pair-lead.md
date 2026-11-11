# Your team reviews in pairs

Where your role file says "the code reviewer", this team uses a review pair: two code reviewers on different runtimes,
which the clerk names for each slice when QA first passes it ("This team's shape" says how). The builder hands each
commit to the slice's QA seat first, and to both reviewers once QA passes it. They review independently.

- **Compare the two reviews** when both verdicts are in for the same commit. Sort the findings into:
  - those both reviewers raised;
  - those only one reviewer raised.

  A finding only one reviewer raised isn't wrong for that reason. Ask the other reviewer to check it against the code.
  Decide each disagreement from the evidence, and tell the builder what must change.
- **Release the pair** once both have recorded PASS at the same commit and you have compared them: tell the clerk, which
  tells each to close its row on the slice and relaunches them.
- **Pull request description:** report both reviews, with what each reviewer ran and at which commit, and how the
  disagreements were settled.
- **No free pair:** when no two free reviewers are on different runtimes, the slice waits for one to free up, unless
  the team setting "One-runtime review pairs while a runtime is out" is on and the clerk can pair two on one runtime
  ("This team's shape" says when). When the team has reviewers on only one runtime, the clerk passes the slice to you:
  proceed only if the person agrees, and say in the pull request which review is missing.
