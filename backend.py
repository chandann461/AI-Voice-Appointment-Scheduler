"""
Corrected Appointment Management API - Pydantic V2 Compatible
Fixed all NameError and deprecation warnings
Converted to user-friendly datetime format (normal day entry format)
"""

# Step 1: Import and initialize database
from table import engine, init_db, patient, SessionLocal, get_db
from typing import Optional, List
import datetime as dt
import logging
from datetime import timezone, timedelta 

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()  # Initialize the database and create tables if they don't exist

# Step 2: Pydantic models for data validation (Pydantic V2)
from pydantic import BaseModel, Field, field_validator, ConfigDict

class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=1, description="Patient's full name")
    reason: str = Field(..., min_length=1, description="Reason for appointment")
    start_time: str = Field(..., description="Appointment start time (format: YYYY-MM-DD HH:MM AM/PM or YYYY-MM-DD HH:MM:SS)")
    
    @field_validator('patient_name')
    @classmethod
    def validate_patient_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Patient name must be at least 2 characters')
        return v.strip()
    
    @field_validator('start_time')
    @classmethod
    def validate_start_time(cls, v):
        """
        Parse start_time string and validate it's in the future
        Accepts formats: 
        - YYYY-MM-DD HH:MM AM/PM
        - YYYY-MM-DD HH:MM:SS
        - YYYY-MM-DD HH:MM
        """
        try:
            # Try parsing with AM/PM format first
            try:
                parsed_time = dt.datetime.strptime(v, "%Y-%m-%d %I:%M %p")
            except ValueError:
                # Try 24-hour format with seconds
                try:
                    parsed_time = dt.datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Try 24-hour format without seconds
                    parsed_time = dt.datetime.strptime(v, "%Y-%m-%d %H:%M")
            
            # Check if time is in the past
            if parsed_time < dt.datetime.now():
                raise ValueError('Appointment time cannot be in the past')
            
            return v
        except ValueError as e:
            if "time is in the past" in str(e):
                raise
            raise ValueError(f'Invalid datetime format. Use: YYYY-MM-DD HH:MM AM/PM or YYYY-MM-DD HH:MM:SS (e.g., 2026-05-15 02:30 PM)')


class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    reason: str
    start_time: str  # Changed to string with formatted datetime
    canceled: bool
    created_at: str  # Changed to string with formatted datetime
    
    model_config = ConfigDict(from_attributes=True)


class CancelAppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=1)
    date: Optional[str] = None  # Changed to string format: YYYY-MM-DD
    appointment_id: Optional[int] = None
    
    @field_validator('patient_name')
    @classmethod
    def validate_patient_name(cls, v):
        return v.strip()
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            dt.datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Date must be in format: YYYY-MM-DD')


class CancelAppointmentResponse(BaseModel):
    patient_name: str
    canceled_cnt: int
    message: str
    
    model_config = ConfigDict(from_attributes=True)


class ListAppointmentsResponse(BaseModel):
    date: str  # Changed to string format: YYYY-MM-DD
    total_appointments: int
    appointments: List[AppointmentResponse]


# ============ HELPER FUNCTIONS ============
def parse_time_string(time_str: str) -> dt.datetime:
    """Convert user-friendly string to datetime object"""
    try:
        # Try AM/PM format first
        try:
            return dt.datetime.strptime(time_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            # Try 24-hour format with seconds
            try:
                return dt.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Try 24-hour format without seconds
                return dt.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError(f'Invalid datetime format: {time_str}')


def format_datetime_friendly(dt_obj: dt.datetime) -> str:
    """Convert datetime object to user-friendly format"""
    return dt_obj.strftime("%Y-%m-%d %I:%M %p")  # e.g., 2026-05-15 02:30 PM


def format_date_friendly(date_obj: dt.date) -> str:
    """Convert date object to user-friendly format"""
    return date_obj.strftime("%Y-%m-%d")  # e.g., 2026-05-15


# Step 3: Create FastAPI endpoints
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

app = FastAPI(
    title="Appointment Management API",
    description="Voice assistant compatible appointment scheduling system",
    version="2.0"
)


@app.get("/")
def root():
    """Root endpoint with API documentation link"""
    return {
        "message": "Appointment API is running!",
        "docs": "Visit /docs for interactive API documentation",
        "health": "ok",
        "datetime_format": "YYYY-MM-DD HH:MM AM/PM (e.g., 2026-05-15 02:30 PM)"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": format_datetime_friendly(dt.datetime.now())
    }


# ---------- SCHEDULE APPOINTMENT ENDPOINT ----------
@app.post(
    "/schedule_appointments/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new appointment",
    tags=["Appointments"]
)
def schedule_appointment(
    request: AppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Schedule a new appointment for a patient.
    
    **Input Format**: start_time should be "YYYY-MM-DD HH:MM AM/PM" 
    Example: "2026-05-15 02:30 PM"
    
    **Voice-friendly response**: Returns confirmation with appointment details
    """
    try:
        # Parse the time string to datetime object
        parsed_start_time = parse_time_string(request.start_time)
        
        # Check if patient already has an appointment at this time
        existing = db.execute(
            select(patient)
            .where(patient.patient_name.ilike(request.patient_name))
            .where(patient.start_time == parsed_start_time)
            .where(patient.canceled == False)
        ).scalars().first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient {request.patient_name} already has an appointment at {request.start_time}"
            )
        
        # Create new appointment
        new_appointment = patient(
            patient_name=request.patient_name,
            reason=request.reason,
            start_time=parsed_start_time
        )
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)
        
        logger.info(f"Appointment scheduled: {new_appointment.id} for {request.patient_name}")
        
        return AppointmentResponse(
            id=new_appointment.id,
            patient_name=new_appointment.patient_name,
            reason=new_appointment.reason,
            start_time=format_datetime_friendly(new_appointment.start_time),
            canceled=new_appointment.canceled,
            created_at=format_datetime_friendly(new_appointment.created_at)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule appointment: {str(e)}"
        )


# ---------- CANCEL APPOINTMENT ENDPOINT ----------
@app.post(
    "/cancel_appointment/",
    response_model=CancelAppointmentResponse,
    summary="Cancel appointment(s)",
    tags=["Appointments"]
)
def cancel_appointment(
    request: CancelAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel appointment(s) for a patient.
    Can cancel by:
    - appointment_id: Cancel specific appointment
    - patient_name + date: Cancel all appointments on that date (format: YYYY-MM-DD)
    
    **Voice-friendly response**: Confirms number of canceled appointments
    """
    try:
        # Validate that at least one filter is provided
        if request.appointment_id is None and request.date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either appointment_id or date (YYYY-MM-DD) to cancel"
            )
        
        # Case 1: Cancel by appointment ID (specific appointment)
        if request.appointment_id is not None:
            appointment = db.get(patient, request.appointment_id)
            
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Appointment {request.appointment_id} not found"
                )
            
            if appointment.canceled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Appointment is already canceled"
                )
            
            appointment.canceled = True
            db.commit()
            
            logger.info(f"Appointment {request.appointment_id} canceled for {appointment.patient_name}")
            
            return CancelAppointmentResponse(
                patient_name=appointment.patient_name,
                canceled_cnt=1,
                message=f"Appointment on {format_datetime_friendly(appointment.start_time)} has been canceled"
            )
        
        # Case 2: Cancel by patient name and date
        parsed_date = dt.datetime.strptime(request.date, "%Y-%m-%d").date()
        start_date = dt.datetime.combine(parsed_date, dt.time.min)
        end_date = start_date + dt.timedelta(days=1)
        
        result = db.execute(
            select(patient)
            .where(patient.patient_name.ilike(request.patient_name))
            .where(patient.start_time >= start_date)
            .where(patient.start_time < end_date)
            .where(patient.canceled == False)
        )
        
        appointments = result.scalars().all()
        
        if not appointments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active appointments found for {request.patient_name} on {request.date}"
            )
        
        # Cancel all matching appointments
        for appt in appointments:
            appt.canceled = True
        
        db.commit()
        
        logger.info(f"Canceled {len(appointments)} appointments for {request.patient_name} on {request.date}")
        
        return CancelAppointmentResponse(
            patient_name=request.patient_name,
            canceled_cnt=len(appointments),
            message=f"Successfully canceled {len(appointments)} appointment(s) for {request.patient_name} on {request.date}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel appointment: {str(e)}"
        )


# ---------- LIST APPOINTMENTS ENDPOINT ----------
@app.get(
    "/list_appointments/",
    response_model=ListAppointmentsResponse,
    summary="Get all appointments for a specific date",
    tags=["Appointments"]
)
def list_appointments(
    date: str,  # Changed to string format: YYYY-MM-DD
    db: Session = Depends(get_db)
):
    """
    Retrieve all non-canceled appointments for a specific date.
    
    **Date Format**: YYYY-MM-DD (e.g., 2026-05-15)
    
    **Voice-friendly response**: Includes date and appointment count
    """
    try:
        # Parse the date string
        try:
            parsed_date = dt.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date must be in format: YYYY-MM-DD (e.g., 2026-05-15)"
            )
        
        # Validate date is not in the past
        if parsed_date < dt.date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot list appointments for past dates"
            )
        
        booked_appointments = []
        
        # Start and end of selected day
        start_date = dt.datetime.combine(parsed_date, dt.time.min)
        end_date = start_date + dt.timedelta(days=1)
        
        result = db.execute(
            select(patient)
            .where(patient.canceled == False)
            .where(patient.start_time >= start_date)
            .where(patient.start_time < end_date)
            .order_by(patient.start_time.asc())
        )
        
        for appointment in result.scalars().all():
            booked_appointments.append(
                AppointmentResponse(
                    id=appointment.id,
                    patient_name=appointment.patient_name,
                    reason=appointment.reason,
                    start_time=format_datetime_friendly(appointment.start_time),
                    canceled=appointment.canceled,
                    created_at=format_datetime_friendly(appointment.created_at)
                )
            )
        
        logger.info(f"Retrieved {len(booked_appointments)} appointments for {date}")
        
        return ListAppointmentsResponse(
            date=date,
            total_appointments=len(booked_appointments),
            appointments=booked_appointments
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointments: {str(e)}"
        )


# ---------- SEARCH APPOINTMENTS BY PATIENT ----------
@app.get(
    "/search_appointments/{patient_name}",
    response_model=ListAppointmentsResponse,
    summary="Search appointments by patient name",
    tags=["Appointments"]
)
def search_appointments_by_patient(
    patient_name: str,
    db: Session = Depends(get_db)
):
    """
    Find all active appointments for a specific patient.
    
    **Voice-friendly response**: Lists all upcoming appointments for the patient
    """
    try:
        if not patient_name or len(patient_name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient name must be at least 2 characters"
            )
        
        result = db.execute(
            select(patient)
            .where(patient.patient_name.ilike(f"%{patient_name}%"))
            .where(patient.canceled == False)
            .where(patient.start_time >= dt.datetime.now())
            .order_by(patient.start_time.asc())
        )
        
        appointments = result.scalars().all()
        
        response_list = [
            AppointmentResponse(
                id=appt.id,
                patient_name=appt.patient_name,
                reason=appt.reason,
                start_time=format_datetime_friendly(appt.start_time),
                canceled=appt.canceled,
                created_at=format_datetime_friendly(appt.created_at)
            )
            for appt in appointments
        ]
        
        logger.info(f"Found {len(appointments)} appointments for patient: {patient_name}")
        
        # Return with today's date as default
        return ListAppointmentsResponse(
            date=format_date_friendly(dt.date.today()),
            total_appointments=len(response_list),
            appointments=response_list
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search appointments: {str(e)}"
        )


# ---------- RESCHEDULE APPOINTMENT ----------
@app.put(
    "/reschedule_appointment/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Reschedule an existing appointment",
    tags=["Appointments"]
)
def reschedule_appointment(
    appointment_id: int,
    new_time: str,  # Changed to string format
    db: Session = Depends(get_db)
):
    """
    Reschedule an appointment to a new date/time.
    
    **Input Format**: new_time should be "YYYY-MM-DD HH:MM AM/PM"
    Example: "2026-05-20 03:00 PM"
    
    **Voice-friendly response**: Confirms new appointment time
    """
    try:
        # Parse the new time string
        parsed_new_time = parse_time_string(new_time)
        
        appointment = db.get(patient, appointment_id)
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found"
            )
        
        if appointment.canceled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reschedule a canceled appointment"
            )
        
        if parsed_new_time < dt.datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New appointment time cannot be in the past"
            )
        
        # Check for conflicts
        existing = db.execute(
            select(patient)
            .where(patient.patient_name == appointment.patient_name)
            .where(patient.start_time == parsed_new_time)
            .where(patient.canceled == False)
            .where(patient.id != appointment_id)
        ).scalars().first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient already has an appointment at this time"
            )
        
        old_time = appointment.start_time
        appointment.start_time = parsed_new_time
        db.commit()
        db.refresh(appointment)
        
        logger.info(f"Appointment {appointment_id} rescheduled from {format_datetime_friendly(old_time)} to {new_time}")
        
        return AppointmentResponse(
            id=appointment.id,
            patient_name=appointment.patient_name,
            reason=appointment.reason,
            start_time=format_datetime_friendly(appointment.start_time),
            canceled=appointment.canceled,
            created_at=format_datetime_friendly(appointment.created_at)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule appointment: {str(e)}"
        )


# Step 4: Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",
        host="127.0.0.1",
        port=2000,
        reload=True,
        log_level="info"
    )
