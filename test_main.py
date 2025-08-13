import json
from unittest.mock import patch

import pytest

from main import (
    parse_arguments,
    read_log_files,
    filter_by_date,
    generate_average_report,
    main
)


class TestParseArguments:

    def test_parse_with_single_file(self):
        with patch("sys.argv", ["main.py", "--file", "test.log", "--report", "average"]):
            args = parse_arguments()
            assert args.file == ["test.log"]
            assert args.report == "average"
            assert args.date is None

    def test_parse_with_multiple_files(self):
        with patch("sys.argv", ["main.py", "--file", "test1.log", "--file", "test2.log", "--report", "average"]):
            args = parse_arguments()
            assert args.file == ["test1.log", "test2.log"]

    def test_parse_with_date(self):
        with patch("sys.argv", ["main.py", "--file", "test.log", "--report", "average", "--date", "2025-06-22"]):
            args = parse_arguments()
            assert args.date == "2025-06-22"


class TestReadLogFiles:

    def test_read_single_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        entries = [
            {"@timestamp": "2025-06-22T20:03:08+00:00", "url": "/api/test", "response_time": 0.1},
            {"@timestamp": "2025-06-22T20:03:09+00:00", "url": "/api/users", "response_time": 0.2}
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        result = read_log_files([str(log_file)])

        assert len(result) == 2
        assert result[0]["url"] == "/api/test"
        assert result[1]["url"] == "/api/users"

    def test_read_file_with_empty_lines(self, tmp_path):
        log_file = tmp_path / "test.log"
        with open(log_file, "w") as f:
            f.write("\n")
            f.write(json.dumps({"url": "/api/test"}) + "\n")
            f.write("\n\n")
            f.write(json.dumps({"url": "/api/users"}) + "\n")

        result = read_log_files([str(log_file)])

        assert len(result) == 2
        assert result[0]["url"] == "/api/test"
        assert result[1]["url"] == "/api/users"

    def test_read_nonexistent_file(self, capsys):
        result = read_log_files(["/nonexistent/file.log"])

        assert len(result) == 0
        captured = capsys.readouterr()
        assert "does not exist" in captured.out

    def test_read_file_with_invalid_json(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        with open(log_file, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"url": "/api/valid"}) + "\n")

        result = read_log_files([str(log_file)])

        assert len(result) == 1
        assert result[0]["url"] == "/api/valid"
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.out


class TestFilterByDate:

    def test_filter_matching_date(self):
        entries = [
            {"@timestamp": "2025-06-22T20:03:08+00:00", "url": "/api/test1"},
            {"@timestamp": "2025-06-23T20:03:08+00:00", "url": "/api/test2"},
            {"@timestamp": "2025-06-22T10:00:00+00:00", "url": "/api/test3"},
        ]

        result = filter_by_date(entries, "2025-06-22")

        assert len(result) == 2
        assert result[0]["url"] == "/api/test1"
        assert result[1]["url"] == "/api/test3"

    def test_filter_no_matching_date(self):
        entries = [
            {"@timestamp": "2025-06-22T20:03:08+00:00", "url": "/api/test"},
        ]

        result = filter_by_date(entries, "2025-06-23")

        assert len(result) == 0

    def test_filter_invalid_timestamp(self):
        entries = [
            {"@timestamp": "invalid", "url": "/api/test1"},
            {"@timestamp": "2025-06-22T20:03:08+00:00", "url": "/api/test2"},
        ]

        result = filter_by_date(entries, "2025-06-22")

        assert len(result) == 1
        assert result[0]["url"] == "/api/test2"


class TestGenerateAverageReport:

    def test_generate_report_basic(self):
        entries = [
            {"url": "/api/homeworks", "response_time": 0.1},
            {"url": "/api/homeworks", "response_time": 0.2},
            {"url": "/api/users", "response_time": 0.3},
        ]

        report = generate_average_report(entries)

        assert "/api/homeworks" in report
        assert "/api/users" in report
        assert "0.15" in report
        assert "0.3" in report
        assert "2" in report

    def test_generate_report_with_query_params(self):
        entries = [
            {"url": "/api/test?param=1", "response_time": 0.1},
            {"url": "/api/test?param=2", "response_time": 0.2},
        ]

        report = generate_average_report(entries)

        assert "/api/test" in report
        assert "?" not in report
        assert "0.15" in report

    def test_generate_report_empty_entries(self):
        report = generate_average_report([])

        assert report == "No log entries found"

    def test_generate_report_no_urls(self):
        entries = [
            {"response_time": 0.1},
            {"response_time": 0.2},
        ]

        report = generate_average_report(entries)

        assert report == "No valid endpoints found"

    def test_report_sorting(self):
        entries = [
            {"url": "/api/rare", "response_time": 0.1},
            {"url": "/api/common", "response_time": 0.1},
            {"url": "/api/common", "response_time": 0.1},
            {"url": "/api/common", "response_time": 0.1},
        ]

        report = generate_average_report(entries)
        lines = report.split("\n")

        assert "/api/common" in lines[1]
        assert "/api/rare" in lines[2]


class TestMain:

    def test_main_success(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        with open(log_file, "w") as f:
            f.write(json.dumps({"url": "/api/test", "response_time": 0.1}) + "\n")

        with patch("sys.argv", ["main.py", "--file", str(log_file), "--report", "average"]):
            main()

        captured = capsys.readouterr()
        assert "/api/test" in captured.out

    def test_main_with_invalid_date(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        log_file.touch()

        with patch("sys.argv", ["main.py", "--file", str(log_file), "--report", "average", "--date", "invalid"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Invalid date format" in captured.out

    def test_main_no_entries(self, tmp_path, capsys):
        log_file = tmp_path / "empty.log"
        log_file.touch()

        with patch("sys.argv", ["main.py", "--file", str(log_file), "--report", "average"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "No valid log entries found" in captured.out

    def test_main_unknown_report(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        with open(log_file, "w") as f:
            f.write(json.dumps({"url": "/api/test"}) + "\n")

        with patch("sys.argv", ["main.py", "--file", str(log_file), "--report", "unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Unknown report type" in captured.out

    def test_main_with_date_filter(self, tmp_path, capsys):
        log_file = tmp_path / "test.log"
        entries = [
            {"@timestamp": "2025-06-22T20:03:08+00:00", "url": "/api/test1", "response_time": 0.1},
            {"@timestamp": "2025-06-23T20:03:08+00:00", "url": "/api/test2", "response_time": 0.2},
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        with patch("sys.argv", ["main.py", "--file", str(log_file), "--report", "average", "--date", "2025-06-22"]):
            main()

        captured = capsys.readouterr()
        assert "/api/test1" in captured.out
        assert "/api/test2" not in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
