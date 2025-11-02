#!/usr/bin/env python3
"""
CosmosDB Seed Data Script

This script populates the CosmosDB database with initial dummy data
for all containers: accounts, payment-methods, beneficiaries, and transactions.

Usage:
    python seed_cosmosdb.py

Requirements:
    - Azure CLI authenticated OR
    - Environment variables set for service principal/managed identity
    - CosmosDB account created with proper RBAC permissions
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CosmosDBSeeder:
    """Handles seeding of CosmosDB with initial data."""
    
    def __init__(self, database_name=None, env_var_name="BANKING_DATABASE_NAME"):
        """Initialize CosmosDB client with key or RBAC authentication."""
        self.endpoint = os.getenv("AZURE_COSMOSDB_URI")
        self.database_name = database_name or os.getenv(env_var_name, "BankingDB")
        self.key = os.getenv("AZURE_COSMOSDB_KEY")
        
        if not self.endpoint:
            raise ValueError("AZURE_COSMOSDB_URI environment variable is not set")
        
        logger.info("Initializing CosmosDB client for seeding")
        logger.info(f"Endpoint: {self.endpoint}")
        logger.info(f"Database: {self.database_name}")
        
        # Use key if available, otherwise fall back to RBAC
        if self.key:
            logger.info("Using CosmosDB key authentication")
            self.client = CosmosClient(url=self.endpoint, credential=self.key)
        else:
            logger.info("Using DefaultAzureCredential (RBAC) authentication")
            credential = DefaultAzureCredential()
            self.client = CosmosClient(url=self.endpoint, credential=credential)
        
        # Initialize database (will be created in setup_database_and_containers)
        self.database = None
    
    def setup_database_and_containers(self):
        """Create database and containers if they don't exist."""
        logger.info("Setting up database and containers...")
        
        # Create database if it doesn't exist
        logger.info(f"Creating database '{self.database_name}' if it doesn't exist...")
        database = self.client.create_database_if_not_exists(id=self.database_name)
        self.database = database
        logger.info(f"✓ Database '{self.database_name}' ready")
        
        # Define containers with their partition keys
        containers_config = [
            {"name": "accounts", "partition_key": "/userName"},
            {"name": "payment-methods", "partition_key": "/accountId"},
            {"name": "beneficiaries", "partition_key": "/accountId"},
            {"name": "transactions", "partition_key": "/accountId"}
        ]
        
        # Create containers if they don't exist
        for config in containers_config:
            logger.info(f"Creating container '{config['name']}' if it doesn't exist...")
            try:
                container = database.create_container_if_not_exists(
                    id=config["name"],
                    partition_key={"paths": [config["partition_key"]], "kind": "Hash"}
                )
                logger.info(f"✓ Container '{config['name']}' ready with partition key {config['partition_key']}")
            except Exception as e:
                logger.error(f"✗ Failed to create container '{config['name']}': {e}")
                raise
    
    def seed_all(self):
        """Seed all containers with initial data."""
        logger.info("=" * 60)
        logger.info("Starting CosmosDB seeding process")
        logger.info("=" * 60)
        
        try:
            # First, ensure database and containers exist
            self.setup_database_and_containers()
            
            # Then seed the data
            self.seed_accounts()
            self.seed_payment_methods()
            self.seed_beneficiaries()
            self.seed_transactions()
            
            logger.info("=" * 60)
            logger.info("✓ CosmosDB seeding completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            raise
    
    def seed_accounts(self):
        """Seed the accounts container."""
        container_name = os.getenv("AZURE_COSMOSDB_ACCOUNT_CONTAINER", "accounts")
        logger.info(f"\n--- Seeding {container_name} container ---")
        container = self.database.get_container_client(container_name)
        
        accounts = [
            {
                "id": "1000",
                "userName": "alice.user@contoso.com",
                "accountHolderFullName": "Alice User",
                "currency": "USD",
                "activationDate": "2022-01-01",
                "balance": "5000"
            },
            {
                "id": "1010",
                "userName": "bob.user@contoso.com",
                "accountHolderFullName": "Bob User",
                "currency": "EUR",
                "activationDate": "2022-01-01",
                "balance": "10000"
            },
            {
                "id": "1020",
                "userName": "charlie.user@contoso.com",
                "accountHolderFullName": "Charlie User",
                "currency": "EUR",
                "activationDate": "2022-01-01",
                "balance": "3000"
            }
        ]
        
        for account in accounts:
            try:
                container.upsert_item(account)
                logger.info(f"✓ Seeded account: {account['id']} - {account['userName']}")
            except Exception as e:
                logger.error(f"✗ Failed to seed account {account['id']}: {e}")
    
    def seed_payment_methods(self):
        """Seed the payment-methods container."""
        container_name = os.getenv("AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER", "payment-methods")
        logger.info(f"\n--- Seeding {container_name} container ---")
        container = self.database.get_container_client(container_name)
        
        payment_methods = [
            # Account 1000 - Alice
            {
                "id": "12345",
                "accountId": "1000",
                "type": "Visa",
                "activationDate": "2022-01-01",
                "expirationDate": "2025-01-01",
                "availableBalance": "500.00",
                "cardNumber": "1234567812345678"
            },
            {
                "id": "23456",
                "accountId": "1000",
                "type": "BankTransfer",
                "activationDate": "2022-01-01",
                "expirationDate": "9999-01-01",
                "availableBalance": "5000.00",
                "cardNumber": None
            },
            # Account 1010 - Bob
            {
                "id": "345678",
                "accountId": "1010",
                "type": "BankTransfer",
                "activationDate": "2022-01-01",
                "expirationDate": "9999-01-01",
                "availableBalance": "10000.00",
                "cardNumber": None
            },
            {
                "id": "55555",
                "accountId": "1010",
                "type": "Visa",
                "activationDate": "2024-01-01",
                "expirationDate": "2028-01-01",
                "availableBalance": "350.00",
                "cardNumber": "637362551913266"
            },
            # Account 1020 - Charlie
            {
                "id": "46748576",
                "accountId": "1020",
                "type": "DirectDebit",
                "activationDate": "2022-02-01",
                "expirationDate": "9999-02-01",
                "availableBalance": "3000.00",
                "cardNumber": None
            }
        ]
        
        for pm in payment_methods:
            try:
                container.upsert_item(pm)
                logger.info(f"✓ Seeded payment method: {pm['id']} ({pm['type']}) for account {pm['accountId']}")
            except Exception as e:
                logger.error(f"✗ Failed to seed payment method {pm['id']}: {e}")
    
    def seed_beneficiaries(self):
        """Seed the beneficiaries container."""
        container_name = os.getenv("AZURE_COSMOSDB_BENEFICIARY_CONTAINER", "beneficiaries")
        logger.info(f"\n--- Seeding {container_name} container ---")
        container = self.database.get_container_client(container_name)
        
        beneficiaries = [
            # Account 1000 - Alice
            {
                "id": "1",
                "accountId": "1000",
                "fullName": "Mike ThePlumber",
                "bankCode": "123456789",
                "bankName": "Intesa Sanpaolo"
            },
            {
                "id": "2",
                "accountId": "1000",
                "fullName": "Jane TheElectrician",
                "bankCode": "987654321",
                "bankName": "UBS"
            },
            # Account 1010 - Bob
            {
                "id": "3",
                "accountId": "1010",
                "fullName": "Sarah TheAccountant",
                "bankCode": "555123456",
                "bankName": "Deutsche Bank"
            },
            {
                "id": "4",
                "accountId": "1010",
                "fullName": "Tom TheLawyer",
                "bankCode": "777888999",
                "bankName": "HSBC"
            },
            # Account 1020 - Charlie
            {
                "id": "5",
                "accountId": "1020",
                "fullName": "Lisa TheDoctor",
                "bankCode": "111222333",
                "bankName": "BNP Paribas"
            }
        ]
        
        for beneficiary in beneficiaries:
            try:
                container.upsert_item(beneficiary)
                logger.info(f"✓ Seeded beneficiary: {beneficiary['id']} - {beneficiary['fullName']} for account {beneficiary['accountId']}")
            except Exception as e:
                logger.error(f"✗ Failed to seed beneficiary {beneficiary['id']}: {e}")
    
    def seed_transactions(self):
        """Seed the transactions container."""
        container_name = os.getenv("AZURE_COSMOSDB_TRANSACTION_CONTAINER", "transactions")
        logger.info(f"\n--- Seeding {container_name} container ---")
        container = self.database.get_container_client(container_name)
        
        transactions = [
            # Account 1010 - Bob (sample transactions)
            {
                "id": "11",
                "accountId": "1010",
                "description": "Payment of the bill 334398",
                "type": "outcome",
                "recipientName": "acme",
                "recipientBankReference": "098734213",
                "paymentType": "BankTransfer",
                "amount": -120.00,
                "timestamp": "2023-06-15T09:15:00"
            },
            {
                "id": "12",
                "accountId": "1010",
                "description": "Salary",
                "type": "income",
                "recipientName": "Contoso Corp",
                "recipientBankReference": "123456789",
                "paymentType": "BankTransfer",
                "amount": 3000.00,
                "timestamp": "2023-06-01T08:00:00"
            },
            {
                "id": "13",
                "accountId": "1010",
                "description": "Groceries at SuperMart",
                "type": "outcome",
                "recipientName": "SuperMart",
                "recipientBankReference": "555666777",
                "paymentType": "Visa",
                "amount": -85.50,
                "timestamp": "2023-06-10T18:30:00"
            },
            {
                "id": "14",
                "accountId": "1010",
                "description": "Electric bill payment",
                "type": "outcome",
                "recipientName": "PowerCo Utilities",
                "recipientBankReference": "111222333",
                "paymentType": "BankTransfer",
                "amount": -75.20,
                "timestamp": "2023-05-25T14:00:00"
            },
            {
                "id": "15",
                "accountId": "1010",
                "description": "Freelance project payment",
                "type": "income",
                "recipientName": "Tech Solutions Inc",
                "recipientBankReference": "444555666",
                "paymentType": "BankTransfer",
                "amount": 1500.00,
                "timestamp": "2023-05-20T10:30:00"
            },
            # Account 1000 - Alice (sample transactions)
            {
                "id": "20",
                "accountId": "1000",
                "description": "Monthly rent payment",
                "type": "outcome",
                "recipientName": "Property Management LLC",
                "recipientBankReference": "999888777",
                "paymentType": "BankTransfer",
                "amount": -1200.00,
                "timestamp": "2023-06-01T10:00:00"
            },
            {
                "id": "21",
                "accountId": "1000",
                "description": "Salary deposit",
                "type": "income",
                "recipientName": "Acme Corporation",
                "recipientBankReference": "123123123",
                "paymentType": "BankTransfer",
                "amount": 4500.00,
                "timestamp": "2023-06-01T09:00:00"
            },
            # Account 1020 - Charlie (sample transactions)
            {
                "id": "30",
                "accountId": "1020",
                "description": "Online shopping",
                "type": "outcome",
                "recipientName": "Amazon",
                "recipientBankReference": "456456456",
                "paymentType": "DirectDebit",
                "amount": -150.75,
                "timestamp": "2023-06-12T15:30:00"
            }
        ]
        
        for txn in transactions:
            try:
                container.upsert_item(txn)
                logger.info(f"✓ Seeded transaction: {txn['id']} - {txn['description']} for account {txn['accountId']}")
            except Exception as e:
                logger.error(f"✗ Failed to seed transaction {txn['id']}: {e}")


class IndustrialDBSeeder(CosmosDBSeeder):
    """Handles seeding of IndustrialDB with inventory and maintenance data."""
    
    def __init__(self):
        """Initialize with IndustrialDB database."""
        super().__init__(database_name="IndustrialDB", env_var_name="INDUSTRIAL_DATABASE_NAME")
    
    def setup_database_and_containers(self):
        """Create database and containers for industrial data."""
        logger.info("Setting up IndustrialDB database and containers...")
        
        # Create database if it doesn't exist
        logger.info(f"Creating database '{self.database_name}' if it doesn't exist...")
        database = self.client.create_database_if_not_exists(id=self.database_name)
        self.database = database
        logger.info(f"✓ Database '{self.database_name}' ready")
        
        # Define containers with their partition keys
        containers_config = [
            {"name": "inventory-items", "partition_key": "/category"},
            {"name": "reservations", "partition_key": "/item_id"},
            {"name": "technicians", "partition_key": "/technician_id"},
            {"name": "maintenance-jobs", "partition_key": "/job_id"},
            {"name": "schedule-slots", "partition_key": "/technician_id"}
        ]
        
        # Create containers if they don't exist
        for config in containers_config:
            logger.info(f"Creating container '{config['name']}' if it doesn't exist...")
            try:
                container = database.create_container_if_not_exists(
                    id=config["name"],
                    partition_key={"paths": [config["partition_key"]], "kind": "Hash"}
                )
                logger.info(f"✓ Container '{config['name']}' ready with partition key {config['partition_key']}")
            except Exception as e:
                logger.error(f"✗ Failed to create container '{config['name']}': {e}")
                raise
    
    def seed_all(self):
        """Seed all industrial containers with initial data."""
        logger.info("=" * 60)
        logger.info("Starting IndustrialDB seeding process")
        logger.info("=" * 60)
        
        try:
            # First, ensure database and containers exist
            self.setup_database_and_containers()
            
            # Then seed the data
            self.seed_inventory_items()
            self.seed_reservations()
            self.seed_technicians()
            self.seed_maintenance_jobs()
            self.seed_schedule_slots()
            
            logger.info("=" * 60)
            logger.info("✓ IndustrialDB seeding completed successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            raise
    
    def seed_inventory_items(self):
        """Seed the inventory-items container."""
        logger.info(f"\n--- Seeding inventory-items container ---")
        container = self.database.get_container_client("inventory-items")
        
        items = [
            # Bearings category
            {
                "id": "PART-001",
                "item_id": "PART-001",
                "name": "Industrial Bearing SKF 6205",
                "category": "bearings",
                "stock_quantity": 45,
                "location": "Warehouse A - Shelf 12",
                "min_stock_level": 10,
                "unit_price": 25.50,
                "supplier": "SKF Industrial Supplies",
                "last_updated": "2023-10-15T14:30:00.000000"
            },
            {
                "id": "PART-002",
                "item_id": "PART-002",
                "name": "Deep Groove Ball Bearing 6308",
                "category": "bearings",
                "stock_quantity": 8,
                "location": "Warehouse A - Shelf 13",
                "min_stock_level": 15,
                "unit_price": 42.00,
                "supplier": "SKF Industrial Supplies",
                "last_updated": "2023-10-14T10:20:00.000000"
            },
            {
                "id": "PART-003",
                "item_id": "PART-003",
                "name": "Tapered Roller Bearing 30208",
                "category": "bearings",
                "stock_quantity": 22,
                "location": "Warehouse A - Shelf 14",
                "min_stock_level": 12,
                "unit_price": 38.75,
                "supplier": "Timken Bearings Ltd",
                "last_updated": "2023-10-13T16:45:00.000000"
            },
            # Motors category
            {
                "id": "PART-004",
                "item_id": "PART-004",
                "name": "AC Induction Motor 3-Phase 5HP",
                "category": "motors",
                "stock_quantity": 12,
                "location": "Warehouse B - Section 3",
                "min_stock_level": 5,
                "unit_price": 450.00,
                "supplier": "Siemens Motors",
                "last_updated": "2023-10-12T09:00:00.000000"
            },
            {
                "id": "PART-005",
                "item_id": "PART-005",
                "name": "Hydraulic Pump Motor 2HP",
                "category": "motors",
                "stock_quantity": 3,
                "location": "Warehouse B - Section 4",
                "min_stock_level": 5,
                "unit_price": 380.00,
                "supplier": "Parker Hannifin",
                "last_updated": "2023-10-11T11:30:00.000000"
            },
            {
                "id": "PART-006",
                "item_id": "PART-006",
                "name": "Servo Motor 1.5kW",
                "category": "motors",
                "stock_quantity": 7,
                "location": "Warehouse B - Section 5",
                "min_stock_level": 4,
                "unit_price": 620.00,
                "supplier": "ABB Motors",
                "last_updated": "2023-10-10T14:15:00.000000"
            },
            # Sensors category
            {
                "id": "PART-007",
                "item_id": "PART-007",
                "name": "Proximity Sensor M18 Inductive",
                "category": "sensors",
                "stock_quantity": 35,
                "location": "Warehouse C - Bin 22",
                "min_stock_level": 20,
                "unit_price": 45.00,
                "supplier": "Omron Electronics",
                "last_updated": "2023-10-09T08:45:00.000000"
            },
            {
                "id": "PART-008",
                "item_id": "PART-008",
                "name": "Temperature Sensor PT100 RTD",
                "category": "sensors",
                "stock_quantity": 18,
                "location": "Warehouse C - Bin 23",
                "min_stock_level": 15,
                "unit_price": 35.50,
                "supplier": "Honeywell Sensing",
                "last_updated": "2023-10-08T13:20:00.000000"
            },
            {
                "id": "PART-009",
                "item_id": "PART-009",
                "name": "Pressure Transducer 0-100 PSI",
                "category": "sensors",
                "stock_quantity": 25,
                "location": "Warehouse C - Bin 24",
                "min_stock_level": 10,
                "unit_price": 85.00,
                "supplier": "Honeywell Sensing",
                "last_updated": "2023-10-07T15:00:00.000000"
            },
            # Filters category
            {
                "id": "PART-010",
                "item_id": "PART-010",
                "name": "Hydraulic Oil Filter 10 Micron",
                "category": "filters",
                "stock_quantity": 60,
                "location": "Warehouse D - Row 5",
                "min_stock_level": 30,
                "unit_price": 18.50,
                "supplier": "Pall Corporation",
                "last_updated": "2023-10-06T10:30:00.000000"
            },
            {
                "id": "PART-011",
                "item_id": "PART-011",
                "name": "Air Filter Cartridge HEPA",
                "category": "filters",
                "stock_quantity": 5,
                "location": "Warehouse D - Row 6",
                "min_stock_level": 12,
                "unit_price": 52.00,
                "supplier": "Donaldson Filters",
                "last_updated": "2023-10-05T12:00:00.000000"
            },
            # Seals category
            {
                "id": "PART-012",
                "item_id": "PART-012",
                "name": "O-Ring NBR 50mm ID",
                "category": "seals",
                "stock_quantity": 120,
                "location": "Warehouse A - Drawer 8",
                "min_stock_level": 50,
                "unit_price": 2.50,
                "supplier": "Parker O-Ring Division",
                "last_updated": "2023-10-04T09:15:00.000000"
            },
            {
                "id": "PART-013",
                "item_id": "PART-013",
                "name": "Shaft Seal 35x52x7mm",
                "category": "seals",
                "stock_quantity": 32,
                "location": "Warehouse A - Drawer 9",
                "min_stock_level": 20,
                "unit_price": 8.75,
                "supplier": "SKF Sealing Solutions",
                "last_updated": "2023-10-03T11:40:00.000000"
            }
        ]
        
        for item in items:
            try:
                container.upsert_item(item)
                logger.info(f"✓ Seeded inventory item: {item['item_id']} - {item['name']} (Stock: {item['stock_quantity']})")
            except Exception as e:
                logger.error(f"✗ Failed to seed item {item['item_id']}: {e}")
    
    def seed_reservations(self):
        """Seed the reservations container."""
        logger.info(f"\n--- Seeding reservations container ---")
        container = self.database.get_container_client("reservations")
        
        reservations = [
            {
                "id": "RES-20231001-001",
                "reservation_id": "RES-20231001-001",
                "item_id": "PART-001",
                "quantity": 5,
                "status": "confirmed",
                "reserved_until": "2023-10-22T14:30:00.000000",
                "requested_by": "John Technician",
                "work_order": "WO-2023-1001",
                "created_at": "2023-10-15T14:30:00.000000"
            },
            {
                "id": "RES-20231002-001",
                "reservation_id": "RES-20231002-001",
                "item_id": "PART-004",
                "quantity": 2,
                "status": "confirmed",
                "reserved_until": "2023-10-25T10:00:00.000000",
                "requested_by": "Sarah Engineer",
                "work_order": "WO-2023-1045",
                "created_at": "2023-10-18T10:00:00.000000"
            },
            {
                "id": "RES-20231003-001",
                "reservation_id": "RES-20231003-001",
                "item_id": "PART-007",
                "quantity": 10,
                "status": "confirmed",
                "reserved_until": "2023-10-28T08:00:00.000000",
                "requested_by": "Mike Electrician",
                "work_order": "WO-2023-1078",
                "created_at": "2023-10-21T08:00:00.000000"
            }
        ]
        
        for reservation in reservations:
            try:
                container.upsert_item(reservation)
                logger.info(f"✓ Seeded reservation: {reservation['reservation_id']} - {reservation['quantity']}x {reservation['item_id']}")
            except Exception as e:
                logger.error(f"✗ Failed to seed reservation {reservation['reservation_id']}: {e}")
    
    def seed_technicians(self):
        """Seed the technicians container."""
        logger.info(f"\n--- Seeding technicians container ---")
        container = self.database.get_container_client("technicians")
        
        technicians = [
            {
                "id": "TECH-001",
                "technician_id": "TECH-001",
                "name": "John Smith",
                "specialization": ["Electrical", "HVAC"],
                "skill_level": "Senior",
                "status": "available",
                "current_location": "Factory Floor A",
                "contact_phone": "+1-555-0123"
            },
            {
                "id": "TECH-002",
                "technician_id": "TECH-002",
                "name": "Sarah Johnson",
                "specialization": ["Mechanical", "Hydraulics"],
                "skill_level": "Expert",
                "status": "available",
                "current_location": "Warehouse B",
                "contact_phone": "+1-555-0124"
            },
            {
                "id": "TECH-003",
                "technician_id": "TECH-003",
                "name": "Michael Chen",
                "specialization": ["Electronics", "Automation"],
                "skill_level": "Senior",
                "status": "busy",
                "current_location": "Production Line 3",
                "contact_phone": "+1-555-0125"
            },
            {
                "id": "TECH-004",
                "technician_id": "TECH-004",
                "name": "Emily Rodriguez",
                "specialization": ["Pneumatics", "Mechanical"],
                "skill_level": "Junior",
                "status": "available",
                "current_location": "Maintenance Shop",
                "contact_phone": "+1-555-0126"
            },
            {
                "id": "TECH-005",
                "technician_id": "TECH-005",
                "name": "David Williams",
                "specialization": ["Electrical", "PLC Programming"],
                "skill_level": "Expert",
                "status": "off_duty",
                "current_location": "Off Site",
                "contact_phone": "+1-555-0127"
            }
        ]
        
        for tech in technicians:
            try:
                container.upsert_item(tech)
                logger.info(f"✓ Seeded technician: {tech['technician_id']} - {tech['name']} ({tech['status']})")
            except Exception as e:
                logger.error(f"✗ Failed to seed technician {tech['technician_id']}: {e}")
    
    def seed_maintenance_jobs(self):
        """Seed the maintenance-jobs container."""
        logger.info(f"\n--- Seeding maintenance-jobs container ---")
        container = self.database.get_container_client("maintenance-jobs")
        
        jobs = [
            {
                "id": "JOB-20231015-001",
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
                "notes": "Requested by: Plant Manager. Customer reported unusual noise."
            },
            {
                "id": "JOB-20231016-001",
                "job_id": "JOB-20231016-001",
                "machine_id": "MACHINE-203",
                "error_code": "ERR-LEAK-15",
                "description": "Hydraulic system leak in main cylinder",
                "priority": "critical",
                "estimated_duration_hours": 4.0,
                "assigned_technician_id": "TECH-002",
                "scheduled_date": "2023-10-18",
                "scheduled_time": "08:00",
                "status": "in_progress",
                "created_at": "2023-10-16T08:15:00.000000",
                "notes": "Requested by: Shift Supervisor. Production halted."
            },
            {
                "id": "JOB-20231014-001",
                "job_id": "JOB-20231014-001",
                "machine_id": "MACHINE-087",
                "error_code": None,
                "description": "Scheduled preventive maintenance - lubrication and inspection",
                "priority": "low",
                "estimated_duration_hours": 2.0,
                "assigned_technician_id": "TECH-004",
                "scheduled_date": "2023-10-14",
                "scheduled_time": "10:00",
                "status": "completed",
                "created_at": "2023-10-10T09:00:00.000000",
                "notes": "Requested by: Maintenance Scheduler. Monthly PM."
            },
            {
                "id": "JOB-20231017-001",
                "job_id": "JOB-20231017-001",
                "machine_id": "MACHINE-156",
                "error_code": "ERR-SENSOR-09",
                "description": "Proximity sensor malfunction on conveyor belt",
                "priority": "medium",
                "estimated_duration_hours": 1.5,
                "assigned_technician_id": "TECH-003",
                "scheduled_date": "2023-10-19",
                "scheduled_time": "13:00",
                "status": "scheduled",
                "created_at": "2023-10-17T11:20:00.000000",
                "notes": "Requested by: Line Operator. Sensor needs replacement."
            },
            {
                "id": "JOB-20231012-001",
                "job_id": "JOB-20231012-001",
                "machine_id": "MACHINE-045",
                "error_code": "ERR-VIBRATION-33",
                "description": "Excessive vibration in main spindle",
                "priority": "high",
                "estimated_duration_hours": 5.0,
                "assigned_technician_id": "TECH-001",
                "scheduled_date": "2023-10-13",
                "scheduled_time": "07:00",
                "status": "cancelled",
                "created_at": "2023-10-12T15:45:00.000000",
                "notes": "Requested by: QA Inspector. Cancelled - issue resolved itself after restart."
            }
        ]
        
        for job in jobs:
            try:
                container.upsert_item(job)
                logger.info(f"✓ Seeded job: {job['job_id']} - {job['machine_id']} ({job['status']})")
            except Exception as e:
                logger.error(f"✗ Failed to seed job {job['job_id']}: {e}")
    
    def seed_schedule_slots(self):
        """Seed the schedule-slots container."""
        logger.info(f"\n--- Seeding schedule-slots container ---")
        container = self.database.get_container_client("schedule-slots")
        
        slots = [
            # TECH-001 slots
            {
                "id": "SLOT-20231020-001",
                "slot_id": "SLOT-20231020-001",
                "technician_id": "TECH-001",
                "date": "2023-10-20",
                "start_time": "09:00",
                "end_time": "17:00",
                "available": False,
                "location": "Factory Floor A"
            },
            {
                "id": "SLOT-20231021-001",
                "slot_id": "SLOT-20231021-001",
                "technician_id": "TECH-001",
                "date": "2023-10-21",
                "start_time": "09:00",
                "end_time": "17:00",
                "available": True,
                "location": "Factory Floor A"
            },
            {
                "id": "SLOT-20231022-001",
                "slot_id": "SLOT-20231022-001",
                "technician_id": "TECH-001",
                "date": "2023-10-22",
                "start_time": "09:00",
                "end_time": "17:00",
                "available": True,
                "location": "Factory Floor A"
            },
            # TECH-002 slots
            {
                "id": "SLOT-20231018-002",
                "slot_id": "SLOT-20231018-002",
                "technician_id": "TECH-002",
                "date": "2023-10-18",
                "start_time": "08:00",
                "end_time": "16:00",
                "available": False,
                "location": "Warehouse B"
            },
            {
                "id": "SLOT-20231019-002",
                "slot_id": "SLOT-20231019-002",
                "technician_id": "TECH-002",
                "date": "2023-10-19",
                "start_time": "08:00",
                "end_time": "16:00",
                "available": True,
                "location": "Warehouse B"
            },
            # TECH-003 slots
            {
                "id": "SLOT-20231019-003",
                "slot_id": "SLOT-20231019-003",
                "technician_id": "TECH-003",
                "date": "2023-10-19",
                "start_time": "13:00",
                "end_time": "21:00",
                "available": False,
                "location": "Production Line 3"
            },
            {
                "id": "SLOT-20231020-003",
                "slot_id": "SLOT-20231020-003",
                "technician_id": "TECH-003",
                "date": "2023-10-20",
                "start_time": "13:00",
                "end_time": "21:00",
                "available": True,
                "location": "Production Line 3"
            },
            # TECH-004 slots
            {
                "id": "SLOT-20231021-004",
                "slot_id": "SLOT-20231021-004",
                "technician_id": "TECH-004",
                "date": "2023-10-21",
                "start_time": "10:00",
                "end_time": "18:00",
                "available": True,
                "location": "Maintenance Shop"
            },
            {
                "id": "SLOT-20231022-004",
                "slot_id": "SLOT-20231022-004",
                "technician_id": "TECH-004",
                "date": "2023-10-22",
                "start_time": "10:00",
                "end_time": "18:00",
                "available": True,
                "location": "Maintenance Shop"
            }
        ]
        
        for slot in slots:
            try:
                container.upsert_item(slot)
                available_str = "available" if slot["available"] else "booked"
                logger.info(f"✓ Seeded schedule slot: {slot['slot_id']} - {slot['technician_id']} on {slot['date']} ({available_str})")
            except Exception as e:
                logger.error(f"✗ Failed to seed schedule slot {slot['slot_id']}: {e}")


def main():
    """Main entry point for the seeding script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed CosmosDB databases")
    parser.add_argument(
        '--database',
        choices=['banking', 'industrial', 'all'],
        default='all',
        help='Which database to seed (default: all)'
    )
    args = parser.parse_args()
    
    try:
        if args.database in ['banking', 'all']:
            logger.info("\n" + "="*60)
            logger.info("SEEDING BANKING DATABASE")
            logger.info("="*60)
            seeder = CosmosDBSeeder()
            seeder.seed_all()
        
        if args.database in ['industrial', 'all']:
            logger.info("\n" + "="*60)
            logger.info("SEEDING INDUSTRIAL DATABASE")
            logger.info("="*60)
            industrial_seeder = IndustrialDBSeeder()
            industrial_seeder.seed_all()
        
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
