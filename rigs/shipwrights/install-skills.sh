#!/bin/bash
# Installs the skills this team's guidance names at user level, for Claude Code and Codex,
# from the table in skills.md beside this script: each from its source at the suggested commit.
#
# usage: install-skills.sh [--dry-run] [--force] [skill...]
#
#   --dry-run  say what would be installed and kept, and change nothing
#   --force    replace a skill that is already installed under the same name
#   skill...   install only these (default: every skill in the table)
#
# Each skill lands in ${CLAUDE_CONFIG_DIR:-~/.claude}/skills/<skill> and
# ${CODEX_HOME:-~/.codex}/skills/<skill>. A skill already there, yours or from an earlier
# run, is kept unless --force, so running this again changes nothing. Needs only curl and
# tar: every source is a public GitHub repository.
set -euo pipefail

usage() { sed -n '5,9s/^# \{0,1\}//p' "$0"; }

dry_run=0
force=0
only=()
for arg in "$@"; do
  case $arg in
    --dry-run) dry_run=1 ;;
    --force) force=1 ;;
    -h | --help) usage; exit 0 ;;
    -*) echo "unknown option $arg" >&2; usage >&2; exit 2 ;;
    *) only+=("$arg") ;;
  esac
done

table="$(cd "$(dirname "$0")" && pwd)/skills.md"
targets=("${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" "${CODEX_HOME:-$HOME/.codex}/skills")

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

strip() { # a table cell without its spaces and backticks
  local cell=${1//\`/}
  cell=${cell#"${cell%%[![:space:]]*}"}
  echo "${cell%"${cell##*[![:space:]]}"}"
}

fetch() { # repo commit -> the folder holding that commit's files
  local repo=$1 commit=$2 stage="$tmp/${1//\//-}-$2"
  if [ ! -d "$stage" ]; then
    mkdir -p "$stage"
    curl -fsSL "https://codeload.github.com/$repo/tar.gz/$commit" | tar -xz -C "$stage"
  fi
  find "$stage" -mindepth 1 -maxdepth 1 -type d | head -1
}

install_one() { # skill repo commit path dest
  local skill=$1 repo=$2 commit=$3 path=$4 dest=$5 root src
  root=$(fetch "$repo" "$commit")
  src=$root
  if [ "$path" != . ]; then src="$root/$path"; fi
  if [ ! -f "$src/SKILL.md" ]; then
    echo "$repo@$commit has no SKILL.md at $path for $skill" >&2
    exit 1
  fi
  rm -rf "$dest.partial"
  mkdir -p "$dest.partial"
  # Hidden entries are the source's own tooling (.github, plugin manifests), not the skill.
  (cd "$src" && find . -mindepth 1 -maxdepth 1 ! -name '.*' -exec cp -R {} "$dest.partial/" \;)
  if ! ls "$dest.partial" | grep -qi '^licen[cs]e'; then
    for notice in "$root"/LICENSE* "$root"/LICENCE* "$root"/NOTICE* "$root"/THIRD_PARTY_LICENSES*; do
      if [ -f "$notice" ]; then cp "$notice" "$dest.partial/"; fi
    done
  fi
  rm -rf "$dest"
  mv "$dest.partial" "$dest"
}

if ! grep -qE '^\|[[:space:]]*`' "$table"; then
  echo "$table has no table of skills" >&2
  exit 1
fi
for skill in ${only[@]+"${only[@]}"}; do
  if ! grep -qE "^\|[[:space:]]*\`$skill\`[[:space:]]*\|" "$table"; then
    echo "skills.md has no skill $skill" >&2
    exit 1
  fi
done

verb=install
if [ $dry_run = 1 ]; then verb="would install"; fi
installed=0
kept=0
while IFS='|' read -r _ skill source path commit licence _; do
  skill=$(strip "$skill")
  if [ ${#only[@]} -gt 0 ] && [[ " ${only[*]} " != *" $skill "* ]]; then continue; fi
  repo=$(sed -nE 's#.*\(https://github\.com/([^/)]+/[^/)]+)\).*#\1#p' <<<"$source")
  path=$(strip "$path")
  commit=$(strip "$commit")
  if [ -z "$repo" ] || [ -z "$path" ] || ! [[ $commit =~ ^[0-9a-f]{40}$ ]]; then
    echo "skills.md: the row for $skill needs a GitHub source link, a path and a full commit" >&2
    exit 1
  fi
  for target in "${targets[@]}"; do
    dest="$target/$skill"
    if { [ -e "$dest" ] || [ -L "$dest" ]; } && [ $force = 0 ]; then
      echo "keep $skill: $dest is already there (--force replaces it)"
      kept=$((kept + 1))
      continue
    fi
    echo "$verb $skill from $repo@${commit:0:7} ($path, $(strip "$licence")) into $dest"
    if [ $dry_run = 0 ]; then
      mkdir -p "$target"
      install_one "$skill" "$repo" "$commit" "$path" "$dest"
    fi
    installed=$((installed + 1))
  done
done < <(grep -E '^\|[[:space:]]*`' "$table")

if [ $dry_run = 1 ]; then
  echo "dry run: would install $installed, keep $kept"
else
  echo "installed $installed, kept $kept"
fi
