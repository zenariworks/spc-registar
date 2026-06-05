#!/usr/bin/env bash
# Enforce the branch-naming convention so auto-tag can version every merge.
# Prefixes mirror .github/workflows/auto-tag.yml. See CONTRIBUTING.md.
#
# Exempt: main/master and detached HEAD (rebase, bisect, CI checkout).
# One-off escape hatch:  ALLOW_BRANCH=1 git commit ...
set -euo pipefail

branch="$(git symbolic-ref --short -q HEAD || true)"

case "$branch" in
  "" | main | master) exit 0 ;;
esac

[ -n "${ALLOW_BRANCH:-}" ] && exit 0

prefix="${branch%%/*}"
case "$prefix" in
  feature | feat | fix | bugfix | hotfix | perf | refactor | chore | docs | build | ci | test | style)
    exit 0 ;;
esac

cat >&2 <<MSG
✗ Грана "$branch" не прати конвенцију именовања (auto-tag је не може верзионисати).
  Дозвољени префикси:
    feature/  feat/                                  → minor
    fix/  bugfix/  hotfix/  perf/  refactor/
    chore/  docs/  build/  ci/  test/  style/        → patch
  Преименуј грану, нпр:  git branch -m feature/${branch#*/}
  Једнократно заобиђи:   ALLOW_BRANCH=1 git commit ...
  Детаљи:                CONTRIBUTING.md
MSG
exit 1
