from pydantic import BaseModel, EmailStr
from typing import Optional, List

# ================= AUTHENTICATION SCHEMAS =================
class SignupSchema(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str


# ================= INTAKE ASSESSMENT SCHEMA =================
class IntakeSchema(BaseModel):
    user_id: int
    symp_periods: bool = False
    symp_hair: bool = False
    symp_thinning: bool = False
    symp_acne: bool = False
    symp_stress: bool = False
    symp_weight: bool = False
    usg_result: Optional[str] = "normal"
    prior_diagnosis: Optional[str] = "none"

    class Config:
        from_attributes = True


# ================= USER PROFILE & ANTHROPOMETRY SCHEMAS =================
class BmiUpdateRequest(BaseModel):
    user_id: int
    height_cm: float
    weight_kg: float

class ProfileUpdateRequest(BaseModel):
    user_id: int
    full_name: str
    dob: Optional[str] = None
    password: Optional[str] = None


# ================= PILLAR 1: NUTRITION & MEAL SCHEMAS =================
class MealLogCreate(BaseModel):
    user_id: int
    meal_name: str
    calories: int
    protein: float = 0.0
    carbs: float = 0.0
    fats: float = 0.0
    meal_type: Optional[str] = "Lunch"
    glycemic_risk: Optional[str] = "Optimal Choice"

    class Config:
        from_attributes = True

class FlexibleScanRequest(BaseModel):
    user_id: Optional[int] = 1
    image_filename: Optional[str] = None
    meal_name: Optional[str] = None
    meal_description: Optional[str] = "Mixed Meal"


# ================= PILLAR 2: MOVEMENT & EXERCISE SCHEMAS =================
class ExerciseCompleteRequest(BaseModel):
    user_id: int
    exercise_name: str
    duration_mins: int
    calories_burned: int


# ================= PILLAR 3: SLEEP SCHEMAS =================
class SleepLogRequest(BaseModel):
    user_id: int
    sleep_hours: float
    bed_time: str
    wake_time: str
    sleep_quality: Optional[str] = "Restful"


# ================= PILLAR 4: MEDICATION & SUPPLEMENT SCHEMAS =================
class AddMedicationRequest(BaseModel):
    user_id: int
    med_name: str
    dosage_frequency: str
    clinical_purpose: Optional[str] = "Prescribed PMOS Protocol"
    icon: Optional[str] = "💊"

class ScanPrescriptionRequest(BaseModel):
    filename: Optional[str] = ""
    extracted_text: Optional[str] = ""


# ================= PILLAR 5: STRESS & MENTAL WELLNESS SCHEMAS =================
class StressResetLogRequest(BaseModel):
    user_id: int
    technique: str
    duration_mins: int
    symptoms: List[str] = []