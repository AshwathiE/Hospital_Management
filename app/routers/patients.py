from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from fastapi.templating import Jinja2Templates
from app.crud.patient import get_patients, get_patient, create_patient, update_patient
from app.crud.patient import get_patients, get_patient, create_patient, update_patient, delete_patient
from app.schemas.patient import PatientCreate, PatientUpdate
from datetime import datetime,date
import datetime
from uuid import UUID
from pydantic import ValidationError
from pydantic import EmailStr
import os
router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"))
@router.get("/", response_class=HTMLResponse)
def list_patients(request: Request, db: Session = Depends(get_db)):
    patients = get_patients(db)
    return templates.TemplateResponse(
        request=request,
        name="patients.html",
        context={"patients": patients}
    )
@router.get("/create", response_class=HTMLResponse)
def create_patient_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="patients.html",
        context={"action": "create"}
    )
@router.post("/create")
def create_patient_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    date_of_birth: datetime.date = Form(...),
    db: Session = Depends(get_db)
):

    try:

        patient = PatientCreate(
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
            date_of_birth=date_of_birth
        )

        create_patient(db, patient)

        return RedirectResponse(
            url="/patients/",
            status_code=303
        )

    except ValidationError as e:

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "create",
                "error": e.errors()[0]["msg"],
                "form_data": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "date_of_birth": date_of_birth
                }
            }
        )

    except ValueError as e:

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "create",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "date_of_birth": date_of_birth
                }
            }
        )

    except IntegrityError:

        db.rollback()

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "create",
                "error": "Patient already exists.",
                "form_data": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "date_of_birth": date_of_birth
                }
            }
        )
# ── Edit ──────────────────────────────────────────────────────────────────────
@router.get("/{patient_id}/edit", response_class=HTMLResponse)
def edit_patient_form(patient_id: UUID, request: Request, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        return RedirectResponse(url="/patients/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="patients.html",
        context={
            "action": "edit",
            "patient": patient,
        }
    )
@router.post("/{patient_id}/edit")
def edit_patient_submit(
    patient_id: UUID,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    date_of_birth: date = Form(...),
    db: Session = Depends(get_db)
):

    try:

        patient_update = PatientUpdate(
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip(),
            date_of_birth=date_of_birth
        )

        updated = update_patient(
            db,
            patient_id,
            patient_update
        )

        if not updated:
            return RedirectResponse(
                url="/patients/",
                status_code=303
            )

        return RedirectResponse(
            url="/patients/",
            status_code=303
        )

    except ValidationError as e:

        patient = get_patient(db, patient_id)

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "edit",
                "patient": patient,
                "error": e.errors()[0]["msg"]
            }
        )

    except ValueError as e:

        patient = get_patient(db, patient_id)

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "edit",
                "patient": patient,
                "error": str(e)
            }
        )

    except IntegrityError:

        db.rollback()

        patient = get_patient(db, patient_id)

        return templates.TemplateResponse(
            request=request,
            name="patients.html",
            context={
                "action": "edit",
                "patient": patient,
                "error": "Patient already exists."
            }
        )
# ── Delete ────────────────────────────────────────────────────────────────────
@router.post("/{patient_id}/delete")
def delete_patient_submit(patient_id: UUID, db: Session = Depends(get_db)):
    """Delete a patient and all their associated appointments."""
    delete_patient(db, patient_id)
    return RedirectResponse(url="/patients/", status_code=303)
 