"""
Time-on-Drug Exposure and Duration Calculations.
Parses exact dates or approximate verbal phrases (e.g., 'about 3 months', '14 weeks', '6 months').
Computes exposure with lower and upper confidence bounds.
"""
from datetime import datetime, timezone
import re
from typing import Optional, Tuple


def parse_duration_to_weeks(start_date_or_phrase: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Returns (lower_bound_weeks, upper_bound_weeks).
    If unknown or missing, returns (None, None).
    """
    if not start_date_or_phrase:
        return None, None

    text = str(start_date_or_phrase).lower().strip()

    # 1. Exact ISO date format (YYYY-MM-DD)
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if date_match:
        try:
            start_dt = datetime.strptime(date_match.group(0), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days = (now - start_dt).days
            weeks = max(0.0, days / 7.0)
            return round(weeks, 1), round(weeks, 1)
        except Exception:
            pass

    # 2. Verbal phrases: "14 weeks", "about 8 weeks"
    w_match = re.search(r'(\d+(?:\.\d+)?)\s*week', text)
    if w_match:
        val = float(w_match.group(1))
        # Add 10% uncertainty margin for verbal estimates
        return round(val * 0.9, 1), round(val * 1.1, 1)

    # 3. Months: "about 3 months", "6 months"
    m_match = re.search(r'(\d+(?:\.\d+)?)\s*month', text)
    if m_match:
        months = float(m_match.group(1))
        weeks = months * 4.33
        return round(weeks * 0.85, 1), round(weeks * 1.15, 1)

    # 4. Years: "1 year", "about 2 years"
    y_match = re.search(r'(\d+(?:\.\d+)?)\s*year', text)
    if y_match:
        years = float(y_match.group(1))
        weeks = years * 52.14
        return round(weeks * 0.9, 1), round(weeks * 1.1, 1)

    # 5. Days: "10 days"
    d_match = re.search(r'(\d+(?:\.\d+)?)\s*day', text)
    if d_match:
        days = float(d_match.group(1))
        weeks = days / 7.0
        return round(weeks, 1), round(weeks, 1)

    return None, None


def check_duration_exceeded(
    start_date_or_phrase: Optional[str],
    max_duration_weeks: int
) -> Tuple[bool, bool, Optional[float]]:
    """
    Returns (exceeded, is_possible, lower_bound_weeks).
    - exceeded: True if lower_bound > max_duration_weeks (high certainty)
    - is_possible: True if upper_bound > max_duration_weeks but lower_bound <= max_duration_weeks
    """
    lower, upper = parse_duration_to_weeks(start_date_or_phrase)
    if lower is None or upper is None:
        return False, False, None

    if lower > max_duration_weeks:
        return True, False, lower
    elif upper > max_duration_weeks:
        return False, True, lower
    return False, False, lower

