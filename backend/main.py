from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

import models
import schemas
from database import engine, Base, get_db
from models import ExerciseLog, SleepLog, HealthLog, User, IntakeAssessment, MealLog, MedicationLog

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


# ================= PYDANTIC SCHEMAS =================
class BmiUpdateRequest(BaseModel):
    user_id: int
    height_cm: float
    weight_kg: float

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

class AddMedicationRequest(BaseModel):
    user_id: int
    med_name: str
    dosage_frequency: str
    clinical_purpose: Optional[str] = "Prescribed PMOS Protocol"
    icon: Optional[str] = "💊"


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

# Clinically mapped PMOS therapeutics database
PMOS_MED_DICTIONARY = [
    {
        "name": "Metformin XR",
        "default_dosage": "500mg | With Dinner",
        "purpose": "Reduces Hepatic Gluconeogenesis & Enhances Insulin Sensitivity",
        "icon": "💊"
    },
    {
        "name": "Myo-Inositol & D-Chiro-Inositol (40:1 ratio)",
        "default_dosage": "2000mg | Morning & Evening",
        "purpose": "Restores Oocyte Quality & Insulin Receptor Binding",
        "icon": "🧬"
    },
    {
        "name": "Spironolactone",
        "default_dosage": "50mg | Morning with Water",
        "purpose": "Androgen Receptor Blocker for Hirsutism & Hormonal Acne",
        "icon": "💊"
    },
    {
        "name": "Berberine HCl",
        "default_dosage": "500mg | 20 mins Before Meals",
        "purpose": "AMPK Activator & Glycemic Volatility Buffer",
        "icon": "🌿"
    },
    {
        "name": "Zinc Picolinate + Saw Palmetto",
        "default_dosage": "30mg | Midday with Food",
        "purpose": "5-Alpha Reductase & Anti-Androgen Follicle Support",
        "icon": "🧴"
    },
    {
        "name": "Vitamin D3 (5000 IU) + K2 (100mcg)",
        "default_dosage": "Morning with Healthy Fat",
        "purpose": "Steroidogenesis & Follicular Maturation Support",
        "icon": "☀️"
    },
    {
        "name": "Magnesium Glycinate",
        "default_dosage": "300mg | 30 mins Before Sleep",
        "purpose": "Lowers Nocturnal Cortisol & Supports GABA Receptor Calming",
        "icon": "🌙"
    },
    {
        "name": "N-Acetyl Cysteine (NAC)",
        "default_dosage": "600mg | Twice Daily Before Food",
        "purpose": "Glutathione Precursor for Ovarian Oxidative Stress Reduction",
        "icon": "🧪"
    },
    {
        "name": "Spearmint Tea Extract",
        "default_dosage": "Twice Daily (Morning & Evening)",
        "purpose": "Lowers Free Plasma Testosterone Levels",
        "icon": "🍵"
    }
]


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

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "dob": user.dob,
        "height_cm": getattr(user, "height_cm", 162.0),
        "weight_kg": getattr(user, "weight_kg", 58.0),
        "bmi": getattr(user, "bmi", 22.1),
        "bmi_category": getattr(user, "bmi_category", "Normal (Lean PMOS)"),
        "assigned_phenotype": latest_assessment.assigned_phenotype if latest_assessment else None,
        "is_calibrated": latest_assessment is not None
    }


@app.get("/api/latest-telemetry/{user_id}")
def get_latest_telemetry(user_id: int, db: Session = Depends(get_db)):
    latest = (
        db.query(HealthLog)
        .filter(HealthLog.user_id == user_id)
        .order_by(HealthLog.id.desc())
        .first()
    )
    if latest:
        return {
            "has_logged": True,
            "stress_level": latest.stress_level,
            "sleep_hours": latest.sleep_hours,
            "exercise_mins": latest.exercise_mins,
            "stability_score": int(latest.risk_score) if latest.risk_score else 67
        }
    else:
        return {
            "has_logged": False
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
def classify_phenotype(data: schemas.IntakeSchema) -> str:
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


# ================= DAILY HEALTH TELEMETRY =================
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


# ================= PILLAR 1: DIET & DYNAMIC CALORIE SPLIT =================
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


# ================= PILLAR 2: DAILY ROTATING EXERCISE & BMI =================
@app.get("/api/exercise-recommendation/{user_id}")
def get_exercise_recommendation(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    bmi = user.bmi if user and user.bmi else 22.1
    
    # 1. Fetch latest meal calories to calibrate target burn
    last_meal = (
        db.query(MealLog)
        .filter(MealLog.user_id == user_id)
        .order_by(MealLog.id.desc())
        .first()
    )
    meal_kcal = last_meal.calories if last_meal else 450

    # 2. Daily Workout Rotation Map
    day_name = datetime.now().strftime("%A")
    
    daily_routines = {
        "Monday": {
            "type": "Legs & Lower Body Workout",
            "icon": "🦵",
            "exercises": "Bodyweight Squats (3x12), Glute Bridges (3x15), Walking Lunges (3x10)",
            "base_time": 25,
            "tip": "Builds leg muscle to naturally balance blood sugar."
        },
        "Tuesday": {
            "type": "Brisk Walk / Light Cardio",
            "icon": "🏃",
            "exercises": "Steady treadmill incline walk, brisk outdoor walk, or light cycling",
            "base_time": 30,
            "tip": "Burns stored calories without making you tired or stressed."
        },
        "Wednesday": {
            "type": "Upper Body & Back Workout",
            "icon": "💪",
            "exercises": "Dumbbell/Bottle Rows (3x12), Wall Push-ups (3x10), Shoulder Press (3x12)",
            "base_time": 25,
            "tip": "Strengthens posture and boosts full-day metabolic rate."
        },
        "Thursday": {
            "type": "Core & Belly Tone Focus",
            "icon": "🧘",
            "exercises": "Plank (3x30 sec), Bird-Dog (3x10), Gentle Ab Crunches (3x15)",
            "base_time": 20,
            "tip": "Tones core muscles without spiking stress hormones."
        },
        "Friday": {
            "type": "Full Body Light Toning",
            "icon": "⚡",
            "exercises": "Step-ups (3x12), Low-Impact Marching (3x1 min), Wall sits (3x30s)",
            "base_time": 30,
            "tip": "Great full-body movement before the weekend."
        },
        "Saturday": {
            "type": "Fun Cardio / Dance Workout",
            "icon": "💃",
            "exercises": "Zumba, dancing, light jogging, or cycling outdoors",
            "base_time": 30,
            "tip": "Improves heart health and releases mood-boosting endorphins."
        },
        "Sunday": {
            "type": "Rest & Gentle Stretch",
            "icon": "🌿",
            "exercises": "Hamstring stretch, Child's pose, deep breathing walk",
            "base_time": 15,
            "tip": "Lets your muscles and hormone levels recover."
        }
    }

    routine = daily_routines.get(day_name, daily_routines["Monday"])
    
    target_burn = int(meal_kcal * 0.45)
    target_burn = max(120, min(350, target_burn))
    
    duration = routine["base_time"]
    if bmi >= 25.0:
        duration += 5
    elif bmi < 19.0:
        duration = max(15, duration - 5)

    completed_today = (
        db.query(ExerciseLog)
        .filter(ExerciseLog.user_id == user_id)
        .order_by(ExerciseLog.id.desc())
        .first()
    )

    return {
        "day": day_name,
        "workout_type": routine["type"],
        "icon": routine["icon"],
        "exercises": routine["exercises"],
        "duration_mins": duration,
        "target_burn_kcal": target_burn,
        "last_meal_name": last_meal.meal_name if last_meal else "Regular Meal",
        "last_meal_kcal": meal_kcal,
        "health_tip": routine["tip"],
        "is_completed_today": bool(completed_today)
    }


@app.post("/api/complete-exercise")
def complete_exercise(data: ExerciseCompleteRequest, db: Session = Depends(get_db)):
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
    if not q:
        return []
    matches = [m for m in PMOS_MED_DICTIONARY if q in m["name"].lower() or q in m["purpose"].lower()]
    return matches[:5]


@app.get("/api/user-medications/{user_id}")
def get_user_medications(user_id: int, db: Session = Depends(get_db)):
    meds = db.query(models.MedicationLog).filter(models.MedicationLog.user_id == user_id).all()
    
    # Auto-seed baseline PMOS stack for new users if empty
    if not meds:
        seed_meds = [
            models.MedicationLog(
                user_id=user_id,
                med_name="Myo-Inositol & D-Chiro-Inositol (40:1 ratio)",
                dosage_frequency="2000mg | Morning & Evening",
                clinical_purpose="Restores Oocyte Quality & Insulin Receptor Binding",
                icon="🧬",
                is_taken_today=True
            ),
            models.MedicationLog(
                user_id=user_id,
                med_name="Metformin XR",
                dosage_frequency="500mg | With Dinner",
                clinical_purpose="Reduces Hepatic Gluconeogenesis",
                icon="💊",
                is_taken_today=False
            ),
            models.MedicationLog(
                user_id=user_id,
                med_name="Zinc Picolinate + Saw Palmetto",
                dosage_frequency="30mg | Midday",
                clinical_purpose="5-Alpha Reductase & Anti-Androgen Support",
                icon="🧴",
                is_taken_today=True
            ),
            models.MedicationLog(
                user_id=user_id,
                med_name="Vitamin D3 (5000 IU) + K2 (100mcg)",
                dosage_frequency="Morning",
                clinical_purpose="Follicular Maturation Support",
                icon="☀️",
                is_taken_today=True
            )
        ]
        db.add_all(seed_meds)
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
def add_user_medication(data: AddMedicationRequest, db: Session = Depends(get_db)):
    clean_name = data.med_name.strip()
    
    # 1. Prevent Duplicate Medication Logging for the Same User
    existing = (
        db.query(models.MedicationLog)
        .filter(
            models.MedicationLog.user_id == data.user_id,
            func.lower(models.MedicationLog.med_name) == clean_name.lower()
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"'{clean_name}' is already active in your protocol.")

    matched = next((m for m in PMOS_MED_DICTIONARY if m["name"].lower() == clean_name.lower()), None)
    icon = matched["icon"] if matched else data.icon or "💊"
    purpose = matched["purpose"] if matched else data.clinical_purpose or "Custom Therapeutic Support"

    new_med = models.MedicationLog(
        user_id=data.user_id,
        med_name=clean_name,
        dosage_frequency=data.dosage_frequency,
        clinical_purpose=purpose,
        icon=icon,
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
        raise HTTPException(status_code=404, detail="Medication not found")
    med.is_taken_today = not med.is_taken_today
    db.commit()
    return {"status": "success", "is_taken_today": med.is_taken_today}


@app.delete("/api/delete-medication/{med_id}")
def delete_medication(med_id: int, db: Session = Depends(get_db)):
    med = db.query(models.MedicationLog).filter(models.MedicationLog.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    db.delete(med)
    db.commit()
    return {"status": "success", "message": "Medication deleted from protocol"}


@app.post("/api/reset-medications-day/{user_id}")
def reset_medications_day(user_id: int, db: Session = Depends(get_db)):
    db.query(models.MedicationLog).filter(models.MedicationLog.user_id == user_id).update({"is_taken_today": False})
    db.commit()
    return {"status": "success", "message": "Medication protocol reset for the new day!"}


class ScanPrescriptionRequest(BaseModel):
    filename: Optional[str] = ""
    extracted_text: Optional[str] = ""

@app.post("/api/scan-prescription")
def scan_prescription(payload: ScanPrescriptionRequest):
    # Combine filename and any extracted text content
    search_corpus = f"{payload.filename} {payload.extracted_text}".lower()

    # Clinical keyword matcher for PMOS medications
    if any(k in search_corpus for k in ["metformin", "glucophage", "glycomet", "met"]):
        return {
            "name": "Metformin XR",
            "dosage": "500mg | With Dinner",
            "purpose": "Reduces Hepatic Gluconeogenesis & Enhances Insulin Sensitivity",
            "icon": "💊"
        }
    elif any(k in search_corpus for k in ["inositol", "myo", "chiro", "ova", "d-chiro"]):
        return {
            "name": "Myo-Inositol & D-Chiro-Inositol (40:1 ratio)",
            "dosage": "2000mg | Morning & Evening",
            "purpose": "Restores Oocyte Quality & Insulin Receptor Binding",
            "icon": "🧬"
        }
    elif any(k in search_corpus for k in ["spirono", "aldactone", "spiro"]):
        return {
            "name": "Spironolactone",
            "dosage": "50mg | Morning with Water",
            "purpose": "Androgen Receptor Blocker for Hirsutism & Acne",
            "icon": "💊"
        }
    elif any(k in search_corpus for k in ["zinc", "saw palmetto", "palmetto"]):
        return {
            "name": "Zinc Picolinate + Saw Palmetto",
            "dosage": "30mg | Midday with Food",
            "purpose": "5-Alpha Reductase & Anti-Androgen Support",
            "icon": "🧴"
        }
    elif any(k in search_corpus for k in ["vitamin d", "vit d", "d3", "cholecalciferol"]):
        return {
            "name": "Vitamin D3 (5000 IU) + K2 (100mcg)",
            "dosage": "Morning with Food",
            "purpose": "Follicular Maturation Support",
            "icon": "☀️"
        }
    elif any(k in search_corpus for k in ["magnesium", "glycinate", "mag"]):
        return {
            "name": "Magnesium Glycinate",
            "dosage": "300mg | 30 mins Before Sleep",
            "purpose": "Lowers Nocturnal Cortisol & Supports GABA Receptor Calming",
            "icon": "🌙"
        }
    elif any(k in search_corpus for k in ["berberine", "berberin"]):
        return {
            "name": "Berberine HCl",
            "dosage": "500mg | 20 mins Before Meals",
            "purpose": "AMPK Activator & Glycemic Volatility Buffer",
            "icon": "🌿"
        }
    else:
        # Prompt selection rather than blindly defaulting to Berberine
        return {
            "name": "",
            "dosage": "",
            "purpose": "",
            "icon": "💊",
            "requires_selection": True
        }