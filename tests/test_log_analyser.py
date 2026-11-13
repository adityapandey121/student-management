def _row(stdout, name):
    for line in stdout.splitlines():
        if line.startswith(name):
            return [int(x) for x in line.split()[-3:]]
    raise AssertionError(f"no row for {name} in:\n{stdout}")


def test_counts_levels(run_bash):
    result = run_bash("log_analyser.sh", "samples/app.log")
    assert result.returncode == 0, result.stderr
    assert _row(result.stdout, "samples/app.log") == [2, 2, 6]


def test_bracketed_levels_and_whole_words(run_bash):
    # "INFORMATIONAL" must not be double-counted, DEBUG is ignored.
    result = run_bash("log_analyser.sh", "samples/worker.log")
    assert _row(result.stdout, "samples/worker.log") == [1, 1, 3]


def test_total_for_multiple_files(run_bash):
    result = run_bash("log_analyser.sh", "samples/app.log", "samples/worker.log")
    assert _row(result.stdout, "TOTAL") == [3, 3, 9]


def test_empty_file(run_bash, tmp_path):
    empty = tmp_path / "empty.log"
    empty.write_text("")
    result = run_bash("log_analyser.sh", empty.as_posix())
    assert result.returncode == 0
    assert "is empty" in result.stderr


def test_missing_file(run_bash):
    result = run_bash("log_analyser.sh", "samples/missing.log")
    assert result.returncode == 2
    assert "not found" in result.stderr


def test_directory_instead_of_file(run_bash):
    result = run_bash("log_analyser.sh", "samples")
    assert result.returncode == 2
    assert "is a directory" in result.stderr


def test_no_arguments(run_bash):
    result = run_bash("log_analyser.sh")
    assert result.returncode == 2
    assert "Usage" in result.stderr
