#!/usr/bin/env bash
# disk_usage.sh - report disk usage and warn when a filesystem is above a threshold.
#
# Usage: disk_usage.sh [-t THRESHOLD] [PATH ...]
#   -t THRESHOLD  warn when usage % is strictly above this value (0-100).
#                 Default: $DISK_THRESHOLD, or 80 if that is unset.
#   PATH          filesystems/paths to check. Default: /
#
# Exit codes: 0 = all below threshold, 1 = at least one warning, 2 = error.
set -uo pipefail

usage() {
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
}

threshold="${DISK_THRESHOLD:-80}"

while getopts ":t:h" opt; do
    case "$opt" in
        t) threshold="$OPTARG" ;;
        h) usage; exit 0 ;;
        :) echo "ERROR: option -$OPTARG needs a value" >&2; exit 2 ;;
        \?) echo "ERROR: unknown option -$OPTARG (use -h for help)" >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

if ! [[ "$threshold" =~ ^[0-9]+$ ]] || (( threshold > 100 )); then
    echo "ERROR: threshold must be a whole number between 0 and 100, got '$threshold'" >&2
    exit 2
fi

if ! command -v df >/dev/null 2>&1; then
    echo "ERROR: 'df' command not found" >&2
    exit 2
fi

paths=("$@")
[[ ${#paths[@]} -eq 0 ]] && paths=("/")

status=0
printf '%-30s %8s %s\n' "MOUNT" "USE%" "STATUS"
for path in "${paths[@]}"; do
    if [[ ! -e "$path" ]]; then
        echo "ERROR: path '$path' does not exist" >&2
        status=2
        continue
    fi
    # -P gives POSIX output: one line per filesystem. Read use% and mount
    # from the end of the line because the filesystem name may contain spaces
    # (e.g. "C:/Program Files/Git" under Git Bash).
    if ! line=$(df -P "$path" 2>&1 | tail -n 1); then
        echo "ERROR: df failed for '$path': $line" >&2
        status=2
        continue
    fi
    used=$(awk '{v = $(NF-1); gsub("%", "", v); print v}' <<<"$line")
    mount=$(awk '{print $NF}' <<<"$line")
    if ! [[ "$used" =~ ^[0-9]+$ ]]; then
        echo "ERROR: could not parse df output for '$path': $line" >&2
        status=2
        continue
    fi
    if (( used > threshold )); then
        printf '%-30s %7s%% %s\n' "$mount" "$used" "WARNING (above ${threshold}%)"
        (( status == 0 )) && status=1
    else
        printf '%-30s %7s%% %s\n' "$mount" "$used" "OK"
    fi
done

exit "$status"
