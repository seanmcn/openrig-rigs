#!/bin/bash
# Releases a team's version, when it has no release yet: tags <team>-v<version> at a commit and
# makes a GitHub release of it.
#
# usage: scripts/release-team.sh rigs/<team> <commit> [notes-file]
#
# The version is the one in the team's agent.yaml at that commit. Without a notes file, GitHub
# writes the notes from the pull requests since the last release. Needs gh, logged in or given
# GH_TOKEN, with permission to write to the repository. Run again, it changes nothing.
set -euo pipefail

team=${1:?usage: scripts/release-team.sh rigs/<team> <commit> [notes-file]}
commit=${2:?usage: scripts/release-team.sh rigs/<team> <commit> [notes-file]}
notes=${3:-}
name=$(basename "$team")

agent=$(git show "$commit:${team%/}/agents/$name/agent.yaml")
version=$(sed -nE 's/^version:[[:space:]]*"?([0-9]+\.[0-9]+\.[0-9]+)"?[[:space:]]*$/\1/p' <<<"$agent")
if [ -z "$version" ]; then
  echo "$team: agent.yaml at ${commit:0:7} has no <major>.<minor>.<patch> version" >&2
  exit 1
fi
tag="$name-v$version"

if gh release view "$tag" >/dev/null 2>&1; then
  echo "$tag is already released"
  exit 0
fi
if [ -n "$notes" ]; then
  gh release create "$tag" --target "$commit" --title "$name $version" --notes-file "$notes"
else
  gh release create "$tag" --target "$commit" --title "$name $version" --generate-notes
fi
echo "released $tag at ${commit:0:7}"
