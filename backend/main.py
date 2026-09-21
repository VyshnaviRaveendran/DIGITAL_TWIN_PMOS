import os
import re
from datetime import datetime, date, time
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, Base, get_db
from models import ExerciseLog, SleepLog, HealthLog, User, IntakeAssessment, MealLog, MedicationLog

from schemas import (
    SignupSchema, LoginSchema, IntakeSchema, BmiUpdateRequest, 
    MealLogCreate, FlexibleScanRequest, ExerciseCompleteRequest, 
    SleepLogRequest, AddMedicationRequest, ScanPrescriptionRequest, 
    StressResetLogRequest
)

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Digital Twin PMOS API")

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DATASET-DRIVEN CLINICAL KNOWLEDGE BASE =================
DATASET_PATH = os.path.join(os.path.dirname(__file__), "pmos_medicines.csv")

def load_medicine_dataset():
    if os.path.exists(DATASET_PATH):
        try:
            return pd.read_csv(DATASET_PATH).fillna("")
        except Exception as e:
            print(f"Error loading pmos_medicines.csv: {e}")
    return pd.DataFrame(columns=[
        "category", "generic_name", "brand_names", "default_dosage", "clinical_purpose", "icon"
    ])

MED_DF = load_medicine_dataset()

def build_search_corpus(df: pd.DataFrame):
    corpus = []
    for _, row in df.iterrows():
        gen_name = str(row.get("generic_name", "")).strip()
        if not gen_name:
            continue

        corpus.append({
            "term": gen_name.lower(),
            "display_name": gen_name,
            "data": row.to_dict(),
            "is_brand": False
        })

        brands = str(row.get("brand_names", ""))
        if brands:
            for brand in brands.split(";"):
                clean_brand = brand.strip()
                if clean_brand:
                    corpus.append({
                        "term": clean_brand.lower(),
                        "display_name": f"{clean_brand} ({gen_name})",
                        "data": row.to_dict(),
                        "is_brand": True
                    })
    return corpus

SEARCH_CORPUS = build_search_corpus(MED_DF)


# ================= ML MODEL INITIALIZATION =================
X_train = np.array([
    [520, 36, 42, 28],  # Underweight / Lean Optimal
    [250, 10, 55, 5],   # High Glycemic Spike Risk
    [450, 32, 15, 30],  # Insulin Resistant Safe
    [180, 5, 35, 2]     # Unbalanced Spike Risk
])
y_train = np.array([2, 0, 1, 0])

meal_knn_model = KNeighborsClassifier(n_neighbors=1)
meal_knn_model.fit(X_train, y_train)


# ================= 4-MEAL PHENOTYPE RECIPE DATABASE =================
RECIPES_DF = pd.DataFrame([
    {"meal_slot": "Breakfast", "name": "Avocado & Pasture-Raised Eggs on Seeded Sourdough", "kcal": 460, "protein": 24, "carbs": 28, "fats": 28, "gi": 35, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Choline and mono-unsaturated fats to support hormone steroidogenesis."},
    {"meal_slot": "Lunch", "name": "Wild Alaskan Salmon & Quinoa Tahini Bowl", "kcal": 580, "protein": 40, "carbs": 32, "fats": 34, "gi": 28, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "High Omega-3s to downregulate follicular inflammation."},
    {"meal_slot": "Dinner", "name": "Slow-Roasted Grass-Fed Beef with Sweet Potato Mash", "kcal": 550, "protein": 42, "carbs": 38, "fats": 26, "gi": 40, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Bioavailable zinc and iron supporting ovarian follicle maturation."},
    {"meal_slot": "Snack", "name": "Raw Macadamia, Walnuts & Pumpkin Seed Cluster", "kcal": 349, "protein": 12, "carbs": 10, "fats": 30, "gi": 15, "phenotype": "Phenotype B: Ovulatory-Hyperandrogenic PMOS", "desc": "Anti-androgenic magnesium & healthy lipid density."},

    {"meal_slot": "Breakfast", "name": "Chia Seed & Flax Pudding with Collagen & Blueberries", "kcal": 380, "protein": 28, "carbs": 16, "fats": 22, "gi": 18, "phenotype": "Phenotype A: Classic PMOS", "desc": "High viscous fiber to blunt morning cortisol & insulin release."},
    {"meal_slot": "Lunch", "name": "Grilled Herb Chicken Breast & Cauliflower Rice Pilaf", "kcal": 490, "protein": 48, "carbs": 18, "fats": 24, "gi": 15, "phenotype": "Phenotype A: Classic PMOS", "desc": "Ultra low-glycemic load maintaining baseline insulin sensitivity."},
    {"meal_slot": "Dinner", "name": "Pan-Seared Halibut with Sautéed Asparagus & Garlic Kale", "kcal": 450, "protein": 44, "carbs": 14, "fats": 24, "gi": 12, "phenotype": "Phenotype A: Classic PMOS", "desc": "Sulforaphane & glutathione to promote estrogen liver conjugation."},
    {"meal_slot": "Snack", "name": "Organic Celery Sticks with Salted Almond Butter", "kcal": 219, "protein": 8, "carbs": 8, "fats": 18, "gi": 10, "phenotype": "Phenotype A: Classic PMOS", "desc": "Electrolytes and protein buffer preventing mid-day sugar cravings."},

    {"meal_slot": "Breakfast", "name": "Poached Eggs, Sautéed Spinach & Roasted Pumpkin Slices", "kcal": 410, "protein": 26, "carbs": 24, "fats": 24, "gi": 30, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Magnesium-dense start preventing adrenal cortisol surges."},
    {"meal_slot": "Lunch", "name": "Free-Range Turkey Breast with Steamed Broccoli & Tahini", "kcal": 510, "protein": 46, "carbs": 20, "fats": 28, "gi": 20, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Tryptophan-rich protein sustaining steady adrenal neurotransmitters."},
    {"meal_slot": "Dinner", "name": "Braised Cod Fillet with Stewed Zucchini & Olive Oil", "kcal": 480, "protein": 38, "carbs": 18, "fats": 28, "gi": 22, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Easily digestible evening protein supporting nocturnal growth hormone."},
    {"meal_slot": "Snack", "name": "Spiced Golden Turmeric Milk with Coconut Cream & Chia", "kcal": 239, "protein": 6, "carbs": 12, "fats": 18, "gi": 15, "phenotype": "Phenotype C: Metabolic-Adrenal PMOS", "desc": "Curcumin anti-inflammatory tonic for evening vagus downregulation."},

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
def signup(data: SignupSchema, db: Session = Depends(get_db)):
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
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or user.password_hash != credentials.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    assessment = (
        db.query(models.IntakeAssessment)
        .filter(models.IntakeAssessment.user_id == user.id)
        .first()
    )
    has_assessed = assessment is not None

    return {
        "access_token": "sample_token_xyz",
        "user_id": user.id,
        "full_name": user.full_name,
        "has_assessed": has_assessed
    }


# ================= USER PROFILE & TELEMETRY =================
@app.get("/api/user-profile/{user_id}")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    latest_assessment = (
        db.query(models.IntakeAssessment)
        .filter(models.IntakeAssessment.user_id == user_id)
        .order_by(models.IntakeAssessment.id.desc())
        .first()
    )

    pheno = latest_assessment.assigned_phenotype if latest_assessment else None

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "dob": user.dob,
        "height_cm": getattr(user, "height_cm", 162.0),
        "weight_kg": getattr(user, "weight_kg", 58.0),
        "bmi": getattr(user, "bmi", 22.1),
        "bmi_category": getattr(user, "bmi_category", "Normal (Lean PMOS)"),
        "assigned_phenotype": pheno,
        "is_calibrated": pheno is not None
    }


@app.get("/api/latest-telemetry/{user_id}")
def get_latest_telemetry(user_id: int, db: Session = Depends(get_db)):
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
            stability_score = 99
        else:
            stability_score = max(15, min(99, int(base_stability - surplus_penalty - glycemic_penalty)))

        return {
            "has_logged": total_calories > 0,
            "total_calories": total_calories,
            "calories_burned": total_burned,
            "net_calories": net_calories,
            "calorie_surplus": calorie_surplus,
            "stability_score": stability_score,
            "is_high_risk": calorie_surplus > 300 or stability_score < 65
        }
    except Exception as e:
        print(f"Error in telemetry calculation: {e}")
        return {
            "has_logged": False,
            "total_calories": 0,
            "calories_burned": 0,
            "net_calories": 0,
            "calorie_surplus": 0.0,
            "stability_score": 99,
            "is_high_risk": False
        }


# ================= ANTHROPOMETRY / BMI ENDPOINT =================
@app.post("/api/update-bmi")
def update_user_bmi(data: BmiUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    height_m = data.height_cm / 100.0
    bmi_val = round(data.weight_kg / (height_m ** 2), 1)
    
    if bmi_val < 18.5:
        category = "Underweight (Lean PMOS)"
    elif 18.5 <= bmi_val < 24.9:
        category = "Normal (Lean / Metabolic Sensitive)"
    elif 25.0 <= bmi_val < 29.9:
        category = "Overweight (Insulin Resistant Risk)"
    else:
        category = "Obese (High Metabolic Strain)"
        
    user.height_cm = data.height_cm
    user.weight_kg = data.weight_kg
    user.bmi = bmi_val
    user.bmi_category = category
    
    db.commit()
    db.refresh(user)
    
    return {
        "status": "success",
        "bmi": bmi_val,
        "bmi_category": category,
        "height_cm": data.height_cm,
        "weight_kg": data.weight_kg
    }


# ================= INTAKE & ROTTERDAM PHENOTYPE EVALUATION =================
def classify_phenotype(data: IntakeSchema) -> str:
    has_hyperandrogenism = data.symp_hair or data.symp_thinning or data.symp_acne
    has_ovulatory_dysfunction = data.symp_periods
    has_pcom_ultrasound = str(data.usg_result).lower() in ["cysts", "polycystic", "pco"]

    if has_hyperandrogenism and has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype A: Classic PMOS"
    elif has_hyperandrogenism and has_ovulatory_dysfunction and not has_pcom_ultrasound:
        return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
    elif has_hyperandrogenism and not has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype C: Metabolic-Adrenal PMOS"
    elif not has_hyperandrogenism and has_ovulatory_dysfunction and has_pcom_ultrasound:
        return "Phenotype D: Normo-Androgenic PMOS"
    elif data.symp_weight or data.symp_stress:
        return "Phenotype C: Metabolic-Adrenal PMOS"
    
    return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"


@app.post("/api/submit-intake")
def submit_intake(data: IntakeSchema, db: Session = Depends(get_db)):
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

    return {
        "status": "success", 
        "assigned_phenotype": assigned_pheno, 
        "assessment_id": assessment_id
    }


# ================= PILLAR 1: DIET & MEAL LOGS =================
@app.post("/api/log-meal")
def log_meal(data: MealLogCreate, db: Session = Depends(get_db)):
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


@app.get("/api/diet-recommendations/{user_id}")
def get_diet_recommendations(user_id: int, db: Session = Depends(get_db)):
    assessment = (
        db.query(models.IntakeAssessment)
        .filter(models.IntakeAssessment.user_id == user_id)
        .order_by(models.IntakeAssessment.id.desc())
        .first()
    )

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


@app.post("/api/scan-meal-image")
def scan_meal_image(payload: dict):
    image_filename = payload.get("image_filename", "").lower()
    meal_name = payload.get("meal_name", "").lower()

    if any(k in image_filename or k in meal_name for k in ["fast", "burger", "pizza", "fries", "noodle", "fried", "sugar", "cake", "crisp"]):
        extracted_macros = {
            "calories": 780,
            "protein": 22,
            "carbs": 85,
            "fats": 38,
            "gi": 75
        }
        classification = "High Glycemic Spike Risk"
        display_name = "Fast Food Meal (High Glycemic)"
    else:
        extracted_macros = {
            "calories": 520,
            "protein": 36,
            "carbs": 42,
            "fats": 28,
            "gi": 35
        }
        classification = "Optimal Choice"
        display_name = payload.get("meal_name", "Balanced Whole Meal")

    return {
        "status": "success",
        "meal_name": display_name,
        "extracted_macros": extracted_macros,
        "classification": classification
    }


# ================= PILLAR 2: EXERCISE & WORKOUT ENDPOINTS =================
@app.get("/api/exercise-recommendation/{user_id}")
def get_exercise_recommendation(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    bmi = user.bmi if user and user.bmi else 22.1
    
    user_meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
    
    total_kcal = sum(m.calories for m in user_meals) if user_meals else 0
    highest_meal = max(user_meals, key=lambda m: m.calories) if user_meals else None
    matched_meal_name = highest_meal.meal_name if highest_meal else "Regular Meal"
    
    target_kcal = 1939.0
    surplus_kcal = max(0.0, total_kcal - target_kcal)

    if surplus_kcal > 0:
        target_burn = int(surplus_kcal)
    else:
        target_burn = 250

    day_name = datetime.now().strftime("%A")
    daily_routines = {
        "Monday": {"type": "Legs & Lower Body Workout", "icon": "🦵", "exercises": "Squats, Glute Bridges, Lunges", "base_time": 25},
        "Tuesday": {"type": "Brisk Walk / Light Cardio", "icon": "🏃", "exercises": "Steady treadmill walk or light cycling", "base_time": 30},
        "Wednesday": {"type": "Upper Body & Back Workout", "icon": "💪", "exercises": "Dumbbell Rows, Wall Push-ups", "base_time": 25},
        "Thursday": {"type": "Core & Belly Tone Focus", "icon": "🧘", "exercises": "Plank, Bird-Dog, Ab Crunches", "base_time": 20},
        "Friday": {"type": "Full Body Light Toning", "icon": "⚡", "exercises": "Step-ups, Low-Impact Marching", "base_time": 30},
        "Saturday": {"type": "Fun Cardio / Dance Workout", "icon": "💃", "exercises": "Zumba or outdoor cycling", "base_time": 30},
        "Sunday": {"type": "Rest & Gentle Stretch", "icon": "🌿", "exercises": "Hamstring stretch, Child's pose", "base_time": 15}
    }

    routine = daily_routines.get(day_name, daily_routines["Tuesday"])
    
    duration = routine["base_time"]
    if surplus_kcal > 400:
        duration += int(surplus_kcal / 25)
    elif surplus_kcal > 200:
        duration += 10

    completed_today = db.query(models.ExerciseLog).filter(
        models.ExerciseLog.user_id == user_id
    ).order_by(models.ExerciseLog.id.desc()).first()

    return {
        "day": day_name,
        "workout_type": routine["type"],
        "icon": routine["icon"],
        "exercises": routine["exercises"],
        "duration_mins": duration,
        "target_burn_kcal": target_burn,
        "last_meal_name": matched_meal_name,
        "total_logged_kcal": total_kcal,
        "surplus_kcal": surplus_kcal,
        "is_completed_today": completed_today is not None
    }


@app.post("/api/complete-exercise")
def complete_exercise(data: ExerciseCompleteRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_exercise = models.ExerciseLog(
        user_id=data.user_id,
        exercise_name=data.exercise_name,
        duration_mins=data.duration_mins,
        calories_burned=data.calories_burned
    )
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)

    return {
        "status": "success",
        "message": f"Successfully logged {data.exercise_name} ({data.calories_burned} kcal burned)",
        "log_id": new_exercise.id
    }


@app.post("/api/reset-exercise/{user_id}")
def reset_exercise_logs(user_id: int, db: Session = Depends(get_db)):
    try:
        deleted_count = db.query(models.ExerciseLog).filter(
            models.ExerciseLog.user_id == user_id
        ).delete(synchronize_session=False)

        db.commit()

        return {
            "status": "success",
            "message": "Exercise logs reset",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ================= PILLAR 3: SLEEP & CIRCADIAN ENDPOINTS =================
@app.get("/api/sleep-recommendation/{user_id}")
def get_sleep_recommendation(user_id: int, db: Session = Depends(get_db)):
    target_hours = 8.0

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


# ================= PILLAR 4: MEDICATION & SUPPLEMENT API =================
@app.get("/api/medication-suggestions")
def get_medication_suggestions(query: str = ""):
    q = query.lower().strip()
    if not q or len(q) < 2:
        return []

    results = []
    seen_generics = set()

    for item in SEARCH_CORPUS:
        if q in item["term"]:
            generic = item["data"]["generic_name"]
            if generic not in seen_generics:
                seen_generics.add(generic)
                results.append({
                    "name": item["display_name"],
                    "default_dosage": item["data"]["default_dosage"],
                    "purpose": item["data"]["clinical_purpose"],
                    "category": item["data"]["category"],
                    "icon": item["data"]["icon"],
                    "score": 100
                })

    return results[:6]


@app.post("/api/scan-prescription")
def scan_prescription(payload: ScanPrescriptionRequest):
    combined_text = f"{payload.filename} {payload.extracted_text}".lower()
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', combined_text)

    best_match = None

    for item in SEARCH_CORPUS:
        term = item["term"]
        if len(term) < 3:
            continue

        if term in clean_text:
            best_match = item
            break

    if best_match:
        data = best_match["data"]
        dosage = data["default_dosage"]

        if any(w in clean_text for w in ["0 0 1", "0-0-1", "night", "9 pm", "bedtime"]):
            if "night" not in dosage.lower():
                dosage = f"{dosage.split('|')[0].strip()} | Night (After Meal)"
        elif any(w in clean_text for w in ["1 0 0", "1-0-0", "morning"]):
            if "morning" not in dosage.lower():
                dosage = f"{dosage.split('|')[0].strip()} | Morning (After Meal)"

        return {
            "name": f"{best_match['display_name']}",
            "dosage": dosage,
            "purpose": data["clinical_purpose"],
            "category": data["category"],
            "icon": data["icon"],
            "confidence": 0.95,
            "not_found": False
        }

    return {
        "name": "",
        "dosage": "",
        "purpose": "",
        "icon": "💊",
        "confidence": 0.0,
        "not_found": True
    }


@app.get("/api/user-medications/{user_id}")
def get_user_medications(user_id: int, db: Session = Depends(get_db)):
    meds = db.query(models.MedicationLog).filter(models.MedicationLog.user_id == user_id).all()
    
    if not meds:
        seed_defaults = [
            ("Myo-Inositol & D-Chiro-Inositol", "2000mg | Morning & Evening", "Restores oocyte quality & insulin receptor binding", "🧬", True),
            ("Metformin XR", "500mg | With Dinner", "Reduces hepatic gluconeogenesis", "💊", False),
            ("Vitamin D3 (5000 IU) + K2", "60000 IU weekly or 2000 IU daily with meal", "Follicular maturation support", "☀️", True)
        ]
        for name, dose, purp, ico, taken in seed_defaults:
            db.add(models.MedicationLog(
                user_id=user_id,
                med_name=name,
                dosage_frequency=dose,
                clinical_purpose=purp,
                icon=ico,
                is_taken_today=taken
            ))
        db.commit()
        meds = db.query(models.MedicationLog).filter(models.MedicationLog.user_id == user_id).all()

    return [
        {
            "id": m.id,
            "name": m.med_name,
            "dosage_frequency": m.dosage_frequency,
            "clinical_purpose": m.clinical_purpose,
            "icon": m.icon,
            "is_taken_today": m.is_taken_today
        }
        for m in meds
    ]


@app.post("/api/add-medication")
def add_medication(data: AddMedicationRequest, db: Session = Depends(get_db)):
    new_med = models.MedicationLog(
        user_id=data.user_id,
        med_name=data.med_name,
        dosage_frequency=data.dosage_frequency,
        clinical_purpose=data.clinical_purpose,
        icon=data.icon,
        is_taken_today=False
    )
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    return {"status": "success", "message": "Medication added", "med_id": new_med.id}


@app.post("/api/toggle-medication-dose/{med_id}")
def toggle_medication_dose(med_id: int, db: Session = Depends(get_db)):
    med = db.query(models.MedicationLog).filter(models.MedicationLog.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication log not found")

    med.is_taken_today = not med.is_taken_today
    db.commit()
    db.refresh(med)
    return {"status": "success", "is_taken_today": med.is_taken_today}

@app.delete("/api/delete-medication/{med_id}")
def delete_medication(med_id: int, db: Session = Depends(get_db)):
    med = db.query(models.MedicationLog).filter(models.MedicationLog.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    db.delete(med)
    db.commit()
    return {"status": "success", "message": f"Medication {med_id} deleted successfully"}

# ================= PILLAR 5: STRESS & MENTAL WELLNESS ENDPOINTS =================
@app.get("/api/stress-recommendation/{user_id}")
def get_stress_recommendation(user_id: int, db: Session = Depends(get_db)):
    latest_reset = (
        db.query(models.StressResetLog)
        .filter(models.StressResetLog.user_id == user_id)
        .order_by(models.StressResetLog.id.desc())
        .first()
    )
    
    current_stress = 4 if latest_reset else 5

    if current_stress >= 7:
        recommended_technique = "4-7-8 Parasympathetic Downregulation"
        duration = 10
        guidance = "High adrenal stress detected. Focus on extended exhalations to activate the vagus nerve and reduce cortisol."
    elif current_stress >= 4:
        recommended_technique = "Box Breathing (4-4-4-4)"
        duration = 5
        guidance = "Moderate stress levels. Use equalized breathing counts to balance autonomic nervous system activity."
    else:
        recommended_technique = "Mindful Diaphragmatic Awareness"
        duration = 5
        guidance = "Optimal baseline state. Maintain calm focus with gentle belly breathing."

    recent_resets = (
        db.query(models.StressResetLog)
        .filter(models.StressResetLog.user_id == user_id)
        .order_by(models.StressResetLog.id.desc())
        .limit(5)
        .all()
    )

    return {
        "current_stress_level": current_stress,
        "recommended_technique": recommended_technique,
        "recommended_duration_mins": duration,
        "clinical_guidance": guidance,
        "total_resets_logged": len(recent_resets)
    }


@app.post("/api/log-stress-reset")
def log_stress_reset(data: StressResetLogRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    symptoms_str = ",".join(data.symptoms) if data.symptoms else ""

    new_log = models.StressResetLog(
        user_id=data.user_id,
        technique=data.technique,
        duration_mins=data.duration_mins,
        symptoms=symptoms_str
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {
        "status": "success",
        "message": f"Logged {data.duration_mins} mins of {data.technique}.",
        "log_id": new_log.id
    }


@app.get("/api/user-stress-logs/{user_id}")
def get_user_stress_logs(user_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(models.StressResetLog)
        .filter(models.StressResetLog.user_id == user_id)
        .order_by(models.StressResetLog.id.desc())
        .all()
    )

    return [
        {
            "id": log.id,
            "technique": log.technique,
            "duration_mins": log.duration_mins,
            "symptoms": log.symptoms.split(",") if log.symptoms else [],
            "date": log.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for log in logs
    ]


@app.post("/api/update-profile")
def update_profile(data: schemas.ProfileUpdateRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.full_name:
        user.full_name = data.full_name

    if data.dob:
        user.dob = data.dob

    if data.password and data.password.strip():
        user.password_hash = data.password.strip()

    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": "Profile updated successfully",
        "full_name": user.full_name,
        "dob": user.dob
    }