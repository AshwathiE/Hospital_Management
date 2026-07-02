from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import date
from uuid import UUID
import re


class PatientBase(BaseModel):
    name: str = Field(
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

    date_of_birth: date

    # Name Validation
    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value.strip() == "":
            raise ValueError("Patient name cannot be empty.")
        return value.title()

    # Phone Validation
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if not re.fullmatch(r"[6-9]\d{9}", value):
            raise ValueError(
                "Phone number must be a valid 10-digit Indian mobile number."
            )
        return value

    # Date of Birth Validation
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        if value > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )
        return value


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100
    )

    email: Optional[EmailStr] = None

    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=10
    )

    date_of_birth: Optional[date] = None

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

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value):
        if value is not None and value > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )
        return value


class Patient(PatientBase):
    id: UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

    class Config:
        from_attributes = True
