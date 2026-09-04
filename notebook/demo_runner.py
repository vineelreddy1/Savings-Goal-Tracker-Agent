"""
Demo Runner for Savings Goal Tracker Agent.
Executes all 6 required scenarios in order, demonstrating tool calls, visible agent trace,
persistent memory across turns, and status transitions.
"""

import sys
import os
from datetime import date

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent import SavingsGoalAgent
from config import DEFAULT_REFERENCE_DATE


def run_all_scenarios():
    ref_date = date(2026, 1, 1)
    agent = SavingsGoalAgent(ref_date=ref_date, verbose=True)

    print("==================================================")
    print("DAY 6 — SAVINGS GOAL TRACKER AGENT DEMO")
    print("==================================================\n")

    # SCENARIO 1 — CREATE GOAL
    print("--- SCENARIO 1: CREATE GOAL ---")
    u1 = "I want to save ₹60,000 by December."
    agent.process_turn(u1)
    print("\n" + "="*50 + "\n")

    # SCENARIO 2 — FIRST SAVING
    print("--- SCENARIO 2: FIRST SAVING ---")
    u2 = "I saved ₹5,000."
    agent.process_turn(u2)
    print("\n" + "="*50 + "\n")

    # SCENARIO 3 — SECOND SAVING
    print("--- SCENARIO 3: SECOND SAVING ---")
    u3 = "I saved another ₹3,000."
    agent.process_turn(u3)
    print("\n" + "="*50 + "\n")

    # SCENARIO 4 — CHECK PROGRESS
    print("--- SCENARIO 4: CHECK PROGRESS ---")
    u4 = "How much have I saved?"
    agent.process_turn(u4)
    print("\n" + "="*50 + "\n")

    # SCENARIO 5 — CHECK REMAINING
    print("--- SCENARIO 5: CHECK REMAINING ---")
    u5 = "How much more do I need?"
    agent.process_turn(u5)
    print("\n" + "="*50 + "\n")

    # SCENARIO 6 — STATUS TRANSITIONS (BEHIND & GOAL_REACHED)
    print("--- SCENARIO 6: STATUS TRANSITION (BEHIND -> GOAL_REACHED) ---")
    
    # 6A: Simulate time passing (fast-forward to July 2026 without adding new savings)
    print("\n>> Fast-forwarding current date to July 1, 2026 (6 months elapsed out of 12)...")
    agent.ref_date = date(2026, 7, 1)
    u6a = "How am I doing on my goal?"
    agent.process_turn(u6a)
    print("\n" + "-"*40 + "\n")

    # 6B: User saves a large lump sum to achieve GOAL_REACHED status
    print("\n>> User logs large saving entry to complete goal...")
    u6b = "I saved ₹52,000."
    agent.process_turn(u6b)
    print("\n" + "="*50 + "\n")

    print("ALL 6 DEMO SCENARIOS COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    run_all_scenarios()
