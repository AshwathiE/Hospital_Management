def get_appointment(db: Session, appointment_id: UUID):
    return db.query(Appointment).filter(Appointment.id==appointment_id).first()