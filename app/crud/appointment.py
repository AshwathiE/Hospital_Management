from datetime import timedelta, datetime, time
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

def get_appointment(db: Session, appointment_id: UUID):
    return db.query(Appointment).filter(Appointment.id==appointment_id).first()

def get_appointments(db: Session, skip:int=0, limit:int=100):
    return db.query(Appointment).filter(Appointment.is_deleted==False).offset(skip).limit(limit).all()

def doctor_is_available(db:Session, doctor_id, appointment_date, appointment_id=None, slot_minutes:int=30):
    start=appointment_date
    end=appointment_date+timedelta(minutes=slot_minutes)
    appointments=db.query(Appointment).filter(Appointment.doctor_id==doctor_id, Appointment.is_deleted==False).all()
    for appt in appointments:
        if appointment_id and appt.id==appointment_id:
            continue
        if appt.appointment_date < end and appt.appointment_date+timedelta(minutes=slot_minutes) > start:
            return appt
    return None

def create_appointment(db:Session, appointment:AppointmentCreate):
    try:
        if appointment.appointment_date < datetime.now():
            raise ValueError("Appointment date cannot be in the past")
        if doctor_is_available(db, appointment.doctor_id, appointment.appointment_date):
            raise ValueError("Doctor is already booked for this time slot.")
        db_appointment=Appointment(
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            appointment_date=appointment.appointment_date,
            status=appointment.status,
            notes=appointment.notes,
        )
        db.add(db_appointment); db.commit(); db.refresh(db_appointment)
        return db_appointment
    except:
        db.rollback(); raise

def update_appointment(db:Session, appointment_id:UUID, appointment_update:AppointmentUpdate):
    db_appointment=get_appointment(db, appointment_id)
    if not db_appointment:
        raise ValueError("Appointment not found.")
    update_data=appointment_update.model_dump(exclude_unset=True) if hasattr(appointment_update,"model_dump") else appointment_update.dict(exclude_unset=True)
    new_doctor=update_data.get("doctor_id", db_appointment.doctor_id)
    new_date=update_data.get("appointment_date", db_appointment.appointment_date)
    if new_date < datetime.now():
        raise ValueError("Appointment date cannot be in the past")
    if doctor_is_available(db,new_doctor,new_date,appointment_id=db_appointment.id):
        raise ValueError("Doctor is already booked for this time slot.")
    try:
        for k,v in update_data.items():
            setattr(db_appointment,k,v)
        db.commit(); db.refresh(db_appointment)
        return db_appointment
    except:
        db.rollback(); raise

def delete_appointment(db:Session, appointment_id:UUID):
    db_appointment=get_appointment(db, appointment_id)
    if not db_appointment:
        raise ValueError("Appointment not found.")
    try:
        db_appointment.is_deleted=True
        db.commit(); db.refresh(db_appointment)
        return db_appointment
    except:
        db.rollback(); raise

def find_nearest_available_slot(db: Session, doctor_id: UUID, requested_dt: datetime, appointment_id: UUID = None) -> datetime:
    """
    Finds the nearest available 30-minute time slot for a doctor that is in the future
    and falls within standard working hours (09:00 to 17:00).
    """
    work_start = time(9, 0)
    work_end = time(17, 0)
    slot_duration = timedelta(minutes=30)
    
    now = datetime.now()
    start_search_dt = requested_dt
    if start_search_dt < now:
        start_search_dt = now

    # Fetch all active appointments for this doctor to avoid N+1 queries
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.is_deleted == False
    ).all()
    
    def is_slot_available(slot_start: datetime) -> bool:
        slot_end = slot_start + slot_duration
        for appt in appointments:
            if appointment_id and appt.id == appointment_id:
                continue
            appt_start = appt.appointment_date
            appt_end = appt_start + slot_duration
            if appt_start < slot_end and appt_end > slot_start:
                return False
        return True

    # 1. Check if the requested/starting slot is available and valid
    if start_search_dt >= now:
        t = start_search_dt.time()
        if t >= work_start and (start_search_dt + slot_duration).time() <= work_end:
            if is_slot_available(start_search_dt):
                return start_search_dt

    # 2. Search outward from start_search_dt
    max_steps = 1000  # Search up to ~20 days (1000 * 30 min slots)
    for step in range(1, max_steps):
        for sign in [1, -1]:
            candidate = start_search_dt + sign * step * slot_duration
            if candidate < now:
                continue
            
            t = candidate.time()
            try:
                candidate_end = candidate + slot_duration
                if t >= work_start and candidate_end.date() == candidate.date() and candidate_end.time() <= work_end:
                    if is_slot_available(candidate):
                        return candidate
            except Exception:
                continue
                
    # Fallback to tomorrow morning
    tomorrow_nine = datetime.combine(now.date() + timedelta(days=1), work_start)
    return tomorrow_nine

def generate_ai_suggestion(db: Session, doctor_id: UUID, requested_time: datetime, suggested_time: datetime) -> str:
    """
    Generates a patient-friendly message suggesting the nearest available slot.
    Uses Gemini API or OpenAI API if keys are available in environment variables,
    otherwise falls back to a locally generated smart suggestion.
    """
    import os
    
    # Retrieve Doctor details
    from app.models.doctor import Doctor
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    doctor_name = doctor.name if doctor else "the doctor"
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    prompt = (
        f"You are an AI Hospital Appointment Scheduler. The patient requested an appointment "
        f"with Dr. {doctor_name} at {requested_time.strftime('%Y-%m-%d %H:%M')}. "
        f"However, this slot is unavailable. The nearest available slot is at "
        f"{suggested_time.strftime('%Y-%m-%d %H:%M')}. "
        f"Generate a brief, polite, and helpful notification message for the patient. "
        f"State clearly that the doctor is unavailable at the requested time and suggest the new time. "
        f"Keep the message under 2 sentences."
    )
    
    # Try Gemini API if key is present
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception:
            pass
            
    # Try OpenAI API if key is present
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.7
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
        except Exception:
            pass
            
    # Local fallback
    req_time_str = requested_time.strftime("%I:%M %p")
    sug_time_str = suggested_time.strftime("%I:%M %p")
    sug_date_str = suggested_time.strftime("%Y-%m-%d")
    
    if requested_time.date() == suggested_time.date():
        return f"Doctor is unavailable at {req_time_str}. Suggested slot: {sug_time_str}"
    else:
        return f"Doctor is unavailable at {req_time_str} on {requested_time.strftime('%Y-%m-%d')}. Suggested slot: {sug_time_str} on {sug_date_str}"
