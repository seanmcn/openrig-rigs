# This team reviews in pairs

Each slice has a review pair: two code reviewers on different runtimes, which the clerk names when QA first passes a
commit ("This team's shape" says how). The builder hands each commit to the slice's QA seat first, and to both
reviewers once QA passes it. They review independently, and each sends you its verdict.

- **Compare the two reviews** when both verdicts are in for the same commit. Sort the findings into:
  - those both reviewers raised;
  - those only one reviewer raised.

  A finding only one reviewer raised isn't wrong for that reason. Ask the other reviewer to check it against the code.
  Decide each disagreement from the proof, and tell the builder what must change. Only the first fix round is
  yours: a disagreement still not settled after one fix round goes to the lead, as your role file says.
- **Release the pair** with the builder and the QA seat, once you have judged the slice and sent it on, as your role
  file says: until then a new commit still goes back to the same pair.
- **Record the comparison** in the slice progress: what each reviewer ran and at which commit, and how each
  disagreement between them was settled, so the pull-request description can report both reviews.
