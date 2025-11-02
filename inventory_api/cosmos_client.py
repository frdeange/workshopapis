"""
CosmosDB Client Module for Azure Functions

This module provides a singleton CosmosDB client instance that uses
Azure RBAC authentication via DefaultAzureCredential for secure access.
"""

import os
import logging
from typing import Optional
from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """
    Singleton CosmosDB client for Industrial API with RBAC authentication.
    
    This client uses DefaultAzureCredential which automatically tries:
    1. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
    2. Managed Identity (when deployed in Azure)
    3. Azure CLI credentials (for local development)
    
    Connects to IndustrialDB database for inventory and maintenance operations.
    """
    
    _instance: Optional['CosmosDBClient'] = None
    _client: Optional[CosmosClient] = None
    _database: Optional[DatabaseProxy] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CosmosDBClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize CosmosDB client with RBAC authentication."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the CosmosDB client using DefaultAzureCredential."""
        try:
            endpoint = os.getenv("AZURE_COSMOSDB_URI")
            database_name = os.getenv("INDUSTRIAL_DATABASE_NAME", "IndustrialDB")
            
            if not endpoint:
                raise ValueError("AZURE_COSMOSDB_URI environment variable is not set")
            
            logger.info("Initializing CosmosDB client with RBAC authentication for IndustrialDB")
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Database: {database_name}")
            
            # Use key-based auth if available (for local development)
            cosmos_key = os.getenv("AZURE_COSMOSDB_KEY")
            
            if cosmos_key:
                logger.info("Using key-based authentication")
                self._client = CosmosClient(url=endpoint, credential=cosmos_key)
            else:
                logger.info("Using RBAC authentication with DefaultAzureCredential")
                credential = DefaultAzureCredential()
                self._client = CosmosClient(url=endpoint, credential=credential)
            
            # Get database reference
            self._database = self._client.get_database_client(database_name)
            logger.info(f"✓ Successfully connected to {database_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB client: {e}")
            raise
    
    def get_container(self, container_name: str) -> ContainerProxy:
        """
        Get a container client for the specified container.
        
        Args:
            container_name: Name of the container (e.g., 'inventory-items', 'reservations')
        
        Returns:
            ContainerProxy: Container client instance
        
        Raises:
            ValueError: If client is not initialized
        """
        if self._database is None:
            raise ValueError("Database client is not initialized")
        
        return self._database.get_container_client(container_name)


# Global singleton instance
_cosmos_client_instance: Optional[CosmosDBClient] = None


def get_cosmos_client() -> CosmosDBClient:
    """
    Get the singleton CosmosDB client instance.
    
    Returns:
        CosmosDBClient: CosmosDB client instance for IndustrialDB
    
    Raises:
        ValueError: If client is not initialized
    """
    global _cosmos_client_instance
    
    if _cosmos_client_instance is None:
        _cosmos_client_instance = CosmosDBClient()
    
    if _cosmos_client_instance._database is None:
        raise ValueError("CosmosDB client is not properly initialized")
    
    return _cosmos_client_instance
