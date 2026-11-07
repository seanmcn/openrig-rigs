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
LANES = ["You", "Lead & planner", "Builder & QA", "Reviewers", "Release manager"]


def work(t: Tokens, slug: str) -> Canvas:
    steps = [  # (lane, name, sublabel, kind), one per row
        (0, "Your goal", "an issue or a request", "step"),
        (1, "Cut and lock", "mission, slices, specs", "step"),
        (2, "Build", "commit in a worktree", "step"),
        (2, "QA checks", "at that commit", "step"),
        (3, "Review", "r1 and r2, apart", "step"),
        (1, "Judge proof", "at that commit", "step"),
        (4, "Open pull requests", "with the merge gate", "step"),
        (0, "Merge", "your decision", "focal"),
        (4, "Approve delivery", "the slice is done", "step"),
    ]
    rows = len(steps)
    bottom = 56 + (rows - 1) * ROW + NODE_H + 16
    c = Canvas(t, slug, LANE_W * len(LANES), bottom + 48, "How the work moves",
               "A slice goes from your goal through the lead, a builder and QA until QA passes, then two reviewers, "
               "the lead's judgement and the release manager, to your merge and its delivery; reviewers' findings "
               "go back to the builder and through QA again.")
    c.legend_x = (LANE_W - NODE_W) // 2
    for k, lane in enumerate(LANES):
        c.eyebrow(k * LANE_W + LANE_W / 2, 28, lane)
        if k:
            c.line(k * LANE_W, 12, k * LANE_W, bottom)
    c.line(0, 40, LANE_W * len(LANES), 40)

    def box(row: int) -> tuple[int, int]:
        return steps[row][0] * LANE_W + (LANE_W - NODE_W) // 2, 56 + row * ROW

    for row, (_, name, sub, kind) in enumerate(steps):
        x, y = box(row)
        c.node(x, y, NODE_W, NODE_H, name, sub, kind)

    def handoff(row: int) -> None:
        """Out of the side facing the next step's lane, across, then down into its top."""
        (x, y), (nx, ny) = box(row), box(row + 1)
        cy, ncx = y + NODE_H / 2, nx + NODE_W / 2
        start = x + NODE_W if steps[row + 1][0] > steps[row][0] else x
        kind = "accent" if steps[row + 1][3] == "focal" else "muted"
        c.arrow([(start, cy), (ncx, cy), (ncx, ny)], kind)

    for row in (0, 1, 3, 4, 5, 6, 7):
        handoff(row)

    # Build and QA, one lane: down to QA, and back up when it fails.
    (bx, by), (qx, qy) = box(2), box(3)
    bcx = bx + NODE_W / 2
    c.arrow([(bcx - 24, by + NODE_H), (bcx - 24, qy)])
    c.arrow([(bcx + 24, qy), (bcx + 24, by + NODE_H)], "dashed")
    c.label(bcx + 32, (by + NODE_H + qy) / 2 + 3, "fails", anchor="start")
    c.label(3 * LANE_W + 48, qy + NODE_H / 2 - 10, "passes")

    # Reviewers' findings go back to the builder, and so through QA again. The label stays clear of the next lane's rule.
    rx, ry = box(4)
    fx = rx + NODE_W / 2 + 24
    c.arrow([(fx, ry), (fx, by + NODE_H / 2), (bx + NODE_W, by + NODE_H / 2)], "dashed")
    c.label(fx + 8, (by + NODE_H / 2 + ry) / 2 + 3, "findings", anchor="start")
    return c


# A slice's lifecycle: phases, a hold, and its outcomes. -------------------------------------------------------------

PW, GAP = 128, 56


def lifecycle(t: Tokens, slug: str) -> Canvas:
    c = Canvas(t, slug, 920, 424, "A slice's lifecycle",
               "A slice's spec is locked, then it is built and checked by QA until QA passes, reviewed, judged, and "
               "its pull requests published; findings, a failing CI run and a rebase loop back, it can be paused or "
               "stopped from any phase, and it is delivered once you merge.")
    c.legend_x = 24
    rail_y = 104
    xs = [24 + i * (PW + GAP) for i in range(5)]
    phases = [("Spec locked", "lead"), ("Building", "builder and QA"), ("In review", "r1 and r2"),
              ("Judged", "lead"), ("Published", "release manager")]
    c.eyebrow(24, 20, "Phases", anchor="start")
    for x, (name, sub) in zip(xs, phases):
        c.node(x, rail_y, PW, NODE_H, name, sub)

    cy = rail_y + NODE_H / 2
    for i, word in enumerate(["assign", "qa pass", "pass", "push"]):
        c.arrow([(xs[i] + PW, cy), (xs[i + 1], cy)])
        c.label(xs[i] + PW + GAP / 2, cy - 10, word)

    # Loops back, above the rail: two short ones, and CI's long one over both, each on its own attach points.
    top = rail_y - 24
    for later, earlier, word in ((2, 1, "findings"), (4, 3, "rebase")):
        sx, ex = xs[later] + 40, xs[earlier] + 88
        c.arrow([(sx, rail_y), (sx, top), (ex, top), (ex, rail_y)], "dashed")
        c.label((sx + ex) / 2, top - 10, word)
    high = top - 40
    sx, ex = xs[4] + 88, xs[1] + 40
    c.arrow([(sx, rail_y), (sx, high), (ex, high), (ex, rail_y)], "dashed")
    c.label((sx + ex) / 2, high - 10, "ci fails")

    # From any phase: a bracket under the rail that pause and stop leave from.
    bracket_y, bracket_end = rail_y + 72, xs[4] + 56
    c.line(24, bracket_y, bracket_end, bracket_y, t.muted)
    c.line(24, bracket_y - 8, 24, bracket_y, t.muted)
    c.line(bracket_end, bracket_y - 8, bracket_end, bracket_y, t.muted)
    c.label(xs[2] + PW / 2, bracket_y - 8, "from any phase")

    held_y = bracket_y + 44
    c.eyebrow(24, held_y - 12, "Held", anchor="start")
    px = xs[1]
    c.node(px, held_y, PW, NODE_H, "Paused", "rows blocked", "held")
    c.arrow([(px + 40, bracket_y), (px + 40, held_y)])
    c.label(px + 32, bracket_y + 26, "pause", anchor="end")
    c.arrow([(px + 88, held_y), (px + 88, bracket_y)], "dashed")
    c.label(px + 96, bracket_y + 26, "resume", anchor="start")

    out_y = held_y + 92
    c.eyebrow(24, out_y - 12, "Outcomes", anchor="start")
    sx = xs[0] + 96
    c.node(xs[0], out_y, PW, NODE_H, "Stopped", "rows closed", "end")
    c.arrow([(sx, bracket_y), (sx, out_y)])
    c.label(sx + 8, bracket_y + 26, "stop", anchor="start")

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
        ("every seat", "Start steps", "startup/context.md", ""),
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


# The team's seats: its five pods, each seat's runtime, and who hands work to whom. -------------------------------

def seats(t: Tokens, slug: str) -> Canvas:
    w, h, pad, gap = 136, 48, 16, 64
    zone_y, zone_h, row1, row2 = 212, 160, 228, 308
    side = w + 2 * pad  # a pod of one column

    # The bottom row of pods, left to right in the order work reaches them.
    plan_x = 24
    dev_x = plan_x + side + 24
    dev_w = 2 * w + 12 + 2 * pad
    review_x = dev_x + dev_w + gap
    release_x = review_x + side + 24
    width = release_x + side + 24
    c = Canvas(t, slug, width, 436, "Shipwrights' seats",
               "The lead, with its peer on the other runtime, hands goals to the planner, slices to the builders and "
               "judged slices to the release manager; the builders hand each commit to QA, then to two reviewers on "
               "different runtimes.")
    c.legend_x = 24
    for name, x, zw in (("plan", plan_x, side), ("dev", dev_x, dev_w), ("review", review_x, side),
                        ("release", release_x, side)):
        c.rect(x, zone_y, zw, zone_h, rx=8)
        c.eyebrow(x, zone_y - 8, name, anchor="start")
    backend_x, frontend_x = dev_x + pad, dev_x + pad + w + 12
    qa_x = dev_x + (dev_w - w) // 2
    c.node(plan_x + pad, row1, w, h, "Planner", "Claude Code")
    c.node(backend_x, row1, w, h, "Backend builder", "Claude Code")
    c.node(frontend_x, row1, w, h, "Frontend builder", "Claude Code")
    c.node(qa_x, row2, w, h, "QA", "Claude Code")
    c.node(review_x + pad, row1, w, h, "Reviewer r1", "Claude Code")
    c.node(review_x + pad, row2, w, h, "Reviewer r2", "Codex")
    c.node(release_x + pad, row1, w, h, "Release manager", "Codex")

    # The orch pod on top: the lead, which you talk to, and its peer on the other runtime.
    lead_x, orch_y = dev_x + dev_w // 2 + 16, 76
    peer_x = lead_x + w + gap
    c.rect(lead_x - pad, orch_y - pad, 2 * w + gap + 2 * pad, h + 2 * pad, rx=8)
    c.eyebrow(lead_x - pad, orch_y - pad - 8, "orch", anchor="start")
    c.node(lead_x, orch_y, w, h, "Lead", "Codex", "focal")
    c.node(peer_x, orch_y, w, h, "Peer", "Claude Code")
    lcx = lead_x + w / 2
    c.arrow([(lcx, 8), (lcx, orch_y)], "accent")
    c.label(lcx + 8, 36, "your goal", anchor="start", accent=True)
    c.arrow([(peer_x, orch_y + h / 2), (lead_x + w, orch_y + h / 2)], "dashed")
    c.label((peer_x + lead_x + w) / 2, orch_y + h / 2 - 8, "follows")

    # The lead's handoffs fan out of its bottom edge, each from its own point.
    bottom = orch_y + h
    planner_cx, dev_cx, release_cx = plan_x + side / 2, dev_x + dev_w / 2, release_x + side / 2
    c.arrow([(lcx - 36, bottom), (lcx - 36, 172), (planner_cx, 172), (planner_cx, row1)])
    c.label((planner_cx + lcx - 36) / 2, 164, "goals")
    c.arrow([(lcx, bottom), (lcx, 184), (dev_cx, 184), (dev_cx, zone_y)])
    c.label(dev_cx + 8, 200, "slices", anchor="start")
    c.arrow([(lcx + 36, bottom), (lcx + 36, 172), (release_cx, 172), (release_cx, row1)])
    c.label((lcx + 36 + release_cx) / 2, 164, "judged slices")

    # Each builder hands its commit to QA, where the two boxes overlap, and the pod hands it to the reviewers once QA
    # passes it.
    c.arrow([((qa_x + backend_x + w) / 2, row1 + h), ((qa_x + backend_x + w) / 2, row2)])
    c.arrow([((frontend_x + qa_x + w) / 2, row1 + h), ((frontend_x + qa_x + w) / 2, row2)])
    c.arrow([(dev_x + dev_w, row1 + h / 2), (review_x, row1 + h / 2)])
    c.label(dev_x + dev_w + gap / 2, row1 + h / 2 - 8, "qa passed")
    return c


# name: (draw, legend, where its SVGs go)
DIAGRAMS = {"seats": (seats, [("focal", "the seat you talk to"), ("dashed", "follows, and takes over if it's down")],
                      TEAM),
            "how-the-work-moves": (work, [("focal", "your step"), ("dashed", "back to an earlier step")], TEAM),
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
