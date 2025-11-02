"""
Azure Function App - Industrial Inventory Management API

HTTP Triggers for inventory and reservation management operations with CosmosDB integration.
Provides endpoints for managing spare parts, checking stock levels, and creating reservations.
"""

import azure.functions as func
import logging
import json
import os
from typing import Optional, List
from datetime import datetime, timedelta
from models import (
    InventoryItem, 
    StockCheckResponse, 
    ReservationRequest, 
    ReservationResponse
)
from cosmos_client import get_cosmos_client
from azure.cosmos import exceptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Function App
app = func.FunctionApp()


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.function_name(name="health")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    
    Returns the health status of the Inventory API service.
    
    Returns:
        200: Service is healthy
        - Response body: {"status": "healthy", "service": "inventory-api"}
    
    Example:
        GET /api/
        Response: {"status": "healthy", "service": "inventory-api"}
    """
    logger.info('Health check request received')
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "inventory-api"}),
        mimetype="application/json",
        status_code=200
    )


# ============================================================================
# INVENTORY ITEM ENDPOINTS
# ============================================================================
# NOTE: Order matters! Specific routes (/inventory/low-stock, /inventory/category/{category})
# must be defined BEFORE parameterized routes (/inventory/{item_id}) to avoid conflicts

@app.function_name(name="get_all_inventory")
@app.route(route="inventory", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_all_inventory(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all inventory items
    
    Retrieve all items in the inventory with their current stock levels.
    
    Returns:
        200: Successfully retrieved inventory items
        - Response body: Array of InventoryItem objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/inventory
        Response: [
            {
                "item_id": "PART-001",
                "name": "Industrial Bearing SKF 6205",
                "category": "bearings",
                "stock_quantity": 45,
                "location": "Warehouse A - Shelf 12",
                "min_stock_level": 10,
                "unit_price": 25.50,
                "supplier": "SKF Industrial Supplies",
                "last_updated": "2023-10-15T14:30:00.000000"
            }
        ]
    """
    try:
        logger.info("GET /inventory - Retrieving all inventory items")
        
        container_name = os.getenv("AZURE_COSMOSDB_INVENTORY_CONTAINER", "inventory-items")
        container = get_cosmos_client().get_container(container_name)
        
        # Query all items
        query = "SELECT * FROM c"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"✓ Retrieved {len(items)} inventory items")
        
        # Convert to InventoryItem models for validation
        inventory_items = [InventoryItem(**item) for item in items]
        
        return func.HttpResponse(
            json.dumps([item.model_dump() for item in inventory_items]),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error retrieving inventory items: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_low_stock_items")
@app.route(route="inventory/low-stock", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_low_stock_items(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get items with low stock
    
    Retrieve all items that are at or below their minimum stock level.
    
    Returns:
        200: Successfully retrieved low stock items
        - Response body: Array of InventoryItem objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/inventory/low-stock
        Response: [
            {
                "item_id": "PART-002",
                "name": "Deep Groove Ball Bearing 6308",
                "category": "bearings",
                "stock_quantity": 8,
                "min_stock_level": 15,
                ...
            }
        ]
    """
    try:
        logger.info("GET /inventory/low-stock - Retrieving low stock items")
        
        container_name = os.getenv("AZURE_COSMOSDB_INVENTORY_CONTAINER", "inventory-items")
        container = get_cosmos_client().get_container(container_name)
        
        # Query items where stock is at or below minimum level
        query = "SELECT * FROM c WHERE c.stock_quantity <= c.min_stock_level"
        
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"✓ Retrieved {len(items)} low stock items")
        
        # Convert to InventoryItem models
        inventory_items = [InventoryItem(**item) for item in items]
        
        return func.HttpResponse(
            json.dumps([item.model_dump() for item in inventory_items]),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error retrieving low stock items: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_items_by_category")
@app.route(route="inventory/category/{category}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_items_by_category(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get items by category
    
    Retrieve all items belonging to a specific category.
    
    Path Parameters:
        category (str): Category name (bearings, motors, sensors, filters, seals, etc.)
    
    Returns:
        200: Successfully retrieved items in category
        - Response body: Array of InventoryItem objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/inventory/category/bearings
        Response: [
            {
                "item_id": "PART-001",
                "name": "Industrial Bearing SKF 6205",
                "category": "bearings",
                "stock_quantity": 45,
                ...
            }
        ]
    """
    try:
        category = req.route_params.get('category')
        logger.info(f"GET /inventory/category/{category} - Retrieving items by category")
        
        container_name = os.getenv("AZURE_COSMOSDB_INVENTORY_CONTAINER", "inventory-items")
        container = get_cosmos_client().get_container(container_name)
        
        # Query items in specific category (using partition key)
        query = "SELECT * FROM c WHERE c.category = @category"
        parameters = [{"name": "@category", "value": category}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=category,
            enable_cross_partition_query=False
        ))
        
        logger.info(f"✓ Retrieved {len(items)} items in category '{category}'")
        
        # Convert to InventoryItem models
        inventory_items = [InventoryItem(**item) for item in items]
        
        return func.HttpResponse(
            json.dumps([item.model_dump() for item in inventory_items]),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error retrieving items for category {category}: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="check_stock")
@app.route(route="inventory/{item_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def check_stock(req: func.HttpRequest) -> func.HttpResponse:
    """
    Check stock for specific item
    
    Check stock availability for a specific item by its ID.
    
    Path Parameters:
        item_id (str): Unique identifier of the inventory item
    
    Returns:
        200: Successfully retrieved stock information
        - Response body: StockCheckResponse object
        404: Item not found
        - Response body: {"error": "Item not found"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/inventory/PART-001
        Response: {
            "item_id": "PART-001",
            "available": true,
            "stock_quantity": 45,
            "location": "Warehouse A - Shelf 12",
            "estimated_delivery_days": null
        }
    """
    try:
        item_id = req.route_params.get('item_id')
        logger.info(f"GET /inventory/{item_id} - Checking stock")
        
        container_name = os.getenv("AZURE_COSMOSDB_INVENTORY_CONTAINER", "inventory-items")
        container = get_cosmos_client().get_container(container_name)
        
        # Query for specific item
        query = "SELECT * FROM c WHERE c.item_id = @itemId"
        parameters = [{"name": "@itemId", "value": item_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            logger.warning(f"✗ Item {item_id} not found")
            return func.HttpResponse(
                json.dumps({"error": "Item not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        item = items[0]
        
        # Create stock check response
        response = StockCheckResponse(
            item_id=item['item_id'],
            available=item['stock_quantity'] > 0,
            stock_quantity=item['stock_quantity'],
            location=item['location'] if item['stock_quantity'] > 0 else None,
            estimated_delivery_days=7 if item['stock_quantity'] == 0 else None
        )
        
        logger.info(f"✓ Stock check for {item_id}: {response.stock_quantity} units available")
        
        return func.HttpResponse(
            json.dumps(response.model_dump()),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error checking stock for {item_id}: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


# ============================================================================
# RESERVATION ENDPOINTS
# ============================================================================

@app.function_name(name="reserve_items")
@app.route(route="inventory/reserve", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def reserve_items(req: func.HttpRequest) -> func.HttpResponse:
    """
    Reserve items for maintenance
    
    Reserve inventory items for scheduled maintenance work.
    
    Request Body:
        ReservationRequest object with fields:
        - item_id: ID of item to reserve
        - quantity: Quantity to reserve
        - requested_by: Person requesting the reservation
        - work_order: Associated work order number
    
    Returns:
        200: Successfully created reservation
        - Response body: ReservationResponse object
        400: Invalid request or insufficient stock
        - Response body: {"error": "error message"}
        404: Item not found
        - Response body: {"error": "Item not found"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        POST /api/inventory/reserve
        Body: {
            "item_id": "PART-001",
            "quantity": 5,
            "requested_by": "John Technician",
            "work_order": "WO-2023-1001"
        }
        Response: {
            "reservation_id": "RES-20231001-001",
            "item_id": "PART-001",
            "quantity": 5,
            "status": "confirmed",
            "reserved_until": "2023-10-22T14:30:00.000000"
        }
    """
    try:
        logger.info("POST /inventory/reserve - Creating reservation")
        
        # Parse request body
        try:
            req_body = req.get_json()
            reservation_req = ReservationRequest(**req_body)
        except ValueError as e:
            logger.error(f"✗ Invalid request body: {e}")
            return func.HttpResponse(
                json.dumps({"error": f"Invalid request body: {str(e)}"}),
                mimetype="application/json",
                status_code=400
            )
        
        # Check if item exists and has sufficient stock
        inventory_container = get_cosmos_client().get_container(
            os.getenv("AZURE_COSMOSDB_INVENTORY_CONTAINER", "inventory-items")
        )
        
        query = "SELECT * FROM c WHERE c.item_id = @itemId"
        parameters = [{"name": "@itemId", "value": reservation_req.item_id}]
        
        items = list(inventory_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            logger.warning(f"✗ Item {reservation_req.item_id} not found")
            return func.HttpResponse(
                json.dumps({"error": "Item not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        item = items[0]
        
        if item['stock_quantity'] < reservation_req.quantity:
            logger.warning(
                f"✗ Insufficient stock for {reservation_req.item_id}: "
                f"requested {reservation_req.quantity}, available {item['stock_quantity']}"
            )
            return func.HttpResponse(
                json.dumps({
                    "error": f"Insufficient stock. Available: {item['stock_quantity']}, Requested: {reservation_req.quantity}"
                }),
                mimetype="application/json",
                status_code=400
            )
        
        # Create reservation
        reservation_container = get_cosmos_client().get_container(
            os.getenv("AZURE_COSMOSDB_RESERVATION_CONTAINER", "reservations")
        )
        
        # Generate reservation ID
        now = datetime.utcnow()
        reservation_id = f"RES-{now.strftime('%Y%m%d-%H%M%S')}"
        reserved_until = now + timedelta(days=7)
        
        reservation_doc = {
            "id": reservation_id,
            "reservation_id": reservation_id,
            "item_id": reservation_req.item_id,
            "quantity": reservation_req.quantity,
            "status": "confirmed",
            "reserved_until": reserved_until.isoformat(),
            "requested_by": reservation_req.requested_by,
            "work_order": reservation_req.work_order,
            "created_at": now.isoformat()
        }
        
        reservation_container.create_item(body=reservation_doc)
        
        response = ReservationResponse(
            reservation_id=reservation_id,
            item_id=reservation_req.item_id,
            quantity=reservation_req.quantity,
            status="confirmed",
            reserved_until=reserved_until.isoformat()
        )
        
        logger.info(f"✓ Created reservation {reservation_id} for {reservation_req.quantity}x {reservation_req.item_id}")
        
        return func.HttpResponse(
            json.dumps(response.model_dump()),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error creating reservation: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_all_reservations")
@app.route(route="reservations", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_all_reservations(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all active reservations
    
    Retrieve all active item reservations.
    
    Returns:
        200: Successfully retrieved reservations
        - Response body: Array of ReservationResponse objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/reservations
        Response: [
            {
                "reservation_id": "RES-20231001-001",
                "item_id": "PART-001",
                "quantity": 5,
                "status": "confirmed",
                "reserved_until": "2023-10-22T14:30:00.000000"
            }
        ]
    """
    try:
        logger.info("GET /reservations - Retrieving all reservations")
        
        container_name = os.getenv("AZURE_COSMOSDB_RESERVATION_CONTAINER", "reservations")
        container = get_cosmos_client().get_container(container_name)
        
        # Query all reservations
        query = "SELECT * FROM c"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"✓ Retrieved {len(items)} reservations")
        
        # Convert to ReservationResponse models
        reservations = [ReservationResponse(**item) for item in items]
        
        return func.HttpResponse(
            json.dumps([res.model_dump() for res in reservations]),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error retrieving reservations: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_reservation")
@app.route(route="reservations/{reservation_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_reservation(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get specific reservation
    
    Retrieve details of a specific reservation.
    
    Path Parameters:
        reservation_id (str): Unique identifier of the reservation
    
    Returns:
        200: Successfully retrieved reservation
        - Response body: ReservationResponse object
        404: Reservation not found
        - Response body: {"error": "Reservation not found"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/reservations/RES-20231001-001
        Response: {
            "reservation_id": "RES-20231001-001",
            "item_id": "PART-001",
            "quantity": 5,
            "status": "confirmed",
            "reserved_until": "2023-10-22T14:30:00.000000"
        }
    """
    try:
        reservation_id = req.route_params.get('reservation_id')
        logger.info(f"GET /reservations/{reservation_id} - Retrieving reservation")
        
        container_name = os.getenv("AZURE_COSMOSDB_RESERVATION_CONTAINER", "reservations")
        container = get_cosmos_client().get_container(container_name)
        
        # Query for specific reservation
        query = "SELECT * FROM c WHERE c.reservation_id = @reservationId"
        parameters = [{"name": "@reservationId", "value": reservation_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            logger.warning(f"✗ Reservation {reservation_id} not found")
            return func.HttpResponse(
                json.dumps({"error": "Reservation not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        reservation = ReservationResponse(**items[0])
        
        logger.info(f"✓ Retrieved reservation {reservation_id}")
        
        return func.HttpResponse(
            json.dumps(reservation.model_dump()),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"✗ Error retrieving reservation {reservation_id}: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )