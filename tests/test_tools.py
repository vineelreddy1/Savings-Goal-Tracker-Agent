"""
Unit tests for tools module.
Tests tool execution, structured output schemas, and validation error handling.
"""

from datetime import date
import pytest
from memory import SavingsMemory
import tools


def test_create_savings_goal_success():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)

    res = tools.create_savings_goal(
        target_amount=60000,
        deadline="2026-12-31",
        memory=mem,
        ref_date=ref_date
    )

    assert res["success"] is True
    assert res["target"] == 60000.0
    assert res["deadline"] == "2026-12-31"
    assert res["required_monthly_saving"] > 0


def test_create_savings_goal_invalid_target():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)

    # Negative target
    res = tools.create_savings_goal(target_amount=-5000, deadline="2026-12-31", memory=mem, ref_date=ref_date)
    assert res["success"] is False
    assert "greater than zero" in res["error"]

    # Zero target
    res2 = tools.create_savings_goal(target_amount=0, deadline="2026-12-31", memory=mem, ref_date=ref_date)
    assert res2["success"] is False


def test_create_savings_goal_invalid_deadline():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)

    res = tools.create_savings_goal(target_amount=60000, deadline="invalid-date", memory=mem, ref_date=ref_date)
    assert res["success"] is False
    assert "Invalid date format" in res["error"]


def test_create_savings_goal_past_deadline():
    ref_date = date(2026, 6, 1)
    mem = SavingsMemory(ref_date=ref_date)

    res = tools.create_savings_goal(target_amount=60000, deadline="2025-12-31", memory=mem, ref_date=ref_date)
    assert res["success"] is False
    assert "cannot be in the past" in res["error"]


def test_log_saving_without_goal():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)

    res = tools.log_saving(amount=5000, memory=mem, ref_date=ref_date)
    assert res["success"] is False
    assert "No active savings goal" in res["error"]


def test_log_saving_invalid_amount():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)
    tools.create_savings_goal(target_amount=60000, deadline="2026-12-31", memory=mem, ref_date=ref_date)

    res = tools.log_saving(amount=-100, memory=mem, ref_date=ref_date)
    assert res["success"] is False
    assert "greater than zero" in res["error"]


def test_log_saving_success():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)
    tools.create_savings_goal(target_amount=60000, deadline="2026-12-31", memory=mem, ref_date=ref_date)

    res = tools.log_saving(amount=5000, memory=mem, ref_date=ref_date)
    assert res["success"] is True
    assert res["amount_added"] == 5000.0
    assert res["total_saved"] == 5000.0
    assert res["remaining"] == 55000.0


def test_get_goal_progress_tool():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)
    tools.create_savings_goal(target_amount=60000, deadline="2026-12-31", memory=mem, ref_date=ref_date)
    tools.log_saving(amount=10000, memory=mem, ref_date=ref_date)

    prog = tools.get_goal_progress(memory=mem, ref_date=ref_date)
    assert prog["target"] == 60000.0
    assert prog["saved"] == 10000.0
    assert prog["remaining"] == 50000.0
    assert prog["percentage"] == 16.67
    assert prog["status"] == "ON_TRACK"
