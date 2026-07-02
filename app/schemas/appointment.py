from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID


class AppointmentBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID

    appointment_date: datetime = Field(
        ...,
        description="Appointment date and time"
    )

    status: str = Field(
        default="Scheduled",
        min_length=3,
        max_length=20
    )

    notes: Optional[str] = Field(
        default=None,
        max_length=500
    )

    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, value):
        if value < datetime.now():
            raise ValueError("Appointment date cannot be in the past.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed_status = [
            "Scheduled",
            "Completed",
            "Cancelled"
        ]

        if value not in allowed_status:
            raise ValueError(
                f"Status must be one of {allowed_status}"
            )

        return value

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value):
        if value is None:
            return None

        value = value.strip()

        if value == "":
            return None

        if len(value) > 500:
            raise ValueError("Notes cannot exceed 500 characters.")

        return value


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    patient_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None
    appointment_date: Optional[datetime] = None

    status: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=20
    )

    notes: Optional[str] = Field(
        default=None,
        max_length=500
    )

    @field_validator("appointment_date")
    @classmethod
    def validate_appointment_date(cls, value):
        if value is not None and value < datetime.now():
            raise ValueError("Appointment date cannot be in the past.")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value is None:
            return None

        allowed_status = [
            "Scheduled",
            "Completed",
            "Cancelled"
        ]

        if value not in allowed_status:
            raise ValueError(
                f"Status must be one of {allowed_status}"
            )

        return value

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value):
        if value is None:
            return None

        value = value.strip()

        if value == "":
            return None

        if len(value) > 500:
            raise ValueError("Notes cannot exceed 500 characters.")

        return value


class Appointment(AppointmentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
