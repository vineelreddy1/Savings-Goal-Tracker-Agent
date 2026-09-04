"""
Tools Module for Savings Goal Tracker Agent.
Defines required tools: create_savings_goal(), log_saving(), and get_goal_progress().
Each tool modifies or queries persistent SavingsMemory state and returns structured JSON-serializable dictionaries.
"""

from datetime import date
from typing import Dict, Any, Optional
from memory import SavingsMemory


def create_savings_goal(
    target_amount: Any,
    deadline: str,
    memory: Optional[SavingsMemory] = None,
    ref_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    TOOL 1: create_savings_goal(target_amount, deadline)
    Creates a new financial savings goal with a target amount and deadline date.

    Returns structured data:
    {
        "success": bool,
        "target": float,
        "deadline": str,
        "required_monthly_saving": float,
        "currency_symbol": str,
        "message": str
    }
    """
    if memory is None:
        memory = SavingsMemory(ref_date=ref_date)

    success, res_data, msg = memory.set_goal(
        target_amount=target_amount,
        deadline_str=deadline,
        ref_date=ref_date
    )

    if not success:
        return {
            "success": False,
            "error": msg,
            "target": target_amount,
            "deadline": deadline
        }

    return res_data


def log_saving(
    amount: Any,
    date_str: Optional[str] = None,
    memory: Optional[SavingsMemory] = None,
    ref_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    TOOL 2: log_saving(amount)
    Records a savings entry into persistent memory state.

    Returns structured data:
    {
        "success": bool,
        "amount_added": float,
        "total_saved": float,
        "remaining": float,
        "percentage": float,
        "currency_symbol": str,
        "status": str
    }
    """
    if memory is None:
        memory = SavingsMemory(ref_date=ref_date)

    success, res_data, msg = memory.add_saving(
        amount=amount,
        date_str=date_str,
        ref_date=ref_date
    )

    if not success:
        return {
            "success": False,
            "error": msg,
            "amount": amount
        }

    return res_data


def get_goal_progress(
    memory: Optional[SavingsMemory] = None,
    ref_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    TOOL 3: get_goal_progress()
    Retrieves complete metrics, time remaining, on-track status, and advice from memory.

    Returns structured data:
    {
        "target": float,
        "saved": float,
        "remaining": float,
        "percentage": float,
        "deadline": str,
        "required_monthly_saving": float,
        "status": str,
        "recommendation": str
    }
    """
    if memory is None:
        memory = SavingsMemory(ref_date=ref_date)

    return memory.get_progress(ref_date=ref_date)
