"""check-team.py on the real Shipwrights folder, and on copies of it changed the ways a person or an update could."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check-team.py"
TEAM = REPO / "rigs" / "shipwrights"


def check(team):
    return subprocess.run([sys.executable, str(SCRIPT), str(team)], capture_output=True, text=True)


class CheckTeamTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.team = Path(self.tmp.name) / "shipwrights"
        shutil.copytree(TEAM, self.team, symlinks=True)
        self.agent = self.team / "agents" / "shipwrights" / "agent.yaml"
        self.vendor = self.team / "agents" / "shipwrights" / "vendor"

    def tearDown(self):
        self.tmp.cleanup()

    def assertFailsWith(self, *messages):
        result = check(self.team)
        self.assertEqual(result.returncode, 1, result.stdout)
        for message in messages:
            self.assertIn(message, result.stderr)

    def test_the_team_passes_and_its_vendored_skills_get_none_of_its_text_checks(self):
        result = check(TEAM)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_an_edited_vendored_skill_fails(self):
        page = self.vendor / "tdd" / "SKILL.md"
        page.write_text(page.read_text() + "\nA local change.\n")
        self.assertFailsWith("tdd/SKILL.md differs from its source")

    def test_a_profile_whose_skills_differ_from_its_seats_cell_fails(self):
        text = self.agent.read_text()
        block = re.search(r"^  qa-codex:\n(?:(?:    .*)?\n)*", text, re.MULTILINE)
        changed = block.group(0).replace(", diagnosing-bugs]", ", diagnosing-bugs, tdd]")
        self.agent.write_text(text.replace(block.group(0), changed))
        self.assertFailsWith("the 'qa-codex' profile selects 'tdd', which skills.md doesn't list for qa")

    def test_a_profile_missing_a_skill_its_seats_cell_names_fails(self):
        text = self.agent.read_text()
        block = re.search(r"^  qa-claude:\n(?:(?:    .*)?\n)*", text, re.MULTILINE)
        changed = block.group(0).replace(", diagnosing-bugs]", "]")
        self.agent.write_text(text.replace(block.group(0), changed))
        self.assertFailsWith("the 'qa-claude' profile doesn't select 'diagnosing-bugs', which skills.md lists for qa")

    def test_a_vendored_skill_named_other_than_its_id_fails(self):
        page = self.vendor / "retro" / "SKILL.md"
        page.write_text(page.read_text().replace("name: retro", "name: retrospective", 1))
        self.assertFailsWith("vendor/retro/SKILL.md is named 'retrospective'")

    def test_a_skill_declared_without_following_its_source_on_restore_fails(self):
        self.agent.write_text(self.agent.read_text().replace(
            "{ id: tdd, path: vendor/tdd, on_restore: follow_source }", "{ id: tdd, path: vendor/tdd }"))
        self.assertFailsWith("'tdd' doesn't follow its source on restore")

    def test_a_version_that_is_not_three_part_fails(self):
        self.agent.write_text(re.sub(r'^version: ".*"$', 'version: "2.0"', self.agent.read_text(), flags=re.MULTILINE))
        self.assertFailsWith('version: "2.0": a team version is written')

    def test_an_unquoted_version_fails_since_the_weekly_update_could_not_bump_it(self):
        self.agent.write_text(re.sub(r'^version: ".*"$', "version: 2.0.0", self.agent.read_text(), flags=re.MULTILINE))
        self.assertFailsWith("version: 2.0.0: a team version is written")

    def test_a_queue_create_example_without_a_summary_fails(self):
        page = self.team / "agents" / "shipwrights" / "guidance" / "judge.md"
        page.write_text(page.read_text() + "\n```sh\nrig queue create --destination <lead> --body-file <file>\n```\n")
        self.assertFailsWith("guidance/judge.md: `rig queue create --destination <lead> --body-file <file>` has no "
                             "--summary")

    def test_a_handoff_example_in_prose_without_a_summary_fails(self):
        page = self.team / "startup" / "review-pair-lead.md"
        page.write_text(page.read_text() + "\nAnswer with `rig queue handoff-and-complete <row> --to <judge>`.\n")
        self.assertFailsWith("startup/review-pair-lead.md: `rig queue handoff-and-complete <row> --to <judge>` has no "
                             "--summary")

    def test_guidance_may_name_a_skill_the_team_ships_in_skills(self):
        own = self.team / "agents" / "shipwrights" / "skills" / "team-made"
        own.mkdir()
        (own / "SKILL.md").write_text("---\nname: team-made\ndescription: A skill the team wrote itself.\n---\n")
        text = self.agent.read_text().replace(
            "    - { id: using-the-tui-together, path: skills/using-the-tui-together, on_restore: follow_source }\n",
            "    - { id: using-the-tui-together, path: skills/using-the-tui-together, on_restore: follow_source }\n"
            "    - { id: team-made, path: skills/team-made, on_restore: follow_source }\n")
        self.agent.write_text(text.replace("skills: [using-the-tui-together,", "skills: [using-the-tui-together, team-made,"))
        page = self.team / "agents" / "shipwrights" / "guidance" / "qa.md"
        page.write_text(page.read_text() + "\nCapture the page with the `team-made` skill.\n")
        result = check(self.team)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_guidance_naming_a_skill_nobody_ships_still_fails(self):
        page = self.team / "agents" / "shipwrights" / "guidance" / "qa.md"
        page.write_text(page.read_text() + "\nCapture the page with the `team-made` skill.\n")
        self.assertFailsWith("names `team-made`: list it in skills.md")


if __name__ == "__main__":
    unittest.main()
