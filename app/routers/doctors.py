
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.templating import Jinja2Templates
import os
from uuid import UUID
from pydantic import ValidationError

from app.database import get_db
from app.crud.doctor import (
    get_doctors,
    get_doctor,
    create_doctor,
    update_doctor,
    delete_doctor
)
from app.schemas.doctor import DoctorCreate, DoctorUpdate

router = APIRouter()

templates = Jinja2Templates(
    directory=os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates"
    )
)

# ------------------- List Doctors -------------------
@router.get("/", response_class=HTMLResponse)
def list_doctors(request: Request, db: Session = Depends(get_db)):
    doctors = get_doctors(db)
    return templates.TemplateResponse(
        request=request,
        name="doctors.html",
        context={"doctors": doctors}
    )

# ------------------- Create Form -------------------
@router.get("/create", response_class=HTMLResponse)
def create_doctor_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="doctors.html",
        context={"action": "create"}
    )

# ------------------- Create Doctor -------------------
@router.post("/create")
def create_doctor_submit(
    request: Request,
    name: str = Form(...),
    specialty: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        doctor = DoctorCreate(
            name=name.strip(),
            specialty=specialty.strip(),
            phone=phone.strip(),
            email=email.strip().lower()
        )

        create_doctor(db, doctor)

        return RedirectResponse(url="/doctors/", status_code=303)

    except ValidationError as e:
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "create",
                "error": e.errors()[0]["msg"],
                "form_data": {
                    "name": name,
                    "specialty": specialty,
                    "phone": phone,
                    "email": email
                }
            }
        )

    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "create",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "specialty": specialty,
                    "phone": phone,
                    "email": email
                }
            }
        )

    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "create",
                "error": "Doctor already exists.",
                "form_data": {
                    "name": name,
                    "specialty": specialty,
                    "phone": phone,
                    "email": email
                }
            }
        )

# ------------------- Edit Form (GET) -------------------
@router.get("/{doctor_id}/edit", response_class=HTMLResponse)
def edit_doctor_form(
    doctor_id: UUID,
    request: Request,
    db: Session = Depends(get_db)
):
    doctor = get_doctor(db, doctor_id)

    if not doctor:
        return RedirectResponse(url="/doctors/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="doctors.html",
        context={
            "action": "edit",
            "doctor": doctor
        }
    )

# ------------------- Edit Submit (POST) -------------------
@router.post("/{doctor_id}/edit")
def edit_doctor_submit(
    doctor_id: UUID,
    request: Request,
    name: str = Form(...),
    specialty: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        doctor_update = DoctorUpdate(
            name=name.strip(),
            specialty=specialty.strip(),
            phone=phone.strip(),
            email=email.strip().lower()
        )

        updated = update_doctor(db, doctor_id, doctor_update)

        if not updated:
            return RedirectResponse(url="/doctors/", status_code=303)

        return RedirectResponse(url="/doctors/", status_code=303)

    except ValidationError as e:
        doctor = get_doctor(db, doctor_id)
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "edit",
                "doctor": doctor,
                "error": e.errors()[0]["msg"]
            }
        )

    except ValueError as e:
        doctor = get_doctor(db, doctor_id)
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "edit",
                "doctor": doctor,
                "error": str(e)
            }
        )

    except IntegrityError:
        db.rollback()
        doctor = get_doctor(db, doctor_id)
        return templates.TemplateResponse(
            request=request,
            name="doctors.html",
            context={
                "action": "edit",
                "doctor": doctor,
                "error": "Doctor already exists."
            }
        )

# ------------------- Delete Doctor -------------------
@router.post("/{doctor_id}/delete")
def delete_doctor_submit(
    doctor_id: UUID,
    db: Session = Depends(get_db)
):
    delete_doctor(db, doctor_id)
    return RedirectResponse(url="/doctors/", status_code=303)
