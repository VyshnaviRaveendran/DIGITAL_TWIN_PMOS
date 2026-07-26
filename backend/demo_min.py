from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from database import get_db, engine, Base
import models

# Create database tables automatically if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class HealthLogCreate(BaseModel):
    user_id: int
    diet_quality: float
    sleep_hours: float
    exercise_minutes: float
    medication_taken: float
    stress_level: float

# ==========================================
# ML MOCK / PREDICTION LOGIC
# ==========================================
def run_ml_model(log: HealthLogCreate) -> float:
    # Basic formula calculation representing machine learning risk scoring
    # Higher stress & low sleep/exercise increase the symptom risk coefficient
    score = (log.stress_level * 0.1) + ((12 - log.sleep_hours) * 0.05) - (log.exercise_minutes * 0.002)
    return round(max(0.0, min(1.0, score)), 2)

def generate_recommendation(risk_score: float) -> str:
    if risk_score > 0.6:
        return "High stress and low recovery metrics detected. Recommended: Immediate rest and hydration sequence."
    elif risk_score > 0.3:
        return "Moderate state vector fluctuation. Recommended: Increase physical movement and balance sleep duration."
    return "Optimal state parameters maintained. Digital Twin operating in nominal range."

# ==========================================
# API ENDPOINTS
# ==========================================
@app.post("/api/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Query models.User (NOT models.UserModel)
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    # 2. Hash password
    hashed_pwd = pwd_context.hash(user_data.password)

    # 3. Create new user record
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/api/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {"message": "Login successful", "user_id": user.id, "full_name": user.full_name}

@app.post("/api/update-twin")
def update_twin(log: HealthLogCreate, db: Session = Depends(get_db)):
    # 1. Run model prediction & generate dynamic recommendation text
    risk_score = run_ml_model(log)
    intervention = generate_recommendation(risk_score)

    # 2. Save log record into MySQL
    db_log = models.HealthLog(
        user_id=log.user_id,
        diet_score=int(log.diet_quality),
        sleep_hours=int(log.sleep_hours),
        exercise_mins=int(log.exercise_minutes),
        medication_status=int(log.medication_taken),
        stress_level=int(log.stress_level),
        risk_score=risk_score
    )
    db.add(db_log)
    db.commit()

    return {
        "symptom_risk_coefficient": risk_score,
        "dynamic_intervention": intervention
    }