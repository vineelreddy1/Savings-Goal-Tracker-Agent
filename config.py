"""
Configuration parameters for Savings Goal Tracker Agent.
"""

from datetime import date
import os

# Default Currency configuration
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "INR")
DEFAULT_CURRENCY_SYMBOL = os.getenv("DEFAULT_CURRENCY_SYMBOL", "₹")

# Reference Date for testing / baseline calculations
# In production, datetime.date.today() is used unless ref_date is specified.
DEFAULT_REFERENCE_DATE = date(2026, 1, 1)

# Execution & Trace Logging
VERBOSE_TRACE = True

# Progress Calculation Tolerances
# A small tolerance (e.g. 5%) ensures slight timing variances don't trigger BEHIND status prematurely.
PACE_TOLERANCE_RATIO = 0.05
