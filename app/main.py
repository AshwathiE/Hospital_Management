import os
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.routers import patients, doctors, appointments
from app.crud.patient import get_patients
from app.crud.doctor import get_doctors
from app.crud.appointment import get_appointments
from app.database import SessionLocal
from app.database import Base, engine
import app.models

# Create database tables
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)
# Get the directory paths
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

# Mount static files (create dir if doesn't exist, to avoid FastAPI startup crash)
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Configure Jinja2 templates
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])

@app.get("/")
def home(request: Request):
    # Render dashboard index with live counts
    db = SessionLocal()
    try:
        patient_count = len(get_patients(db))
        doctor_count = len(get_doctors(db))
        appointment_count = len(get_appointments(db))
    finally:
        db.close()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Dashboard - Hospital Appointment System",
            "patient_count": patient_count,
            "doctor_count": doctor_count,
            "appointment_count": appointment_count
        }
    )
