"""
Repository Layer for Account API

This module provides data access layer (DAL) for interacting with CosmosDB.
Repositories handle all CRUD operations and queries to the database.

Architecture pattern: Repository Pattern
- Abstracts data access logic from business logic
- Makes code more testable and maintainable
- Allows easy switching between data sources
"""

import os
import logging
from typing import List, Optional, Dict, Any
from azure.cosmos import ContainerProxy, exceptions
from cosmos_client import get_cosmos_client
from models import Account, PaymentMethod, PaymentMethodSummary, Beneficiary

logger = logging.getLogger(__name__)


class AccountRepository:
    """
    Repository for Account data operations.
    
    Container: Configured via AZURE_COSMOSDB_ACCOUNT_CONTAINER env variable
    Partition Key: Configured via AZURE_COSMOSDB_ACCOUNT_CONTAINER_PARTITION_KEY env variable
    """
    
    def __init__(self):
        """Initialize repository with CosmosDB container reference."""
        container_name = os.getenv("AZURE_COSMOSDB_ACCOUNT_CONTAINER", "accounts")
        self.container: ContainerProxy = get_cosmos_client().get_container(container_name)
    
    def get_by_id(self, account_id: str, user_name: str) -> Optional[Account]:
        """
        Get account by ID using point read (most efficient).
        
        Args:
            account_id: The account ID
            user_name: The userName (partition key)
            
        Returns:
            Account object or None if not found
        """
        try:
            logger.info(f"Fetching account with id={account_id}, userName={user_name}")
            
            # Point read: most efficient way to retrieve a document (1 RU)
            item = self.container.read_item(
                item=account_id,
                partition_key=user_name
            )
            
            logger.info(f"Account found: {account_id}")
            return Account(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Account not found: {account_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching account {account_id}: {e}")
            raise
    
    def get_by_user_name(self, user_name: str) -> List[Account]:
        """
        Get all accounts for a specific user.
        
        Args:
            user_name: The userName to search for
            
        Returns:
            List of Account objects
        """
        try:
            logger.info(f"Fetching accounts for user: {user_name}")
            
            # Query within partition for efficiency
            query = "SELECT * FROM c WHERE c.userName = @userName"
            parameters = [{"name": "@userName", "value": user_name}]
            
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_name,
                enable_cross_partition_query=False
            )
            
            accounts = [Account(**item) for item in items]
            logger.info(f"Found {len(accounts)} accounts for user {user_name}")
            return accounts
            
        except Exception as e:
            logger.error(f"Error fetching accounts for user {user_name}: {e}")
            raise
    
    def create(self, account: Account) -> Account:
        """
        Create a new account.
        
        Args:
            account: Account object to create
            
        Returns:
            Created Account object
        """
        try:
            logger.info(f"Creating account: {account.id}")
            
            # Convert Pydantic model to dict for CosmosDB
            account_dict = account.model_dump()
            
            created_item = self.container.create_item(body=account_dict)
            logger.info(f"Account created successfully: {account.id}")
            return Account(**created_item)
            
        except Exception as e:
            logger.error(f"Error creating account {account.id}: {e}")
            raise
    
    def update(self, account: Account) -> Account:
        """
        Update an existing account.
        
        Args:
            account: Account object with updated data
            
        Returns:
            Updated Account object
        """
        try:
            logger.info(f"Updating account: {account.id}")
            
            account_dict = account.model_dump()
            
            updated_item = self.container.upsert_item(body=account_dict)
            logger.info(f"Account updated successfully: {account.id}")
            return Account(**updated_item)
            
        except Exception as e:
            logger.error(f"Error updating account {account.id}: {e}")
            raise
    
    def delete(self, account_id: str, user_name: str) -> bool:
        """
        Delete an account.
        
        Args:
            account_id: The account ID to delete
            user_name: The userName (partition key)
            
        Returns:
            True if deleted successfully
        """
        try:
            logger.info(f"Deleting account: {account_id}")
            
            self.container.delete_item(
                item=account_id,
                partition_key=user_name
            )
            
            logger.info(f"Account deleted successfully: {account_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Account not found for deletion: {account_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting account {account_id}: {e}")
            raise


class PaymentMethodRepository:
    """
    Repository for PaymentMethod data operations.
    
    Container: Configured via AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER env variable
    Partition Key: Configured via AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER_PARTITION_KEY env variable
    """
    
    def __init__(self):
        """Initialize repository with CosmosDB container reference."""
        container_name = os.getenv("AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER", "payment-methods")
        self.container: ContainerProxy = get_cosmos_client().get_container(container_name)
    
    def get_by_id(self, payment_method_id: str, account_id: str) -> Optional[PaymentMethod]:
        """
        Get payment method by ID using point read.
        
        Args:
            payment_method_id: The payment method ID
            account_id: The accountId (partition key)
            
        Returns:
            PaymentMethod object or None if not found
        """
        try:
            logger.info(f"Fetching payment method: id={payment_method_id}, accountId={account_id}")
            
            item = self.container.read_item(
                item=payment_method_id,
                partition_key=account_id
            )
            
            logger.info(f"Payment method found: {payment_method_id}")
            return PaymentMethod(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Payment method not found: {payment_method_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching payment method {payment_method_id}: {e}")
            raise
    
    def get_by_account_id(self, account_id: str) -> List[PaymentMethod]:
        """
        Get all payment methods for a specific account.
        
        Args:
            account_id: The accountId to search for
            
        Returns:
            List of PaymentMethod objects
        """
        try:
            logger.info(f"Fetching payment methods for account: {account_id}")
            
            # Query within partition
            query = "SELECT * FROM c WHERE c.accountId = @accountId"
            parameters = [{"name": "@accountId", "value": account_id}]
            
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=account_id,
                enable_cross_partition_query=False
            )
            
            payment_methods = [PaymentMethod(**item) for item in items]
            logger.info(f"Found {len(payment_methods)} payment methods for account {account_id}")
            return payment_methods
            
        except Exception as e:
            logger.error(f"Error fetching payment methods for account {account_id}: {e}")
            raise
    
    def create(self, payment_method: PaymentMethod) -> PaymentMethod:
        """
        Create a new payment method.
        
        Args:
            payment_method: PaymentMethod object to create
            
        Returns:
            Created PaymentMethod object
        """
        try:
            logger.info(f"Creating payment method: {payment_method.id}")
            
            payment_dict = payment_method.model_dump()
            
            created_item = self.container.create_item(body=payment_dict)
            logger.info(f"Payment method created successfully: {payment_method.id}")
            return PaymentMethod(**created_item)
            
        except Exception as e:
            logger.error(f"Error creating payment method {payment_method.id}: {e}")
            raise
    
    def update(self, payment_method: PaymentMethod) -> PaymentMethod:
        """
        Update an existing payment method.
        
        Args:
            payment_method: PaymentMethod object with updated data
            
        Returns:
            Updated PaymentMethod object
        """
        try:
            logger.info(f"Updating payment method: {payment_method.id}")
            
            payment_dict = payment_method.model_dump()
            
            updated_item = self.container.upsert_item(body=payment_dict)
            logger.info(f"Payment method updated successfully: {payment_method.id}")
            return PaymentMethod(**updated_item)
            
        except Exception as e:
            logger.error(f"Error updating payment method {payment_method.id}: {e}")
            raise


class BeneficiaryRepository:
    """
    Repository for Beneficiary data operations.
    
    Container: Configured via AZURE_COSMOSDB_BENEFICIARY_CONTAINER env variable
    Partition Key: Configured via AZURE_COSMOSDB_BENEFICIARY_CONTAINER_PARTITION_KEY env variable
    """
    
    def __init__(self):
        """Initialize repository with CosmosDB container reference."""
        container_name = os.getenv("AZURE_COSMOSDB_BENEFICIARY_CONTAINER", "beneficiaries")
        self.container: ContainerProxy = get_cosmos_client().get_container(container_name)
    
    def get_by_account_id(self, account_id: str) -> List[Beneficiary]:
        """
        Get all beneficiaries for a specific account.
        
        Args:
            account_id: The accountId to search for
            
        Returns:
            List of Beneficiary objects
        """
        try:
            logger.info(f"Fetching beneficiaries for account: {account_id}")
            
            # Query within partition
            query = "SELECT * FROM c WHERE c.accountId = @accountId"
            parameters = [{"name": "@accountId", "value": account_id}]
            
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=account_id,
                enable_cross_partition_query=False
            )
            
            beneficiaries = [Beneficiary(**item) for item in items]
            logger.info(f"Found {len(beneficiaries)} beneficiaries for account {account_id}")
            return beneficiaries
            
        except Exception as e:
            logger.error(f"Error fetching beneficiaries for account {account_id}: {e}")
            raise
    
    def create(self, beneficiary: Beneficiary, account_id: str) -> Beneficiary:
        """
        Create a new beneficiary.
        
        Args:
            beneficiary: Beneficiary object to create
            account_id: The accountId (partition key)
            
        Returns:
            Created Beneficiary object
        """
        try:
            logger.info(f"Creating beneficiary: {beneficiary.id} for account {account_id}")
            
            beneficiary_dict = beneficiary.model_dump()
            # Ensure accountId is set for partition key
            beneficiary_dict["accountId"] = account_id
            
            created_item = self.container.create_item(body=beneficiary_dict)
            logger.info(f"Beneficiary created successfully: {beneficiary.id}")
            return Beneficiary(**created_item)
            
        except Exception as e:
            logger.error(f"Error creating beneficiary {beneficiary.id}: {e}")
            raise
    
    def delete(self, beneficiary_id: str, account_id: str) -> bool:
        """
        Delete a beneficiary.
        
        Args:
            beneficiary_id: The beneficiary ID to delete
            account_id: The accountId (partition key)
            
        Returns:
            True if deleted successfully
        """
        try:
            logger.info(f"Deleting beneficiary: {beneficiary_id}")
            
            self.container.delete_item(
                item=beneficiary_id,
                partition_key=account_id
            )
            
            logger.info(f"Beneficiary deleted successfully: {beneficiary_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Beneficiary not found for deletion: {beneficiary_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting beneficiary {beneficiary_id}: {e}")
            raise
