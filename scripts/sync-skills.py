#!/usr/bin/env python3
"""Keeps a team's skills at the pins its skills.md lists.

usage: scripts/sync-skills.py rigs/<team> [--check | --update [owner/repo ...] [--report FILE]]

skills.md's table is the only list of the team's skills. With no option, this copies each skill
in it from its source at the row's commit into the team's agents/<agent>/vendor/<skill>, removes
copies the table no longer lists, and writes agent.yaml's skill lines from the table: a
declaration for each copy, after the team's own skills in skills/, and each profile's skills,
which are the team's own and those whose Seats cell names the profile's role (a profile is named
<role>-<runtime>) or `all`.

A copy is the skill's folder without its hidden entries (a source's own tooling, such as .github
or plugin manifests), plus the source's licence files when the skill has no licence of its own.

--check says whether every copy matches its source at its pin, and changes nothing.

--update moves each source, or those named, to what skills.md's Sources table says it follows:
the newest release among the tags matching its pattern, or its branch's head. It moves a source
only when that changes one of its skills' copies, then copies them again, bumps the team's patch
version and writes a report for the weekly job: the release notes, and the reasons a person
should read the update before it merges.

Sources are public Git repositories, read with git alone: a shallow, sparse fetch of the pinned
commit. SYNC_SKILLS_GIT_URL replaces https://github.com/{repo}.git, and SYNC_SKILLS_CACHE the
cache of fetched commits (~/.cache/openrig-rigs/skill-sources).

Standard library and git only, as check-team.py is, which reads skills.md with this file's
table() and skill_name().
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

GIT_URL = os.environ.get("SYNC_SKILLS_GIT_URL") or "https://github.com/{repo}.git"
CACHE = Path(os.environ.get("SYNC_SKILLS_CACHE") or Path.home() / ".cache" / "openrig-rigs" / "skill-sources")

# The folder in an agent's folder that holds the copies.
VENDOR_FOLDER = "vendor"
# A licence of the skill's own, and the files a source's licence comes in when it has none.
OWN_LICENCE = re.compile(r"^licen[cs]e", re.IGNORECASE)
SOURCE_LICENCE = re.compile(r"^(LICENSE|LICENCE|NOTICE|THIRD_PARTY_LICENSES)")
# A team version, written quoted, as agent.yaml's `version`.
VERSION = re.compile(r'^version: "(\d+)\.(\d+)\.(\d+)"$', re.MULTILINE)
# The runtime a profile's name ends in, after its role.
RUNTIME_SUFFIX = re.compile(r"-(claude|codex)$")
# A source cell, which links its GitHub repository.
SOURCE_LINK = re.compile(r"\[([\w.-]+/[\w.-]+)\]\(https://github\.com/\1\)")


class SyncError(Exception):
    pass


class Row(NamedTuple):
    skill: str
    repo: str
    path: str
    commit: str
    seats: frozenset  # roles, or `all`


def cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def table(text, first):
    """The rows of the Markdown table whose header's first cell is `first`, each as (line number, {column: cell}). The
    table ends at the first line that isn't a table row, so another table in the same file is never read as part of
    it."""
    rows, header = [], None
    for number, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|"):
            header = None
            continue
        row = cells(line)
        if row[0] == first:
            header = row
        elif header and not set(row[0]) <= set("-: "):
            rows.append((number, dict(zip(header, row))))
    return rows


def skill_name(page):
    """The name in a SKILL.md's frontmatter, or None."""
    front = re.match(r"---\n(.*?)\n---", page.read_text(encoding="utf-8"), re.DOTALL)
    name = re.search(r"^name:\s*['\"]?(.+?)['\"]?\s*$", front.group(1), re.MULTILINE) if front else None
    return name.group(1) if name else None


def repo_of(cell):
    match = SOURCE_LINK.fullmatch(cell)
    if not match:
        raise SyncError(f"{cell!r} is not a GitHub source link")
    return match.group(1)


def read_rows(team):
    """The table's rows. A source has one pin, so its rows share one commit."""
    rows = []
    for number, row in table((team / "skills.md").read_text(), "Skill"):
        skill = row["Skill"].strip("`")
        commit = row["Commit"].strip("`")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise SyncError(f"skills.md:{number}: {skill!r} has no full commit")
        seats = frozenset(seat.strip().strip("`") for seat in row["Seats"].split(",") if seat.strip())
        rows.append(Row(skill, repo_of(row["Source"]), row["Path"].strip("`"), commit, seats))
    if not rows:
        raise SyncError("skills.md has no table of skills")
    for repo in sorted({row.repo for row in rows}):
        if len({row.commit for row in rows if row.repo == repo}) > 1:
            raise SyncError(f"skills.md: the rows from {repo} pin different commits; a source has one pin")
    return rows


def agent_folder(team):
    agents = sorted(team.glob("agents/*/agent.yaml"))
    if len(agents) != 1:
        raise SyncError(f"{team} needs exactly one agents/*/agent.yaml, not {len(agents)}")
    return agents[0].parent


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SyncError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def checkout(repo, commit, paths):
    """A working tree of the source at this commit holding these paths and the top-level files, fetched once and
    cached, since a commit's files never change. A marker written last says the fetch finished, so one cut short is
    fetched again."""
    tree = CACHE / repo.replace("/", "--") / commit
    done = tree / ".git" / "sync-skills-done"
    if not done.is_file():
        shutil.rmtree(tree, ignore_errors=True)
        tree.mkdir(parents=True)
        git(tree, "init", "-q")
        git(tree, "remote", "add", "origin", GIT_URL.format(repo=repo))
        git(tree, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit)
        if "." not in paths:
            git(tree, "sparse-checkout", "set", "--cone", *paths)
        git(tree, "checkout", "-q", "FETCH_HEAD")
        done.touch()
    elif "." in paths:
        git(tree, "sparse-checkout", "disable")
    elif git(tree, "config", "--bool", "--default", "false", "core.sparseCheckout") == "true":
        git(tree, "sparse-checkout", "add", *paths)
    return tree


def copy_skill(root, path, dest):
    """Copies the skill at `path` in a source's tree to `dest`, as the module docstring says."""
    src = root if path == "." else root / path
    if not (src / "SKILL.md").is_file():
        raise SyncError(f"no SKILL.md at {path}")
    partial = dest.with_name(dest.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    for entry in sorted(src.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.copytree(entry, partial / entry.name, symlinks=True)
        else:
            shutil.copy2(entry, partial / entry.name, follow_symlinks=False)
    if not any(OWN_LICENCE.match(entry.name) for entry in partial.iterdir()):
        for entry in sorted(root.iterdir()):
            if entry.is_file() and SOURCE_LICENCE.match(entry.name):
                shutil.copy2(entry, partial / entry.name)
    shutil.rmtree(dest, ignore_errors=True)
    partial.rename(dest)


def copy_skills(rows, into, missing=None):
    """Writes every row's copy under `into`, and removes folders there that no row names. A skill its source no
    longer has stops the sync, or, given a `missing` list, is added to it and skipped."""
    into.mkdir(parents=True, exist_ok=True)
    by_pin = {}
    for row in rows:
        by_pin.setdefault((row.repo, row.commit), []).append(row)
    for (repo, commit), pinned in by_pin.items():
        tree = checkout(repo, commit, sorted({row.path for row in pinned}))
        for row in pinned:
            try:
                copy_skill(tree, row.path, into / row.skill)
            except SyncError as error:
                if missing is None:
                    raise SyncError(f"{row.skill}: {repo}@{commit[:7]}: {error}") from None
                missing.append(row.skill)
    for leftover in sorted({p.name for p in into.iterdir()} - {row.skill for row in rows}):
        shutil.rmtree(into / leftover)


def write_agent(agent_yaml, rows):
    """Writes agent.yaml's skill declarations and each profile's skills from the table, as the module docstring says.
    It reads the layout the team writes: `resources:` then `  skills:` with one flow-style entry per line, and each
    profile's `      skills: [...]` on one line."""
    text = agent_yaml.read_text()
    declared = re.search(r"^resources:\n  skills:\n((?:    - \{.*\}\n)*)", text, re.MULTILINE)
    if not declared:
        raise SyncError(f"{agent_yaml}: no resources.skills list, one `- {{ id: ..., path: ... }}` a line")
    own_lines = [line for line in declared.group(1).splitlines(keepends=True) if "path: skills/" in line]
    own = re.findall(r"id:\s*([\w.-]+)", "".join(own_lines))
    copies = [f"    - {{ id: {row.skill}, path: {VENDOR_FOLDER}/{row.skill}, on_restore: follow_source }}\n"
              for row in rows]
    text = text[:declared.start(1)] + "".join(own_lines + copies) + text[declared.end(1):]

    def select(match):
        role = RUNTIME_SUFFIX.sub("", match.group(1))
        skills = own + [row.skill for row in rows if row.seats & {role, "all"}]
        return re.sub(r"^(      skills:\s*)\[[^\]]*\]", lambda m: f"{m.group(1)}[{', '.join(skills)}]",
                      match.group(0), count=1, flags=re.MULTILINE)

    head, profiles = text.split("\nprofiles:\n", 1) if "\nprofiles:\n" in text else (text, "")
    profiles = re.sub(r"^  ([\w-]+):\n(?:(?:    .*)?\n)*", select, profiles, flags=re.MULTILINE)
    agent_yaml.write_text(head + ("\nprofiles:\n" + profiles if profiles else ""))


class Source(NamedTuple):
    repo: str
    follows: str  # a tag pattern holding <version>, or a branch
    tags: bool  # whether `follows` is a tag pattern
    release: str  # the tag at the pin, or "none"
    line: int


def read_sources(text):
    """The Sources table: what each source's pin follows, and the release it is at."""
    sources = []
    for number, row in table(text, "Source"):
        match = re.fullmatch(r"`([^`]+)`( tags)?", row.get("Follows", ""))
        if not match or bool(match.group(2)) != ("<version>" in match.group(1)):
            raise SyncError(f"skills.md:{number}: Follows is a tag pattern holding <version>, as `v<version>` "
                            "tags, or a branch, as `main`")
        sources.append(Source(repo_of(row["Source"]), match.group(1), bool(match.group(2)), row["Release"], number))
    return sources


def newest(source):
    """The commit a source's pin should be at now, and its release: the highest version among the tags its pattern
    matches, or the head of the branch it follows."""
    url = GIT_URL.format(repo=source.repo)
    if not source.tags:
        head = git(None, "ls-remote", url, f"refs/heads/{source.follows}").split()
        if not head:
            raise SyncError(f"{source.repo} has no branch {source.follows!r}")
        return head[0], "none"
    prefix, suffix = (re.escape(part) for part in source.follows.split("<version>", 1))
    pattern = re.compile(rf"refs/tags/({prefix}(\d+)\.(\d+)\.(\d+){suffix})(\^\{{\}})?")
    tags = {}
    for line in git(None, "ls-remote", "--tags", url).splitlines():
        commit, ref = line.split("\t")
        if match := pattern.fullmatch(ref):
            # An annotated tag's own line names the tag object; its peeled line (^{}) names the commit.
            if match.group(5) or match.group(1) not in tags:
                tags[match.group(1)] = (tuple(int(n) for n in match.group(2, 3, 4)), commit)
    if not tags:
        raise SyncError(f"{source.repo} has no tag matching {source.follows}")
    tag = max(tags, key=lambda name: tags[name][0])
    return tags[tag][1], tag


def licence_files(folder):
    return {path.name: path.read_bytes() for path in sorted(folder.iterdir())
            if path.is_file() and (OWN_LICENCE.match(path.name) or SOURCE_LICENCE.match(path.name))}


def hold_reasons(rows, fresh, vendored, missing, label):
    """Why a person should read this update before it merges: a skill gone from its source, one renamed, or a
    licence changed."""
    reasons = []
    for row in rows:
        old, new = vendored / row.skill, fresh / row.skill
        if row.skill in missing:
            reasons.append(f"`{row.skill}` is gone from {row.repo} at {label}: there's no SKILL.md at `{row.path}`")
            continue
        if (name := skill_name(new / "SKILL.md")) != row.skill:
            reasons.append(f"`{row.skill}`'s SKILL.md is named {name!r} at {label}, so seats can't select it as "
                           f"`{row.skill}`")
        if old.is_dir() and licence_files(old) != licence_files(new):
            reasons.append(f"`{row.skill}`'s licence changed at {label}: check the Licence column and NOTICE.md")
    return reasons


def bump_patch(agent_yaml):
    text = agent_yaml.read_text()
    match = VERSION.search(text)
    if not match:
        raise SyncError(f'{agent_yaml}: version is not "<major>.<minor>.<patch>"')
    major, minor, patch = (int(n) for n in match.groups())
    version = f"{major}.{minor}.{patch + 1}"
    agent_yaml.write_text(text[:match.start()] + f'version: "{version}"' + text[match.end():])
    return version


def set_release(line, header, release):
    """A Sources table row with its Release cell set."""
    row = cells(line)
    row[header.index("Release")] = release
    return "| " + " | ".join(row) + " |\n"


def update(team, only):
    """Moves each source (or only those named) to the commit `newest` gives, where that changes any of its skills'
    copies, rewriting skills.md's pins and copying the skills again. Returns the report the weekly job reads."""
    table_path = team / "skills.md"
    lines = table_path.read_text().splitlines(keepends=True)
    rows, sources = read_rows(team), read_sources("".join(lines))
    unknown = set(only) - {source.repo for source in sources}
    if unknown:
        raise SyncError(f"skills.md's Sources table has no {', '.join(sorted(unknown))}")
    folder = agent_folder(team)
    vendored = folder / VENDOR_FOLDER
    notes, reasons = [], []
    for source in sources:
        if only and source.repo not in only:
            continue
        source_rows = [row for row in rows if row.repo == source.repo]
        commit, release = newest(source)
        if not source_rows or source_rows[0].commit == commit:
            continue
        old = source_rows[0].commit
        moved = [row._replace(commit=commit) for row in source_rows]
        label = release if source.tags else commit[:7]
        with tempfile.TemporaryDirectory() as tmp:
            fresh, missing = Path(tmp), []
            copy_skills(moved, fresh, missing)
            changed = [row.skill for row in source_rows if row.skill in missing
                       or files(fresh / row.skill) != files(vendored / row.skill)]
            if not changed:
                continue
            reasons += hold_reasons(moved, fresh, vendored, missing, label)
            for skill in changed:
                shutil.rmtree(vendored / skill, ignore_errors=True)
                if skill not in missing:
                    shutil.copytree(fresh / skill, vendored / skill, symlinks=True)
        for number, row in table("".join(lines), "Skill"):
            if repo_of(row["Source"]) == source.repo:
                lines[number - 1] = lines[number - 1].replace(f"`{old}`", f"`{commit}`", 1)
        header = next(cells(line) for line in reversed(lines[:source.line]) if cells(line)[0] == "Source")
        lines[source.line - 1] = set_release(lines[source.line - 1], header, release)
        was = f"{source.release} (`{old[:7]}`)" if source.tags and source.release != "none" else f"`{old[:7]}`"
        now = f"{release} (`{commit[:7]}`)" if source.tags else f"`{commit[:7]}`"
        notes.append(f"- [{source.repo}](https://github.com/{source.repo}): {was} → {now} "
                     f"([compare](https://github.com/{source.repo}/compare/{old}...{commit})): "
                     + ", ".join(f"`{skill}`" for skill in changed))
    if not notes:
        return {"changed": False}
    table_path.write_text("".join(lines))
    version = bump_patch(folder / "agent.yaml")
    return {"changed": True, "team": team.name, "version": version, "holds": reasons,
            "notes": "The weekly update of the team's skills.\n\n" + "\n".join(notes) + "\n"}


def files(folder):
    """Each file under a folder by its path there, as (bytes, executable), with a symlink as its target."""
    found = {}
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder).as_posix()
        if path.is_symlink():
            found[rel] = (os.readlink(path).encode(), False)
        elif path.is_file():
            found[rel] = (path.read_bytes(), os.access(path, os.X_OK))
    return found


def differences(expected, actual):
    """How the vendored folder `actual` differs from the fresh copy `expected`, one line each."""
    want, have = files(expected), files(actual)
    lines = [f"{rel} is missing" for rel in sorted(want.keys() - have.keys())]
    lines += [f"{rel} isn't in its source" for rel in sorted(have.keys() - want.keys())]
    lines += [f"{rel} differs from its source" for rel in sorted(want.keys() & have.keys()) if want[rel] != have[rel]]
    return lines


def check(rows, vendored):
    """The differences between the vendored copies and fresh copies at the table's pins."""
    if not vendored.is_dir():
        return [f"{vendored} is missing"]
    with tempfile.TemporaryDirectory() as fresh:
        copy_skills(rows, Path(fresh))
        return [f"{vendored.name}/{line}" for line in differences(Path(fresh), vendored)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("team", type=Path, help="the team folder, such as rigs/shipwrights")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="say whether the vendored copies match the table's "
                      "pins, and change nothing")
    mode.add_argument("--update", nargs="*", metavar="SOURCE", help="move every source, or these (owner/repo), to "
                      "its newest release or branch head, and bump the team's patch version")
    parser.add_argument("--report", type=Path, help="with --update, write what changed, as JSON, to this file")
    args = parser.parse_args()
    if args.report and args.update is None:
        parser.error("--report goes with --update")
    team = args.team
    try:
        rows = read_rows(team)
        folder = agent_folder(team)
        vendored = folder / VENDOR_FOLDER
        if args.check:
            problems = check(rows, vendored)
            for problem in problems:
                print(problem, file=sys.stderr)
            print(f"{team}: {'vendored skills match their pins' if not problems else f'{len(problems)} differences'}")
            return 1 if problems else 0
        if args.update is not None:
            report = update(team, args.update)
            if args.report:
                args.report.write_text(json.dumps(report, indent=2) + "\n")
            print(f"{team}: " + (f"{report['version']}, {len(report['holds'])} holds" if report["changed"]
                                 else "every source is at its newest"))
            return 0
        copy_skills(rows, vendored)
        write_agent(folder / "agent.yaml", rows)
    except SyncError as error:
        print(f"sync-skills: {error}", file=sys.stderr)
        return 1
    print(f"{team}: copied {len(rows)} skills and wrote agent.yaml's skill lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
