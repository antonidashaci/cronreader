from datetime import datetime

import pytest

from cronreader import CronError, describe, next_runs, parse_field


def test_step_and_range_expansion():
    assert parse_field("*/15", 0) == {0, 15, 30, 45}
    assert parse_field("3-6", 1) == {3, 4, 5, 6}
    assert parse_field("1,3,5", 4) == {1, 3, 5}
    assert parse_field("mon-fri", 4) == {1, 2, 3, 4, 5}
    assert parse_field("jan,dec", 3) == {1, 12}


def test_sunday_is_both_zero_and_seven():
    assert parse_field("7", 4) == {0}
    assert parse_field("0", 4) == {0}


def test_out_of_range_is_rejected():
    with pytest.raises(CronError):
        parse_field("99", 0)
    with pytest.raises(CronError):
        parse_field("*/0", 0)


def test_wrong_field_count_is_rejected():
    with pytest.raises(CronError):
        describe("0 9 * *")


def test_describe_reads_like_english():
    assert describe("0 9 * * 1-5").startswith("At 09:00 on Monday")
    assert describe("@daily") == "At 00:00 every day."
    assert describe("* * * * *").startswith("Every minute")


def test_next_runs_are_in_order_and_match():
    after = datetime(2026, 3, 2, 8, 0)  # a Monday
    assert next_runs("0 9 * * 1-5", 3, after=after) == [
        datetime(2026, 3, 2, 9, 0),
        datetime(2026, 3, 3, 9, 0),
        datetime(2026, 3, 4, 9, 0),
    ]


def test_day_fields_are_ored_when_both_restricted():
    # the 1st of the month OR any Friday
    runs = next_runs("0 0 1 * 5", 3, after=datetime(2026, 4, 28, 0, 0))
    assert runs == [
        datetime(2026, 5, 1, 0, 0),  # a Friday that is also the 1st
        datetime(2026, 5, 8, 0, 0),
        datetime(2026, 5, 15, 0, 0),
    ]


def test_impossible_schedule_returns_nothing():
    assert next_runs("0 0 30 2 *", 1, after=datetime(2026, 1, 1)) == []
