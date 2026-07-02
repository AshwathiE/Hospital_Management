from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from uuid import UUID
import re

class DoctorBase(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    specialty: str = Field(
        ...,
        min_length=3,
        max_length=100
    )

    email: EmailStr

    phone: str = Field(
        ...,
        min_length=10,
        max_length=10
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value.strip() == "":
            raise ValueError("Doctor name cannot be empty.")
        return value.title()

    @field_validator("specialty")
    @classmethod
    def validate_specialty(cls, value):
        if value.strip() == "":
            raise ValueError("Specialty cannot be empty.")
        return value.title()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError(
                "Phone number must be a valid 10-digit Indian mobile number."
            )
        return value


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    specialty: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=10)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError(
                "Phone number must be a valid 10-digit Indian mobile number."
            )
        return value


class Doctor(DoctorBase):
    id: UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

    class Config:
        from_attributes = True
