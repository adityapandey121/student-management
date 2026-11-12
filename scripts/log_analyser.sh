#!/usr/bin/env bash
# log_analyser.sh - count ERROR, WARN and INFO entries in one or more log files.
#
# Usage: log_analyser.sh LOGFILE [LOGFILE ...]
#
# A line is counted when the level appears as a whole word, e.g.
#   2024-05-01 10:00:00 ERROR Database connection lost
#   [WARN] disk almost full
# WARNING is counted as WARN.
#
# Exit codes: 0 = success, 2 = bad usage or unreadable file.
set -uo pipefail

if [[ $# -eq 0 ]]; then
    echo "Usage: $(basename "$0") LOGFILE [LOGFILE ...]" >&2
    exit 2
fi

status=0
total_e=0; total_w=0; total_i=0

printf '%-35s %7s %7s %7s\n' "FILE" "ERROR" "WARN" "INFO"
for file in "$@"; do
    if [[ ! -e "$file" ]]; then
        echo "ERROR: file '$file' not found" >&2
        status=2; continue
    fi
    if [[ -d "$file" ]]; then
        echo "ERROR: '$file' is a directory, expected a log file" >&2
        status=2; continue
    fi
    if [[ ! -r "$file" ]]; then
        echo "ERROR: file '$file' is not readable (check permissions)" >&2
        status=2; continue
    fi

    read -r e w i < <(awk '
        /(^|[^A-Za-z])ERROR([^A-Za-z]|$)/            { e++; next }
        /(^|[^A-Za-z])WARN(ING)?([^A-Za-z]|$)/       { w++; next }
        /(^|[^A-Za-z])INFO([^A-Za-z]|$)/             { i++ }
        END { printf "%d %d %d\n", e, w, i }' "$file")

    printf '%-35s %7d %7d %7d\n' "$file" "$e" "$w" "$i"
    total_e=$((total_e + e)); total_w=$((total_w + w)); total_i=$((total_i + i))
    if [[ ! -s "$file" ]]; then
        echo "NOTE: '$file' is empty" >&2
    fi
done

if [[ $# -gt 1 ]]; then
    printf '%-35s %7d %7d %7d\n' "TOTAL" "$total_e" "$total_w" "$total_i"
fi

exit "$status"
