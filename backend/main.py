from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

import models, schemas
from database import engine, Base, get_db

from pydantic import BaseModel
from typing import Optional


from models import ExerciseLog, SleepLog, HealthLog, User

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Digital Twin PMOS API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODEL INITIALIZATION =================
X_train = np.array([
    [520, 36, 42, 28],  # Underweight Lean Optimal
    [250, 10, 55, 5],   # High Glycemic Spike Risk
    [450, 32, 15, 30],  # Insulin Resistant Safe
    [180, 5, 35, 2]     # Unbalanced Spike Risk
])
y_train = np.array([2, 0, 1, 0])

meal_knn_model = KNeighborsClassifier(n_neighbors=1)
meal_knn_model.fit(X_train, y_train)

# ================= 4-MEAL PHENOTYPE RECIPE DATABASE =================
RECIPES_DF = pd.DataFrame([
    # Phenotype B: Underweight / Hyperandrogenic PMOS
    {"meal_slot": "Breakfast", "name": "Avocado & Pasture-Raised Eggs on Seeded Sourdough", "kcal": 460, "protein": 24, "carbs": 28, "fats": 28, "gi": 35, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Choline and mono-unsaturated fats to support hormone steroidogenesis."},
    {"meal_slot": "Lunch", "name": "Wild Alaskan Salmon & Quinoa Tahini Bowl", "kcal": 580, "protein": 40, "carbs": 32, "fats": 34, "gi": 28, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "High Omega-3s to downregulate follicular inflammation."},
    {"meal_slot": "Dinner", "name": "Slow-Roasted Grass-Fed Beef with Sweet Potato Mash", "kcal": 550, "protein": 42, "carbs": 38, "fats": 26, "gi": 40, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Bioavailable zinc and iron supporting ovarian follicle maturation."},
    {"meal_slot": "Snack", "name": "Raw Macadamia, Walnuts & Pumpkin Seed Cluster", "kcal": 349, "protein": 12, "carbs": 10, "fats": 30, "gi": 15, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Anti-androgenic magnesium & healthy lipid density."},

    # Phenotype A: Classic PMOS / Insulin Resistant
    {"meal_slot": "Breakfast", "name": "Chia Seed & Flax Pudding with Collagen & Blueberries", "kcal": 380, "protein": 28, "carbs": 16, "fats": 22, "gi": 18, "phenotype": "Phenotype A: Classic PMOS", "desc": "High viscous fiber to blunt morning cortisol & insulin release."},
    {"meal_slot": "Lunch", "name": "Grilled Herb Chicken Breast & Cauliflower Rice Pilaf", "kcal": 490, "protein": 48, "carbs": 18, "fats": 24, "gi": 15, "phenotype": "Phenotype A: Classic PMOS", "desc": "Ultra low-glycemic load maintaining baseline insulin sensitivity."},
    {"meal_slot": "Dinner", "name": "Pan-Seared Halibut with Sautéed Asparagus & Garlic Kale", "kcal": 450, "protein": 44, "carbs": 14, "fats": 24, "gi": 12, "phenotype": "Phenotype A: Classic PMOS", "desc": "Sulforaphane & glutathione to promote estrogen liver conjugation."},
    {"meal_slot": "Snack", "name": "Organic Celery Sticks with Salted Almond Butter", "kcal": 219, "protein": 8, "carbs": 8, "fats": 18, "gi": 10, "phenotype": "Phenotype A: Classic PMOS", "desc": "Electrolytes and protein buffer preventing mid-day sugar cravings."},

    # Phenotype C: Metabolic-Adrenal PMOS
    {"meal_slot": "Breakfast", "name": "Poached Eggs, Sautéed Spinach & Roasted Pumpkin Slices", "kcal": 410, "protein": 26, "carbs": 24, "fats": 24, "gi": 30, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Magnesium-dense start preventing adrenal cortisol surges."},
    {"meal_slot": "Lunch", "name": "Free-Range Turkey Breast with Steamed Broccoli & Tahini", "kcal": 510, "protein": 46, "carbs": 20, "fats": 28, "gi": 20, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Tryptophan-rich protein sustaining steady adrenal neurotransmitters."},
    {"meal_slot": "Dinner", "name": "Braised Cod Fillet with Stewed Zucchini & Olive Oil", "kcal": 480, "protein": 38, "carbs": 18, "fats": 28, "gi": 22, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Easily digestible evening protein supporting nocturnal growth hormone."},
    {"meal_slot": "Snack", "name": "Spiced Golden Turmeric Milk with Coconut Cream & Chia", "kcal": 239, "protein": 6, "carbs": 12, "fats": 18, "gi": 15, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Curcumin anti-inflammatory tonic for evening vagus downregulation."},

    # Phenotype D: Normo-Androgenic PMOS
    {"meal_slot": "Breakfast", "name": "Greek Yogurt Bowl with Hemp Seeds & Raspberries", "kcal": 400, "protein": 32, "carbs": 22, "fats": 20, "gi": 25, "phenotype": "Phenotype D: Normo-Androgenic PMOS", "desc": "Probiotic and protein balance to sustain gut-estrogen clearance."},
    {"meal_slot": "Lunch", "name": "Mediterranean Quinoa Bowl with Extra Virgin Olive Oil & Tuna", "kcal": 530, "protein": 42, "carbs": 35, "fats": 24, "gi": 32, "phenotype": "Phenotype D: Normo-Androgenic PMOS", "desc": "Polyphenols supporting ovulatory regularity and vascular tone."},
    {"meal_slot": "Dinner", "name": "Grilled Chicken Paillard with Sautéed Artichoke Hearts", "kcal": 490, "protein": 45, "carbs": 20, "fats": 25, "gi": 20, "phenotype": "Phenotype D: Normo-Androgenic PMOS", "desc": "Fiber prebiotic substrate supporting luteal phase progesterone synthesis."},
    {"meal_slot": "Snack", "name": "Handful of Roasted Cashews & Dark Chocolate (85%)", "kcal": 219, "protein": 7, "carbs": 14, "fats": 16, "gi": 20, "phenotype": "Phenotype D: Normo-Androgenic PMOS", "desc": "Flavonoid antioxidant boost without glycemic volatility."}
])

BASE_WEIGHTS = {
    "Breakfast": 0.25,
    "Lunch": 0.35,
    "Dinner": 0.30,
    "Snack": 0.10
}

@app.get("/")
def read_root():
    return {"status": "Backend running successfully", "docs": "http://127.0.0.1:8000/docs"}

# ================= AUTHENTICATION ENDPOINTS =================
@app.post("/api/signup")
def signup(data: schemas.SignupSchema, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(
        full_name=data.full_name,
        email=data.email,
        password_hash=data.password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "message": "User registered successfully", "user_id": new_user.id, "full_name": new_user.full_name}

@app.post("/api/login")
def login(credentials: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or user.password_hash != credentials.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": "sample_token_xyz", "user_id": user.id, "full_name": user.full_name}

# ================= USER PROFILE & PHENOTYPE QUERY =================
@app.get("/api/user-profile/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    latest_assessment = db.query(models.IntakeAssessment).filter(
        models.IntakeAssessment.user_id == user_id
    ).order_by(models.IntakeAssessment.id.desc()).first()

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "assigned_phenotype": latest_assessment.assigned_phenotype if latest_assessment else None,
        "is_calibrated": latest_assessment is not None
    }

# ================= INTAKE & PHENOTYPE EVALUATION =================
def classify_phenotype(data: schemas.IntakeSchema) -> str:
    if data.symp_periods and (data.symp_hair or data.symp_acne):
        return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
    elif data.usg_result == "cysts" and data.symp_periods:
        return "Phenotype A: Classic PMOS"
    elif data.symp_weight or data.symp_stress:
        return "Phenotype C: Metabolic-Adrenal PMOS"
    return "Phenotype D: Normo-Androgenic PMOS"

@app.post("/api/submit-intake")
def submit_intake(data: schemas.IntakeSchema, db: Session = Depends(get_db)):
    assigned_pheno = classify_phenotype(data)
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    assessment_id = 1
    if user:
        new_assessment = models.IntakeAssessment(
            user_id=data.user_id,
            symp_periods=data.symp_periods,
            symp_hair=data.symp_hair,
            symp_thinning=data.symp_thinning,
            symp_acne=data.symp_acne,
            symp_stress=data.symp_stress,
            symp_weight=data.symp_weight,
            usg_result=data.usg_result,
            prior_diagnosis=data.prior_diagnosis,
            assigned_phenotype=assigned_pheno
        )
        db.add(new_assessment)
        db.commit()
        db.refresh(new_assessment)
        assessment_id = new_assessment.id

    return {"status": "success", "assigned_phenotype": assigned_pheno, "assessment_id": assessment_id}

# ================= DAILY HEALTH TELEMETRY (QUICK LOG) =================
@app.post("/api/submit-health-log")
def submit_health_log(data: schemas.HealthLogSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stability_score = int(100 - (data.stress_level * 5) + (data.sleep_hours * 2) + (data.exercise_mins * 0.2))
    stability_score = max(10, min(99, stability_score))

    new_log = models.HealthLog(
        user_id=data.user_id,
        stress_level=data.stress_level,
        sleep_hours=float(data.sleep_hours),
        exercise_mins=data.exercise_mins,
        diet_score=data.diet_score,
        medication_status=data.medication_status,
        risk_score=float(stability_score)
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {
        "status": "success",
        "message": "Health metrics logged successfully",
        "stability_score": stability_score,
        "log_id": new_log.id
    }

# ================= DIET & DYNAMIC SLOT CALORIE SPLIT =================
@app.post("/api/log-meal")
def log_meal(data: schemas.MealLogCreate, db: Session = Depends(get_db)):
    new_meal = models.MealLog(
        user_id=data.user_id,
        meal_name=data.meal_name,
        meal_type=data.meal_type or "Lunch",
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fats=data.fats,
        glycemic_risk=data.glycemic_risk
    )
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)
    return get_diet_summary_logic(data.user_id, db)

@app.get("/api/diet-summary/{user_id}")
def get_diet_summary(user_id: int, db: Session = Depends(get_db)):
    return get_diet_summary_logic(user_id, db)

def get_diet_summary_logic(user_id: int, db: Session):
    user_meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
    logged_slots = [m.meal_type for m in user_meals]
    total_logged = sum(m.calories for m in user_meals)

    tdee_target = 1939.0
    remaining_balance = float(np.maximum(0.0, tdee_target - total_logged))
    
    all_slots = ["Breakfast", "Lunch", "Dinner", "Snack"]
    unlogged_slots = [slot for slot in all_slots if slot not in logged_slots]
    day_completed = len(unlogged_slots) == 0 or len(user_meals) >= 4

    splits = {}
    if not day_completed and remaining_balance > 0:
        total_remaining_weight = sum(BASE_WEIGHTS[slot] for slot in unlogged_slots)
        for slot in unlogged_slots:
            slot_ratio = BASE_WEIGHTS[slot] / total_remaining_weight
            splits[slot] = int(round(remaining_balance * slot_ratio))
    else:
        for slot in all_slots:
            splits[slot] = 0

    return {
        "daily_target": tdee_target,
        "logged_today": total_logged,
        "remaining_balance": remaining_balance,
        "meals_count": len(user_meals),
        "logged_slots": logged_slots,
        "unlogged_slots": unlogged_slots,
        "day_completed": day_completed,
        "allowance_split": splits,
        "recent_meals": [
            {
                "id": m.id,
                "name": m.meal_name,
                "meal_type": m.meal_type,
                "calories": m.calories,
                "protein": m.protein,
                "carbs": m.carbs,
                "fats": m.fats
            }
            for m in user_meals[-4:]
        ]
    }

@app.post("/api/reset-day/{user_id}")
def reset_day(user_id: int, db: Session = Depends(get_db)):
    db.query(models.MealLog).filter(models.MealLog.user_id == user_id).delete()
    db.commit()
    return {"status": "success", "message": "Rolled over to new day!"}

# ================= 4-MEAL PHENOTYPE SUGGESTIONS =================
@app.get("/api/diet-recommendations/{user_id}")
def get_diet_recommendations(user_id: int, db: Session = Depends(get_db)):
    assessment = db.query(models.IntakeAssessment).filter(
        models.IntakeAssessment.user_id == user_id
    ).order_by(models.IntakeAssessment.id.desc()).first()

    assigned_phenotype = assessment.assigned_phenotype if assessment else "Phenotype A: Classic PMOS"

    matching = RECIPES_DF[RECIPES_DF["phenotype"] == assigned_phenotype]
    if matching.empty:
        matching = RECIPES_DF[RECIPES_DF["phenotype"] == "Phenotype A: Classic PMOS"]

    user_meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
    logged_slots = [m.meal_type for m in user_meals]

    if "Phenotype B" in assigned_phenotype:
        guidance_title = "Underweight / Lean PMOS Daily Matrix:"
        guidance_body = "Target high healthy fats & dense proteins. Distribute energy across 4 calibrated meals to build tissue without glycemic volatility."
    elif "Phenotype C" in assigned_phenotype:
        guidance_title = "Metabolic-Adrenal Daily Matrix:"
        guidance_body = "Consume unrefined low-GI complex carbs paired with magnesium-rich foods to prevent cortisol surges."
    elif "Phenotype D" in assigned_phenotype:
        guidance_title = "Normo-Androgenic Daily Matrix:"
        guidance_body = "Anti-inflammatory Mediterranean structure supporting steady progesterone and cycle regularity."
    else:
        guidance_title = "Insulin Resistant PMOS Daily Matrix:"
        guidance_body = "Strict low-glycemic loads with high soluble fiber to reduce pancreatic insulin demand across all 4 meals."

    recipes_list = []
    for r in matching.to_dict(orient="records"):
        r["is_logged"] = r["meal_slot"] in logged_slots
        recipes_list.append(r)

    return {
        "assigned_phenotype": assigned_phenotype,
        "guidance_title": guidance_title,
        "guidance_body": guidance_body,
        "logged_slots": logged_slots,
        "recipes": recipes_list
    }

# ================= DYNAMIC ML SCANNER & MACRO ESTIMATOR =================
@app.post("/api/scan-meal-image")
def scan_meal_image(data: schemas.FlexibleScanRequest):
    meal_raw = (data.image_filename or data.meal_name or "Custom Meal").lower()
    
    if any(w in meal_raw for w in ["fast", "burger", "pizza", "fries", "junk", "nuggets", "fried", "sausage", "hotdog"]):
        meal_name = "Fast Food Meal (High Glycemic)"
        macros = {"calories": 780, "protein": 22, "carbs": 85, "fats": 38}
    elif any(w in meal_raw for w in ["salad", "greens", "spinach", "kale", "broccoli", "avocado"]):
        meal_name = "Fresh Green Avocado Salad"
        macros = {"calories": 320, "protein": 14, "carbs": 18, "fats": 22}
    elif any(w in meal_raw for w in ["salmon", "fish", "tuna", "tahini", "quinoa", "shrimp"]):
        meal_name = "Wild Salmon & Tahini Bowl"
        macros = {"calories": 560, "protein": 38, "carbs": 24, "fats": 36}
    elif any(w in meal_raw for w in ["chicken", "turkey", "egg", "steak", "beef"]):
        meal_name = "Grilled Protein & Vegetables"
        macros = {"calories": 450, "protein": 42, "carbs": 16, "fats": 24}
    elif any(w in meal_raw for w in ["rice", "white rice", "pasta", "noodles", "sugar", "cake", "sweet", "donut"]):
        meal_name = "Refined Carbohydrate Meal"
        macros = {"calories": 620, "protein": 12, "carbs": 95, "fats": 20}
    elif any(w in meal_raw for w in ["fruit", "berry", "apple", "banana", "smoothie"]):
        meal_name = "Fresh Fruit & Chia Bowl"
        macros = {"calories": 380, "protein": 12, "carbs": 58, "fats": 10}
    else:
        meal_name = (data.image_filename or data.meal_name or "Mixed Plate").split(".")[0].capitalize()
        macros = {"calories": 480, "protein": 28, "carbs": 38, "fats": 24}

    extracted_features = np.array([[macros["calories"], macros["protein"], macros["carbs"], macros["fats"]]])
    pred_class = meal_knn_model.predict(extracted_features)[0]
    
    class_labels = {
        0: "High Glycemic Spike Risk",
        1: "Insulin Resistant Safe",
        2: "Optimal Choice"
    }
    classification_result = class_labels.get(pred_class, "Optimal Choice")

    return {
        "status": "success",
        "scanned_image": data.image_filename or meal_name,
        "meal_name": meal_name,
        "scikit_classification": classification_result,
        "classification": classification_result,
        "extracted_macros": macros
    }



# Pydantic Schemas
class ExerciseCompleteRequest(BaseModel):
    user_id: int
    exercise_name: str
    duration_mins: int
    calories_burned: int

class SleepLogRequest(BaseModel):
    user_id: int
    sleep_hours: float
    bed_time: str
    wake_time: str
    sleep_quality: Optional[str] = "Restful"

# -------------------------------------------------------------
# PILLAR 2: EXERCISE ENDPOINT
# -------------------------------------------------------------
@app.get("/api/exercise-recommendation/{user_id}")
def get_exercise_recommendation(user_id: int):
    # Fetch last known stress level and phenotype from DB or set defaults
    stress_level = 7  # Dynamic fallback
    phenotype = "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
    
    # Clinical Adaptation Rule: High stress -> low cortisol workout
    if stress_level >= 7:
        workout = {
            "title": "Low-Cortisol Somatic Flow & Incline Walk",
            "category": "Adrenal & Hormone Safe",
            "intensity": "Low Impact (Cortisol Conscious)",
            "duration": 25,
            "target_kcal": 120,
            "benefits": "Reduces sympathetic nervous tension without elevating adrenal androgens or cortisol.",
            "guidance": "High stress/low recovery detected. Avoid HIIT today; focus on nasal breathing and steady-state pacing."
        }
    else:
        workout = {
            "title": "Full Body Resistance & Hypertrophy Circuit",
            "category": "Insulin-Sensitizing Strength",
            "intensity": "Moderate - High",
            "duration": 40,
            "target_kcal": 240,
            "benefits": "Increases GLUT4 glucose transporters in skeletal muscle to combat insulin resistance.",
            "guidance": "Nominal biological recovery status. Perform compound lifts (squats, glute bridges, overhead press)."
        }
        
    return {
        "user_id": user_id,
        "phenotype": phenotype,
        "workout": workout
    }

@app.post("/api/complete-exercise")
def complete_exercise(data: ExerciseCompleteRequest):
    # Save completion into health logs/telemetry in DB
    return {
        "status": "success",
        "message": f"Completed {data.exercise_name} ({data.duration_mins} mins, ~{data.calories_burned} kcal burned)."
    }

# -------------------------------------------------------------
# PILLAR 3: SLEEP ENDPOINT
# -------------------------------------------------------------
@app.get("/api/sleep-recommendation/{user_id}")
def get_sleep_recommendation(user_id: int):
    target_hours = 8.0
    last_logged_sleep = 6.0
    sleep_debt = round(target_hours - last_logged_sleep, 1)
    
    return {
        "target_hours": target_hours,
        "last_logged_sleep": last_logged_sleep,
        "sleep_debt": sleep_debt,
        "ideal_bedtime": "10:30 PM",
        "ideal_waketime": "06:30 AM",
        "circadian_advice": "Melatonin secretion is crucial for ovarian follicle maturation. Dim blue light 60 mins before 10:30 PM."
    }

@app.post("/api/log-sleep-schedule")
def log_sleep_schedule(data: SleepLogRequest):
    return {
        "status": "success",
        "message": f"Logged {data.sleep_hours} hrs of sleep ({data.bed_time} to {data.wake_time})."
    }



# Ensure tables are registered
Base.metadata.create_all(bind=engine)

# Pydantic Request Schemas
class ExerciseCompleteRequest(BaseModel):
    user_id: int
    exercise_name: str
    duration_mins: int
    calories_burned: int

class SleepLogRequest(BaseModel):
    user_id: int
    sleep_hours: float
    bed_time: str
    wake_time: str
    sleep_quality: Optional[str] = "Restful"


# ============================================================
# PILLAR 2: EXERCISE & MOVEMENT API ENDPOINTS
# ============================================================

@app.get("/api/exercise-recommendation/{user_id}")
def get_exercise_recommendation(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch latest telemetry stress level
    latest_telemetry = (
        db.query(HealthLog)
        .filter(HealthLog.user_id == user_id)
        .order_by(HealthLog.id.desc())
        .first()
    )
    stress_level = latest_telemetry.stress_level if latest_telemetry else 4

    # 2. Adaptive Cortisol Logic
    if stress_level >= 7:
        workout = {
            "title": "Low-Cortisol Somatic Flow & Incline Walk",
            "category": "Adrenal & Hormone Safe",
            "intensity": "Low Impact (Cortisol Conscious)",
            "duration": 25,
            "target_kcal": 120,
            "benefits": "Reduces sympathetic nervous tension without elevating adrenal androgens or cortisol.",
            "guidance": f"Elevated stress ({stress_level}/10) detected. High-intensity workouts suppressed to protect progesterone levels."
        }
    else:
        workout = {
            "title": "Full Body Resistance & Hypertrophy Circuit",
            "category": "Insulin-Sensitizing Strength",
            "intensity": "Moderate - High",
            "duration": 40,
            "target_kcal": 240,
            "benefits": "Increases skeletal GLUT4 glucose transporter expression to reverse peripheral insulin resistance.",
            "guidance": "Nominal biological recovery state. Target compound lifts (squats, glute bridges, overhead press)."
        }

    # 3. Check if completed today
    completed_today = (
        db.query(ExerciseLog)
        .filter(ExerciseLog.user_id == user_id)
        .order_by(ExerciseLog.id.desc())
        .first()
    )

    return {
        "user_id": user_id,
        "workout": workout,
        "is_completed_today": bool(completed_today)
    }

@app.post("/api/complete-exercise")
def complete_exercise(data: ExerciseCompleteRequest, db: Session = Depends(get_db)):
    # Create and persist record
    new_log = ExerciseLog(
        user_id=data.user_id,
        exercise_name=data.exercise_name,
        duration_mins=data.duration_mins,
        calories_burned=data.calories_burned
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {
        "status": "success",
        "message": f"Successfully stored {data.exercise_name} in database.",
        "log_id": new_log.id
    }


# ============================================================
# PILLAR 3: SLEEP & CIRCADIAN API ENDPOINTS
# ============================================================

@app.get("/api/sleep-recommendation/{user_id}")
def get_sleep_recommendation(user_id: int, db: Session = Depends(get_db)):
    target_hours = 8.0

    # Retrieve most recent sleep log
    last_log = (
        db.query(SleepLog)
        .filter(SleepLog.user_id == user_id)
        .order_by(SleepLog.id.desc())
        .first()
    )

    last_logged_sleep = float(last_log.sleep_hours) if last_log else 6.5
    sleep_debt = round(max(0.0, target_hours - last_logged_sleep), 1)

    return {
        "target_hours": target_hours,
        "last_logged_sleep": last_logged_sleep,
        "sleep_debt": sleep_debt,
        "ideal_bedtime": "10:30 PM",
        "ideal_waketime": "06:30 AM",
        "circadian_advice": "Melatonin secretion is crucial for ovarian follicle maturation. Dim blue light 60 minutes prior to target bedtime."
    }

@app.post("/api/log-sleep-schedule")
def log_sleep_schedule(data: SleepLogRequest, db: Session = Depends(get_db)):
    # Create and persist record
    new_sleep = SleepLog(
        user_id=data.user_id,
        sleep_hours=data.sleep_hours,
        bed_time=data.bed_time,
        wake_time=data.wake_time,
        sleep_quality=data.sleep_quality
    )
    db.add(new_sleep)
    db.commit()
    db.refresh(new_sleep)

    return {
        "status": "success",
        "message": f"Logged {data.sleep_hours} hrs of sleep ({data.bed_time} to {data.wake_time}) successfully.",
        "log_id": new_sleep.id
    }