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
- the role guidance carries the rules the team relies on, and none it has dropped;
- every seat this team added or renamed has a profile with its guidance, a member in
  rig.yaml and runtimes in configurations.yaml, and the old names are gone;
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
}

# (guidance file, phrase it must contain, why)
GUIDANCE_RULES = [
    ("lead.md", "rig watchdog", "the slice time limit wakes the lead through a watchdog"),
    ("lead.md", "## Stop and pause", "stop and pause hold work without stopping sessions"),
    ("lead.md", "--wake-after", "waits are queue blocks with a wake"),
    ("lead.md", "--subject commit:<sha>", "the lead judges proof at the commit it checked"),
    ("lead.md", "Never judge without a commit", "a judgement always names a commit"),
    ("lead.md", "judge the slice again", "a rebase that changes the code needs a new judgement"),
    ("planner.md", "`repos:`", "each slice's SPEC.md frontmatter lists the repositories it touches"),
    ("planner.md", "in merge order", "the repositories are listed in the order their pull requests merge"),
    ("release-manager.md", "judged at the commit you are about to push", "only proof judged at the pushed commit publishes"),
    ("builder-backend.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("builder-backend.md", "inside the worktree", "commands run from inside the worktree"),
    ("qa.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("qa.md", "inside the worktree", "commands run from inside the worktree"),
    ("code-reviewer.md", "AGENTS.md", "a slice starts by reading the repository's AGENTS.md"),
    ("code-reviewer.md", "inside the worktree", "commands run from inside the worktree"),
    ("peer.md", "rig watchdog register", "a watchdog wakes the peer; it never polls"),
    ("peer.md", "10 minutes", "the peer takes over only after the lead is down for 10 minutes"),
    ("peer.md", "Never compact the lead", "the peer restores the lead and never compacts it"),
    ("peer.md", "## Hand back", "the peer hands back with a recap"),
    ("planner.md", "wayfinder", "large work with open questions is charted with wayfinder"),
    ("planner.md", "rig scope mission graph", "the build order comes from the mission graph"),
    ("planner.md", "Confirm each triage result with the person", "the planner honours the triage setting"),
    ("planner.md", "UI, backend or both", "each slice is tagged UI, backend or both"),
    ("builder-frontend.md", "builder-backend.md", "the frontend builder runs the backend builder's guidance too"),
    ("builder-frontend.md", "Never use `impeccable live`", "the frontend builder never uses live mode"),
    ("builder-frontend.md", "impeccable detect", "the frontend builder runs the detector itself"),
    ("builder-frontend.md", "screenshot", "each changed state is shown in a real browser"),
    ("release-manager.md", "--force-with-lease", "the release manager pushes rebased branches only with lease"),
    ("release-manager.md", "never `main`", "the release manager never pushes to main"),
    ("release-manager.md", "external:ci", "CI is a queue block with a wake"),
    ("release-manager.md", "release-candidate", "the release manager marks a ready mission release-candidate"),
    ("release-manager.md", "--scope delivery", "the release manager approves each merged slice for delivery"),
]

# (guidance file, phrase it must not contain, why)
FORBIDDEN_RULES = [
    ("lead.md", "Push the builder's branch", "the release manager publishes, not the lead"),
]

# Profiles this team added or renamed from Workshop's, and the guidance files each must deliver.
PROFILE_GUIDANCE = {
    "peer": ["guidance/lead.md", "guidance/peer.md"],
    "planner": ["guidance/planner.md"],
    "builder-backend": ["guidance/builder-backend.md"],
    "builder-frontend": ["guidance/builder-backend.md", "guidance/builder-frontend.md"],
    "release-manager": ["guidance/release-manager.md"],
}
# Seats that hold each profile: pod.member in rig.yaml and configurations.yaml.
SEATS = {"dev.backend": "builder-backend", "dev.frontend": "builder-frontend"}
# Names the team renamed, which no file in it may still use: (pattern, what replaced it).
RETIRED_NAMES = [
    (r"dev[.-]build\b", "the dev.backend seat (dev-backend)"),
    # NOTICE.md still names Workshop's own guidance/builder.md, which is where ours came from.
    (r"profile: builder(?![\w-])|(?<!workshop/guidance/)(?<![\w-])builder\.md|: builder(?![\w-])", "the builder-backend profile and builder-backend.md"),
    (r"(?m)^  builder:$", "the builder-backend profile"),
    (r"(?<![\w-])backend-builder\b", "the builder-backend profile and builder-backend.md"),
    (r"(?<![\w-])frontend-builder\b", "the builder-frontend profile and builder-frontend.md"),
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
    "developing-openrig",
    "openrig-world",
}

# Lower-case names in backticks in the team's text that are not skills: seats, states,
# branches, proof types, and impeccable's own commands.
NOT_SKILLS = {
    # the rig and its seats' sessions
    "shipwrights", "orch-lead", "orch-peer", "plan-planner", "dev-backend", "dev-frontend", "check-qa",
    "review-r1", "review-r2", "release-manager",
    # commands, states, tiers, branches, proof types and roster fields
    "rig", "gh", "cd", "routine", "deep", "running", "stopped", "recoverable", "unknown", "main",
    "release-candidate", "rev1-r1", "rev1-r2", "capabilities", "why",
    # impeccable's own commands
    "shape", "critique", "audit", "polish", "harden", "typeset", "quieter", "distill", "layout", "init", "generate",
}


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


def check_skills_table(rows, profiles, problems):
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
            if seat != "all" and seat not in profiles:
                fail(problems, f"{where}: {skill!r} names {seat!r}, which is no profile")
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
    profiles = set()
    for agent_yaml in sorted(team.glob("agents/*/agent.yaml")):
        profiles.update(profile_blocks(agent_yaml))
    rows = read_skills_table(team, problems)
    listed = check_skills_table(rows, profiles, problems)
    check_guidance_skills(team, rows, listed, problems)
    check_install_script(team, listed, problems)
    check_bundle_skills(team, listed, problems)


def check_guidance(team, problems):
    # Whitespace is collapsed, so a phrase still matches where the text wraps it.
    guidance = {
        path.name: " ".join(path.read_text(encoding="utf-8").split()) for path in team.glob("agents/*/guidance/*.md")
    }
    for name, phrase, why in GUIDANCE_RULES:
        if name not in guidance:
            fail(problems, f"guidance/{name} is missing")
        elif phrase not in guidance[name]:
            fail(problems, f"guidance/{name} lacks {phrase!r}: {why}")
    for name, phrase, why in FORBIDDEN_RULES:
        if phrase in guidance.get(name, ""):
            fail(problems, f"guidance/{name} still has {phrase!r}: {why}")
    for name, text in sorted(guidance.items()):
        if RETRO_PHRASE not in text:
            fail(problems, f"guidance/{name} lacks {RETRO_PHRASE!r}: every seat writes a retrospective note")


def check_seats(team, problems):
    blocks = {}
    for agent_yaml in sorted(team.glob("agents/*/agent.yaml")):
        blocks.update(profile_blocks(agent_yaml))
    rig = (team / "rig.yaml").read_text(encoding="utf-8") if (team / "rig.yaml").is_file() else ""
    seated = set(re.findall(r"^\s*profile:\s*([\w-]+)", rig, re.MULTILINE))
    configured = (team / "configurations.yaml").read_text(encoding="utf-8") if (team / "configurations.yaml").is_file() else ""
    for profile, paths in PROFILE_GUIDANCE.items():
        block = blocks.get(profile)
        if block is None:
            fail(problems, f"agent.yaml has no {profile!r} profile")
            continue
        for path in paths:
            if f"path: {path}" not in block:
                fail(problems, f"the {profile!r} profile doesn't deliver {path}")
        if profile not in seated:
            fail(problems, f"rig.yaml seats no member with the {profile!r} profile")
        if not re.search(rf"(?<![\w-]){re.escape(profile)}(?![\w-])", configured):
            fail(problems, f"configurations.yaml offers no runtime for the {profile!r} profile")
    for seat, profile in SEATS.items():
        member = seat.split(".", 1)[1]
        if not re.search(rf"- id: {re.escape(member)}\n(?:\s+\w+: .*\n)*?\s+profile: {re.escape(profile)}\n", rig):
            fail(problems, f"rig.yaml has no member {member!r} with the {profile!r} profile")
        if not re.search(rf"^\s*{re.escape(seat)}:.*(?<![\w-]){re.escape(profile)}(?![\w-])", configured, re.MULTILINE):
            fail(problems, f"configurations.yaml offers {seat!r} no runtime with the {profile!r} profile")
    for path in sorted(team.rglob("*")):
        try:
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, replacement in RETIRED_NAMES:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                fail(problems, f"{path}:{line}: {match.group(0)!r} was renamed to {replacement}")


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
    check_seats(team, problems)
    check_bundle(team, problems)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{team}: {'ok' if not problems else f'{len(problems)} problems'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
