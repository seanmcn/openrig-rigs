# Your team reviews in pairs

Where your role file says "the code reviewer", this team uses a review pair: two code reviewers on different runtimes,
which the clerk names for each slice when QA first passes it ("This team's shape" says how). The builder hands each
commit to the slice's QA seat first, and to both reviewers once QA passes it. They review independently, and the judge
compares their reviews.

- **Both reviews in the pull request:** the release manager reports them in the description, with what each reviewer
  ran and at which commit, and how the disagreements were settled, from what the judge records in the slice progress.
- **No free pair:** when no two free reviewers are on different runtimes, the slice waits for one to free up, unless
  the team setting "One-runtime review pairs while a runtime is out" is on and the clerk can pair two on one runtime
  ("This team's shape" says when). When the team has reviewers on only one runtime, the clerk passes the slice to you:
  proceed only if the person agrees, and record in the slice progress which review is missing, so the release
  manager says so in the pull request.
