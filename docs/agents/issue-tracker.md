# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`, with `--label bug` or `--label enhancement` when one fits. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Make an issue a sub-issue of a parent**: `gh issue create --parent <parent> ...`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>` (database id, as in **Blocking** below). Without sub-issues, put `Part of #<parent>` at the top of the child body.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh issue create --blocked-by <n>,<n> ...` or `gh issue edit <child> --add-blocked-by <blocker>` (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Count open blockers**: `gh api repos/<owner>/<repo>/issues/<n> --jq .issue_dependencies_summary.blocked_by` (open blockers only; 0 means startable). `gh issue view <n> --json blockedBy` also lists closed blockers, so filter it: `--jq '[.blockedBy.nodes[] | select(.state == "OPEN")] | length'`.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Set an issue's triage role**: swap its triage label, as `triage-labels.md` says.
- **Close**: post the explanation with `gh issue comment <number> --body "..."`, then `gh issue close <number>`. On an already-closed issue, `gh issue close --comment` drops the comment and still exits 0.

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

In a fork, `gh` can default to the upstream parent, so before the first `gh issue create` of a session, check the target with `gh repo view --json nameWithOwner` and confirm it with the user if it is not this repo.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same states as issues, recorded as `triage-labels.md` says, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number>`, then `gh pr view <number> --comments` (off a TTY, `--comments` prints only the comments, not the body), and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh api --paginate 'repos/{owner}/{repo}/pulls?state=open' --jq '.[] | select(.author_association | IN("OWNER","MEMBER","COLLABORATOR") | not) | {number, title, author: .user.login, author_association, labels: [.labels[].name]}'`.
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue. Keep the top of its body short, so a person can take it in at a glance, and collapse the rest. A spec has its own layout, in **A spec's layout** below. Every other issue goes:

1. Two to five plain sentences on what the issue is about and why it matters, with no heading.
2. What done looks like, as a short checklist, if the skill's template has acceptance criteria.
3. Everything else the skill's template asks for (the full spec or ticket, with its headings), in a collapsed section at the bottom:

   ```markdown
   <details><summary>Full spec</summary>

   ...

   </details>
   ```

   Name the summary after what's inside, such as "Full spec" or "Full ticket". Keep the blank line after `<summary>`, or GitHub won't render the Markdown inside.

The same goes for any issue a skill creates, and for an issue body a skill rewrites. A spec from `/create-spec` starts its title with `Spec:`; a ticket from `/create-tickets` is a sub-issue of its spec; anything a person could have filed takes `bug` or `enhancement`.

A ticket a person carries out, labelled `ready-for-human`, has the steps themselves as its checklist: every command, value and place to click, in the order they're done, so the person can work straight down it. Copy the steps from the runbook or setup guide that holds them, and link the section they came from as background. "Follow SETUP 7a" is a pointer, not a step. In any issue, link every document you mention, to the heading when you mean one section of it.

A comment that carries a brief, such as triage's agent brief, takes the same shape: a few plain sentences on what the work is and why, the acceptance criteria as a checklist, then the whole brief collapsed in `<details><summary>Agent brief</summary>`.

### A spec's layout

A spec from `/create-spec`, and any spec body a skill rewrites, keeps the template's sections in the template's order, with no summary sentences above them. Problem Statement and Solution are the summary, so they stay open at the top. User Stories, Implementation Decisions and Testing Decisions are long, so each one collapses behind its own heading, which carries a count: the numbered stories, or the top-level bullets. Out of Scope and Further Notes stay open.

```markdown
## Problem Statement

...

## Solution

...

<details><summary><h2>User Stories (27)</h2></summary>

1. As ...

</details>

<details><summary><h2>Implementation Decisions (12)</h2></summary>

- ...

</details>

<details><summary><h2>Testing Decisions (5)</h2></summary>

- ...

</details>

## Out of Scope

...

## Further Notes

...
```

GitHub shows a heading inside `<summary>` beside the expand arrow, so a collapsed section still reads as a section. Keep the blank line after `</summary>`, or GitHub won't render the Markdown inside.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

Then, before changing anything, be on a branch for it. `main` only takes pull requests, so if you're on `main`, `git switch -c <n>-<slug>` from it, where `<n>` is the issue number and `<slug>` comes from its title: the name GitHub itself gives a branch for an issue.

## Wayfinding operations

Used by `/scope-epic`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue titled `Map: ...`, holding the Notes / Decisions-so-far / Fog body. The map is already the short version, an index people read, so it doesn't follow the collapse rule in **publish to the issue tracker**: leave every section of it open.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (see **Make an issue a sub-issue of a parent**). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Its title starts with its kind (`Research:`/`Prototype:`/`Decision:`/`Task:`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: see **Blocking** under Conventions.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (see **Count open blockers**, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far. The comment opens with the answer in one or two plain sentences; put the working (research findings, options weighed, the grilling) under it in `<details><summary>How we got there</summary>`, with the blank line after `<summary>`.
