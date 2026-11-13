# Operations scripts

All scripts live in `scripts/`, sample inputs in `samples/`. They need only
Bash (Linux, macOS, or Git Bash on Windows) and Python 3.10+. Nothing has to
be installed to *run* them; `pytest` is only needed for the tests.

| Script | Purpose | Exit codes |
|--------|---------|-----------|
| `disk_usage.sh` | Disk usage per filesystem, warns above a threshold | 0 OK, 1 warning, 2 error |
| `log_analyser.sh` | Counts ERROR / WARN / INFO lines per log file | 0 OK, 2 error |
| `summarize.py` | Summary of a JSON or text file | 0 OK, 2 error |

The exit codes make the scripts usable from cron or CI. For example,
`scripts/disk_usage.sh -t 90 || send_alert`.

## disk_usage.sh

```bash
bash scripts/disk_usage.sh                # check / with default threshold 80
bash scripts/disk_usage.sh -t 90 / /var   # custom threshold, several paths
DISK_THRESHOLD=70 bash scripts/disk_usage.sh
bash scripts/disk_usage.sh -h             # help
```

Error cases handled: non-numeric or out-of-range threshold, missing option
value, unknown option, path that does not exist, `df` missing or failing,
unparseable `df` output.

Sample output (Git Bash on Windows):

```text
$ bash scripts/disk_usage.sh -t 90 /
MOUNT                              USE% STATUS
/                                   52% OK
# exit code: 0

$ bash scripts/disk_usage.sh -t 50 /
MOUNT                              USE% STATUS
/                                   52% WARNING (above 50%)
# exit code: 1

$ bash scripts/disk_usage.sh -t abc
ERROR: threshold must be a whole number between 0 and 100, got 'abc'
# exit code: 2

$ bash scripts/disk_usage.sh /no/such/path
MOUNT                              USE% STATUS
ERROR: path '/no/such/path' does not exist
# exit code: 2
```

## log_analyser.sh

```bash
bash scripts/log_analyser.sh samples/app.log
bash scripts/log_analyser.sh samples/*.log      # per-file rows plus TOTAL
```

The level must appear as a whole word, so `INFORMATIONAL` is not counted as
`INFO`. Both `2026-01-01 10:00 ERROR msg` and `[ERROR] msg` work. `WARNING`
counts as `WARN`.

Error cases handled: no arguments, missing file, directory instead of file,
unreadable file (permissions). An empty file is reported as a note and gets
zero counts.

```text
$ bash scripts/log_analyser.sh samples/app.log samples/worker.log
FILE                                  ERROR    WARN    INFO
samples/app.log                           2       2       6
samples/worker.log                        1       1       3
TOTAL                                     3       3       9
# exit code: 0

$ bash scripts/log_analyser.sh samples/missing.log
FILE                                  ERROR    WARN    INFO
ERROR: file 'samples/missing.log' not found
# exit code: 2

$ bash scripts/log_analyser.sh samples
FILE                                  ERROR    WARN    INFO
ERROR: 'samples' is a directory, expected a log file
# exit code: 2
```

## summarize.py

```bash
python scripts/summarize.py samples/students.json              # group by "course"
python scripts/summarize.py samples/students.json --field name
python scripts/summarize.py samples/notes.txt --top 3
python scripts/summarize.py samples/students.json --format json  # machine readable
```

Files ending in `.json` are parsed as JSON. Anything else is treated as text.

Error cases handled: missing file, directory, empty file, invalid JSON (with
line and column), non-UTF-8 or binary file, invalid `--top` value.

```text
$ python scripts/summarize.py samples/students.json
Summary of samples/students.json (json-list)
  records: 5
  object_records: 5
  fields: course, id, name
  course breakdown:
    Math: 2
    Physics: 1
    Chemistry: 1
  missing_field: 1
# exit code: 0

$ python scripts/summarize.py samples/notes.txt --top 3
Summary of samples/notes.txt (text)
  lines: 3
  words: 23
  characters: 124
  top words: student (2), demo (2), in (2)
# exit code: 0

$ python scripts/summarize.py samples/invalid.json
ERROR: invalid JSON at line 1, column 30: Illegal trailing comma before end of object
# exit code: 2

$ python scripts/summarize.py missing.json
ERROR: file 'missing.json' not found
# exit code: 2
```

## Tests

```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -v
```

`tests/` covers the normal case and at least two error cases for every
script (23 tests). Bash-based tests are skipped automatically if `bash` is not
on `PATH`.
