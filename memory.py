"""
Memory Module for Savings Goal Tracker Agent.
Provides persistent in-memory state tracking for active savings goals, savings log entries,
total saved accumulator, goal creation date, and conversation turn history.
"""

from datetime import date
from typing import Dict, Any, List, Optional, Tuple
from config import DEFAULT_REFERENCE_DATE, DEFAULT_CURRENCY, DEFAULT_CURRENCY_SYMBOL
from savings_logic import parse_deadline, calculate_goal_progress, format_currency


class SavingsMemory:
    """
    SavingsMemory holds persistent financial state across user conversation turns.
    """

    def __init__(
        self,
        ref_date: Optional[date] = None,
        currency: str = DEFAULT_CURRENCY,
        currency_symbol: str = DEFAULT_CURRENCY_SYMBOL
    ):
        self.ref_date = ref_date if ref_date is not None else DEFAULT_REFERENCE_DATE
        self.currency = currency
        self.currency_symbol = currency_symbol

        # Goal parameters
        self.target_amount: Optional[float] = None
        self.deadline: Optional[date] = None
        self.creation_date: Optional[date] = None

        # Savings history entries: List[Dict[str, Any]]
        # format: [{"amount": 5000.0, "date": "2026-01-05"}]
        self.savings_entries: List[Dict[str, Any]] = []

        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []

    def has_active_goal(self) -> bool:
        """Returns True if a valid goal has been created."""
        return self.target_amount is not None and self.deadline is not None

    def set_goal(
        self,
        target_amount: Any,
        deadline_str: str,
        ref_date: Optional[date] = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Creates or updates a savings goal. Validates target amount and deadline date.
        """
        current_ref = ref_date if ref_date is not None else self.ref_date

        # Validate target_amount
        try:
            target_val = float(target_amount)
        except (ValueError, TypeError):
            return False, {}, f"Target amount must be a positive number, got '{target_amount}'."

        if target_val <= 0:
            return False, {}, f"Target amount must be greater than zero. Got {self.currency_symbol}{target_val:,.2f}."

        # Parse & validate deadline
        success, parsed_date, msg = parse_deadline(deadline_str, ref_date=current_ref)
        if not success:
            return False, {}, msg

        # Store goal in memory
        self.target_amount = target_val
        self.deadline = parsed_date
        self.creation_date = current_ref

        # Calculate initial required monthly saving
        progress_info = self.get_progress(ref_date=current_ref)

        result_data = {
            "success": True,
            "target": self.target_amount,
            "deadline": self.deadline.isoformat(),
            "creation_date": self.creation_date.isoformat(),
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "required_monthly_saving": progress_info["required_monthly_saving"],
            "required_weekly_saving": progress_info["required_weekly_saving"],
            "message": f"Savings goal of {format_currency(self.target_amount, self.currency_symbol)} by {self.deadline.isoformat()} successfully set."
        }

        return True, result_data, "Goal successfully created."

    def add_saving(
        self,
        amount: Any,
        date_str: Optional[str] = None,
        ref_date: Optional[date] = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Logs a savings entry into memory. Accumulates total savings.
        """
        current_ref = ref_date if ref_date is not None else self.ref_date

        if not self.has_active_goal():
            return False, {}, "No active savings goal found. Please create a savings goal first (e.g. 'I want to save ₹60,000 by December')."

        # Validate amount
        try:
            amt_val = float(amount)
        except (ValueError, TypeError):
            return False, {}, f"Savings amount must be a positive number, got '{amount}'."

        if amt_val <= 0:
            return False, {}, f"Savings amount must be greater than zero. Got {self.currency_symbol}{amt_val:,.2f}."

        # Entry date
        entry_date = date_str if date_str else current_ref.isoformat()

        # Add entry
        entry = {
            "amount": amt_val,
            "date": entry_date
        }
        self.savings_entries.append(entry)

        # Calculate progress
        progress_info = self.get_progress(ref_date=current_ref)

        result_data = {
            "success": True,
            "amount_added": amt_val,
            "total_saved": progress_info["saved"],
            "target": progress_info["target"],
            "remaining": progress_info["remaining"],
            "percentage": progress_info["percentage"],
            "currency_symbol": self.currency_symbol,
            "status": progress_info["status"],
            "message": f"Successfully logged {format_currency(amt_val, self.currency_symbol)}. Total saved: {format_currency(progress_info['saved'], self.currency_symbol)}."
        }

        return True, result_data, "Savings successfully recorded."

    def get_total_saved(self) -> float:
        """Calculates total savings recorded across all entries."""
        return sum(entry["amount"] for entry in self.savings_entries)

    def get_progress(self, ref_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Returns full progress breakdown using pure Python calculation logic.
        """
        current_ref = ref_date if ref_date is not None else self.ref_date

        if not self.has_active_goal():
            return {
                "active_goal": False,
                "target": 0.0,
                "saved": 0.0,
                "remaining": 0.0,
                "percentage": 0.0,
                "deadline": None,
                "status": "NOT_STARTED",
                "recommendation": "No savings goal configured.",
                "currency_symbol": self.currency_symbol
            }

        total_saved = self.get_total_saved()
        creation_date = self.creation_date if self.creation_date else current_ref

        progress = calculate_goal_progress(
            target=self.target_amount,
            total_saved=total_saved,
            creation_date=creation_date,
            current_date=current_ref,
            deadline=self.deadline,
            symbol=self.currency_symbol
        )
        progress["active_goal"] = True
        progress["entries_count"] = len(self.savings_entries)
        return progress

    def get_memory_summary(self) -> str:
        """Returns a string representation of memory state for agent logging."""
        if not self.has_active_goal():
            return "Memory State: No active goal set. 0 savings entries."

        tot_saved = self.get_total_saved()
        rem = max(0.0, self.target_amount - tot_saved)
        return (
            f"Memory State:\n"
            f"  - Target: {format_currency(self.target_amount, self.currency_symbol)}\n"
            f"  - Deadline: {self.deadline.isoformat()}\n"
            f"  - Total Saved: {format_currency(tot_saved, self.currency_symbol)}\n"
            f"  - Remaining: {format_currency(rem, self.currency_symbol)}\n"
            f"  - Total Entries: {len(self.savings_entries)}\n"
            f"  - Goal Creation Date: {self.creation_date.isoformat()}"
        )

    def add_history(self, role: str, content: str) -> None:
        """Appends a turn message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def reset(self) -> None:
        """Resets all goal memory state."""
        self.target_amount = None
        self.deadline = None
        self.creation_date = None
        self.savings_entries = []
        self.conversation_history = []
