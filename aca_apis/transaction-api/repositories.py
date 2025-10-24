"""
Repository Layer for Transaction API

This module provides data access layer (DAL) for interacting with CosmosDB.
Repository handles all CRUD operations and queries for transactions.

Architecture pattern: Repository Pattern
- Abstracts data access logic from business logic
- Makes code more testable and maintainable
- Allows easy switching between data sources
"""

import os
import logging
from typing import List, Optional
from azure.cosmos import ContainerProxy, exceptions
from cosmos_client import get_cosmos_client
from models import Transaction

logger = logging.getLogger(__name__)


class TransactionRepository:
    """
    Repository for Transaction data operations.
    
    Container: Configured via AZURE_COSMOSDB_TRANSACTION_CONTAINER env variable
    Partition Key: Configured via AZURE_COSMOSDB_TRANSACTION_CONTAINER_PARTITION_KEY env variable
    """
    
    def __init__(self):
        """Initialize repository with CosmosDB container reference."""
        container_name = os.getenv("AZURE_COSMOSDB_TRANSACTION_CONTAINER", "transactions")
        self.container: ContainerProxy = get_cosmos_client().get_container(container_name)
    
    def get_by_id(self, transaction_id: str, account_id: str) -> Optional[Transaction]:
        """
        Get transaction by ID using point read (most efficient).
        
        Args:
            transaction_id: The transaction ID
            account_id: The accountId (partition key)
            
        Returns:
            Transaction object or None if not found
        """
        try:
            logger.info(f"Fetching transaction with id={transaction_id}, accountId={account_id}")
            
            # Point read: most efficient way to retrieve a document (1 RU)
            item = self.container.read_item(
                item=transaction_id,
                partition_key=account_id
            )
            
            logger.info(f"Transaction found: {transaction_id}")
            return Transaction(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Transaction not found: {transaction_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            raise
    
    def get_by_account_id(self, account_id: str, limit: Optional[int] = None) -> List[Transaction]:
        """
        Get transactions for a specific account, ordered by timestamp descending.
        
        Args:
            account_id: The accountId to search for
            limit: Maximum number of transactions to return
            
        Returns:
            List of Transaction objects
        """
        try:
            logger.info(f"Fetching transactions for account: {account_id}")
            
            # Query within partition for efficiency, ordered by timestamp DESC
            query = """
                SELECT * FROM c 
                WHERE c.accountId = @accountId 
                ORDER BY c.timestamp DESC
            """
            parameters = [{"name": "@accountId", "value": account_id}]
            
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=account_id,
                enable_cross_partition_query=False
            )
            
            # Convert to list and apply limit if specified
            transactions = [Transaction(**item) for item in items]
            
            if limit is not None and len(transactions) > limit:
                transactions = transactions[:limit]
            
            logger.info(f"Found {len(transactions)} transactions for account {account_id}")
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions for account {account_id}: {e}")
            raise
    
    def search_by_recipient_name(self, account_id: str, recipient_name: str) -> List[Transaction]:
        """
        Search transactions by recipient name (case-insensitive contains).
        
        Args:
            account_id: The accountId to search within
            recipient_name: The recipient name to search for
            
        Returns:
            List of matching Transaction objects
        """
        try:
            logger.info(f"Searching transactions for account {account_id} with recipient name: {recipient_name}")
            
            # Query within partition with CONTAINS for case-insensitive search
            query = """
                SELECT * FROM c 
                WHERE c.accountId = @accountId 
                AND CONTAINS(LOWER(c.recipientName), LOWER(@recipientName))
                ORDER BY c.timestamp DESC
            """
            parameters = [
                {"name": "@accountId", "value": account_id},
                {"name": "@recipientName", "value": recipient_name}
            ]
            
            items = self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=account_id,
                enable_cross_partition_query=False
            )
            
            transactions = [Transaction(**item) for item in items]
            logger.info(f"Found {len(transactions)} matching transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            raise
    
    def create(self, transaction: Transaction) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            transaction: Transaction object to create
            
        Returns:
            Created Transaction object
        """
        try:
            logger.info(f"Creating transaction: {transaction.id}")
            
            # Convert Pydantic model to dict for CosmosDB
            transaction_dict = transaction.model_dump()
            
            created_item = self.container.create_item(body=transaction_dict)
            logger.info(f"Transaction created successfully: {transaction.id}")
            return Transaction(**created_item)
            
        except Exception as e:
            logger.error(f"Error creating transaction {transaction.id}: {e}")
            raise
    
    def update(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction.
        
        Args:
            transaction: Transaction object with updated data
            
        Returns:
            Updated Transaction object
        """
        try:
            logger.info(f"Updating transaction: {transaction.id}")
            
            transaction_dict = transaction.model_dump()
            
            updated_item = self.container.upsert_item(body=transaction_dict)
            logger.info(f"Transaction updated successfully: {transaction.id}")
            return Transaction(**updated_item)
            
        except Exception as e:
            logger.error(f"Error updating transaction {transaction.id}: {e}")
            raise
    
    def delete(self, transaction_id: str, account_id: str) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: The transaction ID to delete
            account_id: The accountId (partition key)
            
        Returns:
            True if deleted successfully
        """
        try:
            logger.info(f"Deleting transaction: {transaction_id}")
            
            self.container.delete_item(
                item=transaction_id,
                partition_key=account_id
            )
            
            logger.info(f"Transaction deleted successfully: {transaction_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Transaction not found for deletion: {transaction_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise
    
    def count_by_account_id(self, account_id: str) -> int:
        """
        Count total transactions for an account.
        
        Args:
            account_id: The accountId to count transactions for
            
        Returns:
            Total count of transactions
        """
        try:
            logger.info(f"Counting transactions for account: {account_id}")
            
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.accountId = @accountId
            """
            parameters = [{"name": "@accountId", "value": account_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                partition_key=account_id,
                enable_cross_partition_query=False
            ))
            
            count = items[0] if items else 0
            logger.info(f"Total transactions for account {account_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting transactions for account {account_id}: {e}")
            raise
