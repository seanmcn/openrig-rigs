# openrig-rigs

Teams of agents for [OpenRig](https://github.com/mvschwarz/openrig), and the words their docs and guidance use.

## Language

### Teams and seats

**Team**:
A set of seats, their guidance and their settings, shipped as one folder under `rigs/` and installed as a bundle.
_Avoid_: crew

**Rig**:
A team installed and running under OpenRig, under its own name, such as `shipwrights` in `rig down shipwrights`.
_Avoid_: team (for the running instance)

**Seat**:
One agent session in a rig, with its own role guidance and runtime.
_Avoid_: member, agent, node, session

**Seat id**:
A seat's name, written `orch-lead`. In `rig.yaml` and `--seat` flags it is `orch.lead` (pod.member), and as a session
it is `orch-lead@shipwrights` (seat id at rig).

**Pod**:
A group of seats with one job in a rig, such as `dev` for the builders or `review` for the code reviewers. A role that
can grow numbers its seats in its pod, such as `dev-backend-1`.

**Profile**:
A seat's role on one runtime in a team's `agent.yaml`: which guidance, skills and startup files a seat gets, and the
model and effort it suggests. A role has one profile per runtime, such as `planner-claude` and `planner-codex`, which
share its guidance.
_Avoid_: profile (for a Codex config profile; say "Codex profile")

**Model tier**:
A class of model by price and capability: top, upper, workhorse, lower or budget. A team's README suggests one for
each role.
_Avoid_: tier (that is a queue row's deadline class)

**Preset**:
A named choice of runtime for every seat, from a team's `configurations.yaml`, such as `recommended`.

**Peer**:
The `orch-peer` seat, the lead's watchdog: it restores the lead after a handover and relaunches it when its seat is down. It never drives.
_Avoid_: peer (for any other seat; say "the other seats")

**Clerk**:
The seat that does the lead's routine coordination by fixed rules, such as `orch-clerk-1`: it routes work to a free
planner, gives each slice its seats once the lead locks its spec, relaunches seats when their part is done, keeps the
roster and records deliveries. When unsure, it hands the question to the lead.
_Avoid_: coordinator, dispatcher

**Overlay**:
A person's own changes on top of a pinned team: their settings, their skills in place of some of the team's, and
their own startup files.
_Avoid_: layer

**Person**:
Whoever runs the rig and decides what merges. Docs written to them say "you"; guidance written for seats says "the
person".
_Avoid_: user (which means the end user of the software being built), operator

### The work

**Mission**:
A person's goal, cut into slices and the dependencies between them.

**Slice**:
One deliverable change: one pull request in each repository it touches, merged in the order its spec lists them.
_Avoid_: piece, ticket

**Spec**:
A slice's `SPEC.md`: what a user gets, when it's done, what's out of scope, what it depends on, and its proof contract.
The lead **locks** it before the slice is built.
_Avoid_: brief; approve (for locking a spec)

**Kind**:
What a slice changes: UI, backend or both. It decides which builder takes the slice. One builder builds each slice, so
a slice of both kinds goes to one frontend builder; the planner cuts both kinds of work as two slices when it can.
_Avoid_: type, area

**Proof**:
What a seat records about a slice at one commit, mostly QA and each reviewer, with a verdict. A builder's screenshots
are proof too.
_Avoid_: evidence

**Verdict**:
The word a proof ends in. **PASS**: it showed what the slice promised. **BLOCKING**: it must change before the slice
can go on. **CONCERNING**: it passes, but something should change, or be argued. **NOT-CLEAR**: the seat couldn't tell,
and the lead decides.

**Fresh seat**:
A builder, QA seat, code reviewer or planner, which the clerk relaunches with a new session after each piece of work:
it keeps its address and remembers nothing of earlier slices. The lead, its peer, the clerk and the release manager
are **long-lived** instead, and hand over to a fresh successor near a full context.
_Avoid_: reset, recycled seat

**Review pair**:
The two code reviewers the clerk names for a slice, on different runtimes, who review the same commits independently.
_Avoid_: reviewer pair, review team

**Proof contract**:
The part of a slice's spec that says what proof the slice needs before it can be judged.

**Judge**:
The lead's decision on a slice's proof at one commit, made again after any change to that commit.

**Merge gate**:
The top of a slice's pull request: whether it can merge, its review and test status at the published commit, how hard
it is to undo, and its blast radius.
_Avoid_: gate (alone)

**Delivered**:
A slice's last state: its pull requests are merged and the release manager has approved it for delivery. A mission
closes when its last slice is delivered.
_Avoid_: done, shipped

**Slice progress**:
A slice's running notes in OpenRig's work tree, where each seat adds its retrospective.
_Avoid_: PROGRESS

### OpenRig

**Kernel operator**:
The OpenRig seat a person talks to first, which starts teams and hands each one the person's goal.
_Avoid_: operator (alone), installer

**Queue row**:
One unit of work handed to a seat on OpenRig's queue; it is claimed, blocked or closed.
_Avoid_: queue item, ticket

**Park**:
To block a queue row you still hold, naming what it waits on and a wake (`rig queue block <row> --on … --wake-after …`),
so it waits without OpenRig's stuck sweep reporting it as stalled.
_Avoid_: sleep, idle

**Orchestrator**:
The seat a seat's stuck or unclaimed queue rows escalate to: the source of its `delegates_to` edge in `rig.yaml`. In
Shipwrights it is the lead, for every seat but the lead and its peer.
_Avoid_: parent, manager

**Handoff**:
The body of a queue row that hands work on: what the work is, where it lives and what the receiving seat needs.
_Avoid_: handoff (for the row itself; say "queue row")

**Roster**:
A team's published list of its seats, each with what its role does and when to ask it, which anyone finds with
`rig roster find`. The clerk curates it.
_Avoid_: directory

**Tier**:
A queue row's deadline class: `routine` is 4 hours and `deep` is 24.
_Avoid_: deadline (for the class)
