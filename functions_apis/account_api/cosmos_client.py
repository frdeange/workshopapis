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
    Singleton CosmosDB client with RBAC authentication.
    
    This client uses DefaultAzureCredential which automatically tries:
    1. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
    2. Managed Identity (when deployed in Azure)
    3. Azure CLI credentials (for local development)
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
            database_name = os.getenv("AZURE_COSMOSDB_DATABASE", "BankingDB")
            
            if not endpoint:
                raise ValueError("AZURE_COSMOSDB_URI environment variable is not set")
            
            logger.info("Initializing CosmosDB client with RBAC authentication")
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Database: {database_name}")
            
            # Use DefaultAzureCredential for RBAC authentication
            credential = DefaultAzureCredential()
            
            # Create CosmosDB client
            self._client = CosmosClient(
                url=endpoint,
                credential=credential
            )
            
            # Get database reference
            self._database = self._client.get_database_client(database_name)
            
            logger.info("CosmosDB client initialized successfully with RBAC")
            
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB client: {e}")
            raise
    
    def get_container(self, container_name: str) -> ContainerProxy:
        """Get a reference to a CosmosDB container."""
        if self._database is None:
            raise RuntimeError("CosmosDB client is not initialized")
        
        return self._database.get_container_client(container_name)
    
    def get_database(self) -> DatabaseProxy:
        """Get a reference to the CosmosDB database."""
        if self._database is None:
            raise RuntimeError("CosmosDB client is not initialized")
        
        return self._database


# Singleton instance
_cosmos_db_client = None


def get_cosmos_client() -> CosmosDBClient:
    """Get the singleton CosmosDB client instance."""
    global _cosmos_db_client
    if _cosmos_db_client is None:
        _cosmos_db_client = CosmosDBClient()
    return _cosmos_db_client
