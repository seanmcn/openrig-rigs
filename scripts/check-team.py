#!/usr/bin/env python3
"""Checks a team folder the way its README promises, beyond what `rig bundle check` covers.

usage: scripts/check-team.py rigs/<team>

- nothing in the team names a word from TEAM_BLOCKLIST, a comma-separated list in the
  environment (such as the people or organisation a team was first built for), case-insensitively;
- no file uses a word in AVOIDED_WORDS, which GLOSSARY.md says to avoid, and each list in ONE_PLACE
  appears only in its own file;
- settings.md holds the team settings with their defaults;
- the team ships no third-party skills: every skill a profile selects is declared, and
  every declared skill sits inside the team folder with its SKILL.md;
- skills.md lists every skill the guidance names, each row with a source, a full commit,
  a licence, the profiles that use it and whether it is required, a required skill's seats being
  exactly the roles whose guidance or start files name it, and install-skills.sh
  reads it (a dry run, into empty folders);
- the role guidance carries the rules the team relies on, and none it has dropped, every
  `rig queue block` example names its `--on` blocker, and every
  role file has its seat add a retrospective note to the slice progress;
- every role in ROLES has one profile per runtime in RUNTIMES, named <role>-<runtime>, each
  delivering the role's guidance and no other, and setting preferences.runtime, and the model
  and effort SUGGESTED_MODEL_AND_EFFORT gives the role on that runtime; agent.yaml has no other
  profiles; the README's Models section names every model the model tiers list and says a rig
  may override a seat's model;
- rig.yaml's summary says the peer may run on either runtime, and NOTICE.md's rows for rig.yaml
  and agent.yaml name every seat and every role;
- rig.yaml declares exactly the seats in SEATS, each a member whose profile is its role's for the
  member's runtime, with each runtime in configurations.yaml mapped to the role's profile there,
  and a row in the README's seat table; the recommended preset keeps the code reviewers on two
  runtimes; the old names are gone, and every pod-prefixed name in the team's text is a seat's;
- startup/team-shape.md names every profile in agent.yaml, and its table gives each role whether
  it can grow and the fewest seats it can shrink to, and it says how a grown seat is numbered and
  how a seat is added to or removed from a running rig;
- the lead is the orchestrator (the only delegates_to source) of every seat but itself and its
  peer in rig.yaml, so every stuck queue row escalates to it, and the peer observes only the lead;
- every `rig` command in the team's text uses only flags OpenRig accepts for it, and only the values
  OpenRig accepts for a flag that takes a fixed set, such as `--status` or `--fields` (RIG_COMMANDS);
- `rig bundle check` passes, when `rig` is installed.

A skill the guidance "names" is any lower-case name in backticks in the guidance, the
culture, the start steps or the settings, other than OpenRig's own skills and the names
in NOT_SKILLS. Every new name in backticks must be one or the other, so a skill can't
slip into the guidance without a row in skills.md.

Standard library only, so it runs anywhere Python 3 does. It reads agent.yaml with
regular expressions, which holds because the team writes skills and `uses` lists in
flow style on one line each.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple


SETTINGS = {
    "Disagreement rounds before the person is asked": "2",
    "Confirm each triage result with the person": "off",
    "Slice time limit": "4 working hours",
    "One-runtime review pairs while a runtime is out": "off",
    "Risky slices": "`risky: true` in the spec",
}

# (guidance file, startup/<file> or a doc at the team's root such as README.md, phrase it must contain, why)
GUIDANCE_RULES = [
    ("clerk.md", "rig watchdog register", "the slice time limit wakes the clerk through a watchdog"),
    ("lead.md", "## Stop and pause", "stop and pause hold work without stopping sessions"),
    ("lead.md", "--wake-after", "waits are queue blocks with a wake"),
    ("judge.md", "--subject commit:<sha>", "the judge judges proof at the commit it checked"),
    ("judge.md", "Never judge without a commit", "a judgement always names a commit"),
    ("judge.md", "judge the slice again", "a rebase that changes the code needs a new judgement"),
    ("startup/team-shape.md", "## Which seats a slice holds", "the clerk assigns every seat a slice uses, from free seats"),
    ("startup/team-shape.md", "The clerk is the only role that assigns worker seats", "two seats never assign the same free seat"),
    ("startup/team-shape.md", "assigns only from its own", "with several clerks, each assigns only the worker seats it owns"),
    ("startup/team-shape.md", "the clerk that took its goal", "with several clerks, a mission stays with the clerk that took its goal"),
    ("clerk.md", "assign only from them", "with several clerks, a clerk assigns only the worker seats it owns"),
    ("lead.md", "the clerk that took its goal", "with several clerks, a mission stays with the clerk that took its goal"),
    # The person's goals go to the clerk, which routes a clear one to a planner without costing the lead a turn.
    ("clerk.md", "## Take the person's goals", "a new goal reaches the clerk, not the lead"),
    ("clerk.md", "whether to take the work on", "the clerk passes the lead a goal it isn't sure the team should take on"),
    ("clerk.md", "a question rather than work to do", "the clerk passes the lead any question"),
    ("clerk.md", "rig queue handoff <the goal's row> --to <the lead>", "a goal the clerk can't settle reaches the lead as the same linked row"),
    ("startup/lead-first-move.md", "The person's goals go to the clerk", "a new goal costs the lead no turn"),
    ("startup/lead-first-move.md", "locking it is how you take the work on", "the lead still decides what the team takes on"),
    ("lead.md", "Locking its cut is how you take the work on", "the lead still decides what the team takes on"),
    ("lead.md", "that goal's row", "the lead closes a goal's row with the result"),
    ("startup/context.md", "the clerk takes the person's goal", "every seat knows goals reach the clerk"),
    ("startup/team-shape.md", "the person's goals come to the clerk", "every seat knows goals reach the clerk"),
    ("README.md", "orch-clerk-1@shipwrights", "the person gives the team work through its clerk"),
    ("planner.md", "the person's goal", "a goal reaches the planner straight from the clerk"),
    ("judge.md", "yours, not the clerk's", "the judge, not the clerk, picks the release manager"),
    ("startup/team-shape.md", "two free code reviewers on different", "a review pair is two code reviewers on different runtimes"),
    ("startup/team-shape.md", "One-runtime review pairs while a runtime is out", "a pair may share a runtime only under the setting"),
    ("startup/team-shape.md", "two different models, one a model tier above the builder's", "a one-runtime pair keeps the review independent of the builder's model"),
    ("startup/team-shape.md", "**No free pair:**", "every seat, the clerk included, reads what happens with no free pair"),
    ("startup/team-shape.md", "rig seat launch <seat> --fresh", "worker seats start fresh for each piece of work"),
    ("startup/team-shape.md", "context-usage-threshold", "long-lived seats hand over at a context threshold"),
    # How every seat waits is written once, in a start file every seat gets.
    ("startup/team-shape.md", "## Waits", "every seat waits the same way"),
    ("startup/team-shape.md", "never a loop of checks", "a wait is a queue block, never polling"),
    ("clerk.md", "\"Waits\" in \"This team's shape\"", "the clerk waits as every seat does"),
    ("judge.md", "\"Waits\" in \"This team's shape\"", "the judge waits as every seat does"),
    ("lead.md", "\"Waits\" in \"This team's shape\"", "the lead waits as every seat does"),
    ("startup/team-shape.md", "the next number in its role's pod", "a grown seat takes the next number in its pod"),
    ("startup/team-shape.md", "the same profile", "a grown seat keeps its role's profile"),
    ("startup/team-shape.md", "the role's edges", "a grown seat gets its role's edges"),
    ("startup/team-shape.md", "`rig add`", "a running rig grows a pod with rig add"),
    ("startup/team-shape.md", "`rig expand`", "a running rig gains a pod with rig expand"),
    ("startup/team-shape.md", "`rig grow` adds only OpenRig's default agent", "rig grow would drop the role and its model"),
    # A rig shrinks a role no further than its fewest seats, and empties a seat before removing it.
    ("startup/team-shape.md", "## Remove a seat", "team-shape.md says how a rig shrinks, not only how it grows"),
    ("startup/team-shape.md", "`rig remove`", "a running rig loses a seat with rig remove"),
    ("startup/team-shape.md", "--fallback", "rig remove refuses a seat with open rows unless they are rerouted"),
    ("startup/team-shape.md", "the worker seats it owns", "a clerk's seats and missions go to another clerk before it goes"),
    ("clerk.md", "a seat is leaving", "the clerk assigns nothing new to a seat that is leaving"),
    ("lead.md", "## Find work when asked", "the lead looks for work only when the person asks"),
    ("lead.md", "Don't go looking for work unless they ask", "with no goal, the lead waits"),
    ("lead.md", "## Close the mission", "the lead closes the person's goal once the clerk says its mission is complete"),
    ("startup/slice-spec.md", "`repos:`", "each slice's SPEC.md frontmatter lists the repositories it touches"),
    ("startup/slice-spec.md", "in merge order", "the repositories are listed in the order their pull requests merge"),
    ("startup/slice-spec.md", "## Proof contract", "each spec ends in the proof contract the judge judges"),
    ("release-manager.md", "judged at the commit you are about to push", "only proof judged at the pushed commit publishes"),
    ("builder-backend.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("builder-backend.md", "inside the worktree", "commands run from inside the worktree"),
    ("builder-backend.md", "until QA records PASS", "QA passes each commit before the reviewers see it"),
    ("qa.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("qa.md", "inside the worktree", "commands run from inside the worktree"),
    ("code-reviewer.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("code-reviewer.md", "inside the worktree", "commands run from inside the worktree"),
    ("peer.md", "rig watchdog register", "a watchdog wakes the peer; it never polls"),
    ("peer.md", "Never compact the lead", "the peer restores the lead and never compacts it"),
    ("peer.md", "down for 10 minutes", "the peer relaunches the lead only after it is down for 10 minutes"),
    ("peer.md", "rig seat launch <lead> --fresh", "the peer relaunches a down lead fresh"),
    ("peer.md", "the recap row", "a relaunched lead gets the recap row a handed-over lead gets"),
    ("peer.md", "still down 10 minutes after", "a lead still down after its relaunch goes to the person"),
    ("peer.md", "Then stop", "the peer stops once it has told the person"),
    ("peer.md", "You never drive", "the peer is a watchdog and never drives"),
    ("startup/team-shape.md", "`peer`, on either runtime", "the peer no longer has to be on the other runtime"),
    ("planner.md", "wayfinder", "large work with open questions is charted with wayfinder"),
    ("planner.md", "rig scope mission graph", "the build order comes from the mission graph"),
    ("planner.md", "Confirm each triage result with the person", "the planner honours the triage setting"),
    ("startup/slice-spec.md", "UI, backend or both", "each slice is tagged UI, backend or both"),
    ("lead.md", "\"What each slice's SPEC says\"", "the lead holds specs to the one shared standard"),
    ("planner.md", "\"What each slice's SPEC says\"", "the planner writes specs to the one shared standard"),
    ("builder-frontend.md", "builder-backend.md", "the frontend builder runs the backend builder's guidance too"),
    ("builder-frontend.md", "Never use `impeccable live`", "the frontend builder never uses live mode"),
    ("builder-frontend.md", "impeccable detect", "the frontend builder runs the detector itself"),
    ("builder-frontend.md", "screenshot", "each changed state is shown in a real browser"),
    ("release-manager.md", "--force-with-lease", "the release manager pushes rebased branches only with lease"),
    ("release-manager.md", "never `main`", "the release manager never pushes to main"),
    ("release-manager.md", "external:ci", "CI is a queue block with a wake"),
    ("release-manager.md", "gh run list", "the CI wait comes from the workflow's recent run times"),
    ("release-manager.md", "external:merge", "the merge is a queue block with a wake that backs off"),
    ("release-manager.md", "release-candidate", "the release manager marks a ready mission release-candidate"),
    ("release-manager.md", "--scope delivery", "the release manager approves each merged slice for delivery"),
    ("qa.md", "--on external:next-commit", "QA parks the lead's row between commits, so the stuck sweep doesn't flag it"),
    ("code-reviewer.md", "--on external:next-commit", "a reviewer parks the lead's row between commits"),
    ("startup/review-pair-reviewer.md", "parked between commits", "a reviewer in a pair parks the lead's row between commits"),
    ("builder-backend.md", "block the rebase row", "the builder parks the rebase row while QA checks it"),
    ("planner.md", "rig queue handoff-and-complete <your row> --to <the lead>",
     "the planner's hand-off is linked, and closes its row as done, so a wait on that row wakes"),
    ("lead.md", "The planner hands you back one combined list", "a survey's list reaches the lead as a row"),
    ("planner.md", "subagent on a cheaper model", "the planner hands reading-heavy side tasks to a cheaper subagent"),
    # The clerk does the lead's routine coordination by fixed rules, and passes anything else to the lead.
    ("clerk.md", "When you are unsure, hand it to the lead", "the clerk's first rule: a budget model never guesses"),
    ("clerk.md", "You never decide", "the clerk applies rules; judgement stays with the lead"),
    ("clerk.md", "to a free planner", "the clerk routes each goal, re-cut, survey and question to a free planner"),
    ("clerk.md", "once the lead has locked its spec", "the clerk hands a slice on only after the lead locks its spec"),
    ("clerk.md", "count the working hours since its `tsCreated`", "the time limit counts from the build row's creation"),
    ("clerk.md", "two free code reviewers on different runtimes", "the clerk names the review pair"),
    # With the setting on, a review pair may share a runtime while the other runtime is out.
    ("clerk.md", "One-runtime review pairs while a runtime is out", "the clerk reads the one-runtime pairing setting"),
    ("clerk.md", "no reviewer on the other runtime has room", "a pair shares a runtime only while the other runtime is out"),
    ("clerk.md", "different models", "a one-runtime pair runs two different models"),
    ("clerk.md", "a model tier above the builder's", "a one-runtime pair keeps one review stronger than the builder's model"),
    ("clerk.md", "preferences.model", "the clerk reads a seat's model from its member or its profile"),
    ("clerk.md", "the `profile` it runs with", "the clerk reads the profile each seat runs with from OpenRig"),
    ("clerk.md", "\"Models\"", "the clerk takes a model's model tier from the README's table"),
    ("clerk.md", "one of each again", "new pairs go back to both runtimes once the other has room"),
    ("clerk.md", "At every new pairing", "the clerk checks the other runtime at each pairing, so pairs go back by themselves"),
    # A seat at its usage limit can't run a command, so OpenRig's own reading says when a runtime is out.
    ("clerk.md", "`agentActivity.reason` is `usage_limit`", "the clerk reads each reviewer's usage limit from rig ps"),
    ("clerk.md", "at least one reviewer and every reviewer on it", "a runtime with no reviewers is missing, not out"),
    ("clerk.md", "saying the person agreed", "the clerk pairs on one runtime on the person's word, through the lead"),
    ("clerk.md", "--add \"Review pair: <reviewer> (<runtime>, <model>)", "the clerk records each pair's models on the slice"),
    ("clerk.md", "shared <runtime>: <other runtime> is out", "the clerk records why a pair shared a runtime"),
    ("clerk.md", "rig seat launch <seat> --fresh", "the clerk relaunches each freed seat fresh"),
    ("clerk.md", "## Publish the team's roster", "the clerk publishes the roster"),
    ("clerk.md", "## Keep the roster current", "the clerk keeps the roster current"),
    ("clerk.md", "Only a build past the limit goes to the lead", "the time-limit reminder wakes the lead only for overdue builds"),
    ("clerk.md", "set its status to `complete`", "the clerk records a mission's completion in its mission.yaml"),
    ("clerk.md", "Tell the lead only when a mission is complete", "a delivered slice doesn't wake the lead"),
    ("clerk.md", "metadata.status", "the clerk sets a mission active when its first slice is handed on"),
    ("lead.md", "## What the clerk does", "the lead knows which jobs the clerk does and what it passes back"),
    # With several clerks, each slice's rows reach the clerk that owns it, not the lead.
    ("clerk.md", "`clerk=<your session>`", "the slice's handoff names its clerk"),
    ("clerk.md", "--add \"Clerk: <your session>\"", "the mission's progress names its clerk"),
    ("clerk.md", "hand it on to that clerk", "a clerk passes another clerk's row to that clerk, not the lead"),
    ("startup/team-shape.md", "it means the slice's clerk", "every seat sends a slice's rows to its own clerk"),
    ("startup/lead-first-move.md", "to the clerk", "the lead sends a goal to the clerk to route to a planner"),
    ("startup/review-pair-lead.md", "the clerk", "the clerk names and releases the review pair"),
    ("builder-backend.md", "ask the clerk for the slice's review pair", "the builder asks the clerk, not the lead, for a pair"),
    ("planner.md", "from the clerk", "the clerk routes work to the planner"),
    ("release-manager.md", "tell the clerk the slice is delivered", "delivery reports go to the clerk, not the lead"),
    ("release-manager.md", "send its link to the clerk", "pull-request links go to the clerk, not the lead"),
    ("builder-backend.md", "rebase only when the clerk sends you a rebase row", "a rebase reaches the builder from the clerk"),
    ("release-manager.md", "the clerk gives it to a builder", "the clerk, not the lead, gives a fix or a rebase to a builder"),
    ("clerk.md", "published: <pull request link>", "the clerk records each pull request the release manager opens"),
    ("lead.md", "pull requests when the clerk tells you", "the lead hears of a mission's pull requests once it completes"),
    # The judge judges each slice from the record, and passes only the hard or risky ones to the lead.
    ("judge.md", "the spec and proof contract the lead locked", "the judge judges against the criteria the lead locked"),
    ("judge.md", "## Compare the reviews", "the judge compares the pair's reviews"),
    ("judge.md", "Disagreement rounds before the person is asked", "the judge reads the disagreement-rounds setting"),
    ("judge.md", "## Pass it to the lead", "the judge passes the hard or risky slices to the lead"),
    ("judge.md", "still not settled after one fix round", "a disagreement that survives a fix round goes to the lead"),
    # What the judge passes to the lead is listed once, in a start file both seats get.
    ("startup/team-shape.md", "## Slices the judge passes to the lead", "one list the judge and the lead both read"),
    ("startup/team-shape.md", "still not settled after one fix round", "a disagreement that survives a fix round goes to the lead"),
    ("startup/team-shape.md", "QA records NOT-CLEAR", "a NOT-CLEAR goes to the lead"),
    ("startup/team-shape.md", "doesn't show an item of the proof contract directly", "a proof item the recorded proof doesn't show directly goes to the lead"),
    ("startup/team-shape.md", "the slice is marked risky", "a risky slice goes to the lead"),
    ("judge.md", "\"Slices the judge passes to the lead\"", "the judge checks each slice against the one list"),
    ("lead.md", "\"Slices the judge passes to the lead\"", "the lead reads the one list"),
    ("startup/team-shape.md", "Risky slices", "the judge reads how the rig marks a slice risky"),
    ("judge.md", "straight to a release manager", "a routine judged slice never waits for the lead"),
    ("judge.md", "Judged routine at <commit>", "the judge records each routine judgement in the slice progress"),
    ("lead.md", "your queue holds only decisions", "no routine slice puts a row on the lead's queue"),
    ("judge.md", "tell the clerk", "the judge releases the seats through the clerk"),
    ("judge.md", "## Release the seats", "the judge hands off to the clerk's section of the same name"),
    ("clerk.md", "## Release the seats", "the clerk takes on from the judge's section of the same name"),
    ("judge.md", "You never decide", "scope, the person and the hard cases stay with the lead"),
    ("startup/review-pair-judge.md", "Compare the two reviews", "the judge compares the pair's reviews"),
    ("startup/review-pair-judge.md", "Release the pair", "the judge releases the pair through the clerk"),
    ("startup/slice-spec.md", "`risky: true`", "the default way a slice is marked risky"),
    ("planner.md", "`risky: true`", "the planner marks a risky slice in its spec"),
    ("lead.md", "## Slices the judge passes you", "the lead decides the slices the judge passes it"),
    ("lead.md", "## Overrule the judge", "the lead keeps the last word"),
    ("lead.md", "the judge tells the builder", "the lead's decision on a passed slice reaches the builder through the judge"),
    ("judge.md", "tell the builder what the lead decided", "the judge alone tells the builder the lead's decision"),
    ("builder-backend.md", "which the judge tells you", "the builder hears the lead's decision from the judge"),
    ("startup/review-pair-judge.md", "still not settled after one fix round", "only a disagreement's first fix round is the judge's"),
    ("lead.md", "with your reason", "the lead overrules only with a reason"),
    ("builder-backend.md", "## Tell the judge it's done", "the builder tells the judge, not the lead, that a slice is ready"),
    ("qa.md", "to the judge", "QA's NOT-CLEAR reaches the lead through the judge"),
    ("code-reviewer.md", "to the judge", "a reviewer's verdict goes to the judge"),
    ("startup/review-pair-reviewer.md", "the judge compares", "the judge compares the pair's findings"),
    ("clerk.md", "the review pair's when the judge tells you it has judged the slice", "the judge releases the pair only once the slice is judged"),
    ("judge.md", "its builder, its QA seat and its review pair", "a rejection or the lead's decision can still need the same pair"),
    ("clerk.md", "the judge tells you it has judged the slice", "the judge releases the builder and QA seat"),
    ("release-manager.md", "from the judge", "the release manager takes judged slices from the judge"),
    ("startup/team-shape.md", "the judge, not the clerk, gives each judged slice", "the judge picks the release manager"),
    # The release manager writes the pull-request description from the record, and keeps it true.
    ("release-manager.md", "## Write the description", "the release manager owns the pull-request description"),
    ("release-manager.md", "the slice's locked spec", "the description says what the spec the lead locked promised"),
    ("release-manager.md", "--subject commit:<sha>", "the description reports proof as judged at its commit"),
    ("release-manager.md", "the judge's slice progress", "the description says how each disagreement was settled"),
    ("release-manager.md", "Fill the repository's pull-request template", "the description fills the repository's template"),
    ("release-manager.md", "what each reviewer ran and at which commit", "the pull request reports both reviews"),
    ("release-manager.md", "which review ran on which model", "the pull request says which review ran on which model"),
    ("release-manager.md", "why the pair shared a runtime", "the pull request says why a pair shared a runtime"),
    ("release-manager.md", "the lead's decision", "a slice the lead decided is described from its decision"),
    ("release-manager.md", "say that it didn't run", "a check the lead decided can't run here is reported as not run"),
    ("release-manager.md", "back to whoever judged the slice", "a claim the record doesn't support goes back, not into the description"),
    ("release-manager.md", "## Keep the description true", "the release manager keeps the description true"),
    ("release-manager.md", "when the reviews, CI or the code change", "the description changes with the reviews, CI and code"),
    ("startup/review-pair-lead.md", "the release manager", "the release manager reports both reviews in the pull request"),
    # The result of checking pull requests together goes back to the release manager that asked for it.
    ("qa.md", "the release manager that asked", "QA's result on pull requests checked together reaches the release manager"),
    ("clerk.md", "the release manager that asked", "the clerk tells QA who asked, and the release manager which row to wait on"),
    ("release-manager.md", "block your row on QA's row", "the release manager waits for the result on QA's row"),
    ("release-manager.md", "fail together, send the failure to the lead", "a failure goes to the lead, as after a CI run"),
    ("lead.md", "fail together, the release manager tells you", "the lead hears of a failure from the release manager"),
    # Every row a slice's seats send the judge is closed, and the builder waits out a NOT-CLEAR on QA's row to the judge.
    ("judge.md", "## Close each row you are sent", "no verdict, NOT-CLEAR or disagreement row stays open on the judge"),
    ("judge.md", "closing it is what wakes the builder", "the judge's closing QA's NOT-CLEAR row wakes the builder"),
    ("qa.md", "name that row in the results", "the builder needs QA's NOT-CLEAR row to the judge to wait on"),
    ("builder-backend.md", "block your row on that row", "the builder waits out a NOT-CLEAR on a queue block"),
    ("lead.md", "a review pair on one runtime", "the lead expects the clerk's question about a one-runtime pair"),
    ("lead.md", "rig ps --nodes", "the lead finds the clerk's session by its seat, not with rig whoami"),
    ("startup/team-shape.md", "rig watchdog stop", "a removed seat's reminders stop with it"),
]

# (guidance file, startup/<file> or a doc at the team's root, phrase it must not contain, why)
FORBIDDEN_RULES = [
    # The lead hears of a goal's missions completing, never of a single delivery.
    ("lead.md", "Each time a piece they picked is delivered", "the lead finds work again when a picked goal is done"),
    ("README.md", "each time a piece you picked is delivered", "the lead finds work again when a picked goal is done"),
    ("clerk.md", "another clerk holds isn't yours: hand it to the lead", "another clerk's row goes to that clerk"),
    ("judge.md", "once you have compared both PASSes", "the pair is released with the builder and QA, once the slice is judged"),
    ("code-reviewer.md", "usage limit, tell the clerk", "a seat at its usage limit can't run a command; OpenRig sees the limit"),
    # rig queue overdue lists only rows in progress, and each claim restarts a row's deadline.
    ("clerk.md", "run `rig queue overdue", "the clerk counts each build's working hours from its row's creation"),
    ("settings.md", "rig queue overdue", "the clerk counts each build's working hours from its row's creation"),
    # A plain handoff moves every wait on the planner's row onto the lead's new row, which stays open for days.
    ("planner.md", "rig queue handoff <your row>", "the planner hands back with handoff-and-complete, so waits on its row wake"),
    ("planner.md", "close the row with one combined list", "a survey's list goes back to the lead as a row"),
    ("lead.md", "Push the builder's branch", "the release manager publishes, not the lead"),
    ("release-manager.md", "external:ci --wake-after 15m", "the CI wait comes from recent run times, not a fixed 15 minutes"),
    ("peer.md", "## Take over", "the peer relaunches a down lead and never drives in its place"),
    ("peer.md", "## Hand back", "the peer never drives, so it has nothing to hand back"),
    ("peer.md", "(driving)", "the peer never drives, so it records no driving decisions"),
    ("peer.md", "not yours to reset", "the peer relaunches a lead that has been down for 10 minutes"),
    ("peer.md", "on the other runtime", "the peer may run on either runtime"),
    ("startup/team-shape.md", "on the other runtime from the lead", "the peer may run on either runtime"),
    # The jobs that moved to the clerk.
    ("lead.md", "## Publish the team's roster", "the clerk publishes the roster"),
    ("lead.md", "rig roster list", "the clerk publishes and keeps the roster"),
    ("lead.md", "rig watchdog register", "the clerk registers the time-limit reminder"),
    ("lead.md", "rig queue overdue", "the clerk checks for overdue builds and passes only those to the lead"),
    ("lead.md", "--tier", "the clerk writes the build rows"),
    ("lead.md", "to a free planner", "the clerk routes work to a planner"),
    ("lead.md", "free code reviewers", "the clerk names the review pair"),
    ("lead.md", "## Release the seats", "the clerk relaunches the seats the judge or the lead releases"),
    ("clerk.md", "## Free the seats", "the clerk's section and the judge's share one name, \"Release the seats\""),
    ("lead.md", "relaunch <seat>", "the clerk relaunches freed seats"),
    ("lead.md", "metadata.status", "the clerk sets a mission active"),
    ("lead.md", "status to `complete`", "the clerk records a mission's completion"),
    ("startup/lead-first-move.md", "to a free planner", "the clerk routes work to a planner"),
    ("startup/lead-first-move.md", "Claim that row", "a goal goes to the clerk, not the lead"),
    ("lead.md", "Claim the kernel operator's goal row", "a goal goes to the clerk, not the lead"),
    ("lead.md", "from its goal on, to one clerk", "a mission stays with the clerk that took its goal"),
    ("startup/team-shape.md", "from its goal on, to one clerk", "a mission stays with the clerk that took its goal"),
    ("startup/context.md", "the lead starts from the person's goal", "a goal goes to the clerk, not the lead"),
    ("README.md", "It hands the goal to the lead", "a goal goes to the clerk, not the lead"),
    ("clerk.md", "Work for the team goes through the lead", "work for the team goes through the clerk"),
    ("startup/review-pair-lead.md", "which you name for each slice", "the clerk names the review pair"),
    ("startup/team-shape.md", "the lead relaunches it", "the clerk relaunches freed seats"),
    ("release-manager.md", "tell the lead the slice is delivered", "delivery reports go to the clerk"),
    ("builder-backend.md", "rebase only when the lead asks you to", "a rebase reaches the builder as a row from the clerk"),
    ("release-manager.md", "the lead gives the fix to a builder", "the lead decides the fix and the clerk gives it to a builder"),
    ("release-manager.md", "and gives the rebase to a builder", "the lead decides the rebase and the clerk gives it to a builder"),
    ("release-manager.md", "gives code changes to a builder", "the lead has code changes made through the clerk"),
    ("release-manager.md", "Tell the lead the pull request's link", "pull-request links go to the clerk"),
    ("peer.md", "time-limit reminder", "the clerk registers the time-limit reminder, not the lead"),
    ("peer.md", "publishes the roster", "the clerk publishes the roster, not the lead"),
    ("peer.md", "The lead does all of that", "the clerk assigns and the judge judges, not the lead"),
    # The jobs that moved to the judge.
    ("lead.md", "## Judge the proof", "the judge judges the proof"),
    ("clerk.md", "never a loop of checks", "how to wait is written once, in team-shape.md"),
    ("judge.md", "never a loop of checks", "how to wait is written once, in team-shape.md"),
    ("lead.md", "never a loop of checks", "how to wait is written once, in team-shape.md"),
    ("lead.md", "Compare the two reviews", "the judge compares the reviews"),
    ("lead.md", "Never judge without a commit", "the judge judges each slice at its commit"),
    ("lead.md", "judge the slice again", "the judge judges a fixed or rebased slice again"),
    ("lead.md", "fewest open rows", "the judge picks the release manager"),
    ("lead.md", "Tell the builder what you decided", "the judge tells the builder the lead's decision"),
    ("lead.md", "tell the builder what must change", "the judge tells the builder the lead's decision"),
    ("lead.md", "compared both PASSes", "the judge releases the review pair"),
    ("startup/review-pair-lead.md", "Compare the two reviews", "the judge compares the reviews"),
    ("startup/review-pair-lead.md", "Release the pair", "the judge releases the pair"),
    ("startup/review-pair-reviewer.md", "the lead compares", "the judge compares the pair's findings"),
    ("builder-backend.md", "## Tell the lead it's done", "the builder tells the judge a slice is ready"),
    ("qa.md", "Send the results to the builder and the lead", "QA's results go to the builder, and a NOT-CLEAR to the judge"),
    ("code-reviewer.md", "short verdict, with what you ran, to the lead", "a reviewer's verdict goes to the judge"),
    ("clerk.md", "the lead tells you it has compared", "the judge releases the review pair"),
    ("clerk.md", "the lead tells you it has judged", "the judge releases the builder and QA seat"),
    ("release-manager.md", "once the lead has judged", "the judge judges each slice"),
    ("startup/team-shape.md", "the lead gives each judged slice", "the judge picks the release manager"),
    # The pull-request description moved to the release manager.
    ("lead.md", "Keep the pull request description true", "the release manager keeps the description true"),
    ("lead.md", "You own the description", "the release manager owns the description"),
    ("lead.md", "the slice's pull-request description", "judged slices reach the release manager without a description"),
    ("lead.md", "the updated description", "the release manager updates the description itself"),
    ("lead.md", "which review ran on which model", "the release manager says which review ran on which model"),
    ("lead.md", "why the pair shared a runtime", "the release manager says why a pair shared a runtime"),
    ("release-manager.md", "comes from the lead", "the release manager writes the description"),
    ("release-manager.md", "as the lead wrote it", "the release manager writes the description"),
    ("release-manager.md", "owns scope and the description", "the lead owns scope; the description is the release manager's"),
    ("startup/review-pair-lead.md", "Pull request description:", "the release manager writes the description"),
    ("startup/slice-spec.md", "personal data", "what makes a slice risky is listed once, in settings.md"),
    ("clerk.md", "QA sends its result to the lead", "QA sends it to the release manager that asked"),
    ("release-manager.md", "QA sends the result to the lead", "QA sends it to the release manager that asked"),
    ("lead.md", "QA sends you the result", "QA sends it to the release manager that asked"),
    # The lead hears of routine slices only through the clerk, when a mission completes.
    ("judge.md", "Then tell the lead", "a routine slice puts no row on the lead's queue"),
    ("lead.md", "close it once you've read it", "a routine slice puts no row on the lead's queue"),
    ("lead.md", "tells you which one", "a routine slice puts no row on the lead's queue"),
    ("lead.md", "The judge tells you of each routine slice", "the lead hears of routine slices through the clerk"),
    ("lead.md", "release manager, telling you", "the judge doesn't tell the lead of each routine slice"),
    ("README.md", "release manager, telling the lead", "the judge doesn't tell the lead of each routine slice"),
    # The glossary's words: a spec is locked, not approved, and a model tier is not a tier.
    ("judge.md", "the lead approved", "the lead locks a spec; it doesn't approve it"),
    ("release-manager.md", "the lead approved", "the lead locks a spec; it doesn't approve it"),
    ("clerk.md", "a tier above", "a model tier, not a queue tier"),
    ("startup/team-shape.md", "a tier above", "a model tier, not a queue tier"),
    # One-runtime pairing starts and stops without the lead.
    ("clerk.md", "the lead tells you so", "the clerk sees a runtime out from rig ps"),
    ("clerk.md", "of its profile in `agents/shipwrights/agent.yaml`", "a seat moved to the other runtime has that runtime's profile"),
    ("clerk.md", "the other runtime is back", "the clerk sees a runtime back at its next pairing, without the lead"),
    ("clerk.md", "pass on to the lead", "a reviewer's usage limit doesn't wake the lead"),
    ("startup/review-pair-lead.md", "the slice waits for one to free up", "No free pair lives in team-shape.md, which the clerk reads"),
    # rig whoami prints the caller's own session, so it never gives the lead the clerk's.
    ("lead.md", "to its session (from `rig whoami", "the clerk's session comes from rig ps"),
]

# Every role, and the guidance files each of its profiles must deliver.
ROLES = {
    "lead": ["guidance/lead.md"],
    "clerk": ["guidance/clerk.md"],
    "peer": ["guidance/peer.md"],
    "planner": ["guidance/planner.md"],
    "builder-backend": ["guidance/builder-backend.md"],
    "builder-frontend": ["guidance/builder-backend.md", "guidance/builder-frontend.md"],
    "qa": ["guidance/qa.md"],
    "code-reviewer": ["guidance/code-reviewer.md"],
    "release-manager": ["guidance/release-manager.md"],
    "judge": ["guidance/judge.md"],
}
# Each runtime a seat may use, and the suffix of its profiles' names. A role has one profile per runtime, such as
# planner-claude and planner-codex, so a seat gets the model suggested for its role on whichever runtime it runs.
RUNTIMES = {"claude-code": "claude", "codex": "codex"}
# The models the README's Models section names, by model tier.
MODELS = {
    "claude-code": {
        "top": "claude-fable-5-2", "upper": "claude-opus-5-5", "workhorse": "claude-sonnet-5-5",
        "budget": "claude-haiku-5-5",
    },
    "codex": {"top": "gpt-6-astra", "workhorse": "gpt-6.1-sol", "lower": "gpt-6.1-terra", "budget": "gpt-6-luna"},
}
# The model each role's profiles suggest on each runtime, as a model tier, and their effort. Codex has no upper model
# tier, so the lead and planner take its top one there. The clerk pairs one code reviewer from each runtime, so the
# Claude reviewer is upper and the Codex one workhorse, and every pair has one of each.
class Suggested(NamedTuple):
    # Each field but effort is named for a runtime's short name in RUNTIMES, and holds a model tier in MODELS.
    claude: str
    codex: str
    effort: str

    def model(self, runtime):
        """The suggested model on a runtime. A runtime with no models, or no field here, raises."""
        return MODELS[runtime][getattr(self, RUNTIMES[runtime])]


SUGGESTED_MODEL_AND_EFFORT = {
    "lead": Suggested("upper", "top", "high"),
    "clerk": Suggested("budget", "budget", "low"),
    "peer": Suggested("budget", "budget", "low"),
    "planner": Suggested("upper", "top", "high"),
    "builder-backend": Suggested("workhorse", "workhorse", "medium"),
    "builder-frontend": Suggested("workhorse", "workhorse", "medium"),
    "qa": Suggested("workhorse", "workhorse", "medium"),
    "code-reviewer": Suggested("upper", "workhorse", "high"),
    "release-manager": Suggested("workhorse", "workhorse", "medium"),
    "judge": Suggested("workhorse", "workhorse", "medium"),
}
# Every seat the team ships and its role: pod.member in rig.yaml and configurations.yaml, and pod-member in the
# README's seat table. A role that can grow numbers its seats, so a grown seat takes the next number in its pod.
SEATS = {
    "orch.lead": "lead", "orch.peer": "peer", "orch.clerk-1": "clerk", "orch.planner-1": "planner",
    "dev.backend-1": "builder-backend", "dev.frontend-1": "builder-frontend",
    "quality.qa-1": "qa", "quality.qa-2": "qa",
    "review.reviewer-1": "code-reviewer", "review.reviewer-2": "code-reviewer", "review.judge-1": "judge",
    "release.manager-1": "release-manager",
}


def profile_name(role, runtime):
    return f"{role}-{RUNTIMES[runtime]}"


# Names the team renamed, which no file in it may still use: (pattern, what replaced it). A renamed seat needs no
# pattern here: check_seat_names catches any pod-prefixed name that is no seat.
RETIRED_NAMES = [
    # NOTICE.md still names Workshop's own guidance/builder.md, which is where ours came from.
    (r"profile: builder(?![\w-])|(?<!workshop/guidance/)(?<![\w-])builder\.md|: builder(?![\w-])", "the builder-backend profile and builder-backend.md"),
    (r"(?m)^  builder:$", "the builder-backend profile"),
    (r"(?<![\w-])backend-builder\b", "the builder-backend profile and builder-backend.md"),
    (r"(?<![\w-])frontend-builder\b", "the builder-frontend profile and builder-frontend.md"),
    # A review's proof type is rev1- and the reviewer's member id.
    (r"(?<![\w-])rev1-r\d\b", "the numbered reviewer seats' proof types, such as rev1-reviewer-1"),
    (r"(?i)fourteen seats|14 seats", "the small team's seat count"),
]
# Pods the team once used, which no seat name may start with: OpenRig's naming guide puts a role in its domain's pod,
# not a pod named for an operation.
RETIRED_PODS = {"check", "plan"}
# Words that start like a seat's name but name no seat: a role, a profile, the review-pair start files, and a mission
# status.
NOT_SEAT_NAMES = {"review-pair", "release-candidate"}
NOT_SEAT_NAMES |= set(ROLES) | {profile_name(role, runtime) for role in ROLES for runtime in RUNTIMES}
# Words GLOSSARY.md says to avoid, as (pattern, what it says instead). OpenRig's own flags, such as `--evidence` and
# `--money-evidence`, keep their names.
AVOIDED_WORDS = [
    (r"(?i)(?<![-\w])evidence\b", "proof, or what a seat ran and saw"),
]
# Lists the team keeps in one file, which every other file points to rather than repeats: (a pattern only the list
# matches, the file that holds it, what the list is). The whitespace of each file is collapsed before matching.
ONE_PLACE = [
    (r"doesn't show [^.]{0,60}directly", "startup/team-shape.md", "the slices the judge passes to the lead"),
]
# Every seat writes a retrospective note in the slice progress before closing its row.
RETRO_PHRASE = "rig scope slice progress"

# The keys `rig ps --nodes --fields` accepts (OpenRig 0.7.11, packages/cli/src/commands/ps.ts), which refuses any
# other. A seat's profile isn't one of them: `rig ps --nodes --json --full` gives it. FLAG_VALUES below uses them.
PS_NODE_FIELDS = {
    "rigId", "rigName", "logicalId", "podId", "podNamespace", "hostSelfId", "canonicalSessionName", "nodeKind",
    "runtime", "communityHarness", "launchWrapper", "model", "modelObservation", "sessionStatus",
    "intentionallyStopped", "startupStatus", "restoreOutcome", "oriented", "lifecycleState", "tmuxAttachCommand",
    "resumeCommand", "latestError", "terminalActive", "hasAssignedWork", "assignedWorkCount", "pendingWorkCount",
    "inProgressWorkCount", "blockedWorkCount", "agentActivity", "needsAttention", "arbitratedNeedsInput",
    "needsInputEvidence", "contextUsage", "heldReason", "startedWithoutRequired", "storedSessionStatus",
    "identityVerdict",
}

# The flags each `rig` command the team's text runs accepts (OpenRig 0.7.11, packages/cli/src/commands), so an example
# that would fail as written fails here. A command not listed here isn't checked.
RIG_COMMANDS = {
    "queue create": "--alert --body --body-context --body-file --destination --evidence-ref --expires-at --full --gate "
                    "--host --human-detail-file --human-intent --human-questions-file --id --json --mission --no-nudge "
                    "--priority --reply-to --slice --source --summary --tags --target-repo --tier --verify",
    "queue claim": "--destination --full --json",
    "queue update": "--actor --blocked-on --closure-reason --closure-required-at --closure-target --evidence-ref --full "
                    "--host --json --note --reopen --resolution --state --summary --wake-after --wake-watchdog",
    "queue block": "--actor --continuation --evidence-ref --full --host --json --note --on --summary --wake-after "
                   "--wake-watchdog",
    "queue resolve": "--actor --bearer --decision --json --no-notify",
    "queue handoff": "--alert --body --body-file --evidence-ref --from --full --gate --host --json --no-nudge --note "
                     "--priority --summary --tags --target-repo --tier --to",
    "queue handoff-and-complete": "--alert --body --body-file --evidence-ref --from --full --gate --host --json "
                                  "--no-nudge --note --priority --summary --tags --target-repo --tier --to",
    "queue show": "--full --host --json",
    "queue list": "--all --all-rigs --destination --full --host --json --limit --mine --owned --source --state "
                  "--target-repo",
    "queue overdue": "--all-rigs --full --json --limit --rig",
    "scope slice progress": "--add --json --mission --section --set --status",
    "scope mission progress": "--add --json --section --set --status",
    "scope slice approve": "--actor --json --locked-artifacts --mission --on-behalf-of --re-approve --reason --scope",
    "scope slice close": "--json --mission --note --reason",
    "scope slice create": "--depends-on --id --intent --json --no-mission-notes --no-notes --template --title",
    "scope mission create": "--depends-on --intent --json --readme-only --template --title",
    "scope mission graph": "--json",
    "scope mission show": "--json",
    "scope mission ls": "--json",
    "proof show": "--json --project",
    "proof judge": "--comparison --evidence --json --operation-id --project --reason --replace --revision --subject "
                   "--verdict",
    "proof add": "--artifact-type --body --candidate-sha --evidences --file --json --media --mission --money-evidence "
                 "--name --replace --self-check --slice-id --verdict",
    "seat launch": "--fresh --json --operator --plan --reason --stop",
    "seat stop": "--json --operator --reason",
    "seat status": "--json",
    "send": "--context --dangerously-interact --force --from --host --json --pod --raw --reason --rig --to "
            "--type-without-checking --urgent --verify --wait-for-idle",
    "capture": "--history-plus-pane --host --json --lines --pod --readable --rig --size",
    "watchdog register": "--active-wake-interval-seconds --interval-seconds --json --message --policy --registered-by "
                         "--requires-job --scan-interval-seconds --spec --target-session --threshold-bytes "
                         "--threshold-mb --threshold-percent --threshold-tokens --watched-file",
    "watchdog list": "--all --full --json --limit",
    "watchdog stop": "--json --reason",
    "ps": "--active --all-hosts --all-rigs --fields --filter --full --host --hosts --include-archived --json --limit "
          "--no-cleanup --nodes --resources --rig --running --session --summary --verbose",
    "remove": "--fallback --json",
    "whoami": "--all-hosts --all-peers --full --host --hosts --json --node-id --session --verbose",
}
RIG_COMMANDS = {command: set(flags.split()) for command, flags in RIG_COMMANDS.items()}
QUEUE_STATES = {"pending", "in-progress", "done", "blocked", "failed", "denied", "canceled", "handed-off"}
PROGRESS_STATUSES = {"active", "done", "blocked"}
# The values OpenRig accepts for a flag that takes a fixed set, as (command, flag): values. A comma-separated value,
# such as `--state pending,blocked` or `--fields runtime,model`, is checked one item at a time.
FLAG_VALUES = {
    ("queue update", "--state"): QUEUE_STATES,
    ("queue list", "--state"): QUEUE_STATES,
    ("queue update", "--closure-reason"): {"handed_off_to", "denied", "canceled", "no-follow-on", "escalation",
                                           "superseded"},
    ("scope slice progress", "--status"): PROGRESS_STATUSES,
    ("scope mission progress", "--status"): PROGRESS_STATUSES,
    ("proof judge", "--verdict"): {"accept", "reject", "withdraw"},
    ("proof add", "--verdict"): {"CLEAR", "BLOCKING", "CONCERNING", "PASS", "NOT-CLEAR"},
    ("watchdog register", "--policy"): {"periodic-reminder", "artifact-pool-ready", "edge-artifact-required",
                                        "workflow-keepalive", "idle-gate-qitem", "context-usage-threshold"},
    ("ps", "--fields"): PS_NODE_FIELDS,
}

SKILL_NAME = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"

# What OpenRig provides itself, which skills.md doesn't list: the Workshop skill this team
# bundles, the openrig-core plugin and its skills, the skill an OpenRig clone ships, and
# OpenRig's public context pack.
OPENRIG_SKILLS = {
    "using-the-tui-together",
    "openrig-core",
    "queue-handoff",
    "claude-compaction-restore",
    "session-compaction-and-restore",
    "orienting-to-an-inherited-seat",
    "retiring-and-inheriting-a-seat",
    "developing-openrig",
    "openrig-world",
}

# Lower-case names in backticks in the team's text that are not skills: seats, states,
# branches, proof types, and impeccable's own commands.
NOT_SKILLS = {
    # the rig, and a grown seat's name in the examples (the seats themselves are added from SEATS below)
    "shipwrights", "backend-2", "dev-backend-2",
    # the pods and the profiles
    "orch", "dev", "quality", "review", "release", "lead", "peer", "clerk", "planner", "builder-backend", "builder-frontend", "qa",
    "code-reviewer", "release-manager", "judge",
    # commands, states, tiers, branches, proof types, roster fields, and a member's model and profile fields
    "model", "rig", "gh", "cd", "routine", "deep", "running", "stopped", "recoverable", "unknown", "main",
    "planned", "active", "complete", "runtime", "profile", "release-candidate", "rev1-", "delegate", "capabilities", "why",
    # impeccable's own commands
    "shape", "critique", "audit", "polish", "harden", "typeset", "quieter", "distill", "layout", "init", "generate",
}
NOT_SKILLS |= {profile_name(role, runtime) for role in ROLES for runtime in RUNTIMES}
# Each seat by its member id (planner-1) and its name (orch-planner-1), and its reviews' proof type (rev1-reviewer-1).
NOT_SKILLS |= {seat.split(".", 1)[1] for seat in SEATS} | {seat.replace(".", "-") for seat in SEATS}
NOT_SKILLS |= {f"rev1-{seat.split('.', 1)[1]}" for seat, role in SEATS.items() if role == "code-reviewer"}


def fail(problems, message):
    problems.append(message)


def markdown(files):
    """The team's Markdown files and their text."""
    return {path: text for path, text in files.items() if path.suffix == ".md" and text is not None}


def table(text, first):
    """The rows of the Markdown table whose header's first cell is `first`, each as (line number, {column: cell}). The
    table ends at the first line that isn't a table row, so another table in the same file is never read as part of
    it."""
    rows, header = [], None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] == first:
            header = cells
        elif header and not set(cells[0]) <= set("-: "):
            rows.append((number, dict(zip(header, cells))))
    return rows


def check_names(team, problems):
    words = [word.strip() for word in os.environ.get("TEAM_BLOCKLIST", "").split(",") if word.strip()]
    if not words:
        print("not run: the blocked-words check (TEAM_BLOCKLIST is empty)")
        return
    pattern = re.compile("|".join(re.escape(word) for word in words), re.IGNORECASE)
    for path, text in team.files.items():
        if pattern.search(str(path.relative_to(team.root))):
            fail(problems, f"{path}: its path names a blocked word")
        for number, line in enumerate((text or "").splitlines(), 1):
            if pattern.search(line):
                fail(problems, f"{path}:{number}: names a blocked word")


def check_one_place(team, problems):
    """A list the team keeps in one file appears in no other, so the copies can't drift apart."""
    for pattern, home, what in ONE_PLACE:
        if not re.search(pattern, " ".join(team.text(home).split())):
            fail(problems, f"{home} no longer lists {what}")
        for path, text in markdown(team.files).items():
            if path != team.root / home and re.search(pattern, " ".join(text.split())):
                fail(problems, f"{path} repeats {what}: point to {home} instead")


def check_glossary_words(team, problems):
    """No file in the team uses a word the glossary says to avoid, other than in OpenRig's own flags."""
    for path, text in team.files.items():
        for pattern, instead in AVOIDED_WORDS:
            for number, line in enumerate((text or "").splitlines(), 1):
                for match in re.finditer(pattern, line):
                    fail(problems, f"{path}:{number}: {match.group(0)!r}: the glossary says {instead}")


def check_settings(team, problems):
    text = team.text("settings.md")
    if not text:
        fail(problems, "settings.md is missing")
        return
    rows = {}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and len(cells) >= 2:
            rows[cells[0]] = cells[1]
    for setting, default in SETTINGS.items():
        if setting not in rows:
            fail(problems, f"settings.md has no row for {setting!r}")
        elif rows[setting] != default:
            fail(problems, f"settings.md: {setting!r} defaults to {rows[setting]!r}, expected {default!r}")


def parse_agent(text):
    """An agent.yaml's declared skills, as id: path, and the skills its profiles select."""
    declared = dict(re.findall(r"-\s*\{\s*id:\s*([\w.-]+),\s*path:\s*([^\s,}]+)", text))
    selected = set()
    for items in re.findall(r"^\s*skills:\s*\[([^\]]*)\]", text, re.MULTILINE):
        selected.update(item.strip() for item in items.split(",") if item.strip())
    return declared, selected


def profile_blocks(text):
    """Each profile's own text in an agent.yaml, keyed by name, from the two-space-indented keys under `profiles:`."""
    body = text.split("\nprofiles:\n", 1)[1] if "\nprofiles:\n" in text else ""
    return dict(re.findall(r"^  ([\w-]+):\n((?:(?:    .*)?\n)*)", body, re.MULTILINE))


def read_skills_table(team, problems):
    """skills.md's rows, from the table whose header starts `| Skill |`, with their line numbers."""
    text = team.text("skills.md")
    if not text:
        fail(problems, "skills.md is missing")
        return []
    rows = table(text, "Skill")
    if not rows:
        fail(problems, "skills.md has no table of skills")
    return rows


def check_skills_table(rows, problems):
    """Each row is complete. Returns the skills listed."""
    listed = set()
    for number, row in rows:
        where = f"skills.md:{number}"
        skill = row.get("Skill", "").strip("`")
        if not re.fullmatch(SKILL_NAME, skill):
            fail(problems, f"{where}: {skill!r} is not a skill name")
        if skill in listed:
            fail(problems, f"{where}: {skill!r} is listed twice")
        listed.add(skill)
        if skill in OPENRIG_SKILLS:
            fail(problems, f"{where}: {skill!r} comes with OpenRig, so skills.md doesn't list it")
        if not re.fullmatch(r"\[([\w.-]+/[\w.-]+)\]\(https://github\.com/\1\)", row.get("Source", "")):
            fail(problems, f"{where}: {skill!r} has no source as a GitHub link")
        if not row.get("Path", "").strip("`"):
            fail(problems, f"{where}: {skill!r} has no path in its source")
        if not re.fullmatch(r"[0-9a-f]{40}", row.get("Commit", "").strip("`")):
            fail(problems, f"{where}: {skill!r} has no full commit")
        if not row.get("Licence"):
            fail(problems, f"{where}: {skill!r} has no licence")
        seats = [seat.strip().strip("`") for seat in row.get("Seats", "").split(",") if seat.strip()]
        if not seats:
            fail(problems, f"{where}: {skill!r} names no seats")
        for seat in seats:
            if seat != "all" and seat not in ROLES:
                fail(problems, f"{where}: {skill!r} names {seat!r}, which is no role")
        if row.get("Need") not in ("required", "optional"):
            fail(problems, f"{where}: {skill!r} is neither required nor optional")
    return listed


def named_in_text(team):
    """Lower-case names in backticks in the guidance, start steps, culture and settings."""
    paths = sorted(team.root.glob("agents/*/guidance/*.md")) + sorted(team.root.glob("startup/*.md"))
    return skill_names(team, paths + [team.root / "CULTURE.md", team.root / "settings.md"])


def check_guidance_skills(team, rows, listed, problems):
    """A skill the text names is in skills.md as required; one it doesn't name is optional."""
    named = named_in_text(team)
    for name, where in sorted(named.items()):
        if name not in listed | OPENRIG_SKILLS | NOT_SKILLS:
            fail(problems, f"{where} names `{name}`: list it in skills.md, or add it to NOT_SKILLS if it isn't a skill")
    for number, row in rows:
        skill = row.get("Skill", "").strip("`")
        if row.get("Need") == "required" and skill not in named:
            fail(problems, f"skills.md:{number}: {skill!r} is required, but the guidance never names it")
        if row.get("Need") == "optional" and skill in named:
            fail(problems, f"skills.md:{number}: {skill!r} is optional, but {named[skill]} names it")


class Seat(NamedTuple):
    fields: dict  # its one-line keys, such as profile and runtime
    files: list  # its own start files


class Rig(NamedTuple):
    shared: list  # the start files every seat gets
    seats: dict  # pod.member: Seat, in rig.yaml's order
    edges: list  # (kind, source, target), with a pod's own edges named pod.member


def parse_rig(text):
    """rig.yaml's start files, seats and edges, read by indentation: a top-level key at column 0, a pod at 2 (`- id`),
    its `members:` and `edges:` at 4, a member at 6 (`- id`) and the member's keys at 8. Standard library only, so no
    YAML parser: this holds because the team writes rig.yaml in that one layout."""
    shared, seats, edges = [], {}, []
    section, pod, part, seat, edge = None, None, None, None, None
    for line in text.splitlines():
        if m := re.match(r"^(\w+):", line):
            section, pod, part, seat, edge = m.group(1), None, None, None, None
        elif section == "pods" and (m := re.match(r"^  - id: ([\w-]+)$", line)):
            pod, part, seat = m.group(1), None, None
        elif pod and (m := re.match(r"^    (\w+):", line)):
            part, seat = m.group(1), None
        elif part == "members" and (m := re.match(r"^      - id: ([\w-]+)$", line)):
            seat = f"{pod}.{m.group(1)}"
            seats[seat] = Seat({}, [])
        elif seat and (m := re.match(r"^        (\w+): (\S.*)$", line)):
            seats[seat].fields[m.group(1)] = m.group(2).strip('"')
        elif m := re.match(r"^\s+- path: (\S+)$", line):
            if seat:
                seats[seat].files.append(m.group(1))
            elif section == "startup":
                shared.append(m.group(1))
        elif (section == "edges" or part == "edges") and (m := re.match(r"^\s+- kind: (\w+)$", line)):
            edge = {"kind": m.group(1)}
        elif edge is not None and (m := re.match(r"^\s+(from|to): (\S+)$", line)):
            edge[m.group(1)] = f"{pod}.{m.group(2)}" if part == "edges" else m.group(2)
            if "from" in edge and "to" in edge:
                edges.append((edge["kind"], edge["from"], edge["to"]))
                edge = None
    return Rig(shared, seats, edges)


class Team(NamedTuple):
    """The team folder, read once: each file's text, rig.yaml parsed, and every profile's own text."""
    root: Path
    files: dict  # path: its text, or None for a file that isn't UTF-8 text
    rig: Rig
    profiles: dict  # profile name: its own text, from every agent.yaml

    def text(self, name):
        """The text of a file by its path in the team folder, or "" when there is none, so a missing file fails the
        checks that need it."""
        return self.files.get(self.root / name) or ""

    def texts(self, pattern):
        """The text of each file matching a glob in the team folder, by path."""
        return {path: self.files[path] for path in sorted(self.root.glob(pattern)) if self.files.get(path) is not None}


def read_team(root):
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                files[path] = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                files[path] = None
    profiles = {}
    for agent_yaml in sorted(root.glob("agents/*/agent.yaml")):
        profiles.update(profile_blocks(files.get(agent_yaml) or ""))
    return Team(root, files, parse_rig(files.get(root / "rig.yaml") or ""), profiles)


def skill_names(team, paths):
    """The lower-case names in backticks in these files, each with the first file that names it."""
    named = {}
    for path in paths:
        for name in re.findall(rf"`({SKILL_NAME})`", team.files.get(path) or ""):
            named.setdefault(name, path.name)
    return named


def check_skill_seats(team, rows, problems):
    """Each required skill's Seats are exactly the roles whose own files name it.

    A role's own files are its guidance and its seats' start files. A role listed also passes when a start file every
    seat gets names the skill, and `all` passes when one of those or CULTURE.md does; CULTURE.md doesn't count for a
    single role, because it names skills only as examples.
    """
    agent_dirs = [path.parent for path in sorted(team.root.glob("agents/*/agent.yaml"))]
    rig = team.rig
    everyone = skill_names(team, [team.root / path for path in rig.shared])
    by_role = {
        role: skill_names(team, [folder / path for folder in agent_dirs for path in guidance]
                          + [team.root / path for seat, seat_role in SEATS.items() if seat_role == role
                             for path in (rig.seats[seat].files if seat in rig.seats else [])])
        for role, guidance in ROLES.items()
    }
    for number, row in rows:
        skill = row.get("Skill", "").strip("`")
        seats = {seat.strip().strip("`") for seat in row.get("Seats", "").split(",") if seat.strip()}
        if row.get("Need") != "required":
            continue
        for seat in sorted(seats):
            if seat == "all":
                if skill not in everyone and skill not in skill_names(team, [team.root / "CULTURE.md"]):
                    fail(problems, f"skills.md:{number}: {skill!r} lists all, but nothing every seat reads names it")
            elif seat in by_role and skill not in by_role[seat] and skill not in everyone:
                fail(problems, f"skills.md:{number}: {skill!r} lists {seat}, but nothing the {seat} reads names it")
        for role, named in sorted(by_role.items()):
            if skill in named and not seats & {role, "all"}:
                fail(problems, f"skills.md:{number}: {skill!r} doesn't list {role}, though {named[skill]} names it")


def check_install_script(team, listed, problems):
    """install-skills.sh reads skills.md: a dry run into empty folders installs every row and writes nothing."""
    script = team.root / "install-skills.sh"
    if not script.is_file():
        fail(problems, f"{script} is missing")
        return
    with tempfile.TemporaryDirectory() as home:
        claude, codex = Path(home, "claude"), Path(home, "codex")
        env = dict(os.environ, HOME=home, CLAUDE_CONFIG_DIR=str(claude), CODEX_HOME=str(codex))
        result = subprocess.run(["bash", str(script), "--dry-run"], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            fail(problems, f"install-skills.sh --dry-run exited {result.returncode}: {result.stderr.strip()}")
            return
        for skill in sorted(listed):
            for folder in (claude / "skills" / skill, codex / "skills" / skill):
                if f"would install {skill} " not in result.stdout or str(folder) not in result.stdout:
                    fail(problems, f"install-skills.sh --dry-run doesn't install {skill!r} into {folder}")
        if any(Path(home).iterdir()):
            fail(problems, "install-skills.sh --dry-run wrote files")


def check_bundle_skills(team, listed, problems):
    """Profiles select only skills that ship in the team folder, and none skills.md lists."""
    agents = team.texts("agents/*/agent.yaml")
    if not agents:
        fail(problems, f"{team.root} has no agents/*/agent.yaml")
        return
    for agent_yaml, text in agents.items():
        declared, selected = parse_agent(text)
        for skill in sorted(selected - declared.keys()):
            fail(problems, f"{agent_yaml}: a profile selects {skill!r}, which no skill resource in the team declares")
        for skill, rel in sorted(declared.items()):
            folder = (agent_yaml.parent / rel).resolve()
            if not folder.is_relative_to(team.root.resolve()):
                fail(problems, f"{agent_yaml}: {skill!r} is outside the team folder")
            elif not (folder / "SKILL.md").is_file():
                fail(problems, f"{folder}: no SKILL.md")
            if skill in listed:
                fail(problems, f"{agent_yaml}: ships {skill!r}, which skills.md says the person installs")
    for leftover in ("skills.lock", "skills.sources"):
        if (team.root / leftover).exists():
            fail(problems, f"{team.root / leftover}: the team no longer pins vendored skills")


def check_skills(team, problems):
    rows = read_skills_table(team, problems)
    listed = check_skills_table(rows, problems)
    check_guidance_skills(team, rows, listed, problems)
    check_skill_seats(team, rows, problems)
    check_install_script(team, listed, problems)
    check_bundle_skills(team, listed, problems)


def check_guidance(team, problems):
    # Whitespace is collapsed, so a phrase still matches where the text wraps it.
    guidance = {path.name: " ".join(text.split()) for path, text in team.texts("agents/*/guidance/*.md").items()}
    # Start files carry rules too, but no retrospective of their own, so they join only the rule checks.
    started = {f"startup/{path.name}": " ".join(text.split()) for path, text in team.texts("startup/*.md").items()}
    # The team's own docs, such as README.md and settings.md, carry rules too, for the person and for every seat.
    docs = {path.name: " ".join(text.split()) for path, text in team.texts("*.md").items()}

    def lookup(name):
        """Where a rule's file is, for messages, and its text, or None when there is no such file."""
        for where, texts in ((name, started), (f"guidance/{name}", guidance), (name, docs)):
            if name in texts:
                return where, texts[name]
        return name, None

    for name, phrase, why in GUIDANCE_RULES:
        where, text = lookup(name)
        if text is None:
            fail(problems, f"{where} is missing")
        elif phrase not in text:
            fail(problems, f"{where} lacks {phrase!r}: {why}")
    for name, phrase, why in FORBIDDEN_RULES:
        where, text = lookup(name)
        if phrase in (text or ""):
            fail(problems, f"{where} still has {phrase!r}: {why}")
    # OpenRig refuses a block without --on, even with a wake, so every example names its blocker straight after the
    # row (a `\` line break may come between). The text's whitespace is collapsed, so a command is one line here, and
    # the 40 characters after the row are only there to show which example it is.
    texts = {**{f"guidance/{name}": text for name, text in guidance.items()}, **started}
    for where, text in sorted(texts.items()):
        for command in re.findall(r"rig queue block <[^>]+>(?! (?:\\ )?--on )[^`]{0,40}", text):
            fail(problems, f"{where}: {command!r} has no --on: rig queue block requires a blocker")
    for name, text in sorted(guidance.items()):
        if RETRO_PHRASE not in text:
            fail(problems, f"guidance/{name} lacks {RETRO_PHRASE!r}: every seat writes a retrospective note")


def rig_commands(text):
    """Each `rig` command in a Markdown text: a line of a code block, with its `\\` continuations joined, or a span in
    backticks, which may wrap across lines."""
    commands, prose, in_block, joined = [], [], False, ""
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_block, joined = not in_block, ""
            continue
        if not in_block:
            prose.append(line)
            continue
        joined += line.strip()
        if joined.endswith("\\"):
            joined = joined[:-1] + " "
            continue
        if joined.startswith("rig "):
            commands.append(joined)
        joined = ""
    commands += re.findall(r"`(rig [^`]+)`", " ".join(" ".join(prose).split()))
    return commands


def check_commands(team, problems):
    """Every `rig` command in the team's text uses only flags OpenRig accepts for it, and only the values it accepts for
    a flag that takes a fixed set, so no example fails as written. A placeholder such as `<state>` isn't checked."""
    for path, text in markdown(team.files).items():
        for command in rig_commands(text):
            # A quoted string and a <placeholder> are one word each, though they may hold spaces.
            words = re.findall(r'"[^"]*"|<[^>]*>|\S+', command)[1:]
            name = next((" ".join(words[:n]) for n in (3, 2, 1) if " ".join(words[:n]) in RIG_COMMANDS), None)
            if name is None:
                continue
            for i, word in enumerate(words):
                if not word.startswith("--"):
                    continue
                # A value may follow the flag as the next word, or after an = in the same one.
                flag, joined, value = word.partition("=")
                if flag not in RIG_COMMANDS[name]:
                    fail(problems, f"{path}: `rig {name}` has no {flag} flag, so `{command}` fails")
                    continue
                allowed = FLAG_VALUES.get((name, flag))
                if not joined:
                    value = words[i + 1] if i + 1 < len(words) else ""
                if allowed is None or not value or value.startswith(("--", "<")):
                    continue
                for item in value.strip('"').split(","):
                    if item not in allowed:
                        fail(problems, f"{path}: `rig {name} {flag}` doesn't take {item!r} "
                                       f"(it takes {', '.join(sorted(allowed))}), so `{command}` fails")


def check_profiles(team, problems):
    """Each role has one profile per runtime, with the role's guidance and the model and effort suggested for it."""
    blocks = team.profiles
    wanted = {profile_name(role, runtime): (role, runtime) for role in ROLES for runtime in RUNTIMES}
    for profile in sorted(blocks.keys() - wanted.keys()):
        fail(problems, f"agent.yaml's {profile!r} profile is no role's profile for a runtime: name it <role>-<runtime>")
    for profile, (role, runtime) in wanted.items():
        block = blocks.get(profile)
        if block is None:
            fail(problems, f"agent.yaml has no {profile!r} profile: the {role!r} role needs one for {runtime}")
            continue
        for path in ROLES[role]:
            if f"path: {path}" not in block:
                fail(problems, f"the {profile!r} profile doesn't deliver {path}")
        for path in sorted(set(re.findall(r"path: (guidance/\S+)", block)) - set(ROLES[role])):
            fail(problems, f"the {profile!r} profile delivers {path}, which isn't the {role!r} role's guidance")
        preferences = dict(re.findall(r"^      (runtime|model|effort):\s*(\S+)", block, re.MULTILINE))
        suggested = SUGGESTED_MODEL_AND_EFFORT[role]
        for key, value in (("runtime", runtime), ("model", suggested.model(runtime)), ("effort", suggested.effort)):
            if preferences.get(key) != value:
                fail(problems, f"the {profile!r} profile's preferences.{key} is {preferences.get(key)!r}, expected {value!r}")
    readme = team.text("README.md")
    section = re.search(r"^## Models\n(.*?)(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL)
    if not section:
        fail(problems, "README.md has no Models section")
        return
    for model in sorted({model for tiers in MODELS.values() for model in tiers.values()}):
        if f"`{model}`" not in section.group(1):
            fail(problems, f"README.md's Models section doesn't name `{model}`")
    if "override" not in section.group(1):
        fail(problems, "README.md's Models section doesn't say a rig may override a seat's model")


def check_review_runtimes(team, problems):
    """A review pair is two code reviewers on different runtimes, so the recommended preset seats them on two."""
    preset = re.search(r"^\s*recommended:\s*\{([^}]*)\}", team.text("configurations.yaml"), re.MULTILINE)
    picks = dict(re.findall(r"([\w.-]+):\s*([\w-]+)", preset.group(1))) if preset else {}
    reviewers = {picks.get(seat) for seat, role in SEATS.items() if role == "code-reviewer"} - {None}
    if len(reviewers) < 2:
        fail(problems, "configurations.yaml's recommended preset puts the code reviewers on "
                       f"{sorted(reviewers) or 'no runtime'}: a review pair needs two runtimes")


def check_members(team, problems):
    """rig.yaml declares exactly the seats in SEATS, each with its role's profile for the runtime it runs on."""
    declared = {seat: member.fields for seat, member in team.rig.seats.items()}
    for seat in sorted(declared.keys() - SEATS.keys()):
        fail(problems, f"rig.yaml declares {seat!r}, which the team doesn't ship: add it to SEATS, or remove it")
    for seat, role in SEATS.items():
        fields = declared.get(seat)
        runtime = (fields or {}).get("runtime")
        if fields is None:
            fail(problems, f"rig.yaml has no member {seat.split('.', 1)[1]!r} in its pod")
        elif runtime not in RUNTIMES:
            fail(problems, f"rig.yaml's {seat!r} runs on {runtime!r}, which is none of {sorted(RUNTIMES)}")
        elif fields.get("profile") != profile_name(role, runtime):
            fail(problems, f"rig.yaml's {seat!r} has the {fields.get('profile')!r} profile, "
                           f"expected {profile_name(role, runtime)!r} for the {role!r} role on {runtime}")


def check_notice(team, problems):
    """NOTICE.md's rows for rig.yaml and agent.yaml say what the team added: every seat and every role's profiles."""
    rows = {}
    for line in team.text("NOTICE.md").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 3:
            rows[cells[0]] = cells[2]
    seats_row, agent_row = rows.get("`rig.yaml`", ""), rows.get("`agents/shipwrights/agent.yaml`", "")
    for seat in SEATS:
        if f"`{seat}`" not in seats_row:
            fail(problems, f"NOTICE.md's rig.yaml row doesn't name the {seat!r} seat")
    for role in ROLES:
        if f"`{role}`" not in agent_row:
            fail(problems, f"NOTICE.md's agent.yaml row doesn't name the {role!r} role's profiles")


def check_summary(team, problems):
    """rig.yaml's summary, which `rig bundle` listings show, says what the README's seat table does about the peer."""
    block = re.search(r"^summary: >\n((?:  .*\n)+)", team.text("rig.yaml"), re.MULTILINE)
    summary = " ".join(block.group(1).split()) if block else ""
    if not re.search(r"a peer [^,]*on either runtime", summary):
        fail(problems, "rig.yaml's summary doesn't say the peer may run on either runtime")


def check_seat_table(team, problems):
    """The README's seat table names every seat the team ships."""
    readme = team.text("README.md")
    for seat in SEATS:
        name = seat.replace(".", "-")
        if not re.search(rf"^\|.*`{re.escape(name)}`.*\|", readme, re.MULTILINE):
            fail(problems, f"README.md's seat table doesn't name {name!r}")


def check_configurations(team, problems):
    """configurations.yaml maps each seat on each runtime to its role's profile there, and offers no other runtime."""
    configured = team.text("configurations.yaml")
    offered = {
        seat: dict(re.findall(r"([\w-]+):\s*([\w-]+)", runtimes))
        for seat, runtimes in re.findall(r"^  ([\w.-]+):\s*\{\s*runtimes:\s*\{([^}]*)\}", configured, re.MULTILINE)
    }
    for seat, role in SEATS.items():
        runtimes = offered.get(seat, {})
        for runtime in RUNTIMES:
            if runtimes.get(runtime) != profile_name(role, runtime):
                fail(problems, f"configurations.yaml maps {seat!r} on {runtime} to {runtimes.get(runtime)!r}, "
                               f"expected {profile_name(role, runtime)!r}")
        for runtime in sorted(runtimes.keys() - RUNTIMES.keys()):
            fail(problems, f"configurations.yaml offers {seat!r} {runtime!r}, which the team has no profiles for")


def check_retired_names(team, problems):
    """No file in the team still uses a name the team renamed."""
    for path, text in team.files.items():
        for pattern, replacement in RETIRED_NAMES:
            for match in re.finditer(pattern, text or ""):
                line = text.count("\n", 0, match.start()) + 1
                fail(problems, f"{path}:{line}: {match.group(0)!r} was renamed to {replacement}")


def seat_names():
    """Each pod's seat names: every seat's member id, and for a numbered one the pattern its grown seats follow."""
    names = {}
    for seat in SEATS:
        pod, member = seat.split(".", 1)
        names.setdefault(pod, []).append(re.escape(member))
        if numbered := re.fullmatch(r"(.+)-\d+", member):
            names[pod].append(rf"{re.escape(numbered.group(1))}-\d+")
    return {pod: re.compile("|".join(members)) for pod, members in names.items()}


def check_seat_names(team, problems):
    """Every name in the team's files that starts with a pod, such as dev.backend-1 or dev-backend-1, names a seat the
    team ships or a grown seat numbered as its role's seats are, so a seat renamed or misspelled anywhere is caught.
    A role or profile shares a pod's words only in its dashed form (release-manager), so a dotted name, or a session's
    name (such as `orch-lead@<rig>`), must be a seat's."""
    pods = seat_names()
    pattern = re.compile(rf"(?<![\w/.@-])({'|'.join(sorted(pods.keys() | RETIRED_PODS))})([.-])([a-z][\w-]*\w)(@?)")
    for path, text in team.files.items():
        for match in pattern.finditer(text or ""):
            pod, separator, member, session = match.groups()
            name = f"{pod}-{member}"
            if pod in pods and pods[pod].fullmatch(member):
                continue
            if separator == "-" and not session and any(name == word or name.startswith(f"{word}-") for word in NOT_SEAT_NAMES):
                continue
            line = text.count("\n", 0, match.start()) + 1
            fail(problems, f"{path}:{line}: {match.group(0)!r} is no seat the team ships: name one in SEATS, such as "
                           f"{next(iter(SEATS))!r}, or a grown seat numbered as its role's are")


# The columns startup/team-shape.md's table fills for every role: whether it can grow, and how far it can shrink.
SHAPE_COLUMNS = ["Can grow", "Fewest seats"]

LEAD = "orch.lead"
# The peer watches the lead and relaunches it when it is down, so its rows mustn't escalate to the lead: with no
# orchestrator, OpenRig sends them to its kernel operator instead.
PEER = "orch.peer"


def check_team_shape(team, problems):
    """startup/team-shape.md is the one place that says which roles can grow or shrink, so it names every profile, and
    its table of roles, whose header starts `| Role |`, gives every role whether it can grow and the fewest seats it
    can shrink to."""
    text = team.text("startup/team-shape.md")
    if not text:
        fail(problems, "startup/team-shape.md is missing")
        return
    for profile in team.profiles:
        if f"`{profile}`" not in text:
            fail(problems, f"startup/team-shape.md doesn't name the {profile!r} profile")
    roles = table(text, "Role")
    if not roles:
        fail(problems, "startup/team-shape.md has no table of roles")
    for number, row in roles:
        for column in SHAPE_COLUMNS:
            if not row.get(column):
                fail(problems, f"startup/team-shape.md:{number}: the table gives the {row['Role']!r} role no {column!r}")


def check_delegation(team, problems):
    """The lead is every other seat's orchestrator, so every stuck queue row escalates to it.

    OpenRig makes the source of a seat's delegates_to edge its orchestrator, and picks the latest-launched one when
    there are several, so a second source would quietly take the lead's place.
    """
    rig = team.rig
    sources = {}
    for kind, source, target in rig.edges:
        if kind == "delegates_to":
            sources.setdefault(target, []).append(source)
        elif kind == "can_observe" and source == PEER and target != LEAD:
            fail(problems, f"rig.yaml: {PEER} observes {target}: it watches only the lead")
    for seat in rig.seats:
        got = sources.get(seat, [])
        if seat in (LEAD, PEER):
            if got:
                fail(problems, f"rig.yaml: {', '.join(got)} delegates to {seat}, which nothing should")
        elif got != [LEAD]:
            fail(problems, f"rig.yaml: {seat}'s delegates_to sources are {got or 'none'}; it needs {LEAD} alone, "
                           "so its stuck rows escalate to the lead")


def check_bundle(team, problems):
    rig = shutil.which("rig")
    if rig is None:
        print("not run: rig bundle check (rig isn't installed here)")
        return
    result = subprocess.run([rig, "bundle", "check", str(team.root)], capture_output=True, text=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        fail(problems, f"rig bundle check exited {result.returncode}: {result.stderr.strip()}")


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    team = read_team(Path(sys.argv[1]))
    problems = []
    check_names(team, problems)
    check_glossary_words(team, problems)
    check_one_place(team, problems)
    check_settings(team, problems)
    check_skills(team, problems)
    check_guidance(team, problems)
    check_commands(team, problems)
    check_profiles(team, problems)
    check_review_runtimes(team, problems)
    check_members(team, problems)
    check_summary(team, problems)
    check_notice(team, problems)
    check_seat_table(team, problems)
    check_configurations(team, problems)
    check_retired_names(team, problems)
    check_seat_names(team, problems)
    check_team_shape(team, problems)
    check_delegation(team, problems)
    check_bundle(team, problems)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{team.root}: {'ok' if not problems else f'{len(problems)} problems'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
