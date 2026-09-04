"""
Unit tests for savings_logic module.
Tests deadline parsing, financial progress math, required savings rates, and status evaluation.
"""

from datetime import date
import pytest
from savings_logic import parse_deadline, calculate_goal_progress, format_currency


def test_parse_deadline_valid_iso():
    ref_date = date(2026, 1, 1)
    success, parsed, msg = parse_deadline("2026-12-31", ref_date=ref_date)
    assert success is True
    assert parsed == date(2026, 12, 31)


def test_parse_deadline_month_year():
    ref_date = date(2026, 1, 1)
    success, parsed, msg = parse_deadline("December 2026", ref_date=ref_date)
    assert success is True
    assert parsed == date(2026, 12, 31)


def test_parse_deadline_invalid_format():
    ref_date = date(2026, 1, 1)
    success, parsed, msg = parse_deadline("invalid-date-string", ref_date=ref_date)
    assert success is False
    assert "Invalid date format" in msg


def test_parse_deadline_past_deadline():
    ref_date = date(2026, 6, 1)
    success, parsed, msg = parse_deadline("2025-12-31", ref_date=ref_date)
    assert success is False
    assert "cannot be in the past" in msg


def test_calculate_goal_progress_not_started():
    creation_date = date(2026, 1, 1)
    current_date = date(2026, 1, 1)
    deadline = date(2026, 12, 31)

    prog = calculate_goal_progress(
        target=60000,
        total_saved=0,
        creation_date=creation_date,
        current_date=current_date,
        deadline=deadline
    )

    assert prog["target"] == 60000.0
    assert prog["saved"] == 0.0
    assert prog["remaining"] == 60000.0
    assert prog["percentage"] == 0.0
    assert prog["status"] == "NOT_STARTED"
    assert prog["required_monthly_saving"] > 0


def test_calculate_goal_progress_on_track():
    # After 2 months of a 12 month goal, saved 10,000 of 60,000 goal (expected is ~10,000)
    creation_date = date(2026, 1, 1)
    current_date = date(2026, 3, 1)
    deadline = date(2026, 12, 31)

    prog = calculate_goal_progress(
        target=60000,
        total_saved=10000,
        creation_date=creation_date,
        current_date=current_date,
        deadline=deadline
    )

    assert prog["saved"] == 10000.0
    assert prog["remaining"] == 50000.0
    assert prog["percentage"] == 16.67
    assert prog["status"] == "ON_TRACK"


def test_calculate_goal_progress_behind():
    # Halfway through year (6 months elapsed out of 12), saved only 5,000 of 60,000 goal (expected is ~30,000)
    creation_date = date(2026, 1, 1)
    current_date = date(2026, 7, 1)
    deadline = date(2026, 12, 31)

    prog = calculate_goal_progress(
        target=60000,
        total_saved=5000,
        creation_date=creation_date,
        current_date=current_date,
        deadline=deadline
    )

    assert prog["status"] == "BEHIND"
    assert prog["remaining"] == 55000.0
    assert prog["required_monthly_saving"] > 5000.0


def test_calculate_goal_progress_goal_reached():
    creation_date = date(2026, 1, 1)
    current_date = date(2026, 6, 1)
    deadline = date(2026, 12, 31)

    prog = calculate_goal_progress(
        target=60000,
        total_saved=65000,  # Over-saved
        creation_date=creation_date,
        current_date=current_date,
        deadline=deadline
    )

    assert prog["status"] == "GOAL_REACHED"
    assert prog["remaining"] == 0.0  # Cannot be negative
    assert prog["percentage"] == 100.0  # Capped at 100%
    assert prog["required_monthly_saving"] == 0.0


def test_format_currency():
    assert format_currency(60000, "₹") == "₹60,000"
    assert format_currency(5000.50, "₹") == "₹5,000.50"
