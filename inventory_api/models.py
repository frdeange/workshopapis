"""
Data models for Industrial Inventory Management API

This module defines Pydantic models for inventory items, reservations,
and related data structures used in the inventory management system.
"""

from typing import Optional
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """
    Complete inventory item information
    
    Represents a spare part or component in the industrial inventory system.
    """
    item_id: str = Field(
        ..., 
        description="Unique identifier for the inventory item",
        example="PART-001"
    )
    name: str = Field(
        ..., 
        description="Name of the inventory item",
        example="Industrial Bearing SKF 6205"
    )
    category: str = Field(
        ..., 
        description="Category of the item (bearings, motors, sensors, filters, seals, etc.)",
        example="bearings"
    )
    stock_quantity: int = Field(
        ..., 
        description="Current quantity in stock",
        example=45
    )
    location: str = Field(
        ..., 
        description="Physical location in warehouse",
        example="Warehouse A - Shelf 12"
    )
    min_stock_level: int = Field(
        ..., 
        description="Minimum stock level threshold for reordering",
        example=10
    )
    unit_price: float = Field(
        ..., 
        description="Unit price in USD",
        example=25.50
    )
    supplier: str = Field(
        ..., 
        description="Supplier name",
        example="SKF Industrial Supplies"
    )
    last_updated: str = Field(
        ..., 
        description="ISO 8601 timestamp of last update",
        example="2023-10-15T14:30:00.000000"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
        }


class StockCheckResponse(BaseModel):
    """
    Response model for stock availability checks
    
    Provides availability status and additional information for an item.
    """
    item_id: str = Field(
        ..., 
        description="Item identifier",
        example="PART-001"
    )
    available: bool = Field(
        ..., 
        description="Whether item is available in stock",
        example=True
    )
    stock_quantity: int = Field(
        ..., 
        description="Current stock quantity",
        example=45
    )
    location: Optional[str] = Field(
        None, 
        description="Physical location if available",
        example="Warehouse A - Shelf 12"
    )
    estimated_delivery_days: Optional[int] = Field(
        None, 
        description="Estimated delivery days if out of stock",
        example=None
    )

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "PART-001",
                "available": True,
                "stock_quantity": 45,
                "location": "Warehouse A - Shelf 12",
                "estimated_delivery_days": None
            }
        }


class ReservationRequest(BaseModel):
    """
    Request model for creating an inventory reservation
    
    Used when maintenance work requires parts to be reserved.
    """
    item_id: str = Field(
        ..., 
        description="ID of the item to reserve",
        example="PART-001"
    )
    quantity: int = Field(
        ..., 
        description="Quantity to reserve",
        example=5,
        gt=0
    )
    requested_by: str = Field(
        ..., 
        description="Name or ID of person requesting reservation",
        example="John Technician"
    )
    work_order: str = Field(
        ..., 
        description="Associated work order number",
        example="WO-2023-1001"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "PART-001",
                "quantity": 5,
                "requested_by": "John Technician",
                "work_order": "WO-2023-1001"
            }
        }


class ReservationResponse(BaseModel):
    """
    Response model for reservation operations
    
    Provides details about a created or retrieved reservation.
    """
    reservation_id: str = Field(
        ..., 
        description="Unique reservation identifier",
        example="RES-20231001-001"
    )
    item_id: str = Field(
        ..., 
        description="ID of reserved item",
        example="PART-001"
    )
    quantity: int = Field(
        ..., 
        description="Quantity reserved",
        example=5
    )
    status: str = Field(
        ..., 
        description="Reservation status (confirmed, pending, cancelled)",
        example="confirmed"
    )
    reserved_until: str = Field(
        ..., 
        description="ISO 8601 timestamp when reservation expires",
        example="2023-10-22T14:30:00.000000"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reservation_id": "RES-20231001-001",
                "item_id": "PART-001",
                "quantity": 5,
                "status": "confirmed",
                "reserved_until": "2023-10-22T14:30:00.000000"
            }
        }
