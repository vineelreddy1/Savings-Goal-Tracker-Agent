"""
Unit tests for memory module and agent cross-turn memory persistence.
Tests state retention, multiple savings accumulation, and agent turn integration.
"""

from datetime import date
import pytest
from memory import SavingsMemory
from agent import SavingsGoalAgent


def test_multiple_savings_entries():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)
    mem.set_goal(target_amount=60000, deadline_str="2026-12-31", ref_date=ref_date)

    mem.add_saving(amount=5000, ref_date=ref_date)
    mem.add_saving(amount=3000, ref_date=ref_date)
    mem.add_saving(amount=2500, ref_date=ref_date)

    assert mem.get_total_saved() == 10500.0
    assert len(mem.savings_entries) == 3

    prog = mem.get_progress(ref_date=ref_date)
    assert prog["saved"] == 10500.0
    assert prog["remaining"] == 49500.0


def test_memory_persistence_across_agent_turns():
    ref_date = date(2026, 1, 1)
    agent = SavingsGoalAgent(ref_date=ref_date, verbose=False)

    # Turn 1: Create goal
    t1 = agent.process_turn("I want to save ₹60,000 by December.")
    assert agent.memory.has_active_goal() is True
    assert agent.memory.target_amount == 60000.0

    # Turn 2: Log first saving
    t2 = agent.process_turn("I saved ₹5,000.")
    assert agent.memory.get_total_saved() == 5000.0

    # Turn 3: Log second saving
    t3 = agent.process_turn("I saved another ₹3,000.")
    assert agent.memory.get_total_saved() == 8000.0

    # Turn 4: Query remaining amount
    t4 = agent.process_turn("How much more do I need?")
    prog = t4["progress"]
    assert prog["saved"] == 8000.0
    assert prog["remaining"] == 52000.0
    assert "52,000" in t4["final_answer"] or "52000" in t4["final_answer"]


def test_memory_reset():
    ref_date = date(2026, 1, 1)
    mem = SavingsMemory(ref_date=ref_date)
    mem.set_goal(target_amount=60000, deadline_str="2026-12-31", ref_date=ref_date)
    mem.add_saving(amount=5000, ref_date=ref_date)

    assert mem.has_active_goal() is True
    mem.reset()

    assert mem.has_active_goal() is False
    assert mem.get_total_saved() == 0.0
    assert len(mem.savings_entries) == 0
