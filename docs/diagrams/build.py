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
OUT = ROOT / "rigs" / "shipwrights" / "diagrams"

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
        self.back: list[str] = []  # connectors and lines, drawn before nodes
        self.front: list[str] = []

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
        x = 0
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

    # Reviewers' findings go back to the builder, and so through QA again.
    rx, ry = box(4)
    fx = rx + NODE_W / 2 + 32
    c.arrow([(fx, ry), (fx, by + NODE_H / 2), (bx + NODE_W, by + NODE_H / 2)], "dashed")
    c.label(fx + 8, (by + NODE_H / 2 + ry) / 2 + 3, "findings", anchor="start")
    return c


# A slice's lifecycle: phases, a hold, and its outcomes. -------------------------------------------------------------

PW, GAP = 128, 56


def lifecycle(t: Tokens, slug: str) -> Canvas:
    c = Canvas(t, slug, 920, 400, "A slice's lifecycle",
               "A slice's spec is locked, then it is built and checked by QA until QA passes, reviewed, judged, and "
               "its pull requests published; findings and rebases loop back, it can be paused or stopped from any phase, and it is "
               "delivered once you merge.")
    rail_y = 80
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

    # Loops back, above the rail.
    top = rail_y - 24
    for later, earlier, word in ((2, 1, "findings"), (4, 3, "rebase")):
        sx, ex = xs[later] + 40, xs[earlier] + 88
        c.arrow([(sx, rail_y), (sx, top), (ex, top), (ex, rail_y)], "dashed")
        c.label((sx + ex) / 2, top - 10, word)

    # From any phase: a bracket under the rail that pause and stop leave from.
    bracket_y, bracket_end = 152, xs[4] + 56
    c.line(24, bracket_y, bracket_end, bracket_y, t.muted)
    c.line(24, bracket_y - 8, 24, bracket_y, t.muted)
    c.line(bracket_end, bracket_y - 8, bracket_end, bracket_y, t.muted)
    c.label(xs[2] + PW / 2, bracket_y - 8, "from any phase")

    held_y = 196
    c.eyebrow(24, held_y - 12, "Held", anchor="start")
    px = xs[1]
    c.node(px, held_y, PW, NODE_H, "Paused", "rows blocked", "held")
    c.arrow([(px + 40, bracket_y), (px + 40, held_y)])
    c.label(px + 32, bracket_y + 26, "pause", anchor="end")
    c.arrow([(px + 88, held_y), (px + 88, bracket_y)], "dashed")
    c.label(px + 96, bracket_y + 26, "resume", anchor="start")

    out_y = 288
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


DIAGRAMS = {"how-the-work-moves": (work, [("focal", "your step"), ("dashed", "back to an earlier step")]),
            "slice-lifecycle": (lifecycle, [("focal", "the outcome you want"), ("held", "held, resumable"),
                                            ("dashed", "back to an earlier phase")])}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (draw, legend) in DIAGRAMS.items():
        for suffix, tokens in (("", LIGHT), ("-dark", DARK)):
            slug = name + suffix
            canvas = draw(tokens, slug)
            (OUT / f"{slug}.svg").write_text(canvas.svg(legend))
            print(f"wrote {(OUT / f'{slug}.svg').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
