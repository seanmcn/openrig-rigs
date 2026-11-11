"""Build the team diagrams: one geometry, a light and a dark SVG each.

    python3 docs/diagrams/build.py

Edit the geometry here, never the SVGs. The canvas is transparent so a diagram takes the colour of the page it sits
on, which means nothing masks a crossing: route every connector and label clear of nodes and of each other. Fonts are
the viewer's system faces, since GitHub shows an SVG as an image that can't fetch web fonts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
TEAM = ROOT / "rigs" / "shipwrights" / "diagrams"
REPO = ROOT / "docs" / "diagrams"

SANS = "Geist, system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


@dataclass(frozen=True)
class Tokens:
    ink: str
    muted: str
    soft: str
    rule: str
    accent: str
    accent_tint: str
    node_fill: str


LIGHT = Tokens("#2d3142", "#4f5d75", "#5a6580", "rgba(45,49,66,0.16)", "#bf4520", "rgba(191,69,32,0.08)",
               "rgba(45,49,66,0.03)")
DARK = Tokens("#f5f5f5", "#bfc0c0", "#949eb2", "rgba(245,245,245,0.16)", "#f08a59", "rgba(240,138,89,0.12)",
              "rgba(255,255,255,0.05)")


class Canvas:
    def __init__(self, t: Tokens, slug: str, width: int, height: int, title: str, desc: str):
        self.t, self.slug, self.width, self.height = t, slug, width, height
        self.title, self.desc = title, desc
        self.legend_x = 0  # where the legend strip starts, in line with the content's left edge
        self.back: list[str] = []  # connectors and lines, drawn before nodes
        self.front: list[str] = []

    def rect(self, x: int, y: int, w: int, h: int, stroke: str | None = None, rx: int = 0) -> None:
        """An unfilled outline, behind everything else: a zone or a band of a layer stack."""
        self.back.insert(0, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" '
                            f'stroke="{stroke or self.t.rule}" stroke-width="1"/>')

    # Nodes ---------------------------------------------------------------------------------------------------------
    def node(self, x: int, y: int, w: int, h: int, name: str, sub: str = "", kind: str = "step") -> None:
        t = self.t
        stroke, fill, dash, width = t.ink, t.node_fill, "", 1.2
        if kind == "focal":
            stroke, fill, width = t.accent, t.accent_tint, 1.6
        elif kind == "held":
            stroke, dash = t.muted, ' stroke-dasharray="5,4"'
        elif kind == "end":
            stroke = t.muted
        self.front.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}"{dash}/>')
        name_colour = t.accent if kind == "focal" else t.ink
        cy = y + h / 2
        if sub:
            self.text(x + w / 2, cy - 3, name, SANS, 13, name_colour, weight=600)
            self.text(x + w / 2, cy + 13, sub, MONO, 10, t.soft)
        else:
            self.text(x + w / 2, cy + 4.5, name, SANS, 13, name_colour, weight=600)

    def text(self, x: float, y: float, s: str, family: str, size: int, fill: str, weight: int = 400,
             anchor: str = "middle", spacing: float = 0) -> None:
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.front.append(
            f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}>{escape(s)}</text>')

    def eyebrow(self, x: float, y: float, s: str, anchor: str = "middle") -> None:
        self.text(x, y, s.upper(), MONO, 10, self.t.soft, anchor=anchor, spacing=1)

    def label(self, x: float, y: float, s: str, anchor: str = "middle", accent: bool = False) -> None:
        self.text(x, y, s.upper(), MONO, 9, self.t.accent if accent else self.t.muted, anchor=anchor, spacing=0.6)

    # Lines ---------------------------------------------------------------------------------------------------------
    def line(self, x1: float, y1: float, x2: float, y2: float, colour: str | None = None) -> None:
        self.back.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour or self.t.rule}" '
                         'stroke-width="1"/>')

    def arrow(self, points: list[tuple[float, float]], kind: str = "muted") -> None:
        """An orthogonal connector through `points`, with r=8 rounded elbows and an arrowhead at the end."""
        colour = {"muted": self.t.muted, "dashed": self.t.muted, "accent": self.t.accent}[kind]
        dash = ' stroke-dasharray="5,4"' if kind == "dashed" else ""
        marker = "accent" if kind == "accent" else "muted"
        self.back.append(f'<path d="{_elbow(points)}" fill="none" stroke="{colour}" stroke-width="1.4"{dash} '
                         f'marker-end="url(#{self.slug}-arrow-{marker})"/>')

    # Output --------------------------------------------------------------------------------------------------------
    def svg(self, legend: list[tuple[str, str]]) -> str:
        t = self.t
        y = self.height - 20
        x = self.legend_x
        items = []
        for kind, text in legend:
            if kind == "focal":
                items.append(f'<rect x="{x}" y="{y - 9}" width="14" height="10" rx="2" fill="{t.accent_tint}" '
                             f'stroke="{t.accent}" stroke-width="1.4"/>')
            elif kind == "held":
                items.append(f'<rect x="{x}" y="{y - 9}" width="14" height="10" rx="2" fill="none" '
                             f'stroke="{t.muted}" stroke-dasharray="3,2"/>')
            else:
                items.append(f'<line x1="{x}" y1="{y - 4}" x2="{x + 16}" y2="{y - 4}" stroke="{t.muted}" '
                             f'stroke-width="1.4" stroke-dasharray="5,4"/>')
            items.append(f'<text x="{x + 22}" y="{y}" font-family="{MONO}" font-size="10" fill="{t.soft}">'
                         f'{escape(text)}</text>')
            x += 22 + len(text) * 6.2 + 28
        markers = "".join(
            f'<marker id="{self.slug}-arrow-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="{colour}"/></marker>'
            for name, colour in (("muted", t.muted), ("accent", t.accent)))
        body = "\n  ".join(self.back + self.front + items)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="{self.width}" height="{self.height}" role="img" '
            f'aria-labelledby="{self.slug}-title {self.slug}-desc">\n'
            f'  <title id="{self.slug}-title">{escape(self.title)}</title>\n'
            f'  <desc id="{self.slug}-desc">{escape(self.desc)}</desc>\n'
            f'  <defs>{markers}</defs>\n  {body}\n</svg>\n')


def _elbow(points: list[tuple[float, float]], r: float = 8) -> str:
    d = [f"M{points[0][0]:g},{points[0][1]:g}"]
    for (x0, y0), (x1, y1), (x2, y2) in zip(points, points[1:], points[2:]):
        # Step back from the corner by r on the way in, and curve to r along the way out.
        ax = x1 - r * _sign(x1 - x0)
        ay = y1 - r * _sign(y1 - y0)
        bx = x1 + r * _sign(x2 - x1)
        by = y1 + r * _sign(y2 - y1)
        d.append(f"L{ax:g},{ay:g} Q{x1:g},{y1:g} {bx:g},{by:g}")
    d.append(f"L{points[-1][0]:g},{points[-1][1]:g}")
    return " ".join(d)


def _sign(v: float) -> int:
    return (v > 0) - (v < 0)


# How the work moves: one lane per role, time running down. ----------------------------------------------------------

LANE_W, NODE_W, NODE_H, ROW = 176, 144, 48, 80


def swimlane(t: Tokens, slug: str, title: str, desc: str, lanes: list[str],
             steps: list[tuple[int, str, str, str]]) -> tuple[Canvas, callable, int]:
    """Lanes side by side and one step per row; each step hands on to the next. Returns the canvas, a function giving a
    row's box, and the bottom of the lanes, so the caller can add its loops."""
    bottom = 56 + (len(steps) - 1) * ROW + NODE_H + 16
    c = Canvas(t, slug, LANE_W * len(lanes), bottom + 48, title, desc)
    c.legend_x = (LANE_W - NODE_W) // 2
    for k, lane in enumerate(lanes):
        c.eyebrow(k * LANE_W + LANE_W / 2, 28, lane)
        if k:
            c.line(k * LANE_W, 12, k * LANE_W, bottom)
    c.line(0, 40, LANE_W * len(lanes), 40)

    def box(row: int) -> tuple[int, int]:
        return steps[row][0] * LANE_W + (LANE_W - NODE_W) // 2, 56 + row * ROW

    for row, (_, name, sub, kind) in enumerate(steps):
        x, y = box(row)
        c.node(x, y, NODE_W, NODE_H, name, sub, kind)
    for row in range(len(steps) - 1):
        (x, y), (nx, ny) = box(row), box(row + 1)
        cx, cy, ncx = x + NODE_W / 2, y + NODE_H / 2, nx + NODE_W / 2
        kind = "accent" if steps[row + 1][3] == "focal" else "muted"
        if steps[row + 1][0] == steps[row][0]:
            c.arrow([(cx, y + NODE_H), (ncx, ny)], kind)  # the same lane: straight down
        else:
            # Out of the side facing the next step's lane, across, then down into its top.
            start = x + NODE_W if steps[row + 1][0] > steps[row][0] else x
            c.arrow([(start, cy), (ncx, cy), (ncx, ny)], kind)
    return c, box, bottom


def work(t: Tokens, slug: str) -> Canvas:
    steps = [  # (lane, name, sublabel, kind), one per row
        (0, "Your goal", "an issue or a request", "step"),
        (1, "Take it on", "goal to the clerk", "step"),
        (3, "Route the work", "to a free planner", "step"),
        (4, "Cut the work", "mission, slices, specs", "step"),
        (1, "Lock specs", "each slice's SPEC", "step"),
        (3, "Assign seats", "builder and QA seat", "step"),
        (2, "Built and reviewed", "the next diagram", "step"),
        (2, "Judge proof", "at the reviewed commit", "step"),
        (5, "Open pull requests", "description and gate", "step"),
        (0, "Merge", "your decision", "focal"),
        (5, "Approve delivery", "tells the clerk", "step"),
        (3, "Record delivery", "mission progress", "step"),
        (1, "Close your goal", "mission complete", "step"),
    ]
    c, box, _ = swimlane(
        t, slug, "How the work moves",
        "The lead takes on your goal and the clerk routes it to a planner, which cuts it; the lead locks each slice's "
        "spec and the clerk assigns it a builder and a QA seat; the judge judges the proof once it is built and "
        "reviewed, passing the hard or risky slices to the lead to decide, and hands it to the release manager, which "
        "writes the description and opens the pull requests; a failing CI run or a conflict goes back through the lead, which decides the fix, "
        "to the clerk to assign; you merge, the release manager approves delivery, the clerk records it, and the lead "
        "closes your goal once its mission is complete.",
        ["You", "Lead", "Judge", "Clerk", "Planner", "Release manager"], steps)
    # A failing CI run or a conflict goes back, through the lead's decision, to the clerk, which assigns the fix or the
    # rebase: up the release manager's lane, clear of the arrow coming in, and into the side of "Assign seats".
    (ox, oy), (ax, ay) = box(8), box(5)
    lx = ox + NODE_W / 2 + 40
    c.arrow([(lx, oy), (lx, ay + NODE_H / 2), (ax + NODE_W, ay + NODE_H / 2)], "dashed")
    c.label(lx - 8, (ay + NODE_H + oy) / 2 + 3, "ci, conflict", anchor="end")
    # The judge passes a hard or risky slice to the lead beside it, which decides and hands it back.
    jx, jy = box(7)
    dx = LANE_W + (LANE_W - NODE_W) // 2
    c.node(dx, jy, NODE_W, NODE_H, "Decide", "hard or risky slices")
    c.arrow([(jx, jy + 16), (dx + NODE_W, jy + 16)], "dashed")
    c.arrow([(dx + NODE_W, jy + 32), (jx, jy + 32)], "dashed")
    c.label(2 * LANE_W, jy - 8, "passed up", anchor="middle")
    return c


def building(t: Tokens, slug: str) -> Canvas:
    steps = [
        (0, "Assign", "builder and QA seat", "step"),
        (1, "Build", "commit in a worktree", "step"),
        (2, "QA checks", "at that commit", "step"),
        (0, "Name a pair", "on two runtimes", "step"),
        (3, "Review", "a pair, apart", "step"),
        (4, "Compare reviews", "then judge", "step"),
    ]
    c, box, _ = swimlane(
        t, slug, "How a slice is built",
        "The clerk assigns a builder and a QA seat; the builder builds a commit and QA checks it, back to the builder "
        "until it passes; the clerk then names a review pair on two runtimes, whose findings go back to the builder "
        "and through QA again; once both pass, the judge compares their reviews and judges.",
        ["Clerk", "Builder", "QA", "Reviewers", "Judge"], steps)
    (bx, by), (qx, qy), (rx, ry) = box(1), box(2), box(4)
    qcx, rcx = qx + NODE_W / 2, rx + NODE_W / 2
    # QA's failures go back to the builder: up from QA's top and into the builder's side above the arrow going out.
    c.arrow([(qcx + 24, qy), (qcx + 24, by + 12), (bx + NODE_W, by + 12)], "dashed")
    c.label(qcx + 32, (by + NODE_H + qy) / 2 + 3, "fails", anchor="start")
    # Reviewers' findings go back to the builder: up the reviewers' lane, over QA, and into the builder's top.
    c.arrow([(rcx + 24, ry), (rcx + 24, by - 16), (bx + NODE_W / 2 + 24, by - 16), (bx + NODE_W / 2 + 24, by)],
            "dashed")
    c.label(rcx + 32, (by + ry) / 2 + 3, "findings", anchor="start")
    # QA's pass goes back to the clerk, and both reviewers' to the judge, labelled above their runs across the lanes.
    c.label(qx - 8, qy + NODE_H / 2 - 8, "passes", anchor="end")
    c.label(rx + NODE_W + 8, ry + NODE_H / 2 - 8, "both pass", anchor="start")
    return c


# A slice's lifecycle: phases, a hold, and its outcomes. -------------------------------------------------------------

PW, GAP = 128, 56


def lifecycle(t: Tokens, slug: str) -> Canvas:
    c = Canvas(t, slug, 920, 456, "A slice's lifecycle",
               "A slice's spec is locked, then it is built and checked by QA until QA passes, reviewed by a pair, "
               "judged and published; findings, a failing CI run and a rebase loop back to building. From any phase "
               "you can pause it and resume it, or stop it; it is delivered once you merge.")
    c.legend_x = 24
    rail_y = 104
    xs = [24 + i * (PW + GAP) for i in range(5)]
    phases = [("Spec locked", "lead"), ("Building", "builder and QA"), ("In review", "a review pair"),
              ("Judged", "judge"), ("Published", "release manager")]
    c.eyebrow(24, 20, "Phases", anchor="start")
    for x, (name, sub) in zip(xs, phases):
        c.node(x, rail_y, PW, NODE_H, name, sub)

    cy = rail_y + NODE_H / 2
    for i, word in enumerate(["assign", "qa pass", "pass", "push"]):
        c.arrow([(xs[i] + PW, cy), (xs[i + 1], cy)])
        c.label(xs[i] + PW + GAP / 2, cy - 10, word)

    # Loops back, above the rail: findings' short one, and the long one for CI and rebases over it, each on its own
    # attach points.
    top = rail_y - 24
    sx, ex = xs[2] + 40, xs[1] + 88
    c.arrow([(sx, rail_y), (sx, top), (ex, top), (ex, rail_y)], "dashed")
    c.label((sx + ex) / 2, top - 10, "findings")
    high = top - 40
    sx, ex = xs[4] + 88, xs[1] + 40
    c.arrow([(sx, rail_y), (sx, high), (ex, high), (ex, rail_y)], "dashed")
    c.label((sx + ex) / 2, high - 10, "ci, rebase")

    # Pause and stop: an explicit "any phase" box, so they don't look like steps of the rail.
    held_y = rail_y + NODE_H + 72
    c.eyebrow(24, held_y - 12, "Pause or stop", anchor="start")
    any_x, paused_x = xs[0], xs[1] + 24
    c.node(any_x, held_y, PW, NODE_H, "Any phase", "of the five above")
    c.node(paused_x, held_y, PW, NODE_H, "Paused", "rows blocked", "held")
    hy = held_y + NODE_H / 2
    c.arrow([(any_x + PW, hy - 8), (paused_x, hy - 8)])
    c.label((any_x + PW + paused_x) / 2, hy - 16, "pause")
    c.arrow([(paused_x, hy + 8), (any_x + PW, hy + 8)], "dashed")
    c.label((any_x + PW + paused_x) / 2, hy + 24, "resume")

    out_y = held_y + NODE_H + 72
    c.eyebrow(24, out_y - 12, "Outcomes", anchor="start")
    c.node(any_x, out_y, PW, NODE_H, "Stopped", "rows closed", "end")
    stop_x = any_x + PW - 32  # right of centre, clear of the eyebrows down the left
    c.arrow([(stop_x, held_y + NODE_H), (stop_x, out_y)])
    c.label(stop_x + 8, held_y + NODE_H + 40, "stop", anchor="start")

    mx = xs[4] + 96
    c.node(xs[4], out_y, PW, NODE_H, "Delivered", "delivery approved", "focal")
    c.arrow([(mx, rail_y + NODE_H), (mx, out_y)], "accent")
    c.label(mx - 8, held_y + 28, "you merge", anchor="end", accent=True)
    return c


# From a team folder to a running rig: what a person runs, and what each step reads and makes. -----------------------

def team_to_rig(t: Tokens, slug: str) -> Canvas:
    c = Canvas(t, slug, 720, 328, "From a team to a running rig",
               "A team's rig.yaml, agent.yaml, start files and settings go into rig bundle install, which starts the "
               "rig's seats; its skills.md goes into install-skills.sh, which installs the skills the seats read.")
    w, h = 168, 48
    left, mid, right = 40, 296, 528
    rows = [64, 128, 192, 256]
    c.rect(24, 40, 200, 280, rx=8)
    c.text(24, 28, "rigs/<team>/", MONO, 10, t.soft, anchor="start", spacing=1)  # a path keeps its case
    c.eyebrow(mid + w / 2, 28, "You run")
    c.eyebrow(right + w / 2, 28, "Your machine")

    team = [("rig.yaml", "pods, seats, runtimes"), ("agent.yaml", "profiles, guidance"),
            ("Start files", "culture, settings"), ("skills.md", "skills it names")]
    for y, (name, sub) in zip(rows, team):
        c.node(left, y, w, h, name, sub)

    install_y, skills_y = rows[1], rows[3]
    c.node(mid, install_y, w, h, "rig bundle install", "--target, --cwd")
    c.node(mid, skills_y, w, h, "install-skills.sh", "at user level")
    c.node(right, install_y, w, h, "Running rig", "a session per seat", "focal")
    c.node(right, skills_y, w, h, "Your skills", "~/.claude, ~/.codex")

    # Three of the team's files fan into the install, each at its own point on its left edge.
    elbow = left + w + 40
    for y, port in zip(rows[:3], (install_y + 12, install_y + 24, install_y + 36)):
        cy = y + h / 2
        c.arrow([(left + w, cy), (elbow, cy), (elbow, port), (mid, port)] if cy != port else [(left + w, cy), (mid, cy)])
    c.arrow([(left + w, skills_y + h / 2), (mid, skills_y + h / 2)])
    c.arrow([(mid + w, install_y + h / 2), (right, install_y + h / 2)], "accent")
    c.arrow([(mid + w, skills_y + h / 2), (right, skills_y + h / 2)])
    sx = right + w / 2
    c.arrow([(sx, skills_y), (sx, install_y + h)])
    c.label(sx + 8, (install_y + h + skills_y) / 2 + 3, "seats read", anchor="start")
    return c


# What a seat starts with, from what every seat shares to what only it gets. ----------------------------------------

def seat_start(t: Tokens, slug: str) -> Canvas:
    c = Canvas(t, slug, 760, 416, "What a seat starts with",
               "Every seat starts with the team's culture, start steps, settings and skills, then its profile's role "
               "guidance and its own start files; an overlay replaces the settings, swaps skills and adds start files.")
    sx, sw, top, rh = 136, 432, 48, 56
    layers = [  # (scope, name, files, what an overlay does)
        ("every seat", "Culture", "CULTURE.md", ""),
        ("every seat", "Start steps", "context.md, team-shape.md", ""),
        ("every seat", "Settings", "settings.md", "your copy"),
        ("every seat", "Skills", "openrig-core, user-level", "swap any for yours"),
        ("per profile", "Role guidance", "guidance/<role>.md", "keep as it is"),
        ("per seat", "Its own start files", "startup/review-pair-*.md", "add your own rules"),
    ]
    c.eyebrow(24, 28, "Scope", anchor="start")
    c.eyebrow(sx + 20, 28, "Layer", anchor="start")
    c.eyebrow(sx + sw - 20, 28, "From", anchor="end")
    c.eyebrow(sx + sw + 24, 28, "In an overlay", anchor="start")
    c.rect(sx, top, sw, rh * len(layers), t.muted, rx=6)
    for i, (_, name, files, overlay) in enumerate(layers):
        y = top + i * rh
        if i:
            c.line(sx, y, sx + sw, y)
        c.text(sx + 20, y + rh / 2 + 4.5, name, SANS, 13, t.ink, weight=600, anchor="start")
        c.text(sx + sw - 20, y + rh / 2 + 4, files, MONO, 10, t.soft, anchor="end")
        if overlay:
            c.label(sx + sw + 24, y + rh / 2 + 3, overlay, anchor="start")

    # A bracket per scope on the left, so the scope narrows down the stack.
    i = 0
    for scope in ("every seat", "per profile", "per seat"):
        n = sum(1 for layer in layers if layer[0] == scope)
        y0, y1 = top + i * rh + 8, top + (i + n) * rh - 8
        bx = sx - 16
        c.line(bx, y0, bx, y1, t.muted)
        c.line(bx, y0, bx + 6, y0, t.muted)
        c.line(bx, y1, bx + 6, y1, t.muted)
        c.label(bx - 8, (y0 + y1) / 2 + 3, scope, anchor="end")
        i += n
    c.arrow([(28, top + 8), (28, top + rh * len(layers) - 8)])
    c.label(24, top + rh * len(layers) + 20, "narrower", anchor="start")
    return c


# The team's seats: its five pods, and each seat's role, member id and runtime. ------------------------------------

def seats(t: Tokens, slug: str) -> Canvas:
    w, h, pad, gap = 168, 48, 16, 24
    side = w + 2 * pad  # a pod of one column
    # The pods below orch, side by side, each a column of its seats: (pod, [(role, member id, runtime)]).
    pods = [
        ("dev", [("Backend builder", "backend-1", "Claude Code"), ("Frontend builder", "frontend-1", "Claude Code")]),
        ("quality", [("QA", "qa-1", "Claude Code"), ("QA", "qa-2", "Claude Code")]),
        ("review", [("Code reviewer", "reviewer-1", "Claude Code"), ("Code reviewer", "reviewer-2", "Codex"),
                    ("Judge", "judge-1", "Claude Code")]),
        ("release", [("Release manager", "manager-1", "Codex")]),
    ]
    width = gap + len(pods) * (side + gap)

    # The orch pod on top, centred: the lead, which you talk to, its peer, which watches the lead and relaunches it, the
    # clerk, which does the lead's routine coordination, and the planner.
    orch = [("Lead", "lead", "Codex", "focal"), ("Peer", "peer", "Claude Code", "held"),
            ("Clerk", "clerk-1", "Claude Code", "step"), ("Planner", "planner-1", "Claude Code", "step")]
    orch_w = len(orch) * w + (len(orch) - 1) * gap + 2 * pad
    orch_x, orch_y = (width - orch_w) // 2, 32
    rows = max(len(members) for _, members in pods)  # every pod's box is as tall as the tallest
    zone_y, zone_h = orch_y + h + 2 * pad + 40, rows * h + (rows + 1) * pad
    c = Canvas(t, slug, width, zone_y + zone_h + 64, "Shipwrights' seats",
               "Shipwrights' twelve seats in five pods: in orch, the lead, its peer, a clerk and a planner; in dev, a backend "
               "builder and a frontend builder; in quality, two QA seats; in review, two code reviewers, one on each "
               "runtime, and a judge; and in release, a release manager. A role that can grow numbers its seats.")
    c.legend_x = 24
    c.rect(orch_x, orch_y, orch_w, h + 2 * pad, rx=8)
    c.eyebrow(orch_x, orch_y - 8, "orch", anchor="start")
    for i, (role, member, runtime, kind) in enumerate(orch):
        c.node(orch_x + pad + i * (w + gap), orch_y + pad, w, h, role, f"{member} · {runtime}", kind)

    for k, (pod, members) in enumerate(pods):
        x = gap + k * (side + gap)
        c.rect(x, zone_y, side, zone_h, rx=8)
        c.eyebrow(x, zone_y - 8, pod, anchor="start")
        for row, (role, member, runtime) in enumerate(members):
            c.node(x + pad, zone_y + pad + row * (h + pad), w, h, role, f"{member} · {runtime}")
    return c


# name: (draw, legend, where its SVGs go)
DIAGRAMS = {"seats": (seats, [("focal", "the seat you talk to"), ("held", "watches the lead and relaunches it")], TEAM),
            "how-the-work-moves": (work, [("focal", "your step"), ("dashed", "back to an earlier step")], TEAM),
            "how-a-slice-is-built": (building, [("dashed", "back to the builder")], TEAM),
            "slice-lifecycle": (lifecycle, [("focal", "the outcome you want"), ("held", "held, resumable"),
                                            ("dashed", "back to an earlier phase")], TEAM),
            "seat-start": (seat_start, [], TEAM),
            "team-to-rig": (team_to_rig, [], REPO)}


def main() -> None:
    for name, (draw, legend, out) in DIAGRAMS.items():
        out.mkdir(parents=True, exist_ok=True)
        for suffix, tokens in (("", LIGHT), ("-dark", DARK)):
            slug = name + suffix
            canvas = draw(tokens, slug)
            (out / f"{slug}.svg").write_text(canvas.svg(legend))
            print(f"wrote {(out / f'{slug}.svg').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
