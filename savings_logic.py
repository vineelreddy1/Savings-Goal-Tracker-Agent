"""
Savings Logic Module for Savings Goal Tracker Agent.
Provides pure Python deterministic financial arithmetic, date parsing, pace calculation,
and status determination.
"""

from datetime import date, datetime
import calendar
import math
from typing import Tuple, Dict, Any, Optional
from config import DEFAULT_REFERENCE_DATE, DEFAULT_CURRENCY_SYMBOL, PACE_TOLERANCE_RATIO


def parse_deadline(
    deadline_str: str,
    ref_date: Optional[date] = None
) -> Tuple[bool, Optional[date], str]:
    """
    Parses deadline strings into a valid datetime.date object.
    Supports formats:
      - ISO YYYY-MM-DD ('2026-12-31')
      - ISO YYYY-MM ('2026-12') -> defaults to last day of month
      - Month name ('December', 'Dec') -> defaults to last day of specified month in reference year
      - Month Year ('December 2026', 'Dec 2026') -> defaults to last day of month
      - Standard dates ('31-12-2026', '12/31/2026')

    Validates that the deadline is not in the past relative to ref_date.
    """
    if ref_date is None:
        ref_date = DEFAULT_REFERENCE_DATE

    if not deadline_str or not isinstance(deadline_str, str):
        return False, None, "Deadline must be a non-empty text string."

    clean_str = deadline_str.strip()
    parsed_date: Optional[date] = None

    # Try ISO YYYY-MM-DD
    try:
        parsed_date = datetime.strptime(clean_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Try ISO YYYY-MM
    if parsed_date is None:
        try:
            dt = datetime.strptime(clean_str, "%Y-%m")
            last_day = calendar.monthrange(dt.year, dt.month)[1]
            parsed_date = date(dt.year, dt.month, last_day)
        except ValueError:
            pass

    # Try DD-MM-YYYY or MM/DD/YYYY
    if parsed_date is None:
        for fmt in ("%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(clean_str, fmt).date()
                break
            except ValueError:
                pass

    # Try Month Year (e.g. 'December 2026', 'Dec 2026')
    if parsed_date is None:
        for fmt in ("%B %Y", "%b %Y"):
            try:
                dt = datetime.strptime(clean_str, fmt)
                last_day = calendar.monthrange(dt.year, dt.month)[1]
                parsed_date = date(dt.year, dt.month, last_day)
                break
            except ValueError:
                pass

    # Try standalone Month name (e.g. 'December', 'Dec')
    if parsed_date is None:
        for fmt in ("%B", "%b"):
            try:
                dt = datetime.strptime(clean_str, fmt)
                year = ref_date.year
                last_day = calendar.monthrange(year, dt.month)[1]
                candidate = date(year, dt.month, last_day)
                # If candidate is earlier than ref_date, assume next year
                if candidate < ref_date:
                    year += 1
                    last_day = calendar.monthrange(year, dt.month)[1]
                    candidate = date(year, dt.month, last_day)
                parsed_date = candidate
                break
            except ValueError:
                pass

    if parsed_date is None:
        return False, None, f"Invalid date format '{deadline_str}'. Please use YYYY-MM-DD or Month Year (e.g., '2026-12-31' or 'December 2026')."

    if parsed_date < ref_date:
        return False, parsed_date, f"Deadline '{parsed_date.isoformat()}' cannot be in the past (Current date: {ref_date.isoformat()})."

    return True, parsed_date, "Successfully parsed deadline."


def format_currency(amount: float, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> str:
    """Formats float amount into currency string with commas."""
    if amount == int(amount):
        return f"{symbol}{int(amount):,}"
    return f"{symbol}{amount:,.2f}"


def calculate_goal_progress(
    target: float,
    total_saved: float,
    creation_date: date,
    current_date: date,
    deadline: date,
    symbol: str = DEFAULT_CURRENCY_SYMBOL
) -> Dict[str, Any]:
    """
    Computes all goal metrics deterministically using Python:
    1. Total saved & remaining amount
    2. Percentage completed
    3. Time remaining (days, months, weeks)
    4. Required monthly & weekly saving
    5. On-track pace status (NOT_STARTED, BEHIND, ON_TRACK, GOAL_REACHED)
    """
    # Defensive capping
    target = max(0.0, float(target))
    total_saved = max(0.0, float(total_saved))

    # Remaining amount cannot be negative
    remaining = max(0.0, target - total_saved)

    # Percentage completed
    if target > 0:
        percentage = round((total_saved / target) * 100.0, 2)
    else:
        percentage = 0.0

    # Capped percentage representation for status display (max 100%)
    display_percentage = min(100.0, percentage)

    # Time calculations
    total_days = (deadline - creation_date).days
    if total_days <= 0:
        total_days = 1  # prevent division by zero

    elapsed_days = (current_date - creation_date).days
    elapsed_days = max(0, min(total_days, elapsed_days))

    remaining_days = (deadline - current_date).days
    remaining_days = max(0, remaining_days)

    # Monthly & Weekly duration units
    remaining_months = max(1.0, round(remaining_days / 30.4375, 1))
    remaining_weeks = max(1.0, round(remaining_days / 7.0, 1))

    # Required savings calculations
    if remaining <= 0:
        required_monthly = 0.0
        required_weekly = 0.0
    else:
        # Number of months remaining (at least 1 to avoid zero division)
        months_divisor = max(1.0, remaining_days / 30.4375)
        weeks_divisor = max(1.0, remaining_days / 7.0)
        required_monthly = round(remaining / months_divisor, 2)
        required_weekly = round(remaining / weeks_divisor, 2)

    # Expected saved pace comparison
    expected_ratio = elapsed_days / total_days
    expected_saved = target * expected_ratio

    # Status Determination
    if total_saved >= target:
        status = "GOAL_REACHED"
    elif total_saved == 0:
        status = "NOT_STARTED"
    elif total_saved >= expected_saved * (1.0 - PACE_TOLERANCE_RATIO):
        status = "ON_TRACK"
    else:
        status = "BEHIND"

    # Grounded simple recommendations based on status
    recommendation = generate_recommendation(status, required_monthly, symbol)

    return {
        "target": target,
        "saved": total_saved,
        "remaining": remaining,
        "percentage": display_percentage,
        "raw_percentage": percentage,
        "creation_date": creation_date.isoformat(),
        "current_date": current_date.isoformat(),
        "deadline": deadline.isoformat(),
        "total_days": total_days,
        "elapsed_days": elapsed_days,
        "remaining_days": remaining_days,
        "remaining_months": remaining_months,
        "remaining_weeks": remaining_weeks,
        "required_monthly_saving": required_monthly,
        "required_weekly_saving": required_weekly,
        "expected_saved": round(expected_saved, 2),
        "status": status,
        "recommendation": recommendation,
        "currency_symbol": symbol
    }


def generate_recommendation(
    status: str,
    required_monthly: float,
    symbol: str = DEFAULT_CURRENCY_SYMBOL
) -> str:
    """
    Generates non-advisor financial guidance based strictly on calculated goal metrics.
    No investment advice, financial products, or guaranteed outcomes.
    """
    formatted_monthly = format_currency(required_monthly, symbol)

    if status == "GOAL_REACHED":
        return "Congratulations! You've reached your savings goal."
    elif status == "ON_TRACK":
        return f"You're on track. Continue saving approximately {formatted_monthly} per month to hit your deadline."
    elif status == "BEHIND":
        return f"You're currently behind the expected pace. You need approximately {formatted_monthly} per month to reach the goal."
    elif status == "NOT_STARTED":
        return f"You haven't recorded any savings yet. Aim to save approximately {formatted_monthly} per month to hit your deadline."
    return f"Keep making progress toward your savings target!"
