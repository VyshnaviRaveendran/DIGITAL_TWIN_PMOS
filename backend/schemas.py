from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupSchema(BaseModel):
    full_name: str
    email: str
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

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


class HealthLogSchema(BaseModel):
    user_id: int
    stress_level: int
    sleep_hours: float
    exercise_mins: int
    diet_score: int
    medication_status: int

    class Config:
        from_attributes = True