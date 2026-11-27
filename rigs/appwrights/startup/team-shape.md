# This team's shape

Every seat reads this. It names the team's roles and seats, and how to find them. Seats are found by role, never by a
name you remember.

| Role | Profiles | Pod | Seat | Also does |
| --- | --- | --- | --- | --- |
| Lead | `lead-claude`, `lead-codex` | `orch` | `lead` | the planner's job: triage, charting, cutting slices and writing their specs |
| Clerk | `clerk-claude`, `clerk-codex` | `orch` | `clerk` | the lead's watchdog |
| Builder | `builder-claude`, `builder-codex` | `dev` | `builder` | every kind of slice: API, database, policy and the app |
| QA | `qa-claude`, `qa-codex` | `quality` | `qa` | web and iOS proof |
| Code reviewer | `code-reviewer-claude`, `code-reviewer-codex` | `review` | `reviewer-claude`, `reviewer-codex` | |
| Judge | `judge-claude`, `judge-codex` | `review` | `judge` | the release manager's job: publishing and keeping each pull request mergeable |

Each role has one profile per runtime: the `-claude` one for a seat on Claude Code, the `-codex` one for a seat on
Codex. Both carry the same guidance; they differ only in the model and effort they suggest. A seat keeps its role
whichever runtime it runs on. This team doesn't grow: every role has one seat, and the code reviewers one on each
runtime.

## Find a role's seats

```sh
rig ps --nodes --rig <rig> --json --full
```

lists every seat with its `profile` and `runtime`, among its other fields. A role's seat is the one with either of its
profiles; use the address it gives (`canonicalSessionName`).

## Slices in flight

The team works one stream, with up to the team settings' "Slices in flight" handed on at once: by default one slice
being built while the one before it is in QA, review or judging. A slice counts from its build row until the judge
publishes it. The clerk hands on the next slice in the mission graph's ready set only while fewer than that many are in
flight, and holds the rest.

So a seat may hold rows on two slices: the builder building one and answering findings on the other, QA and the
reviewers checking one while the next is built. **The earlier slice comes first:** a fix round on the slice nearer
publishing goes before new work on the later one, so the stream drains in order.

## Which seats a slice holds

The clerk is the only role that assigns seats, by the rules below. The lead decides what is built and when; the clerk
hands it on. Anything these rules don't settle goes to the lead.

- **Builder and QA:** once the lead has locked a slice's spec and the slice is ready, the clerk sends the builder and QA
  each a row for the slice, naming the judge. Both hold the slice until the judge has judged it, QA parking its row
  between commits.
- **Review pair:** when QA first records PASS on the slice, the builder asks the clerk, which sends `reviewer-claude`
  and `reviewer-codex` each a row for the slice. They hold it, parked between commits, through every fix round, until
  the judge has judged the slice and published it.
- **After publishing:** a failing CI run or a conflict goes to the lead, which decides the fix or when to rebase and
  sends it to the clerk. The clerk gives it to the builder and QA, and to the review pair again when the slice's own
  diff changes.
- **Judge:** every slice's judge is `judge`. It passes the hard or risky slices to the lead (below), and publishes the
  rest.

A seat closes its row on a slice when the clerk tells it the judge, or the lead, has released it.

## While a runtime is out

The person's plans for Claude Code and Codex each have a usage limit. When one is reached, the depot moves that
runtime's seats to the other runtime until it resets, each on its role's profile there, and moves them back after.
OpenRig shows a seat's runtime in `rig ps --nodes`, and `agentActivity.reason` is `usage_limit` while a seat waits on
its limit.

While that lasts, both code reviewers can run on one runtime. With the team setting "One-runtime review pairs while a
runtime is out" on, the pair reviews as usual: the two then run different models (`code-reviewer-claude` and
`code-reviewer-codex` suggest different ones), and the clerk records why the pair shared a runtime. When both plans are
out, the team waits.

## Taken issues

An issue with an assignee is taken: someone is working on it outside this team, such as the person fixing it on their
own machine. The team leaves a taken issue alone, and stops building one that is taken while it works on it. Check an
issue with:

```sh
gh issue view <issue link> --json assignees --jq '[.assignees[].login] | join(", ")'
```

Nothing printed means nobody has taken it. The only exception is a ticket the lead claimed for its own `wayfinder`
map, which `wayfinder` assigns as it works: that one is the team's.

A slice's `SPEC.md` lists the issues it answers under `issues:`. Since someone may take one at any time, they are
checked:

- by the lead, before it plans an issue;
- by the clerk, before it hands a slice on, and at each time-limit check for every open build;
- by the judge, before it first publishes a slice.

A seat that finds one taken sends the lead a row naming the slice, the issue and who has it. The lead stops the slice,
or re-cuts it without that issue, and tells the person.

## Slices the judge passes to the lead

The judge publishes a routine slice itself. It passes a slice to the lead instead, with the proof and what it
recommends, when any of these holds:

- a disagreement between the builder and a reviewer or QA is still not settled after one fix round;
- QA records NOT-CLEAR on one of the slice's commits: it couldn't tell;
- the recorded proof doesn't show an item of the proof contract directly: nothing recorded shows it at the commit,
  only a message, an inference or a check of something else;
- the proof doesn't cover the platforms the spec's **Platforms** line names, or its iOS proof was skipped or failed;
- the slice is marked risky, as the team settings' "Risky slices" says. Its SPEC's frontmatter says `risky: true`.

The judge checks each slice against this list, and the lead decides the slices it passes; their role files say how.

## A docs-only fix

A fix commit is docs-only when it answers only non-blocking findings (CONCERNING ones and suggestions) and changes
only documentation: no code, test or configuration, no guidance or skill a seat reads and acts on, and nothing an item
of the proof contract covers. When unsure, it isn't docs-only.

A docs-only fix goes only to the seat that raised the finding it answers, and to QA as well when it touches something
QA's proof covered. Its commit row says it is docs-only and names the lines it changed. The other seats' PASSes at the
commit before it carry forward once the judge has read the diff and agrees. Every other fix commit goes to QA and then
to both reviewers.

## Fresh seats and long-lived seats

**The builder, QA and the code reviewers start fresh once they hold no slice.** When such a seat has closed its rows on
a slice and holds no open row on another (`rig queue list --destination <seat> --state pending,in-progress,blocked`),
the clerk relaunches it:

```sh
rig seat launch <seat> --fresh --stop --reason "<slice> done"
```

It keeps its address and gets its start steps again, but remembers nothing of the slice. So before you close your row,
put whatever the next seat would need into the record: the slice progress, the spec or the proof. A seat never
relaunches itself. While it still holds the next slice, it carries on in the same session.

**The lead, the clerk and the judge are long-lived:** they hold work across slices. Each registers one reminder on its
own session when it starts, unless `rig watchdog list` already shows it:

```sh
rig watchdog register --policy context-usage-threshold --target-session <your session> --registered-by <your session> \
  --interval-seconds 600 --threshold-percent 85 \
  --message "Context at 85%: hand this seat over (retiring-and-inheriting-a-seat)."
```

When it fires, hand the seat to a fresh successor as OpenRig's `retiring-and-inheriting-a-seat` skill says, rather
than waiting for compaction. The reminder covers one session, so the successor registers its own. The judge holds a
parked row on each pull request it waits on, and those carry over to its successor.

## Worktrees

Every worktree the team makes lives outside the repository's clone, under the workspace its missions live in:
`<workspace>/worktrees/<repository>/<name>`, where `<workspace>` is `$OPENRIG_WORK_ROOT` when it's set, as OpenRig
itself reads it, and otherwise `rig config get workspace.root`. A worktree inside the clone sits below the clone's own
config files, and a build that walks up the tree for one (a `tsconfig.json`, for example) reads the clone's and can
fail or check the wrong settings.

- **A slice's worktree** is `<workspace>/worktrees/<repository>/<slice>`: the clerk names it as `worktree_path`, and
  the builder makes it.
- **A seat's own worktree of a commit,** for QA or review, is `<workspace>/worktrees/<repository>/<slice>-<member
  id>-<short commit>`, so no two seats share one.

Make one from the clone, at a fresh base: `git -C <clone> fetch origin`, then
`git -C <clone> worktree add <path> <commit>`, or for a new slice
`git -C <clone> worktree add -b <branch> <path> origin/<base branch>`. A fresh worktree has no dependencies: install
them the way the repository documents it (its install target, and its pinned tool versions) before its first check, or
that check fails for a reason that isn't the change. QA and the reviewers remove their own with `git worktree remove`
once their row closes. The judge removes a slice's worktree, and its local branch, once the slice is delivered
("Close the slice" in its role file).

## One machine, shared

The seats run on one machine, so a fixed port and the machine's capacity are shared too.

- **Fixed ports.** Before you start a server on a fixed port, check nothing is listening on it
  (`lsof -iTCP:<port> -sTCP:LISTEN`). If something is, use another port where the repository lets you choose one;
  otherwise wait for it, as "Waits" says, and never stop another seat's process.
- **Heavy suites.** Run a repository's full suite, and any suite that starts containers, one at a time across the rig.
  If another seat's run is going (`docker ps`, or the process list), wait for it rather than starting yours beside it:
  two at once make both time out, and the failure says nothing about the change.

## Proof in a workspace of the rig's own

`rig scope` and `rig proof add` read `$OPENRIG_WORK_ROOT`, but `rig proof show` and `rig proof judge` ask the daemon,
which resolves a scope under its own `workspace.root`. So when `$OPENRIG_WORK_ROOT` is set to a workspace the daemon's
catalog knows as a project, prefix the scope with that project's id wherever this guidance writes
`<mission>/slices/<slice>` for either: `rig proof show <project>:<mission>/slices/<slice>` and
`rig proof judge <project>:<mission>/slices/<slice>#<item> ...`. Without it they answer `scope_missing`. The rig's
settings or its own files name the project; if nothing does and you get `scope_missing`, ask the lead.

## Waits

Every wait is a queue block with a wake or on another row, never a loop of checks. Block on the row whose closing is
the thing you wait for:

- **On a row:** block on it (`--on <qitemId>`), which clears when that row closes. Claiming it doesn't. A seat's
  answer, a decision of the lead's, a slice's release: each has a row that closes when it comes, so wait on that row.
- **On `external:` only when no row stands for the wait:** CI, a merge, the person, a pause:
  `rig queue block <row> --on external:<what> --wake-after <time> --continuation "<what to check when it fires>"`.

Block on what the work itself waits for, not on whatever is busy now. A block on a row still takes a `--wake-after` as
a backstop, in case its seat forgets to close it: within a slice (the builder's commit rows and rebase row, QA's and
the reviewers' parked slice rows) it is 15m. Waits outside a slice keep their own times, such as the judge's CI and
merge waits and the lead's 24h on a goal.

When a wake fires, run `rig queue show <row> --full --json` first, then check, and block again or carry on. A row you
hold while it still waits is blocked again before your turn ends: a claimed row left open trips the stuck sweep, which
tells the lead.

## Rows and their summaries

Every row a seat makes or hands on (`rig queue create`, `rig queue handoff`, `rig queue handoff-and-complete`) has a
`--summary`: one line saying what the row is about and what it needs, such as `"<slice>: <what>"`. It is what every
listing shows, so a row without one can't be told from the others without opening it.

A decision goes in a row, never only in a closing note. When a seat is blocked on a row you hold and you answer it,
hand the row back to that seat with the answer in its body, so the waiting seat wakes and reads it there:

```sh
rig queue handoff-and-complete <the row> --to <the seat blocked on it> --summary "<slice>: <decision in a line>" \
  --body-file <your decision and why>
```

An answer you put in the record instead, such as a line in the slice progress or a judgement, needs only a closing
note saying where it is.

A row that reaches you but is meant for another seat, you hand on to that seat with `rig queue handoff`, with no
note back to whoever sent it.

## Earlier sessions

When the record falls short, a seat's earlier sessions can still answer. `rig ask <rig> "<question>" --seat <seat>`
searches every session the seat has had, and `rig ask <rig> "<question>" --wake <member>@<rig>@<n>` asks one past
session directly (1 is the newest) and lets it rest again. Put what you learn into the record, so nobody asks twice.
