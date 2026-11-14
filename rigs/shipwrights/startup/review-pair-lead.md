# Your team reviews in pairs

Where your role file says "the code reviewer", this team uses a review pair: two code reviewers on different runtimes,
which the clerk names for each slice when QA first passes it ("This team's shape" says how). The builder hands each
commit to the slice's QA seat first, and to both reviewers once QA passes it. They review independently, and the judge
compares their reviews.

- **Both reviews in the pull request:** the release manager reports them in the description, with what each reviewer
  ran and at which commit, and how the disagreements were settled, from what the judge records in the slice progress.
- **Reviewers on only one runtime:** when the team has reviewers on only one runtime, the clerk asks you ("No free
  pair" in "This team's shape"). Ask the person, then hand the clerk's row back to it saying whether they agreed,
  as "Rows and their summaries" in "This team's shape" says:

  ```sh
  rig queue handoff-and-complete <the clerk's row> --to <the clerk> \
    --summary "One-runtime pair: the person <agreed|declined>" --body-file <their words>
  ```

  When they did, the clerk pairs two reviewers on that runtime and records why in the slice progress, so the release
  manager says so in the pull request. Naming the reviewers stays the clerk's.
