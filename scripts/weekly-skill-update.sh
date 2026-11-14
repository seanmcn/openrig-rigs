#!/bin/bash
# The weekly update of a team's skills: moves each source to what skills.md's Sources table says
# it follows, checks the team, and keeps one pull request for it, which merges itself and
# releases the team's next patch version when nothing calls for a person.
#
# usage: scripts/weekly-skill-update.sh rigs/<team>
#
# Before merging it runs the checks the check workflow runs on other pull requests:
# check-team.py, with rig bundle check when rig is installed, and the script tests. It holds the
# pull request open for a person, saying why at its top, when one fails, a skill is gone from its
# source or renamed there, or a skill's licence changed. A later run
# replaces that pull request's branch and text rather than opening another, and closes it when
# main needs no update any more.
#
# It starts from origin/main on the branch skills-update/<team>. DRY_RUN=1 stops before anything
# leaves the machine: no push, pull request, merge or release, and prints what it would send.
# Otherwise it needs gh, logged in or given GH_TOKEN, with permission to push, open and merge
# pull requests and make releases.
set -euo pipefail

team=${1:?usage: scripts/weekly-skill-update.sh rigs/<team>}
team=${team%/}
name=$(basename "$team")
branch="skills-update/$name"
dry_run=${DRY_RUN:-0}
scripts=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

open_pr() { gh pr list --head "$branch" --base main --state open --json number --jq '.[0].number // empty'; }

if [ "$dry_run" = 0 ]; then
  git fetch -q origin main
  git switch -q -C "$branch" origin/main
fi

python3 "$scripts/sync-skills.py" "$team" --update --report "$work/report.json"
if [ "$(jq -r .changed "$work/report.json")" != true ]; then
  echo "$team: every source is at its newest"
  if [ "$dry_run" = 0 ] && pr=$(open_pr) && [ -n "$pr" ]; then
    gh pr close "$pr" --delete-branch --comment "main has the newest skills now, so this update isn't needed."
  fi
  exit 0
fi
version=$(jq -r .version "$work/report.json")
jq -r '.holds[]' "$work/report.json" >"$work/holds"

# The checks the check workflow runs, since a pull request this opens with the workflow's token starts no workflow.
# The version raise it also checks is the patch bump sync-skills.py has just made.
if ! python3 "$scripts/check-team.py" "$team" >"$work/check.log" 2>&1; then
  echo "\`scripts/check-team.py $team\` fails; its output is at the end." >>"$work/holds"
fi
if ! python3 -m unittest discover -s "$scripts/tests" >>"$work/check.log" 2>&1; then
  echo "The script tests (\`python3 -m unittest discover -s scripts/tests\`) fail; their output is at the end." >>"$work/holds"
fi

jq -r .notes "$work/report.json" >"$work/notes.md"
{
  if [ -s "$work/holds" ]; then
    echo "**Held for a person.** This update doesn't merge itself, because:"
    echo
    sed 's/^/- /' "$work/holds"
    echo
  else
    echo "**Merges itself** once opened: the team's checks pass, and no skill is gone, renamed or relicensed."
    echo
  fi
  echo "Releases \`$name-v$version\`."
  echo
  cat "$work/notes.md"
  if grep -q -e check-team -e unittest "$work/holds"; then
    printf '\n<details><summary>Output of the checks</summary>\n\n```\n'
    tail -n 60 "$work/check.log"
    printf '```\n\n</details>\n'
  fi
} >"$work/body.md"

title="chore($name): take the week's skill updates, as $version"
if [ "$dry_run" != 0 ]; then
  echo "DRY_RUN: would push $branch and open or update a pull request: $title"
  cat "$work/body.md"
  exit 0
fi

git add -A "$team"
git commit -q -m "$title" -m "$(cat "$work/notes.md")"
git push -q --force origin "HEAD:refs/heads/$branch"
if pr=$(open_pr) && [ -n "$pr" ]; then
  gh pr edit "$pr" --title "$title" --body-file "$work/body.md" >/dev/null
else
  gh pr create --base main --head "$branch" --title "$title" --body-file "$work/body.md" >/dev/null
  pr=$(open_pr)
fi
echo "pull request #$pr: $title"

if [ -s "$work/holds" ]; then
  echo "held for a person:"
  cat "$work/holds"
  exit 0
fi
gh pr merge "$pr" --rebase --delete-branch
merged=$(gh pr view "$pr" --json mergeCommit --jq .mergeCommit.oid)
git fetch -q origin main
"$scripts/release-team.sh" "$team" "$merged" "$work/notes.md"
