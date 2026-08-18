from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


# ================= USER ACCOUNT & SPECIFICATIONS =================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    dob = Column(String(20), nullable=True)

    # Anthropometric / BMI Baseline Fields
    height_cm = Column(Float, default=162.0)
    weight_kg = Column(Float, default=58.0)
    bmi = Column(Float, default=22.1)
    bmi_category = Column(String(50), default="Normal (Lean PMOS)")

    # Relationships
    health_logs = relationship("HealthLog", back_populates="user", cascade="all, delete-orphan")
    intake_assessments = relationship("IntakeAssessment", back_populates="user", cascade="all, delete-orphan")
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    exercise_logs = relationship("ExerciseLog", back_populates="user", cascade="all, delete-orphan")
    sleep_logs = relationship("SleepLog", back_populates="user", cascade="all, delete-orphan")


# ================= INTAKE ASSESSMENT TABLE =================
class IntakeAssessment(Base):
    __tablename__ = "intake_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    symp_periods = Column(Boolean, default=False)
    symp_hair = Column(Boolean, default=False)
    symp_thinning = Column(Boolean, default=False)
    symp_acne = Column(Boolean, default=False)
    symp_stress = Column(Boolean, default=False)
    symp_weight = Column(Boolean, default=False)

    usg_result = Column(String(50))
    prior_diagnosis = Column(String(50))
    assigned_phenotype = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="intake_assessments")


# ================= HEALTH TELEMETRY TABLE =================
class HealthLog(Base):
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    diet_score = Column(Integer, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    exercise_mins = Column(Integer, nullable=False)
    medication_status = Column(Integer, nullable=False)
    stress_level = Column(Integer, nullable=False)
    risk_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_logs")


# ================= PILLAR 1: DIET & MEAL LOGS =================
class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    meal_name = Column(String(150), nullable=False)
    meal_type = Column(String(50), default="Custom")  # Breakfast, Lunch, Dinner, Snack
    calories = Column(Integer, nullable=False)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    glycemic_risk = Column(String(100), default="Optimal Choice")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="meal_logs")


# ================= PILLAR 2: EXERCISE LOGS =================
class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    exercise_name = Column(String(150), nullable=False)
    duration_mins = Column(Integer, nullable=False)
    calories_burned = Column(Integer, nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="exercise_logs")


# ================= PILLAR 3: SLEEP LOGS =================
class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    sleep_hours = Column(Float, nullable=False)
    bed_time = Column(String(10), nullable=False)
    wake_time = Column(String(10), nullable=False)
    sleep_quality = Column(String(50), default="Restful")
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sleep_logs")