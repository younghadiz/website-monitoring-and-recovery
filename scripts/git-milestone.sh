#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
    echo "Usage: bash scripts/git-milestone.sh BRANCH MESSAGE FILE..."
    exit 2
fi

expected_branch="$1"
message="$2"
shift 2

test "$(git branch --show-current)" = "$expected_branch"
git diff --cached --quiet
git diff --check

git add -- "$@"
git diff --cached --check
git diff --cached --stat
git diff --cached

read -r -p "Review complete. Type commit to continue: " answer
test "$answer" = "commit"

git commit -m "$message"
test -z "$(git status --porcelain)"

git push -u origin "$expected_branch"
git push gitlab "$expected_branch"

git switch develop
test -z "$(git status --porcelain)"
git pull --ff-only origin develop

git merge --no-ff "$expected_branch" \
  -m "merge: integrate ${expected_branch}"

git push origin develop
git push gitlab develop

test -z "$(git status --porcelain)"
git status --short --branch
