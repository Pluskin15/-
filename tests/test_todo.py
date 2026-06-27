from datetime import date, timedelta

import pytest

from todo import (
    Task,
    filter_tasks,
    parse_due_date,
    sort_tasks,
    validate_priority,
    validate_title,
)


def future_date(days: int) -> str:
    return (date.today() + timedelta(days=days)).strftime("%d.%m.%Y")


def test_parse_due_date_accepts_future_date():
    value = future_date(1)
    assert parse_due_date(value).strftime("%d.%m.%Y") == value


def test_parse_due_date_rejects_past_date():
    value = (date.today() - timedelta(days=1)).strftime("%d.%m.%Y")
    with pytest.raises(ValueError):
        parse_due_date(value)


def test_validate_title_rejects_empty_title():
    with pytest.raises(ValueError):
        validate_title("   ")


def test_validate_priority_rejects_unknown_priority():
    with pytest.raises(ValueError):
        validate_priority("срочный")


def test_sort_tasks_orders_by_status_due_date_and_priority():
    tasks = [
        Task("done", "", future_date(1), "высокий", True),
        Task("low", "", future_date(1), "низкий", False),
        Task("high", "", future_date(1), "высокий", False),
        Task("soon", "", future_date(0), "средний", False),
    ]
    assert [task.title for task in sort_tasks(tasks)] == ["soon", "high", "low", "done"]


def test_filter_tasks_active_and_completed():
    tasks = [
        Task("active", "", future_date(1), "низкий"),
        Task("done", "", future_date(1), "низкий", True),
    ]
    assert [task.title for task in filter_tasks(tasks, "2")] == ["active"]
    assert [task.title for task in filter_tasks(tasks, "3")] == ["done"]
