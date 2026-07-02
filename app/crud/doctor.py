from sqlalchemy.orm import Session
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from uuid import UUID
from datetime import datetime


def get_doctor(db: Session, doctor_id: UUID):
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()


def get_doctors(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Doctor)
        .filter(Doctor.is_deleted == False)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_doctor(db: Session, doctor: DoctorCreate):

    # Email already exists
    existing = db.query(Doctor).filter(
        Doctor.email == doctor.email
    ).first()

    if existing:
        raise ValueError("Doctor with this email already exists.")

    db_doctor = Doctor(
        name=doctor.name,
        specialty=doctor.specialty,
        email=doctor.email,
        phone=doctor.phone,
        created_at=datetime.utcnow()
    )

    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    return db_doctor


def update_doctor(db: Session, doctor_id: UUID, doctor_update: DoctorUpdate):

    db_doctor = get_doctor(db, doctor_id)

    if not db_doctor:
        return None

    update_data = (
        doctor_update.model_dump(exclude_unset=True)
        if hasattr(doctor_update, "model_dump")
        else doctor_update.dict(exclude_unset=True)
    )

    # Duplicate email validation
    if "email" in update_data:

        existing = (
            db.query(Doctor)
            .filter(
                Doctor.email == update_data["email"],
                Doctor.id != doctor_id
            )
            .first()
        )

        if existing:
            raise ValueError("Doctor with this email already exists.")

    for key, value in update_data.items():
        setattr(db_doctor, key, value)

    db_doctor.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_doctor)

    return db_doctor


def delete_doctor(db: Session, doctor_id: UUID):

    db_doctor = get_doctor(db, doctor_id)

    if not db_doctor:
        return None

    db_doctor.is_deleted = True
    db_doctor.deleted_at = datetime.utcnow()

    db.commit()

    return db_doctor


def delete_doctor(db: Session, doctor_id: UUID):
    """Delete a doctor record."""
    db_doctor = get_doctor(db, doctor_id)

    if not db_doctor:
        return None

    db_doctor.is_deleted = True
    db_doctor.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(db_doctor)

    return db_doctor

def get_doctors(db: Session):
    return (
        db.query(Doctor)
        .filter(Doctor.is_deleted == False)
        .all()
    )
