# Industrial Inventory Management API

Azure Function API for managing spare parts and components inventory in manufacturing facilities.

## Overview

This API provides comprehensive inventory management capabilities including:
- Real-time stock level monitoring
- Category-based inventory organization
- Low stock alerts
- Reservation system for maintenance work
- Integration with Azure Cosmos DB

## Architecture

- **Runtime**: Python 3.11+
- **Framework**: Azure Functions
- **Database**: Azure Cosmos DB (IndustrialDB)
- **Authentication**: RBAC (Role-Based Access Control) via Azure AD

## Database Schema

### Collections

#### inventory-items
- **Partition Key**: `/category`
- **Purpose**: Store spare parts and components inventory
- **Fields**:
  - `item_id`: Unique identifier
  - `name`: Item name
  - `category`: bearings, motors, sensors, filters, seals, etc.
  - `stock_quantity`: Current stock level
  - `location`: Warehouse location
  - `min_stock_level`: Reorder threshold
  - `unit_price`: Price per unit (USD)
  - `supplier`: Supplier name
  - `last_updated`: ISO 8601 timestamp

#### reservations
- **Partition Key**: `/item_id`
- **Purpose**: Track inventory reservations for maintenance work
- **Fields**:
  - `reservation_id`: Unique identifier
  - `item_id`: Reserved item
  - `quantity`: Reserved quantity
  - `status`: confirmed, pending, cancelled
  - `reserved_until`: Expiration timestamp
  - `requested_by`: Requester name/ID
  - `work_order`: Associated work order
  - `created_at`: Creation timestamp

## API Endpoints

### Health Check

#### `GET /api/`
Check API health status.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "inventory-api"
}
```

### Inventory Endpoints

#### `GET /api/inventory`
Get all inventory items.

**Response**: `200 OK` - Array of inventory items

#### `GET /api/inventory/{item_id}`
Check stock for a specific item.

**Parameters**:
- `item_id` (path): Item identifier (e.g., "PART-001")

**Response**: `200 OK`
```json
{
  "item_id": "PART-001",
  "available": true,
  "stock_quantity": 45,
  "location": "Warehouse A - Shelf 12",
  "estimated_delivery_days": null
}
```

#### `GET /api/inventory/category/{category}`
Get all items in a specific category.

**Parameters**:
- `category` (path): Category name (e.g., "bearings", "motors", "sensors")

**Response**: `200 OK` - Array of inventory items in category

#### `GET /api/inventory/low-stock`
Get items at or below minimum stock level.

**Response**: `200 OK` - Array of low stock items

### Reservation Endpoints

#### `POST /api/inventory/reserve`
Create a new reservation.

**Request Body**:
```json
{
  "item_id": "PART-001",
  "quantity": 5,
  "requested_by": "John Technician",
  "work_order": "WO-2023-1001"
}
```

**Response**: `200 OK`
```json
{
  "reservation_id": "RES-20231001-001",
  "item_id": "PART-001",
  "quantity": 5,
  "status": "confirmed",
  "reserved_until": "2023-10-22T14:30:00.000000"
}
```

**Error Responses**:
- `404`: Item not found
- `400`: Insufficient stock
- `500`: Server error

#### `GET /api/reservations`
Get all active reservations.

**Response**: `200 OK` - Array of reservations

#### `GET /api/reservations/{reservation_id}`
Get specific reservation details.

**Parameters**:
- `reservation_id` (path): Reservation identifier

**Response**: `200 OK` - Reservation object

## Environment Variables

Configure these in `local.settings.json` for local development:

```json
{
  "FUNCTIONS_WORKER_RUNTIME": "python",
  "AZURE_COSMOSDB_URI": "https://your-cosmos.documents.azure.com:443/",
  "AZURE_COSMOSDB_KEY": "your-key-here",
  "INDUSTRIAL_DATABASE_NAME": "IndustrialDB",
  "AZURE_COSMOSDB_INVENTORY_CONTAINER": "inventory-items",
  "AZURE_COSMOSDB_RESERVATION_CONTAINER": "reservations"
}
```

For production deployments, use:
- **RBAC authentication** (recommended): Configure managed identity
- **Key-based authentication** (alternative): Set `AZURE_COSMOSDB_KEY`

## Local Development

### Prerequisites
- Python 3.11+
- Azure Functions Core Tools
- Azure CLI (authenticated)
- Access to Azure Cosmos DB

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure settings**:
   - Copy `local.settings.json.example` to `local.settings.json`
   - Update Cosmos DB connection details

3. **Seed database** (first time only):
   ```bash
   python ../seed_cosmosdb.py
   ```

4. **Run locally**:
   ```bash
   func start
   ```

5. **Test endpoints**:
   ```bash
   # Health check
   curl http://localhost:7071/api/
   
   # Get all inventory
   curl http://localhost:7071/api/inventory
   
   # Check specific item
   curl http://localhost:7071/api/inventory/PART-001
   
   # Get items by category
   curl http://localhost:7071/api/inventory/category/bearings
   
   # Get low stock items
   curl http://localhost:7071/api/inventory/low-stock
   
   # Create reservation
   curl -X POST http://localhost:7071/api/inventory/reserve \
     -H "Content-Type: application/json" \
     -d '{
       "item_id": "PART-001",
       "quantity": 5,
       "requested_by": "Test User",
       "work_order": "WO-TEST-001"
     }'
   ```

## Deployment

### Azure Function App

1. **Create Function App**:
   ```bash
   az functionapp create \
     --name inventory-api-func \
     --resource-group your-rg \
     --storage-account yourstorage \
     --runtime python \
     --runtime-version 3.11 \
     --functions-version 4
   ```

2. **Configure Managed Identity**:
   ```bash
   az functionapp identity assign \
     --name inventory-api-func \
     --resource-group your-rg
   ```

3. **Grant Cosmos DB Access**:
   ```bash
   az cosmosdb sql role assignment create \
     --account-name your-cosmos \
     --resource-group your-rg \
     --scope "/" \
     --principal-id <managed-identity-principal-id> \
     --role-definition-id 00000000-0000-0000-0000-000000000002
   ```

4. **Deploy**:
   ```bash
   func azure functionapp publish inventory-api-func
   ```

### API Management (APIM)

To expose this API through Azure API Management:

1. **Import OpenAPI Spec**:
   - Use the `openapi-spec.json` file
   - Configure backend to point to Function App

2. **Configure Policies**:
   - Rate limiting
   - Authentication (subscription keys, OAuth, etc.)
   - Response caching for read operations

3. **Set up Products**:
   - Create product for internal/external access
   - Assign subscription keys

## Models

### InventoryItem
Complete inventory item with stock and location details.

### StockCheckResponse
Availability status with location and delivery estimates.

### ReservationRequest
Request to reserve items for maintenance work.

### ReservationResponse
Confirmed reservation with expiration details.

## Error Handling

All endpoints return standard error responses:

```json
{
  "error": "Error description"
}
```

Status codes:
- `200`: Success
- `400`: Bad request (validation errors, insufficient stock)
- `404`: Resource not found
- `500`: Internal server error

## Logging

All operations are logged with:
- Request details (endpoint, parameters)
- Operation results (success/failure)
- Error details for troubleshooting

Logs are available in:
- Local: Console output
- Azure: Application Insights

## Security

- **Authentication**: Azure AD RBAC (production) or Key-based (development)
- **Authorization**: Function-level controls via `auth_level`
- **Data Encryption**: At rest (Cosmos DB) and in transit (HTTPS)
- **Secret Management**: Azure Key Vault for production credentials

## Future Enhancements

- [ ] Implement reservation cancellation endpoint
- [ ] Add inventory update/adjustment endpoints
- [ ] Implement automatic reordering for low stock
- [ ] Add historical tracking for stock movements
- [ ] Integrate with maintenance scheduling API
- [ ] Add analytics for inventory turnover
- [ ] Implement barcode/QR code scanning support

## Support

For issues or questions:
- Check logs in Application Insights
- Review Cosmos DB metrics for performance issues
- Validate environment variable configuration
- Ensure database is seeded with initial data

## License

Internal use only - Banking APIs Workshop Project
