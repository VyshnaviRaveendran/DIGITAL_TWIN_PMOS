# backend/services/cycle_service.py
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import models

def parse_date_safely(val: Any) -> date:
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return date.today()

def calculate_cycle_tracker_summary(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Computes current menstrual cycle phase, cycle day, estimated ovulation,
    next period date, and phase-specific PMOS endocrine guidance.
    """
    latest_log = (
        db.query(models.CycleLog)
        .filter(models.CycleLog.user_id == user_id)
        .order_by(models.CycleLog.period_start_date.desc(), models.CycleLog.id.desc())
        .first()
    )

    if not latest_log:
        return {
            "has_logged": False,
            "current_phase": "Pending Entry",
            "cycle_day": "--",
            "estimated_ovulation": "--",
            "next_period_date": "--",
            "guidance": "Log your most recent period start date below to calculate your current cycle phase, estimated ovulation window, and endocrine lifestyle recommendations."
        }

    start_date = parse_date_safely(latest_log.period_start_date)
    today = date.today()
    cycle_length = latest_log.cycle_length_days if (latest_log.cycle_length_days and latest_log.cycle_length_days > 20) else 28

    days_diff = (today - start_date).days

    if days_diff < 0:
        # Future date logged
        cycle_day = 1
        current_cycle_start = start_date
    else:
        # Calculate current cycle iteration
        cycles_elapsed = days_diff // cycle_length
        current_cycle_start = start_date + timedelta(days=cycles_elapsed * cycle_length)
        cycle_day = (today - current_cycle_start).days + 1

    next_period = current_cycle_start + timedelta(days=cycle_length)
    ovulation_offset = max(10, cycle_length - 14)
    estimated_ovulation = current_cycle_start + timedelta(days=ovulation_offset)

    # Menstrual Phase Classifications
    if cycle_day <= 5:
        phase = "Menstrual Phase"
        guidance = "Endocrine reset window. Prioritize iron-dense whole foods, magnesium, and gentle movement like restorative walking."
    elif cycle_day <= ovulation_offset - 2:
        phase = "Follicular Phase"
        guidance = "Rising estrogen improves insulin sensitivity. Optimal window for progressive resistance training and nutrient-dense complex carbs."
    elif cycle_day <= ovulation_offset + 2:
        phase = "Ovulatory Phase"
        guidance = "Peak LH and estrogen surge. Support estrogen clearance with cruciferous vegetables, hydration, and steady zone-2 cardio."
    else:
        phase = "Luteal Phase"
        guidance = "Progesterone dominant phase. Support luteal satiety with healthy lipids (avocado, seeds), magnesium, and sleep hygiene to blunt PMS cravings."

    return {
        "has_logged": True,
        "current_phase": phase,
        "cycle_day": cycle_day,
        "estimated_ovulation": estimated_ovulation.strftime("%Y-%m-%d"),
        "next_period_date": next_period.strftime("%Y-%m-%d"),
        "guidance": guidance
    }
