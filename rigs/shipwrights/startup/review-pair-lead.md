# Your team reviews in pairs

Where your role file says "the code reviewer", this team uses a review pair: two code reviewers on different runtimes,
which the clerk names for each slice when QA first passes it ("This team's shape" says how). The builder hands each
commit to the slice's QA seat first, and to both reviewers once QA passes it. They review independently, and the judge
compares their reviews.

- **Both reviews in the pull request:** the release manager reports them in the description, with what each reviewer
  ran and at which commit, and how the disagreements were settled, from what the judge records in the slice progress.
- **Reviewers on only one runtime:** when the team has reviewers on only one runtime, the clerk passes the slice to
  you ("No free pair" in "This team's shape"): proceed only if the person agrees, and record in the slice progress
  which review is missing, so the release manager says so in the pull request.
