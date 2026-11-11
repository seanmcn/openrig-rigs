#!/usr/bin/env python3
"""Checks a team folder the way its README promises, beyond what `rig bundle check` covers.

usage: scripts/check-team.py rigs/<team>

- nothing in the team names a word from TEAM_BLOCKLIST, a comma-separated list in the
  environment (such as the people or organisation a team was first built for), case-insensitively;
- settings.md holds the team settings with their defaults;
- the team ships no third-party skills: every skill a profile selects is declared, and
  every declared skill sits inside the team folder with its SKILL.md;
- skills.md lists every skill the guidance names, each row with a source, a full commit,
  a licence, the profiles that use it and whether it is required, and install-skills.sh
  reads it (a dry run, into empty folders);
- the role guidance carries the rules the team relies on, and none it has dropped, every
  `rig queue block` example names its `--on` blocker, and every
  role file has its seat add a retrospective note to the slice progress;
- every role in ROLES has one profile per runtime in RUNTIMES, named <role>-<runtime>, each
  delivering the role's guidance and no other, and setting preferences.runtime, the model SUGGESTED for the role
  on that runtime and its effort; agent.yaml has no other profiles; the README's Models section
  names every model the tiers list and says a rig may override a seat's model;
- rig.yaml declares exactly the seats in SEATS, each a member whose profile is its role's for the
  member's runtime, with each runtime in configurations.yaml mapped to the role's profile there,
  and a row in the README's seat table; the recommended preset keeps the code reviewers on two
  runtimes; and the old names are gone;
- startup/team-shape.md names every profile in agent.yaml, so each role says whether it can grow,
  and says how a grown seat is numbered and added to a running rig;
- the lead is the orchestrator (the only delegates_to source) of every seat but itself and its
  peer in rig.yaml, so every stuck queue row escalates to it;
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


SETTINGS = {
    "Disagreement rounds before the person is asked": "2",
    "Confirm each triage result with the person": "off",
    "Slice time limit": "4 working hours",
    "One-runtime review pairs while a runtime is out": "off",
    "Risky slices": "`risky: true` in the spec",
}

# (guidance file, or startup/<file>, phrase it must contain, why)
GUIDANCE_RULES = [
    ("clerk.md", "rig watchdog register", "the slice time limit wakes the clerk through a watchdog"),
    ("lead.md", "## Stop and pause", "stop and pause hold work without stopping sessions"),
    ("lead.md", "--wake-after", "waits are queue blocks with a wake"),
    ("judge.md", "--subject commit:<sha>", "the judge judges proof at the commit it checked"),
    ("judge.md", "Never judge without a commit", "a judgement always names a commit"),
    ("judge.md", "judge the slice again", "a rebase that changes the code needs a new judgement"),
    ("startup/team-shape.md", "## Which seats a slice holds", "the clerk assigns every seat a slice uses, from free seats"),
    ("startup/team-shape.md", "The clerk is the only role that assigns seats", "two seats never assign the same free seat"),
    ("startup/team-shape.md", "two free code reviewers on different", "a review pair is two code reviewers on different runtimes"),
    ("startup/team-shape.md", "One-runtime review pairs while a runtime is out", "a pair may share a runtime only under the setting"),
    ("startup/team-shape.md", "two different models, one a tier above the builder's", "a one-runtime pair keeps the review independent of the builder's model"),
    ("startup/review-pair-lead.md", "One-runtime review pairs while a runtime is out", "with the setting off, No free pair works as before"),
    ("startup/team-shape.md", "rig seat launch <seat> --fresh", "worker seats start fresh for each piece of work"),
    ("startup/team-shape.md", "context-usage-threshold", "long-lived seats hand over at a context threshold"),
    ("startup/team-shape.md", "the next number in its role's pod", "a grown seat takes the next number in its pod"),
    ("startup/team-shape.md", "the same profile", "a grown seat keeps its role's profile"),
    ("startup/team-shape.md", "the role's edges", "a grown seat gets its role's edges"),
    ("startup/team-shape.md", "`rig add`", "a running rig grows a pod with rig add"),
    ("startup/team-shape.md", "`rig expand`", "a running rig gains a pod with rig expand"),
    ("startup/team-shape.md", "`rig grow` adds only OpenRig's default agent", "rig grow would drop the role and its model"),
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
    ("planner.md", "rig queue handoff", "the planner's hand-off is linked, so its closed row has a successor"),
    ("planner.md", "subagent on a cheaper model", "the planner hands reading-heavy side tasks to a cheaper subagent"),
    # The clerk does the lead's routine coordination by fixed rules, and passes anything else to the lead.
    ("clerk.md", "When you are unsure, hand it to the lead", "the clerk's first rule: a budget model never guesses"),
    ("clerk.md", "You never decide", "the clerk applies rules; judgement stays with the lead"),
    ("clerk.md", "to a free planner", "the clerk routes each goal, re-cut, survey and question to a free planner"),
    ("clerk.md", "once the lead has locked its spec", "the clerk hands a slice on only after the lead locks its spec"),
    ("clerk.md", "--tier", "each build row carries the tier for the slice time limit"),
    ("clerk.md", "two free code reviewers on different runtimes", "the clerk names the review pair"),
    # With the setting on, a review pair may share a runtime while the other runtime is out.
    ("clerk.md", "One-runtime review pairs while a runtime is out", "the clerk reads the one-runtime pairing setting"),
    ("clerk.md", "no reviewer on the other runtime has room", "a pair shares a runtime only while the other runtime is out"),
    ("clerk.md", "different models", "a one-runtime pair runs two different models"),
    ("clerk.md", "a tier above the builder's", "a one-runtime pair keeps one review stronger than the builder's model"),
    ("clerk.md", "preferences.model", "the clerk reads a seat's model from its member or its profile"),
    ("clerk.md", "\"Models\"", "the clerk takes a model's tier from the README's tier table"),
    ("clerk.md", "one of each again", "new pairs go back to both runtimes once the other has room"),
    ("clerk.md", "--add \"Review pair: <reviewer> (<runtime>, <model>)", "the clerk records each pair's models on the slice"),
    ("clerk.md", "shared <runtime>: <other runtime> is out", "the clerk records why a pair shared a runtime"),
    ("clerk.md", "rig seat launch <seat> --fresh", "the clerk relaunches each freed seat fresh"),
    ("clerk.md", "## Publish the team's roster", "the clerk publishes the roster"),
    ("clerk.md", "## Keep the roster current", "the clerk keeps the roster current"),
    ("clerk.md", "rig queue overdue", "the clerk checks for builds past the slice time limit"),
    ("clerk.md", "Only a build past the limit goes to the lead", "the time-limit reminder wakes the lead only for overdue builds"),
    ("clerk.md", "--status complete", "the clerk records a mission's completion"),
    ("clerk.md", "Tell the lead only when a mission is complete", "a delivered slice doesn't wake the lead"),
    ("clerk.md", "metadata.status", "the clerk sets a mission active when its first slice is handed on"),
    ("lead.md", "## What the clerk does", "the lead knows which jobs the clerk does and what it passes back"),
    ("startup/lead-first-move.md", "to the clerk", "the lead sends a goal to the clerk to route to a planner"),
    ("startup/review-pair-lead.md", "the clerk", "the clerk names and releases the review pair"),
    ("builder-backend.md", "ask the clerk for the slice's review pair", "the builder asks the clerk, not the lead, for a pair"),
    ("planner.md", "from the clerk", "the clerk routes work to the planner"),
    ("release-manager.md", "tell the clerk the slice is delivered", "delivery reports go to the clerk, not the lead"),
    # The judge judges each slice from the record, and passes only the hard or risky ones to the lead.
    ("judge.md", "the spec and proof contract the lead locked", "the judge judges against the criteria the lead approved"),
    ("judge.md", "## Compare the reviews", "the judge compares the pair's reviews"),
    ("judge.md", "Disagreement rounds before the person is asked", "the judge reads the disagreement-rounds setting"),
    ("judge.md", "## Pass it to the lead", "the judge passes the hard or risky slices to the lead"),
    ("judge.md", "still not settled after one fix round", "a disagreement that survives a fix round goes to the lead"),
    ("judge.md", "QA records NOT-CLEAR", "a NOT-CLEAR goes to the lead"),
    ("judge.md", "has no direct evidence", "a proof item without direct evidence goes to the lead"),
    ("judge.md", "the slice is marked risky", "a risky slice goes to the lead"),
    ("judge.md", "Risky slices", "the judge reads how the rig marks a slice risky"),
    ("judge.md", "straight to a release manager", "a routine judged slice never waits for the lead"),
    ("judge.md", "tell the lead", "the lead hears of each routine slice the judge sends on"),
    ("judge.md", "tell the clerk", "the judge releases the seats through the clerk"),
    ("judge.md", "You never decide", "scope, the person and the hard cases stay with the lead"),
    ("startup/review-pair-judge.md", "Compare the two reviews", "the judge compares the pair's reviews"),
    ("startup/review-pair-judge.md", "Release the pair", "the judge releases the pair through the clerk"),
    ("startup/slice-spec.md", "`risky: true`", "the default way a slice is marked risky"),
    ("planner.md", "`risky: true`", "the planner marks a risky slice in its spec"),
    ("lead.md", "## Slices the judge passes you", "the lead decides the slices the judge passes it"),
    ("lead.md", "## Overrule the judge", "the lead keeps the last word"),
    ("lead.md", "with your reason", "the lead overrules only with a reason"),
    ("builder-backend.md", "## Tell the judge it's done", "the builder tells the judge, not the lead, that a slice is ready"),
    ("qa.md", "to the judge", "QA's NOT-CLEAR reaches the lead through the judge"),
    ("code-reviewer.md", "to the judge", "a reviewer's verdict goes to the judge"),
    ("startup/review-pair-reviewer.md", "the judge compares", "the judge compares the pair's findings"),
    ("clerk.md", "the judge tells you it has compared both PASSes", "the judge releases the review pair"),
    ("clerk.md", "the judge tells you it has judged the slice", "the judge releases the builder and QA seat"),
    ("release-manager.md", "from the judge", "the release manager takes judged slices from the judge"),
    ("startup/team-shape.md", "the judge gives each judged slice", "the judge picks the release manager"),
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
]

# (guidance file, phrase it must not contain, why)
FORBIDDEN_RULES = [
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
    ("lead.md", "## Free the seats", "the clerk frees and relaunches seats"),
    ("lead.md", "relaunch <seat>", "the clerk relaunches freed seats"),
    ("lead.md", "metadata.status", "the clerk sets a mission active"),
    ("lead.md", "--status complete", "the clerk records a mission's completion"),
    ("startup/lead-first-move.md", "to a free planner", "the clerk routes work to a planner"),
    ("startup/review-pair-lead.md", "which you name for each slice", "the clerk names the review pair"),
    ("startup/team-shape.md", "the lead relaunches it", "the clerk relaunches freed seats"),
    ("release-manager.md", "tell the lead the slice is delivered", "delivery reports go to the clerk"),
    ("peer.md", "time-limit reminder", "the clerk registers the time-limit reminder, not the lead"),
    ("peer.md", "publishes the roster", "the clerk publishes the roster, not the lead"),
    # The jobs that moved to the judge.
    ("lead.md", "## Judge the proof", "the judge judges the proof"),
    ("lead.md", "Compare the two reviews", "the judge compares the reviews"),
    ("lead.md", "Never judge without a commit", "the judge judges each slice at its commit"),
    ("lead.md", "judge the slice again", "the judge judges a fixed or rebased slice again"),
    ("lead.md", "fewest open rows", "the judge picks the release manager"),
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
# The models the README's Models section names, by tier.
CLAUDE = {"top": "claude-fable-5-2", "upper": "claude-opus-5-5", "workhorse": "claude-sonnet-5-5", "budget": "claude-haiku-5-5"}
CODEX = {"top": "gpt-6-astra", "workhorse": "gpt-6.1-sol", "lower": "gpt-6.1-terra", "budget": "gpt-6-luna"}
# The model each role's profiles suggest on each runtime, and their effort. Codex has no upper tier, so the lead and
# planner take its top one there. The lead pairs one code reviewer from each runtime, so the Claude reviewer is upper
# and the Codex one workhorse, and every pair has one of each.
SUGGESTED = {
    "lead": ({"claude-code": CLAUDE["upper"], "codex": CODEX["top"]}, "high"),
    "clerk": ({"claude-code": CLAUDE["budget"], "codex": CODEX["budget"]}, "low"),
    "peer": ({"claude-code": CLAUDE["budget"], "codex": CODEX["budget"]}, "low"),
    "planner": ({"claude-code": CLAUDE["upper"], "codex": CODEX["top"]}, "high"),
    "builder-backend": ({"claude-code": CLAUDE["workhorse"], "codex": CODEX["workhorse"]}, "medium"),
    "builder-frontend": ({"claude-code": CLAUDE["workhorse"], "codex": CODEX["workhorse"]}, "medium"),
    "qa": ({"claude-code": CLAUDE["workhorse"], "codex": CODEX["workhorse"]}, "medium"),
    "code-reviewer": ({"claude-code": CLAUDE["upper"], "codex": CODEX["workhorse"]}, "high"),
    "release-manager": ({"claude-code": CLAUDE["workhorse"], "codex": CODEX["workhorse"]}, "medium"),
    "judge": ({"claude-code": CLAUDE["workhorse"], "codex": CODEX["workhorse"]}, "medium"),
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


# Names the team renamed, which no file in it may still use: (pattern, what replaced it).
RETIRED_NAMES = [
    (r"dev[.-]build\b", "the dev.backend-1 seat (dev-backend-1)"),
    # NOTICE.md still names Workshop's own guidance/builder.md, which is where ours came from.
    (r"profile: builder(?![\w-])|(?<!workshop/guidance/)(?<![\w-])builder\.md|: builder(?![\w-])", "the builder-backend profile and builder-backend.md"),
    (r"(?m)^  builder:$", "the builder-backend profile"),
    (r"(?<![\w-])backend-builder\b", "the builder-backend profile and builder-backend.md"),
    (r"(?<![\w-])frontend-builder\b", "the builder-frontend profile and builder-frontend.md"),
    # OpenRig's naming guide puts a role in its domain's pod, not a pod named for an operation.
    (r"(?<![\w-])check[.-]qa\b", "the quality.qa-1 seat (quality-qa-1)"),
    # The small team numbers the seats of a role that can grow, and gives the planner and QA new pods.
    (r"(?<![\w-])plan[.-]planner\b", "the orch.planner-1 seat (orch-planner-1)"),
    (r"(?<![\w-])dev[.-](?:backend|frontend)\d*(?![\w-])", "the numbered builder seats, such as dev.backend-1"),
    (r"(?<![\w-])dev[.-]qa", "the quality pod's numbered QA seats, such as quality.qa-1"),
    (r"(?<![\w-])review[.-]r\d\b|(?<![\w-])rev1-r\d\b", "the numbered reviewer seats, such as review.reviewer-1"),
    # The bare release-manager is the profile; only the seat's names are retired.
    (r"(?<![\w-])release\.manager(?![\w-])|(?<![\w-])release-manager@", "the release.manager-1 seat (release-manager-1)"),
    (r"(?i)fourteen seats|14 seats", "the small team's seat count"),
]
# Every seat writes a retrospective note in the slice progress before closing its row.
RETRO_PHRASE = "rig scope slice progress"

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
    # commands, states, tiers, branches, proof types, roster fields and a member's model field
    "model", "rig", "gh", "cd", "routine", "deep", "running", "stopped", "recoverable", "unknown", "main",
    "planned", "active", "runtime", "release-candidate", "rev1-", "delegate", "capabilities", "why",
    # impeccable's own commands
    "shape", "critique", "audit", "polish", "harden", "typeset", "quieter", "distill", "layout", "init", "generate",
}
NOT_SKILLS |= {profile_name(role, runtime) for role in ROLES for runtime in RUNTIMES}
# Each seat by its member id (planner-1) and its name (orch-planner-1), and its reviews' proof type (rev1-reviewer-1).
NOT_SKILLS |= {seat.split(".", 1)[1] for seat in SEATS} | {seat.replace(".", "-") for seat in SEATS}
NOT_SKILLS |= {f"rev1-{seat.split('.', 1)[1]}" for seat, role in SEATS.items() if role == "code-reviewer"}


def fail(problems, message):
    problems.append(message)


def check_names(team, problems):
    words = [word.strip() for word in os.environ.get("TEAM_BLOCKLIST", "").split(",") if word.strip()]
    if not words:
        print("not run: the blocked-words check (TEAM_BLOCKLIST is empty)")
        return
    pattern = re.compile("|".join(re.escape(word) for word in words), re.IGNORECASE)
    for path in sorted(team.rglob("*")):
        if not path.is_file():
            continue
        if pattern.search(str(path.relative_to(team))):
            fail(problems, f"{path}: its path names a blocked word")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                fail(problems, f"{path}:{number}: names a blocked word")


def check_settings(team, problems):
    path = team / "settings.md"
    if not path.is_file():
        fail(problems, f"{path} is missing")
        return
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and len(cells) >= 2:
            rows[cells[0]] = cells[1]
    for setting, default in SETTINGS.items():
        if setting not in rows:
            fail(problems, f"settings.md has no row for {setting!r}")
        elif rows[setting] != default:
            fail(problems, f"settings.md: {setting!r} defaults to {rows[setting]!r}, expected {default!r}")


def parse_agent(agent_yaml):
    text = agent_yaml.read_text(encoding="utf-8")
    declared = dict(re.findall(r"-\s*\{\s*id:\s*([\w.-]+),\s*path:\s*([^\s,}]+)", text))
    selected = set()
    for items in re.findall(r"^\s*skills:\s*\[([^\]]*)\]", text, re.MULTILINE):
        selected.update(item.strip() for item in items.split(",") if item.strip())
    return declared, selected


def profile_blocks(agent_yaml):
    """Each profile's own text, keyed by name, from the two-space-indented keys under `profiles:`."""
    text = agent_yaml.read_text(encoding="utf-8")
    body = text.split("\nprofiles:\n", 1)[1] if "\nprofiles:\n" in text else ""
    return dict(re.findall(r"^  ([\w-]+):\n((?:(?:    .*)?\n)*)", body, re.MULTILINE))


def read_skills_table(team, problems):
    """skills.md's rows, from the table whose header starts `| Skill |`, with their line numbers."""
    path = team / "skills.md"
    if not path.is_file():
        fail(problems, f"{path} is missing")
        return []
    rows = []
    header = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[0] == "Skill":
            header = cells
        elif header and not set(cells[0]) <= set("-: "):
            rows.append((number, dict(zip(header, cells))))
    if not rows:
        fail(problems, f"{path} has no table of skills")
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
    files = sorted(team.glob("agents/*/guidance/*.md")) + sorted(team.glob("startup/*.md"))
    files += [team / "CULTURE.md", team / "settings.md"]
    named = {}
    for path in files:
        if path.is_file():
            for name in re.findall(rf"`({SKILL_NAME})`", path.read_text(encoding="utf-8")):
                named.setdefault(name, path.name)
    return named


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


def check_install_script(team, listed, problems):
    """install-skills.sh reads skills.md: a dry run into empty folders installs every row and writes nothing."""
    script = team / "install-skills.sh"
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
    agents = sorted(team.glob("agents/*/agent.yaml"))
    if not agents:
        fail(problems, f"{team} has no agents/*/agent.yaml")
        return
    for agent_yaml in agents:
        declared, selected = parse_agent(agent_yaml)
        for skill in sorted(selected - declared.keys()):
            fail(problems, f"{agent_yaml}: a profile selects {skill!r}, which no skill resource in the team declares")
        for skill, rel in sorted(declared.items()):
            folder = (agent_yaml.parent / rel).resolve()
            if not folder.is_relative_to(team.resolve()):
                fail(problems, f"{agent_yaml}: {skill!r} is outside the team folder")
            elif not (folder / "SKILL.md").is_file():
                fail(problems, f"{folder}: no SKILL.md")
            if skill in listed:
                fail(problems, f"{agent_yaml}: ships {skill!r}, which skills.md says the person installs")
    for leftover in ("skills.lock", "skills.sources"):
        if (team / leftover).exists():
            fail(problems, f"{team / leftover}: the team no longer pins vendored skills")


def check_skills(team, problems):
    rows = read_skills_table(team, problems)
    listed = check_skills_table(rows, problems)
    check_guidance_skills(team, rows, listed, problems)
    check_install_script(team, listed, problems)
    check_bundle_skills(team, listed, problems)


def check_guidance(team, problems):
    # Whitespace is collapsed, so a phrase still matches where the text wraps it.
    guidance = {
        path.name: " ".join(path.read_text(encoding="utf-8").split()) for path in team.glob("agents/*/guidance/*.md")
    }
    # Start files carry rules too, but no retrospective of their own, so they join only the rule checks.
    started = {
        f"startup/{path.name}": " ".join(path.read_text(encoding="utf-8").split()) for path in team.glob("startup/*.md")
    }
    for name, phrase, why in GUIDANCE_RULES:
        text = started.get(name, guidance.get(name))
        where = name if name in started else f"guidance/{name}"
        if text is None:
            fail(problems, f"{where} is missing")
        elif phrase not in text:
            fail(problems, f"{where} lacks {phrase!r}: {why}")
    for name, phrase, why in FORBIDDEN_RULES:
        where = name if name in started else f"guidance/{name}"
        if phrase in started.get(name, guidance.get(name, "")):
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


def check_profiles(team, problems):
    """Each role has one profile per runtime, with the role's guidance and the model and effort suggested for it."""
    blocks = {}
    for agent_yaml in sorted(team.glob("agents/*/agent.yaml")):
        blocks.update(profile_blocks(agent_yaml))
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
        models, effort = SUGGESTED[role]
        for key, value in (("runtime", runtime), ("model", models[runtime]), ("effort", effort)):
            if preferences.get(key) != value:
                fail(problems, f"the {profile!r} profile's preferences.{key} is {preferences.get(key)!r}, expected {value!r}")
    readme = (team / "README.md").read_text(encoding="utf-8") if (team / "README.md").is_file() else ""
    section = re.search(r"^## Models\n(.*?)(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL)
    if not section:
        fail(problems, "README.md has no Models section")
        return
    for model in sorted({*CLAUDE.values(), *CODEX.values()}):
        if f"`{model}`" not in section.group(1):
            fail(problems, f"README.md's Models section doesn't name `{model}`")
    if "override" not in section.group(1):
        fail(problems, "README.md's Models section doesn't say a rig may override a seat's model")


def check_seats(team, problems):
    rig = (team / "rig.yaml").read_text(encoding="utf-8") if (team / "rig.yaml").is_file() else ""
    configured = (team / "configurations.yaml").read_text(encoding="utf-8") if (team / "configurations.yaml").is_file() else ""
    offered = {
        seat: dict(re.findall(r"([\w-]+):\s*([\w-]+)", runtimes))
        for seat, runtimes in re.findall(r"^  ([\w.-]+):\s*\{\s*runtimes:\s*\{([^}]*)\}", configured, re.MULTILINE)
    }
    # A review pair is two code reviewers on different runtimes, so the recommended preset seats them on at least two.
    preset = re.search(r"^\s*recommended:\s*\{([^}]*)\}", configured, re.MULTILINE)
    picks = dict(re.findall(r"([\w.-]+):\s*([\w-]+)", preset.group(1))) if preset else {}
    reviewers = {picks.get(seat) for seat, role in SEATS.items() if role == "code-reviewer"} - {None}
    if len(reviewers) < 2:
        fail(problems, "configurations.yaml's recommended preset puts the code reviewers on "
                       f"{sorted(reviewers) or 'no runtime'}: a review pair needs two runtimes")
    declared = members(rig)
    for seat in sorted(declared.keys() - SEATS.keys()):
        fail(problems, f"rig.yaml declares {seat!r}, which the team doesn't ship: add it to SEATS, or remove it")
    readme = (team / "README.md").read_text(encoding="utf-8") if (team / "README.md").is_file() else ""
    for seat, role in SEATS.items():
        member, name = seat.split(".", 1)[1], seat.replace(".", "-")
        if not re.search(rf"^\|.*`{re.escape(name)}`.*\|", readme, re.MULTILINE):
            fail(problems, f"README.md's seat table doesn't name {name!r}")
        fields = declared.get(seat)
        runtime = fields and fields.get("runtime")
        if fields is None:
            fail(problems, f"rig.yaml has no member {member!r} in its pod")
        elif runtime not in RUNTIMES:
            fail(problems, f"rig.yaml's {seat!r} runs on {runtime!r}, which is none of {sorted(RUNTIMES)}")
        elif fields.get("profile") != profile_name(role, runtime):
            fail(problems, f"rig.yaml's {seat!r} has the {fields.get('profile')!r} profile, "
                           f"expected {profile_name(role, runtime)!r} for the {role!r} role on {runtime}")
        runtimes = offered.get(seat, {})
        for runtime in RUNTIMES:
            if runtimes.get(runtime) != profile_name(role, runtime):
                fail(problems, f"configurations.yaml maps {seat!r} on {runtime} to {runtimes.get(runtime)!r}, "
                               f"expected {profile_name(role, runtime)!r}")
        for runtime in sorted(runtimes.keys() - RUNTIMES.keys()):
            fail(problems, f"configurations.yaml offers {seat!r} {runtime!r}, which the team has no profiles for")
    for path in sorted(team.rglob("*")):
        try:
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, replacement in RETIRED_NAMES:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                fail(problems, f"{path}:{line}: {match.group(0)!r} was renamed to {replacement}")


def members(rig):
    """Every seat in rig.yaml's pods, as pod.member, with its one-line fields, such as its profile and runtime."""
    seats, pod, seat = {}, None, None
    for line in rig.splitlines():
        if m := re.match(r"^  - id: ([\w-]+)$", line):
            pod, seat = m.group(1), None
        elif line == "edges:":
            pod, seat = None, None
        elif (m := re.match(r"^      - id: ([\w-]+)$", line)) and pod:
            seat = f"{pod}.{m.group(1)}"
            seats[seat] = {}
        elif (m := re.match(r"^        (\w+): (\S.*)$", line)) and seat:
            seats[seat][m.group(1)] = m.group(2).strip('"')
    return seats


LEAD = "orch.lead"
# The peer watches the lead and relaunches it when it is down, so its rows mustn't escalate to the lead: with no
# orchestrator, OpenRig sends them to its operator instead.
PEER = "orch.peer"


def check_team_shape(team, problems):
    """startup/team-shape.md is the one place that says which roles can grow, so it names every profile."""
    path = team / "startup" / "team-shape.md"
    if not path.is_file():
        fail(problems, "startup/team-shape.md is missing")
        return
    text = path.read_text(encoding="utf-8")
    for agent_yaml in sorted(team.glob("agents/*/agent.yaml")):
        for profile in profile_blocks(agent_yaml):
            if f"`{profile}`" not in text:
                fail(problems, f"startup/team-shape.md doesn't name the {profile!r} profile")


def check_delegation(team, problems):
    """The lead is every other seat's orchestrator, so every stuck queue row escalates to it.

    OpenRig makes the source of a seat's delegates_to edge its orchestrator, and picks the latest-launched one when
    there are several, so a second source would quietly take the lead's place.
    """
    path = team / "rig.yaml"
    if not path.is_file():
        return
    seats, sources, pod = [], {}, None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if m := re.match(r"^  - id: ([\w-]+)$", line):
            pod = m.group(1)
        elif line == "edges:":
            pod = None
        elif (m := re.match(r"^      - id: ([\w-]+)$", line)) and pod:
            seats.append(f"{pod}.{m.group(1)}")
        elif re.match(r"^\s*- kind: delegates_to$", line):
            source = re.search(r"from: (\S+)", lines[i + 1]).group(1)
            target = re.search(r"to: (\S+)", lines[i + 2]).group(1)
            if pod:
                source, target = f"{pod}.{source}", f"{pod}.{target}"
            sources.setdefault(target, []).append(source)
    for seat in seats:
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
    result = subprocess.run([rig, "bundle", "check", str(team)], capture_output=True, text=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        fail(problems, f"rig bundle check exited {result.returncode}: {result.stderr.strip()}")


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    team = Path(sys.argv[1])
    problems = []
    check_names(team, problems)
    check_settings(team, problems)
    check_skills(team, problems)
    check_guidance(team, problems)
    check_profiles(team, problems)
    check_seats(team, problems)
    check_team_shape(team, problems)
    check_delegation(team, problems)
    check_bundle(team, problems)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{team}: {'ok' if not problems else f'{len(problems)} problems'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
