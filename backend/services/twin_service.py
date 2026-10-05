# backend/services/twin_service.py
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import models

def calculate_latest_telemetry(user_id: int, db: Session) -> Dict[str, Any]:
    try:
        user_meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
        total_calories = sum(m.calories for m in user_meals)
        high_gi_count = sum(1 for m in user_meals if "High" in (m.glycemic_risk or ""))

        today_exercises = db.query(models.ExerciseLog).filter(models.ExerciseLog.user_id == user_id).all()
        total_burned = sum(e.calories_burned for e in today_exercises)

        target_kcal = 1939.0
        net_calories = max(0.0, total_calories - total_burned)
        calorie_surplus = max(0.0, net_calories - target_kcal)

        base_stability = 100
        surplus_penalty = int((calorie_surplus / 100.0) * 8)
        glycemic_penalty = high_gi_count * 10

        if total_calories == 0:
            stability_score = 100
        else:
            stability_score = max(15, min(100, int(base_stability - surplus_penalty - glycemic_penalty)))

        return {
            "has_logged": total_calories > 0,
            "total_calories": total_calories,
            "calories_burned": total_burned,
            "net_calories": net_calories,
            "calorie_surplus": calorie_surplus,
            "stability_score": stability_score,
            "is_high_risk": bool(calorie_surplus > 300 or stability_score < 65)
        }
    except Exception as e:
        print(f"Error in telemetry calculation: {e}")
        return {
            "has_logged": False,
            "total_calories": 0,
            "calories_burned": 0,
            "net_calories": 0,
            "calorie_surplus": 0.0,
            "stability_score": 100,
            "is_high_risk": False
        }

def compute_twin_risk_and_interventions(payload: dict, db: Session) -> Dict[str, Any]:
    user_id = payload.get("user_id")

    # If parameters not directly provided, inspect recent logs
    sleep = payload.get("sleep_hours")
    exercise = payload.get("exercise_minutes")
    stress = payload.get("stress_level")

    if user_id:
        if sleep is None:
            last_sleep = (
                db.query(models.SleepLog)
                .filter(models.SleepLog.user_id == user_id)
                .order_by(models.SleepLog.id.desc())
                .first()
            )
            sleep = float(last_sleep.sleep_hours) if last_sleep else 7.0

        if exercise is None:
            user_exercises = db.query(models.ExerciseLog).filter(models.ExerciseLog.user_id == user_id).all()
            exercise = sum(e.duration_mins for e in user_exercises) if user_exercises else 30.0

        if stress is None:
            recent_stress = (
                db.query(models.StressResetLog)
                .filter(models.StressResetLog.user_id == user_id)
                .order_by(models.StressResetLog.id.desc())
                .first()
            )
            stress = 4.0 if recent_stress else 5.0
    else:
        sleep = sleep if sleep is not None else 7.0
        exercise = exercise if exercise is not None else 30.0
        stress = stress if stress is not None else 5.0

    # Risk score calculation [0.05, 0.95]
    risk_score = round(max(0.05, min(0.95, (stress * 0.1) + ((8.0 - sleep) * 0.05) - (exercise * 0.002))), 2)

    # Dynamic single-line intervention
    if risk_score > 0.6:
        intervention = "Elevated biological stress vector detected. Engage Parasympathetic 4-7-8 Reset immediately and prioritize sleep hygiene."
    elif risk_score > 0.3:
        intervention = "Fluctuating stability vector. Maintain balanced complex carbs at dinner and ensure hydration."
    else:
        intervention = "Digital Twin stable. Optimal biological equilibrium maintained across all 5 Pillars."

    # Multi-Pillar detailed recommendations list
    recommendations: List[Dict[str, str]] = []

    if sleep < 7.0:
        recommendations.append({
            "type": "risk",
            "title": "Sleep Debt Warning",
            "body": f"Logged {sleep}h of sleep (target: 8h). Nocturnal cortisol elevations may impair insulin sensitivity."
        })
    else:
        recommendations.append({
            "type": "optimal",
            "title": "Circadian Rest Optimal",
            "body": "Sufficient sleep duration promotes ovarian steroidogenesis and normal morning fasting glucose."
        })

    if stress >= 6:
        recommendations.append({
            "type": "risk",
            "title": "Sympathetic Nervous Strain",
            "body": "Adrenal overload detected. Perform Box Breathing or the 4-7-8 protocol to trigger vagal acetylcholine release."
        })
    else:
        recommendations.append({
            "type": "optimal",
            "title": "Adrenal Balance",
            "body": "Stress levels are controlled, minimizing stress-driven androgen conversions."
        })

    if exercise < 20:
        recommendations.append({
            "type": "risk",
            "title": "Sedentary Window",
            "body": "Less than 20 minutes of movement logged today. A 15-minute post-meal walk blunts glycemic spikes."
        })
    else:
        recommendations.append({
            "type": "optimal",
            "title": "Metabolic Muscular Uptake",
            "body": f"Logged {int(exercise)} mins of activity, activating non-insulin-mediated GLUT4 glucose clearance."
        })

    return {
        "symptom_risk_coefficient": risk_score,
        "dynamic_intervention": intervention,
        "recommendations": recommendations
    }

def generate_clinical_health_report(user_id: int, days: int, db: Session) -> Dict[str, Any]:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {}

    assessment = (
        db.query(models.IntakeAssessment)
        .filter(models.IntakeAssessment.user_id == user_id)
        .order_by(models.IntakeAssessment.id.desc())
        .first()
    )

    cycle_logs = (
        db.query(models.CycleLog)
        .filter(models.CycleLog.user_id == user_id)
        .order_by(models.CycleLog.period_start_date.desc())
        .all()
    )

    meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
    exercises = db.query(models.ExerciseLog).filter(models.ExerciseLog.user_id == user_id).all()
    meds = db.query(models.MedicationLog).filter(models.MedicationLog.user_id == user_id).all()
    stress_logs = db.query(models.StressResetLog).filter(models.StressResetLog.user_id == user_id).all()

    total_calories = sum(m.calories for m in meals)
    high_gi_count = sum(1 for m in meals if "High" in (m.glycemic_risk or ""))
    avg_daily_calories = round(total_calories / max(1, len(meals) or 1), 1) if meals else 0

    total_workouts = len(exercises)
    total_burned = sum(e.calories_burned for e in exercises)
    active_meds = [m.med_name for m in meds]

    formatted_cycles = []
    for c in cycle_logs:
        start_val = c.period_start_date
        start_str = start_val.strftime("%Y-%m-%d") if isinstance(start_val, (date, datetime)) else str(start_val)
        formatted_cycles.append({
            "start": start_str,
            "flow": c.flow_intensity or "Medium",
            "length": c.cycle_length_days or 28,
            "notes": c.notes or "-"
        })

    return {
        "report_metadata": {
            "patient_name": user.full_name or "Patient",
            "timeframe_days": days,
            "generated_date": date.today().isoformat(),
            "assigned_phenotype": assessment.assigned_phenotype if assessment else "Phenotype A: Classic PMOS",
            "height_cm": getattr(user, "height_cm", 162),
            "weight_kg": getattr(user, "weight_kg", 58),
            "bmi": getattr(user, "bmi", 22.1),
            "bmi_category": getattr(user, "bmi_category", "Normal")
        },
        "cycle_summary": {
            "total_cycles_logged": len(cycle_logs),
            "recent_periods": formatted_cycles
        },
        "pillar_analytics": {
            "diet": {
                "avg_daily_calories": avg_daily_calories,
                "total_calories_logged": total_calories,
                "high_gi_meals_count": high_gi_count
            },
            "exercise": {
                "total_completed_workouts": total_workouts,
                "total_calories_burned": total_burned
            },
            "medications": {
                "active_protocol": active_meds
            },
            "stress_and_symptoms": {
                "total_resets_completed": len(stress_logs)
            }
        }
    }
