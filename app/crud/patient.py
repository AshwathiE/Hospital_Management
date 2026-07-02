# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from datetime import datetime

def get_patient(db: Session, patient_id: UUID):
    """Retrieve a single patient by ID."""
    return db.query(Patient).filter(Patient.id == patient_id).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve a list of patients."""
    return db.query(Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: PatientCreate):
    """Create a new patient record."""
    db_patient = Patient(
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        date_of_birth=patient.date_of_birth
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def update_patient(db: Session, patient_id: UUID, patient_update: PatientUpdate):
    """Update patient details."""
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
    # Support both dictionary forms depending on Pydantic v1 vs v2
    update_data = patient_update.model_dump(exclude_unset=True) if hasattr(patient_update, "model_dump") else patient_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)

    db.commit()
    db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: UUID):
    """Delete a patient record."""
    db_patient = get_patient(db, patient_id)
    if not db_patient:
        return None
    db_patient.is_deleted = True
    db_patient.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patients(db: Session):
    return (
        db.query(Patient)
        .filter(Patient.is_deleted == False)
        .all()
    )