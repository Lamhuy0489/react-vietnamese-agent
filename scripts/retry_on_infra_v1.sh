#!/usr/bin/env bash
# Rerun a resumable runner while it exits 2 (endpoint unreachable).
# Usage: scripts/retry_on_infra_v1.sh [ATTEMPTS] [WAIT_SECONDS] -- command...
# Any other exit code ends the loop and is passed through. The serving notebooks
# stop after 30 idle minutes, so waiting much longer than that cannot help.
set -u
attempts=${1:-20}; wait_seconds=${2:-120}; shift 2; [ "${1:-}" = "--" ] && shift
for ((i = 1; i <= attempts; i++)); do
  "$@"; rc=$?
  echo "attempt $i rc=$rc $(date +%H:%M)"
  [ "$rc" -ne 2 ] && exit "$rc"
  [ "$i" -lt "$attempts" ] && sleep "$wait_seconds"
done
exit 2
