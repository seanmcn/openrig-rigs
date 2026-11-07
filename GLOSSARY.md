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
A group of seats with one job in a rig, such as `dev` for the builders and QA or `review` for the review pair.

**Profile**:
A seat's role in a team's `agent.yaml`: which guidance, skills and startup files a seat gets.
_Avoid_: profile (for a Codex config profile; say "Codex profile")

**Preset**:
A named choice of runtime for every seat, from a team's `configurations.yaml`, such as `recommended`.

**Peer**:
The `orch-peer` seat, which follows the lead's work and takes over when the lead's seat is down.
_Avoid_: peer (for any other seat; say "the other seats")

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
What a slice changes: UI, backend or both. It decides which builder takes the slice; a slice of both kinds stays with
one frontend builder.
_Avoid_: type, area

**Proof**:
What a seat records about a slice at one commit, mostly QA and each reviewer, with a verdict: PASS, BLOCKING,
CONCERNING or NOT-CLEAR. A builder's screenshots and the release manager's checks after a rebase are proof too.
_Avoid_: evidence

**Proof contract**:
The part of a slice's spec that says what proof the slice needs before it can be judged.

**Judge**:
The lead's decision on a slice's proof at one commit, made again after any change to that commit.

**Merge gate**:
The top of a slice's pull request: whether it can merge, its review and test status at the published commit, how hard
it is to undo, and its blast radius.
_Avoid_: gate (alone)

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

**Handoff**:
The body of a queue row that hands work on: what the work is, where it lives and what the receiving seat needs.
_Avoid_: handoff (for the row itself; say "queue row")

**Roster**:
A team's published list of its seats, what each is good at and when to ask it, which anyone finds with
`rig roster find`. The lead curates it.
_Avoid_: directory

**Tier**:
A queue row's deadline class: `routine` is 4 hours and `deep` is 24.
_Avoid_: deadline (for the class)
