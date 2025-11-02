# Maintenance API

Azure Function API for managing technician schedules and maintenance job bookings in manufacturing facilities.

## Features

- **Technician Management**: Track technicians, specializations, availability, and locations
- **Scheduling System**: Manage technician schedules and find available time slots
- **Job Booking**: Automatic technician assignment for maintenance jobs
- **Job Tracking**: Monitor job status from scheduling to completion
- **Priority Management**: Handle jobs by priority (low, medium, high, critical)

## Endpoints

### Health Check
- `GET /api/health` - Service health status

### Technician Operations
- `GET /api/technicians` - Get all technicians
- `GET /api/technicians/available` - Get only available technicians
- `GET /api/technicians/{technician_id}` - Get specific technician details

### Schedule Operations
- `GET /api/schedule/next-available` - Find next available maintenance slot
- `GET /api/schedule/technician/{technician_id}` - Get technician schedule (with ?days=N parameter)

### Job Operations
- `POST /api/jobs/book` - Book a new maintenance job
- `GET /api/jobs` - Get all maintenance jobs
- `GET /api/jobs/{job_id}` - Get specific job details
- `GET /api/jobs/status/{status}` - Get jobs by status (scheduled, in_progress, completed, cancelled)
- `PUT /api/jobs/{job_id}/status` - Update job status (with ?new_status= parameter)

## Database Schema

### IndustrialDB Database
- **technicians** container (partition key: `/technician_id`)
- **maintenance-jobs** container (partition key: `/job_id`)
- **schedule-slots** container (partition key: `/technician_id`)

## Environment Variables

```
AZURE_COSMOSDB_URI=https://<account>.documents.azure.com:443/
INDUSTRIAL_DATABASE_NAME=IndustrialDB
AZURE_COSMOSDB_TECHNICIANS_CONTAINER=technicians
AZURE_COSMOSDB_JOBS_CONTAINER=maintenance-jobs
AZURE_COSMOSDB_SCHEDULE_CONTAINER=schedule-slots
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `local.settings.json` with your CosmosDB credentials

3. Run the function:
```bash
func start --port 7075
```

4. Seed the database (from project root):
```bash
python seed_cosmosdb.py --database industrial
```

## Deployment

Deploy to Azure using:
```bash
func azure functionapp publish <function-app-name> --python
```

Or use GitHub Actions for CI/CD.

## Authentication

Uses Azure RBAC with `DefaultAzureCredential`:
- **Local**: Azure CLI credentials
- **Deployed**: Managed Identity

Ensure the identity has `Cosmos DB Built-in Data Contributor` role.

## Job Status Flow

```
scheduled → in_progress → completed
                      ↘ cancelled
```

## Priority Levels

- **low**: Routine maintenance
- **medium**: Standard repairs
- **high**: Important issues affecting production
- **critical**: Emergency repairs, production stopped
