from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas
from database import engine, Base, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Enable CORS for Live Server (127.0.0.1:5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend running successfully", "docs": "http://127.0.0.1:8000/docs"}

@app.post("/api/signup")
def signup(data: schemas.SignupSchema, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_user = db.query(models.User).filter(models.User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Map incoming data to User model attributes (full_name, email, password_hash)
    new_user = models.User(
        full_name=data.full_name,
        email=data.email,
        password_hash=data.password  # Note: Integrate passlib / bcrypt in production
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": "User registered successfully", "user_id": new_user.id}

@app.post("/api/login")
def login(credentials: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or user.password_hash != credentials.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    return {"access_token": "sample_token_xyz", "user_id": user.id}

def classify_phenotype(data: schemas.IntakeSchema) -> str:
    # Diagnostic Phenotype Logic
    if data.symp_periods and (data.symp_hair or data.symp_acne):
        return "Phenotype B: Ovulatory-Hyperandrogenic PMOS"
    elif data.usg_result == "cysts" and data.symp_periods:
        return "Phenotype A: Classic PMOS"
    elif data.symp_weight or data.symp_stress:
        return "Phenotype C: Metabolic-Adrenal PMOS"
    return "Phenotype D: Normo-Androgenic PMOS"

@app.post("/api/submit-intake")
def submit_intake(data: schemas.IntakeSchema, db: Session = Depends(get_db)):
    # Verify User Exists
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {data.user_id} not found in database.")

    assigned_pheno = classify_phenotype(data)

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

    return {
        "status": "success",
        "message": "Intake assessment recorded",
        "assigned_phenotype": assigned_pheno,
        "assessment_id": new_assessment.id
    }