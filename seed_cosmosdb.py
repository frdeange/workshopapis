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
    
    def __init__(self):
        """Initialize CosmosDB client with RBAC authentication."""
        self.endpoint = os.getenv("AZURE_COSMOSDB_URI")
        self.database_name = os.getenv("AZURE_COSMOSDB_DATABASE", "BankingDB")
        
        if not self.endpoint:
            raise ValueError("AZURE_COSMOSDB_URI environment variable is not set")
        
        logger.info("Initializing CosmosDB client for seeding")
        logger.info(f"Endpoint: {self.endpoint}")
        logger.info(f"Database: {self.database_name}")
        
        # Use DefaultAzureCredential for RBAC
        credential = DefaultAzureCredential()
        self.client = CosmosClient(url=self.endpoint, credential=credential)
        self.database = self.client.get_database_client(self.database_name)
    
    def seed_all(self):
        """Seed all containers with initial data."""
        logger.info("=" * 60)
        logger.info("Starting CosmosDB seeding process")
        logger.info("=" * 60)
        
        try:
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


def main():
    """Main entry point for the seeding script."""
    try:
        seeder = CosmosDBSeeder()
        seeder.seed_all()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
