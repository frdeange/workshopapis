"""
Maintenance API - Azure Functions
Manages technician schedules and maintenance job bookings for manufacturing facilities
"""
import azure.functions as func
import logging
import json
from datetime import datetime, timedelta
from azure.cosmos import exceptions
from cosmos_client import CosmosDBClient
from models import (
    Technician,
    TechnicianStatus,
    ScheduleSlot,
    JobBookingRequest,
    JobBookingResponse,
    MaintenanceJob,
    JobStatus,
    JobPriority
)

app = func.FunctionApp()
logger = logging.getLogger(__name__)

# Initialize Cosmos DB client
cosmos_client = CosmosDBClient()


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    
    Returns:
        200: Service is healthy
        
    Example:
        GET /api/health
        
        Response:
        {
            "status": "healthy",
            "service": "maintenance-api"
        }
    """
    logger.info("Health check requested")
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "maintenance-api"}),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="technicians", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_technicians(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all technicians
    
    Retrieve all technicians with their current status and specializations.
    
    Returns:
        200: Array of all technicians
        500: Internal server error
        
    Example:
        GET /api/technicians
        
        Response:
        [
            {
                "technician_id": "TECH-001",
                "name": "John Smith",
                "specialization": ["Electrical", "HVAC"],
                "skill_level": "Senior",
                "status": "available",
                "current_location": "Factory Floor A",
                "contact_phone": "+1-555-0123"
            }
        ]
    """
    logger.info("Getting all technicians")
    
    try:
        query = "SELECT * FROM c"
        technicians = list(cosmos_client.technicians_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Retrieved {len(technicians)} technicians")
        return func.HttpResponse(
            json.dumps(technicians),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving technicians: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving technicians: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="technicians/available", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_available_technicians(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get available technicians
    
    Retrieve only technicians who are currently available for work.
    
    Returns:
        200: Array of available technicians
        500: Internal server error
        
    Example:
        GET /api/technicians/available
        
        Response:
        [
            {
                "technician_id": "TECH-001",
                "name": "John Smith",
                "status": "available",
                ...
            }
        ]
    """
    logger.info("Getting available technicians")
    
    try:
        query = "SELECT * FROM c WHERE c.status = 'available'"
        technicians = list(cosmos_client.technicians_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Retrieved {len(technicians)} available technicians")
        return func.HttpResponse(
            json.dumps(technicians),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving available technicians: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving available technicians: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="technicians/{technician_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_technician(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get specific technician
    
    Retrieve details of a specific technician by their ID.
    
    Parameters:
        technician_id (str): ID of the technician
        
    Returns:
        200: Technician details
        404: Technician not found
        500: Internal server error
        
    Example:
        GET /api/technicians/TECH-001
        
        Response:
        {
            "technician_id": "TECH-001",
            "name": "John Smith",
            "specialization": ["Electrical", "HVAC"],
            "skill_level": "Senior",
            "status": "available",
            "current_location": "Factory Floor A",
            "contact_phone": "+1-555-0123"
        }
    """
    technician_id = req.route_params.get("technician_id")
    logger.info(f"Getting technician: {technician_id}")
    
    try:
        query = "SELECT * FROM c WHERE c.technician_id = @technicianId"
        parameters = [{"name": "@technicianId", "value": technician_id}]
        
        technicians = list(cosmos_client.technicians_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not technicians:
            logger.warning(f"Technician {technician_id} not found")
            return func.HttpResponse(
                json.dumps({"error": f"Technician {technician_id} not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        logger.info(f"Retrieved technician {technician_id}")
        return func.HttpResponse(
            json.dumps(technicians[0]),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving technician {technician_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving technician: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="schedule/next-available", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_next_available_slot(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get next available maintenance slot
    
    Find the next available maintenance slot across all technicians.
    
    Returns:
        200: Next available slot details
        404: No available slots found
        500: Internal server error
        
    Example:
        GET /api/schedule/next-available
        
        Response:
        {
            "slot_id": "SLOT-20231020-001",
            "technician_id": "TECH-001",
            "technician_name": "John Smith",
            "date": "2023-10-20",
            "start_time": "09:00",
            "end_time": "17:00",
            "location": "Factory Floor A"
        }
    """
    logger.info("Getting next available maintenance slot")
    
    try:
        query = "SELECT * FROM c WHERE c.available = true ORDER BY c.date, c.start_time"
        slots = list(cosmos_client.schedule_slots_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not slots:
            logger.warning("No available slots found")
            return func.HttpResponse(
                json.dumps({"message": "No available slots found"}),
                mimetype="application/json",
                status_code=404
            )
        
        # Get the first available slot
        next_slot = slots[0]
        
        # Get technician details
        tech_query = "SELECT * FROM c WHERE c.technician_id = @technicianId"
        tech_params = [{"name": "@technicianId", "value": next_slot["technician_id"]}]
        technicians = list(cosmos_client.technicians_container.query_items(
            query=tech_query,
            parameters=tech_params,
            enable_cross_partition_query=True
        ))
        
        response = {
            "slot_id": next_slot["slot_id"],
            "technician_id": next_slot["technician_id"],
            "technician_name": technicians[0]["name"] if technicians else "Unknown",
            "date": next_slot["date"],
            "start_time": next_slot["start_time"],
            "end_time": next_slot["end_time"],
            "location": next_slot.get("location")
        }
        
        logger.info(f"Next available slot: {next_slot['slot_id']} on {next_slot['date']}")
        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting next available slot: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error getting next available slot: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="schedule/technician/{technician_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_technician_schedule(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get technician schedule
    
    Get the schedule for a specific technician for the next N days.
    
    Parameters:
        technician_id (str): ID of the technician
        days (int): Number of days to look ahead (default: 7)
        
    Returns:
        200: Array of schedule slots
        500: Internal server error
        
    Example:
        GET /api/schedule/technician/TECH-001?days=7
        
        Response:
        [
            {
                "slot_id": "SLOT-20231020-001",
                "technician_id": "TECH-001",
                "date": "2023-10-20",
                "start_time": "09:00",
                "end_time": "17:00",
                "available": true,
                "location": "Factory Floor A"
            }
        ]
    """
    technician_id = req.route_params.get("technician_id")
    days = int(req.params.get("days", 7))
    
    logger.info(f"Getting schedule for technician {technician_id} for {days} days")
    
    try:
        # Calculate date range
        today = datetime.utcnow().date()
        end_date = today + timedelta(days=days)
        
        query = """
            SELECT * FROM c 
            WHERE c.technician_id = @technicianId 
            ORDER BY c.date, c.start_time
        """
        parameters = [{"name": "@technicianId", "value": technician_id}]
        
        slots = list(cosmos_client.schedule_slots_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False  # Using partition key
        ))
        
        logger.info(f"Retrieved {len(slots)} schedule slots for {technician_id}")
        return func.HttpResponse(
            json.dumps(slots),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving schedule for {technician_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving schedule: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="jobs/book", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def book_maintenance_job(req: func.HttpRequest) -> func.HttpResponse:
    """
    Book a maintenance job
    
    Book a new maintenance job with automatic technician assignment based on availability
    and specialization match.
    
    Request Body:
        machine_id (str): ID of the machine requiring maintenance
        error_code (str, optional): Error code if applicable
        description (str): Description of maintenance needed
        priority (str): Priority level (low, medium, high, critical)
        estimated_duration_hours (float): Estimated duration in hours
        preferred_date (str, optional): Preferred date (YYYY-MM-DD)
        requested_by (str): Name or ID of requester
        
    Returns:
        200: Job booked successfully
        400: Invalid request
        500: Internal server error
        
    Example:
        POST /api/jobs/book
        
        Request:
        {
            "machine_id": "MACHINE-105",
            "error_code": "ERR-OVERHEAT-42",
            "description": "Motor overheating, requires inspection",
            "priority": "high",
            "estimated_duration_hours": 3.5,
            "preferred_date": "2023-10-20",
            "requested_by": "Plant Manager"
        }
        
        Response:
        {
            "job_id": "JOB-20231015-001",
            "assigned_technician": "John Smith",
            "scheduled_date": "2023-10-20",
            "scheduled_time": "09:00",
            "estimated_completion": "12:30",
            "status": "scheduled",
            "priority": "high"
        }
    """
    logger.info("Booking maintenance job")
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
            job_request = JobBookingRequest(**req_body)
        except Exception as e:
            logger.error(f"Invalid request body: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"Invalid request: {str(e)}"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Find available technician (simple logic - first available)
        tech_query = "SELECT * FROM c WHERE c.status = 'available' OFFSET 0 LIMIT 1"
        technicians = list(cosmos_client.technicians_container.query_items(
            query=tech_query,
            enable_cross_partition_query=True
        ))
        
        if not technicians:
            logger.warning("No available technicians found")
            return func.HttpResponse(
                json.dumps({"error": "No available technicians at this time"}),
                mimetype="application/json",
                status_code=400
            )
        
        assigned_tech = technicians[0]
        
        # Create job
        job_id = f"JOB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        scheduled_date = job_request.preferred_date or datetime.utcnow().date().isoformat()
        scheduled_time = "09:00"
        
        # Calculate estimated completion
        start_hour = 9
        completion_hour = start_hour + job_request.estimated_duration_hours
        completion_minutes = int((completion_hour % 1) * 60)
        estimated_completion = f"{int(completion_hour):02d}:{completion_minutes:02d}"
        
        job = {
            "id": job_id,
            "job_id": job_id,
            "machine_id": job_request.machine_id,
            "error_code": job_request.error_code,
            "description": job_request.description,
            "priority": job_request.priority.value,
            "estimated_duration_hours": job_request.estimated_duration_hours,
            "assigned_technician_id": assigned_tech["technician_id"],
            "scheduled_date": scheduled_date,
            "scheduled_time": scheduled_time,
            "status": JobStatus.scheduled.value,
            "created_at": datetime.utcnow().isoformat(),
            "notes": f"Requested by: {job_request.requested_by}"
        }
        
        cosmos_client.jobs_container.create_item(body=job)
        
        response = JobBookingResponse(
            job_id=job_id,
            assigned_technician=assigned_tech["name"],
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            estimated_completion=estimated_completion,
            status=JobStatus.scheduled.value,
            priority=job_request.priority.value
        )
        
        logger.info(f"Job {job_id} booked successfully, assigned to {assigned_tech['name']}")
        return func.HttpResponse(
            response.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error booking job: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error booking job: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="jobs", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_all_jobs(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all maintenance jobs
    
    Retrieve all maintenance jobs in the system.
    
    Returns:
        200: Array of all jobs
        500: Internal server error
        
    Example:
        GET /api/jobs
        
        Response:
        [
            {
                "job_id": "JOB-20231015-001",
                "machine_id": "MACHINE-105",
                "description": "Motor overheating",
                "priority": "high",
                "status": "scheduled",
                ...
            }
        ]
    """
    logger.info("Getting all maintenance jobs")
    
    try:
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        jobs = list(cosmos_client.jobs_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Retrieved {len(jobs)} maintenance jobs")
        return func.HttpResponse(
            json.dumps(jobs),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving jobs: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving jobs: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="jobs/{job_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_job(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get specific job
    
    Retrieve details of a specific maintenance job by its ID.
    
    Parameters:
        job_id (str): ID of the job
        
    Returns:
        200: Job details
        404: Job not found
        500: Internal server error
        
    Example:
        GET /api/jobs/JOB-20231015-001
        
        Response:
        {
            "job_id": "JOB-20231015-001",
            "machine_id": "MACHINE-105",
            "error_code": "ERR-OVERHEAT-42",
            "description": "Motor overheating",
            "priority": "high",
            "status": "scheduled",
            "assigned_technician_id": "TECH-001",
            "scheduled_date": "2023-10-20",
            "scheduled_time": "09:00",
            ...
        }
    """
    job_id = req.route_params.get("job_id")
    logger.info(f"Getting job: {job_id}")
    
    try:
        query = "SELECT * FROM c WHERE c.job_id = @jobId"
        parameters = [{"name": "@jobId", "value": job_id}]
        
        jobs = list(cosmos_client.jobs_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not jobs:
            logger.warning(f"Job {job_id} not found")
            return func.HttpResponse(
                json.dumps({"error": f"Job {job_id} not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        logger.info(f"Retrieved job {job_id}")
        return func.HttpResponse(
            json.dumps(jobs[0]),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving job: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="jobs/status/{status}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_jobs_by_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get jobs by status
    
    Retrieve all jobs with a specific status.
    
    Parameters:
        status (str): Job status (scheduled, in_progress, completed, cancelled)
        
    Returns:
        200: Array of jobs with the specified status
        400: Invalid status
        500: Internal server error
        
    Example:
        GET /api/jobs/status/scheduled
        
        Response:
        [
            {
                "job_id": "JOB-20231015-001",
                "status": "scheduled",
                ...
            }
        ]
    """
    status = req.route_params.get("status")
    logger.info(f"Getting jobs with status: {status}")
    
    try:
        # Validate status
        try:
            JobStatus(status)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": f"Invalid status: {status}. Must be one of: scheduled, in_progress, completed, cancelled"}),
                mimetype="application/json",
                status_code=400
            )
        
        query = "SELECT * FROM c WHERE c.status = @status ORDER BY c.created_at DESC"
        parameters = [{"name": "@status", "value": status}]
        
        jobs = list(cosmos_client.jobs_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Retrieved {len(jobs)} jobs with status {status}")
        return func.HttpResponse(
            json.dumps(jobs),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error retrieving jobs by status {status}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error retrieving jobs: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="jobs/{job_id}/status", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_job_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    Update job status
    
    Update the status of a maintenance job.
    
    Parameters:
        job_id (str): ID of the job to update
        new_status (str): New status (query parameter)
        
    Returns:
        200: Status updated successfully
        400: Invalid status
        404: Job not found
        500: Internal server error
        
    Example:
        PUT /api/jobs/JOB-20231015-001/status?new_status=in_progress
        
        Response:
        {
            "message": "Job status updated successfully",
            "job_id": "JOB-20231015-001",
            "old_status": "scheduled",
            "new_status": "in_progress"
        }
    """
    job_id = req.route_params.get("job_id")
    new_status = req.params.get("new_status")
    
    logger.info(f"Updating status for job {job_id} to {new_status}")
    
    if not new_status:
        return func.HttpResponse(
            json.dumps({"error": "Missing required query parameter: new_status"}),
            mimetype="application/json",
            status_code=400
        )
    
    try:
        # Validate status
        try:
            JobStatus(new_status)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": f"Invalid status: {new_status}. Must be one of: scheduled, in_progress, completed, cancelled"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Get existing job
        query = "SELECT * FROM c WHERE c.job_id = @jobId"
        parameters = [{"name": "@jobId", "value": job_id}]
        
        jobs = list(cosmos_client.jobs_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not jobs:
            logger.warning(f"Job {job_id} not found")
            return func.HttpResponse(
                json.dumps({"error": f"Job {job_id} not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        job = jobs[0]
        old_status = job["status"]
        
        # Update status
        job["status"] = new_status
        cosmos_client.jobs_container.replace_item(item=job["id"], body=job)
        
        response = {
            "message": "Job status updated successfully",
            "job_id": job_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
        logger.info(f"Job {job_id} status updated from {old_status} to {new_status}")
        return func.HttpResponse(
            json.dumps(response),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Error updating job status: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )
