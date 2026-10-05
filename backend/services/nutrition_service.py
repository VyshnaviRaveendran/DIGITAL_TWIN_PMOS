# backend/services/nutrition_service.py
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sqlalchemy.orm import Session
import models

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

def evaluate_meal_macros(image_filename: str = "", meal_name: str = "") -> dict:
    image_filename_lower = (image_filename or "").lower()
    meal_name_lower = (meal_name or "").lower()
    trigger_words = ["fast", "burger", "pizza", "fries", "noodle", "fried", "sugar", "cake", "crisp", "soda"]

    if any(k in image_filename_lower or k in meal_name_lower for k in trigger_words):
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
        display_name = meal_name if meal_name else "Balanced Whole Meal"

    return {
        "status": "success",
        "meal_name": display_name,
        "extracted_macros": extracted_macros,
        "classification": classification
    }

def calculate_diet_summary(user_id: int, db: Session) -> dict:
    user_meals = db.query(models.MealLog).filter(models.MealLog.user_id == user_id).all()
    logged_slots = [m.meal_type for m in user_meals]
    total_logged = sum(m.calories for m in user_meals)
    tdee_target = 1939.0
    remaining_balance = float(max(0.0, tdee_target - total_logged))

    all_slots = ["Breakfast", "Lunch", "Dinner", "Snack"]
    unlogged_slots = [slot for slot in all_slots if slot not in logged_slots]
    day_completed = len(unlogged_slots) == 0 or len(user_meals) >= 4
    splits = {}

    if not day_completed and remaining_balance > 0:
        total_remaining_weight = sum(BASE_WEIGHTS[slot] for slot in unlogged_slots)
        for slot in unlogged_slots:
            slot_ratio = BASE_WEIGHTS[slot] / total_remaining_weight if total_remaining_weight > 0 else 0.25
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

def get_diet_recommendations_for_user(user_id: int, db: Session) -> dict:
    assessment = (
        db.query(models.IntakeAssessment)
        .filter(models.IntakeAssessment.user_id == user_id)
        .order_by(models.IntakeAssessment.id.desc())
        .first()
    )
    if not assessment:
        return {
            "assigned_phenotype": "Pending Assessment",
            "guidance_title": "Assessment Needed:",
            "guidance_body": "Complete your health assessment in the main dashboard to calculate personalized meal recommendations.",
            "logged_slots": [],
            "recipes": []
        }

    assigned_phenotype = assessment.assigned_phenotype or "Phenotype A: Classic PMOS"
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
