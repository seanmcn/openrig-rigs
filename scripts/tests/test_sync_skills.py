"""sync-skills.py, run as a person or the weekly job runs it, against local Git repositories standing in for GitHub."""

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "sync-skills.py"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Source:
    """A Git repository holding skills, as a GitHub source would."""

    def __init__(self, root, repo):
        self.repo = repo
        self.path = Path(root, "github", repo)
        self.path.mkdir(parents=True)
        git(self.path, "init", "-q", "-b", "main")
        git(self.path, "config", "user.email", "test@example.com")
        git(self.path, "config", "user.name", "Test")
        # GitHub serves any commit by its SHA, and partial clones; a local repository does only when told to.
        git(self.path, "config", "uploadpack.allowReachableSHA1InWant", "true")
        git(self.path, "config", "uploadpack.allowFilter", "true")

    def commit(self, files, tag=None):
        for name, text in files.items():
            path = self.path / name
            if text is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", "change", "--allow-empty")
        if tag:
            git(self.path, "tag", "-a", tag, "-m", tag)
        return git(self.path, "rev-parse", "HEAD")


def skill_page(name, body="Do the thing."):
    return f"---\nname: {name}\ndescription: {name} for tests\n---\n\n{body}\n"


class SyncSkillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.team = self.root / "team"
        (self.team / "agents" / "acme").mkdir(parents=True)
        self.env = dict(
            os.environ,
            SYNC_SKILLS_GIT_URL=f"file://{self.root}/github/{{repo}}",
            SYNC_SKILLS_CACHE=str(self.root / "cache"),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_team(self, skills, sources, version="2.0.0"):
        """skills: (skill, repo, path, commit, licence[, seats]); sources: (repo, follows, release)."""
        rows = "\n".join(
            f"| `{skill}` | [{repo}](https://github.com/{repo}) | `{path}` | `{commit}` | {licence} | "
            f"{seats[0] if seats else 'all'} | required |"
            for skill, repo, path, commit, licence, *seats in skills
        )
        source_rows = "\n".join(
            f"| [{repo}](https://github.com/{repo}) | {follows} | {release} |" for repo, follows, release in sources
        )
        (self.team / "skills.md").write_text(textwrap.dedent("""\
            # Skills

            | Skill | Source | Path | Commit | Licence | Seats | Need |
            | --- | --- | --- | --- | --- | --- | --- |
            {rows}

            ## Sources

            | Source | Follows | Release |
            | --- | --- | --- |
            {source_rows}
            """).format(rows=rows, source_rows=source_rows))
        self.agent_yaml.write_text(textwrap.dedent(f"""\
            name: acme
            version: "{version}"

            resources:
              skills:
                - {{ id: own-skill, path: skills/own-skill, on_restore: follow_source }}
                - {{ id: dropped, path: vendor/dropped, on_restore: follow_source }}
              plugins: []

            profiles:
              lead-claude:
                summary: Leads.
                uses:
                  skills: [own-skill, dropped]
              qa-codex:
                summary: Tests.
                uses:
                  skills: [own-skill]
            """))

    @property
    def agent_yaml(self):
        return self.team / "agents" / "acme" / "agent.yaml"

    def run_sync(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.team), *args],
                              capture_output=True, text=True, env=self.env)

    def vendored(self, skill):
        return self.team / "agents" / "acme" / "vendor" / skill

    def test_vendors_each_skill_at_its_pin_without_hidden_files_and_with_the_source_licence(self):
        source = Source(self.root, "acme/skills")
        pinned = source.commit({
            "LICENSE": "MIT licence text\n",
            "README.md": "the repo's readme\n",
            "skills/tdd/SKILL.md": skill_page("tdd"),
            "skills/tdd/references/loop.md": "red, green\n",
            "skills/tdd/.github/workflow.yml": "tooling\n",
        }, tag="v1.0.0")
        source.commit({"skills/tdd/SKILL.md": skill_page("tdd", "A later version.")})
        self.write_team([("tdd", "acme/skills", "skills/tdd", pinned, "MIT")], [("acme/skills", "`v<version>` tags", "v1.0.0")])

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        copy = self.vendored("tdd")
        self.assertEqual(sorted(str(p.relative_to(copy)) for p in copy.rglob("*") if p.is_file()),
                         ["LICENSE", "SKILL.md", "references/loop.md"])
        self.assertIn("Do the thing.", (copy / "SKILL.md").read_text())
        self.assertEqual((copy / "LICENSE").read_text(), "MIT licence text\n")

    def test_vendoring_declares_each_skill_and_gives_each_profile_its_roles_skills_from_the_table(self):
        source = Source(self.root, "acme/skills")
        pinned = source.commit({"LICENSE": "MIT\n", "tdd/SKILL.md": skill_page("tdd"),
                                "retro/SKILL.md": skill_page("retro"), "lint/SKILL.md": skill_page("lint")})
        self.write_team([("tdd", "acme/skills", "tdd", pinned, "MIT", "qa"),
                         ("retro", "acme/skills", "retro", pinned, "MIT", "lead"),
                         ("lint", "acme/skills", "lint", pinned, "MIT", "all")],
                        [("acme/skills", "`main`", "none")])

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.agent_yaml.read_text()
        declared = re.search(r"  skills:\n((?:    - .*\n)+)", text).group(1)
        self.assertEqual(declared.splitlines(), [
            "    - { id: own-skill, path: skills/own-skill, on_restore: follow_source }",
            "    - { id: tdd, path: vendor/tdd, on_restore: follow_source }",
            "    - { id: retro, path: vendor/retro, on_restore: follow_source }",
            "    - { id: lint, path: vendor/lint, on_restore: follow_source }",
        ])
        self.assertIn("  lead-claude:\n    summary: Leads.\n    uses:\n      skills: [own-skill, retro, lint]\n", text)
        self.assertIn("  qa-codex:\n    summary: Tests.\n    uses:\n      skills: [own-skill, tdd, lint]\n", text)
        self.assertIn("  plugins: []\n", text)

    def test_check_passes_on_a_clean_copy_and_names_every_difference_otherwise(self):
        source = Source(self.root, "acme/skills")
        pinned = source.commit({
            "LICENSE": "MIT\n",
            "skills/tdd/SKILL.md": skill_page("tdd"),
            "skills/pr/SKILL.md": skill_page("pr"),
            "skills/pr/template.md": "a template\n",
        })
        self.write_team([("tdd", "acme/skills", "skills/tdd", pinned, "MIT"),
                         ("pr", "acme/skills", "skills/pr", pinned, "MIT")],
                        [("acme/skills", "`main`", "none")])
        self.assertEqual(self.run_sync().returncode, 0)

        clean = self.run_sync("--check")
        self.assertEqual(clean.returncode, 0, clean.stderr)

        (self.vendored("tdd") / "SKILL.md").write_text(skill_page("tdd", "Edited here."))
        (self.vendored("tdd") / "notes.md").write_text("added here\n")
        (self.vendored("pr") / "template.md").unlink()
        (self.vendored("stale")).mkdir()
        (self.vendored("stale") / "SKILL.md").write_text(skill_page("stale"))

        dirty = self.run_sync("--check")

        self.assertEqual(dirty.returncode, 1)
        for expected in ("tdd/SKILL.md differs", "tdd/notes.md isn't in", "pr/template.md is missing", "stale"):
            self.assertIn(expected, dirty.stderr)
        self.assertIn("Edited here.", (self.vendored("tdd") / "SKILL.md").read_text(), "--check changes nothing")

    def update(self, *sources):
        report = self.root / "report.json"
        result = self.run_sync("--update", *sources, "--report", str(report))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(report.read_text())

    def test_update_moves_a_source_to_its_newest_release_and_releases_a_patch_version(self):
        source = Source(self.root, "acme/skills")
        first = source.commit({"LICENSE": "MIT\n", "skills/tdd/SKILL.md": skill_page("tdd")}, tag="skill-v1.2.0")
        source.commit({"skills/tdd/SKILL.md": skill_page("tdd", "Release two.")}, tag="skill-v1.10.0")
        newest = git(source.path, "rev-parse", "HEAD")
        source.commit({"skills/tdd/SKILL.md": skill_page("tdd", "The CLI's release.")}, tag="cli-v9.0.0")
        source.commit({"skills/tdd/SKILL.md": skill_page("tdd", "Unreleased.")})
        self.write_team([("tdd", "acme/skills", "skills/tdd", first, "MIT")],
                        [("acme/skills", "`skill-v<version>` tags", "skill-v1.2.0")])
        self.run_sync()

        report = self.update()

        table = (self.team / "skills.md").read_text()
        self.assertIn(f"`{newest}`", table)
        self.assertNotIn(first, table)
        self.assertIn("| [acme/skills](https://github.com/acme/skills) | `skill-v<version>` tags | skill-v1.10.0 |", table)
        self.assertIn("Release two.", (self.vendored("tdd") / "SKILL.md").read_text())
        self.assertIn('version: "2.0.1"', (self.agent_yaml).read_text())
        self.assertEqual(report["version"], "2.0.1")
        self.assertEqual(report["holds"], [])
        self.assertIn("acme/skills", report["notes"])
        self.assertIn(f"skill-v1.2.0 (`{first[:7]}`) → skill-v1.10.0 (`{newest[:7]}`)", report["notes"])
        self.assertIn(f"https://github.com/acme/skills/compare/{first}...{newest}", report["notes"])
        self.assertIn("`tdd`", report["notes"])
        self.assertEqual(self.run_sync("--check").returncode, 0)

    def test_update_follows_a_branch_and_leaves_a_pin_whose_skills_did_not_change(self):
        source = Source(self.root, "acme/skills")
        pinned = source.commit({"LICENSE": "MIT\n", "skills/tdd/SKILL.md": skill_page("tdd")})
        source.commit({"README.md": "only the repo's readme moved\n"})
        self.write_team([("tdd", "acme/skills", "skills/tdd", pinned, "MIT")], [("acme/skills", "`main`", "none")])
        self.run_sync()
        before = (self.team / "skills.md").read_text()

        self.assertEqual(self.update(), {"changed": False})
        self.assertEqual((self.team / "skills.md").read_text(), before)
        self.assertIn('version: "2.0.0"', (self.agent_yaml).read_text())

        head = source.commit({"skills/tdd/SKILL.md": skill_page("tdd", "On main now.")})
        report = self.update()

        self.assertEqual(report["version"], "2.0.1")
        self.assertIn(f"`{head}`", (self.team / "skills.md").read_text())
        self.assertIn(f"`{pinned[:7]}` → `{head[:7]}`", report["notes"])
        self.assertIn("On main now.", (self.vendored("tdd") / "SKILL.md").read_text())

    def test_a_fetch_cut_short_is_fetched_again_rather_than_read_as_an_empty_source(self):
        source = Source(self.root, "acme/skills")
        pinned = source.commit({"LICENSE": "MIT\n", "skills/tdd/SKILL.md": skill_page("tdd")})
        self.write_team([("tdd", "acme/skills", "skills/tdd", pinned, "MIT")], [("acme/skills", "`main`", "none")])
        cut_short = self.root / "cache" / "acme--skills" / pinned / ".git"
        cut_short.mkdir(parents=True)  # what `git init` leaves when the fetch after it fails

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.vendored("tdd") / "SKILL.md").is_file())

    def test_a_source_whose_rows_pin_different_commits_is_refused(self):
        source = Source(self.root, "acme/skills")
        first = source.commit({"LICENSE": "MIT\n", "tdd/SKILL.md": skill_page("tdd"), "pr/SKILL.md": skill_page("pr")})
        second = source.commit({"pr/SKILL.md": skill_page("pr", "Later.")})
        self.write_team([("tdd", "acme/skills", "tdd", first, "MIT"), ("pr", "acme/skills", "pr", second, "MIT")],
                        [("acme/skills", "`main`", "none")])

        result = self.run_sync("--check")

        self.assertEqual(result.returncode, 1)
        self.assertIn("the rows from acme/skills pin different commits", result.stderr)

    def test_update_holds_for_a_skill_gone_or_renamed_upstream_and_for_a_changed_licence(self):
        gone, renamed, relicensed = (Source(self.root, f"acme/{name}") for name in ("gone", "renamed", "relicensed"))
        pins = {
            "gone": gone.commit({"LICENSE": "MIT\n", "tdd/SKILL.md": skill_page("tdd")}),
            "renamed": renamed.commit({"LICENSE": "MIT\n", "pr/SKILL.md": skill_page("pr")}),
            "relicensed": relicensed.commit({"LICENSE": "MIT\n", "grill/SKILL.md": skill_page("grill")}),
        }
        gone.commit({"tdd/SKILL.md": None, "other/SKILL.md": skill_page("other")})
        renamed.commit({"pr/SKILL.md": skill_page("pull-request")})
        relicensed.commit({"LICENSE": "GPL\n"})
        self.write_team([("tdd", "acme/gone", "tdd", pins["gone"], "MIT"),
                         ("pr", "acme/renamed", "pr", pins["renamed"], "MIT"),
                         ("grill", "acme/relicensed", "grill", pins["relicensed"], "MIT")],
                        [(f"acme/{name}", "`main`", "none") for name in ("gone", "renamed", "relicensed")])
        self.run_sync()

        report = self.update()

        holds = "\n".join(report["holds"])
        self.assertEqual(len(report["holds"]), 3, holds)
        self.assertIn("`tdd` is gone from acme/gone", holds)
        self.assertIn("`pr`'s SKILL.md is named 'pull-request'", holds)
        self.assertIn("`grill`'s licence changed", holds)
        self.assertFalse(self.vendored("tdd").exists(), "the PR shows the skill gone")
        self.assertEqual((self.vendored("grill") / "LICENSE").read_text(), "GPL\n")


if __name__ == "__main__":
    unittest.main()
