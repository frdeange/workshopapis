"""
Pydantic models for Maintenance API
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TechnicianStatus(str, Enum):
    """Technician availability status"""
    available = "available"
    busy = "busy"
    off_duty = "off_duty"


class JobPriority(str, Enum):
    """Maintenance job priority levels"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class JobStatus(str, Enum):
    """Maintenance job status"""
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Technician(BaseModel):
    """Technician model representing maintenance personnel"""
    technician_id: str = Field(
        ...,
        description="Unique identifier for the technician",
        examples=["TECH-001"]
    )
    name: str = Field(
        ...,
        description="Full name of the technician",
        examples=["John Smith"]
    )
    specialization: List[str] = Field(
        ...,
        description="List of technical specializations",
        examples=[["Electrical", "HVAC"]]
    )
    skill_level: str = Field(
        ...,
        description="Skill level (Junior, Senior, Expert)",
        examples=["Senior"]
    )
    status: TechnicianStatus = Field(
        ...,
        description="Current availability status",
        examples=["available"]
    )
    current_location: str = Field(
        ...,
        description="Current location or facility",
        examples=["Factory Floor A"]
    )
    contact_phone: str = Field(
        ...,
        description="Contact phone number",
        examples=["+1-555-0123"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "technician_id": "TECH-001",
                "name": "John Smith",
                "specialization": ["Electrical", "HVAC"],
                "skill_level": "Senior",
                "status": "available",
                "current_location": "Factory Floor A",
                "contact_phone": "+1-555-0123"
            }
        }


class ScheduleSlot(BaseModel):
    """Schedule slot for technician availability"""
    slot_id: str = Field(
        ...,
        description="Unique identifier for the schedule slot",
        examples=["SLOT-20231015-001"]
    )
    technician_id: str = Field(
        ...,
        description="ID of the technician",
        examples=["TECH-001"]
    )
    date: str = Field(
        ...,
        description="Date of the slot (YYYY-MM-DD)",
        examples=["2023-10-15"]
    )
    start_time: str = Field(
        ...,
        description="Start time (HH:MM)",
        examples=["09:00"]
    )
    end_time: str = Field(
        ...,
        description="End time (HH:MM)",
        examples=["17:00"]
    )
    available: bool = Field(
        ...,
        description="Whether the slot is available",
        examples=[True]
    )
    location: Optional[str] = Field(
        None,
        description="Location for the slot",
        examples=["Factory Floor A"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "slot_id": "SLOT-20231015-001",
                "technician_id": "TECH-001",
                "date": "2023-10-15",
                "start_time": "09:00",
                "end_time": "17:00",
                "available": True,
                "location": "Factory Floor A"
            }
        }


class JobBookingRequest(BaseModel):
    """Request model for booking a maintenance job"""
    machine_id: str = Field(
        ...,
        description="ID of the machine requiring maintenance",
        examples=["MACHINE-105"]
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code if applicable",
        examples=["ERR-OVERHEAT-42"]
    )
    description: str = Field(
        ...,
        description="Description of the maintenance needed",
        examples=["Motor overheating, requires inspection and bearing replacement"]
    )
    priority: JobPriority = Field(
        ...,
        description="Priority level of the job",
        examples=["high"]
    )
    estimated_duration_hours: float = Field(
        ...,
        gt=0,
        description="Estimated duration in hours",
        examples=[3.5]
    )
    preferred_date: Optional[str] = Field(
        None,
        description="Preferred date for the job (YYYY-MM-DD)",
        examples=["2023-10-20"]
    )
    requested_by: str = Field(
        ...,
        description="Name or ID of person requesting the maintenance",
        examples=["Plant Manager"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "MACHINE-105",
                "error_code": "ERR-OVERHEAT-42",
                "description": "Motor overheating, requires inspection and bearing replacement",
                "priority": "high",
                "estimated_duration_hours": 3.5,
                "preferred_date": "2023-10-20",
                "requested_by": "Plant Manager"
            }
        }


class JobBookingResponse(BaseModel):
    """Response model after booking a maintenance job"""
    job_id: str = Field(
        ...,
        description="Unique identifier for the job",
        examples=["JOB-20231015-001"]
    )
    assigned_technician: str = Field(
        ...,
        description="Name of the assigned technician",
        examples=["John Smith"]
    )
    scheduled_date: str = Field(
        ...,
        description="Scheduled date (YYYY-MM-DD)",
        examples=["2023-10-20"]
    )
    scheduled_time: str = Field(
        ...,
        description="Scheduled time (HH:MM)",
        examples=["09:00"]
    )
    estimated_completion: str = Field(
        ...,
        description="Estimated completion time (HH:MM)",
        examples=["12:30"]
    )
    status: str = Field(
        ...,
        description="Job status",
        examples=["scheduled"]
    )
    priority: str = Field(
        ...,
        description="Job priority",
        examples=["high"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "JOB-20231015-001",
                "assigned_technician": "John Smith",
                "scheduled_date": "2023-10-20",
                "scheduled_time": "09:00",
                "estimated_completion": "12:30",
                "status": "scheduled",
                "priority": "high"
            }
        }


class MaintenanceJob(BaseModel):
    """Complete maintenance job model"""
    job_id: str = Field(
        ...,
        description="Unique identifier for the job",
        examples=["JOB-20231015-001"]
    )
    machine_id: str = Field(
        ...,
        description="ID of the machine",
        examples=["MACHINE-105"]
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code if applicable",
        examples=["ERR-OVERHEAT-42"]
    )
    description: str = Field(
        ...,
        description="Job description",
        examples=["Motor overheating, requires inspection and bearing replacement"]
    )
    priority: JobPriority = Field(
        ...,
        description="Job priority",
        examples=["high"]
    )
    estimated_duration_hours: float = Field(
        ...,
        description="Estimated duration in hours",
        examples=[3.5]
    )
    assigned_technician_id: Optional[str] = Field(
        None,
        description="ID of assigned technician",
        examples=["TECH-001"]
    )
    scheduled_date: Optional[str] = Field(
        None,
        description="Scheduled date (YYYY-MM-DD)",
        examples=["2023-10-20"]
    )
    scheduled_time: Optional[str] = Field(
        None,
        description="Scheduled time (HH:MM)",
        examples=["09:00"]
    )
    status: JobStatus = Field(
        ...,
        description="Job status",
        examples=["scheduled"]
    )
    created_at: str = Field(
        ...,
        description="Creation timestamp",
        examples=["2023-10-15T14:30:00.000000"]
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes",
        examples=["Customer reported unusual noise"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "JOB-20231015-001",
                "machine_id": "MACHINE-105",
                "error_code": "ERR-OVERHEAT-42",
                "description": "Motor overheating, requires inspection and bearing replacement",
                "priority": "high",
                "estimated_duration_hours": 3.5,
                "assigned_technician_id": "TECH-001",
                "scheduled_date": "2023-10-20",
                "scheduled_time": "09:00",
                "status": "scheduled",
                "created_at": "2023-10-15T14:30:00.000000",
                "notes": "Customer reported unusual noise"
            }
        }
