import os


def test_ok_when_threshold_is_100(run_bash):
    result = run_bash("disk_usage.sh", "-t", "100", "/")
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_warns_when_threshold_is_0(run_bash):
    result = run_bash("disk_usage.sh", "-t", "0", "/")
    assert result.returncode == 1
    assert "WARNING (above 0%)" in result.stdout


def test_threshold_from_environment(run_bash):
    env = {**os.environ, "DISK_THRESHOLD": "0"}
    result = run_bash("disk_usage.sh", "/", env=env)
    assert result.returncode == 1


def test_rejects_non_numeric_threshold(run_bash):
    result = run_bash("disk_usage.sh", "-t", "abc")
    assert result.returncode == 2
    assert "threshold must be a whole number" in result.stderr


def test_rejects_threshold_above_100(run_bash):
    result = run_bash("disk_usage.sh", "-t", "150")
    assert result.returncode == 2


def test_missing_path(run_bash):
    result = run_bash("disk_usage.sh", "/definitely/not/here")
    assert result.returncode == 2
    assert "does not exist" in result.stderr
