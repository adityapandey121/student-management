import json

import pytest

import summarize
from conftest import SAMPLES


def test_json_list_summary():
    result = summarize.summarize_file(SAMPLES / "students.json")
    assert result["records"] == 5
    assert result["fields"] == ["course", "id", "name"]
    assert result["value_counts"] == {"Math": 2, "Physics": 1, "Chemistry": 1}
    assert result["missing_field"] == 1


def test_group_by_other_field():
    result = summarize.summarize_file(SAMPLES / "students.json", field="name")
    assert result["value_counts"]["Alice"] == 1


def test_text_summary():
    result = summarize.summarize_file(SAMPLES / "notes.txt", top=2)
    assert result["lines"] == 3
    assert result["words"] == 23
    assert len(result["top_words"]) == 2


def test_cli_json_output(capsys):
    assert summarize.main([str(SAMPLES / "students.json"), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["records"] == 5


def test_missing_file(capsys):
    assert summarize.main(["does-not-exist.json"]) == 2
    assert "not found" in capsys.readouterr().err


def test_invalid_json(capsys):
    assert summarize.main([str(SAMPLES / "invalid.json")]) == 2
    assert "invalid JSON at line 1" in capsys.readouterr().err


def test_empty_file(tmp_path, capsys):
    empty = tmp_path / "empty.json"
    empty.write_text("   \n")
    assert summarize.main([str(empty)]) == 2
    assert "is empty" in capsys.readouterr().err


def test_directory(capsys):
    assert summarize.main([str(SAMPLES)]) == 2
    assert "is a directory" in capsys.readouterr().err


def test_binary_file(tmp_path, capsys):
    binary = tmp_path / "data.txt"
    binary.write_bytes(b"\xff\xfe\x00\x81")
    assert summarize.main([str(binary)]) == 2
    assert "not UTF-8" in capsys.readouterr().err


def test_invalid_top_argument():
    with pytest.raises(SystemExit) as exc:
        summarize.main([str(SAMPLES / "notes.txt"), "--top", "0"])
    assert exc.value.code == 2
