from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
import os
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import Optional

from app.database import get_db
from app.crud.appointment import (
    get_appointments,
    get_appointment,
    create_appointment,
    update_appointment,
    delete_appointment,
    find_nearest_available_slot,
    generate_ai_suggestion
)
from app.crud.patient import get_patients
from app.crud.doctor import get_doctors
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)


# ---------------- LIST ----------------
@router.get("/", response_class=HTMLResponse)
def list_appointments(request: Request, db: Session = Depends(get_db)):

    appointments = get_appointments(db)

    return templates.TemplateResponse(
        request=request,
        name="appointments.html",
        context={
            "appointments": appointments
        }
    )


# ---------------- CREATE FORM ----------------
@router.get("/create", response_class=HTMLResponse)
def create_form(request: Request, db: Session = Depends(get_db)):

    return templates.TemplateResponse(
        request=request,
        name="appointments.html",
        context={
            "action": "create",
            "patients": get_patients(db),
            "doctors": get_doctors(db)
        }
    )


# ---------------- CREATE SUBMIT ----------------
@router.post("/create")
def create_submit(
    request: Request,
    patient_id: UUID = Form(...),
    doctor_id: UUID = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    status: str = Form("Scheduled"),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):

    appointment_datetime = datetime.strptime(
        f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
    )
    
    if appointment_datetime < datetime.now():
        return templates.TemplateResponse(
            request=request,
            name="appointments.html",
            context={
                "action": "create",
                "error": "Booking cannot be done for the past date.",
                "patients": get_patients(db),
                "doctors": get_doctors(db),
                "form_data": {
                    "patient_id": patient_id,
                    "doctor_id": doctor_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "status": status,
                    "notes": notes,
                }
            }
        )

    try:
        appointment = AppointmentCreate(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_datetime,
            status=status,
            notes=notes
        )
        result = create_appointment(db, appointment)
        return RedirectResponse("/appointments/", status_code=303)
    except ValueError as e:
        suggested_dt = find_nearest_available_slot(db, doctor_id, appointment_datetime)
        suggestion_text = generate_ai_suggestion(db, doctor_id, appointment_datetime, suggested_dt)
        
        return templates.TemplateResponse(
            request=request,
            name="appointments.html",
            context={
                "action": "create",
                "patients": get_patients(db),
                "doctors": get_doctors(db),
                "error": f"{str(e)} AI Suggestion: {suggestion_text}",
                "suggested_date": suggested_dt.strftime("%Y-%m-%d"),
                "suggested_time": suggested_dt.strftime("%H:%M"),
                "suggestion_text": suggestion_text,
                "form_data": {
                    "patient_id": patient_id,
                    "doctor_id": doctor_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "status": status,
                    "notes": notes,
                },
            }
        )


# ---------------- EDIT FORM ----------------
@router.get("/{appointment_id}/edit", response_class=HTMLResponse)
def edit_form(appointment_id: UUID, request: Request, db: Session = Depends(get_db)):

    appointment = get_appointment(db, appointment_id)

    if not appointment:
        return RedirectResponse("/appointments/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="appointments.html",
        context={
            "action": "edit",
            "appointment": appointment,
            "patients": get_patients(db),
            "doctors": get_doctors(db),
            "form_data": {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "appointment_date": appointment.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": appointment.appointment_date.strftime("%H:%M"),
                "status": appointment.status,
                "notes": appointment.notes,
            }
        }
    )


# ---------------- UPDATE ----------------
@router.post("/{appointment_id}/edit")
def update_submit(
    appointment_id: UUID,
    request: Request,
    patient_id: UUID = Form(...),
    doctor_id: UUID = Form(...),
    appointment_date: str = Form(...),
    appointment_time: str = Form(...),
    status: str = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):

    appointment_datetime = datetime.strptime(
        f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
    )

    if appointment_datetime < datetime.now():
        return templates.TemplateResponse(
            request=request,
            name="appointments.html",
            context={
                "action": "edit",
                "error": "Booking cannot be done for past dates.",
                "patients": get_patients(db),
                "doctors": get_doctors(db),
                "form_data": {
                    "id": appointment_id,
                    "patient_id": patient_id,
                    "doctor_id": doctor_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "status": status,
                    "notes": notes,
                }
            }
        )

    try:
        appointment_update = AppointmentUpdate(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_datetime,
            status=status,
            notes=notes
        )

        updated = update_appointment(db, appointment_id, appointment_update)

        if not updated:
            return RedirectResponse(url="/appointments/", status_code=303)

        return RedirectResponse(url="/appointments/", status_code=303)

    except ValueError as e:
        suggested_dt = find_nearest_available_slot(db, doctor_id, appointment_datetime, appointment_id)
        suggestion_text = generate_ai_suggestion(db, doctor_id, appointment_datetime, suggested_dt)
        
        db_appointment = get_appointment(db, appointment_id)
        return templates.TemplateResponse(
            request=request,
            name="appointments.html",
            context={
                "action": "edit",
                "appointment": db_appointment,
                "patients": get_patients(db),
                "doctors": get_doctors(db),
                "error": f"{str(e)} AI Suggestion: {suggestion_text}",
                "suggested_date": suggested_dt.strftime("%Y-%m-%d"),
                "suggested_time": suggested_dt.strftime("%H:%M"),
                "suggestion_text": suggestion_text,
                "form_data": {
                    "id": appointment_id,
                    "patient_id": patient_id,
                    "doctor_id": doctor_id,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "status": status,
                    "notes": notes,
                }
            }
        )

# ---------------- AI SUGGESTION ENDPOINT ----------------
class SuggestTimeRequest(BaseModel):
    doctor_id: UUID
    appointment_date: str
    appointment_time: str
    appointment_id: Optional[UUID] = None

@router.post("/suggest-time")
def suggest_time(payload: SuggestTimeRequest, db: Session = Depends(get_db)):
    try:
        requested_datetime = datetime.strptime(
            f"{payload.appointment_date} {payload.appointment_time}", "%Y-%m-%d %H:%M"
        )
    except ValueError:
        return {"available": False, "error": "Invalid date or time format."}

    from app.crud.appointment import doctor_is_available
    conflicting = doctor_is_available(
        db, 
        payload.doctor_id, 
        requested_datetime, 
        payload.appointment_id
    )
    
    if not conflicting:
        return {"available": True}
        
    suggested_dt = find_nearest_available_slot(
        db, 
        payload.doctor_id, 
        requested_datetime, 
        payload.appointment_id
    )
    
    suggestion_text = generate_ai_suggestion(
        db, 
        payload.doctor_id, 
        requested_datetime, 
        suggested_dt
    )
    
    return {
        "available": False,
        "suggested_date": suggested_dt.strftime("%Y-%m-%d"),
        "suggested_time": suggested_dt.strftime("%H:%M"),
        "suggestion_text": suggestion_text
    }

# ---------------- DELETE ----------------
@router.post("/{appointment_id}/delete")
def delete_submit(appointment_id: UUID, db: Session = Depends(get_db)):

    delete_appointment(db, appointment_id)

    return RedirectResponse("/appointments/", status_code=303)