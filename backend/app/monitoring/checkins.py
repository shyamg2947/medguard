"""
Weekly Check-in Engine with Fast-Forward Demo Clock.
Allows scheduling routine check-ins and fast-forwarding time in demo mode.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

_demo_clock_offset_days: int = 0
_scheduled_checkins: Dict[str, Dict[str, Any]] = {}


def get_current_time() -> datetime:
    """Returns current simulated time factoring in demo clock offset."""
    return datetime.now(timezone.utc) + timedelta(days=_demo_clock_offset_days)


def fast_forward_demo_clock(days: int = 7) -> datetime:
    global _demo_clock_offset_days
    _demo_clock_offset_days += days
    return get_current_time()


def reset_demo_clock():
    global _demo_clock_offset_days
    _demo_clock_offset_days = 0


def schedule_patient_checkin(
    patient_id: str,
    day_of_week: str = "Sunday",
    time_str: str = "10:00",
    channel: str = "simulator",
) -> Dict[str, Any]:
    _scheduled_checkins[patient_id] = {
        "patient_id": patient_id,
        "day_of_week": day_of_week,
        "time_str": time_str,
        "channel": channel,
        "active": True,
        "last_sent": None,
        "next_due": get_current_time() + timedelta(days=7),
    }
    return _scheduled_checkins[patient_id]


def cancel_patient_checkin(patient_id: str) -> bool:
    if patient_id in _scheduled_checkins:
        _scheduled_checkins[patient_id]["active"] = False
        return True
    return False


def get_due_checkins() -> List[Dict[str, Any]]:
    now = get_current_time()
    due = []
    for pid, sched in _scheduled_checkins.items():
        if sched["active"] and sched.get("next_due") and now >= sched["next_due"]:
            due.append(sched)
    return due

