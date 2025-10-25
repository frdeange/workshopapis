"""
CosmosDB Client with RBAC Authentication (Singleton Pattern)
"""
import os
import logging
from typing import Optional
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

# Singleton instance
_cosmos_db_client: Optional['CosmosDBClient'] = None


class CosmosDBClient:
    """
    Singleton CosmosDB client with RBAC authentication
    """
    
    def __init__(self):
        self._client: Optional[CosmosClient] = None
        self._database = None
        self._endpoint = os.getenv("AZURE_COSMOSDB_URI")
        self._database_name = os.getenv("AZURE_COSMOSDB_DATABASE", "BankingDB")
        
        if not self._endpoint:
            raise ValueError(
                "AZURE_COSMOSDB_URI environment variable must be set"
            )
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize CosmosDB client with RBAC authentication"""
        try:
            logger.info("Initializing CosmosDB client with RBAC authentication")
            logger.info(f"Endpoint: {self._endpoint}")
            logger.info(f"Database: {self._database_name}")
            
            # Use DefaultAzureCredential for RBAC authentication
            credential = DefaultAzureCredential()
            
            # Create CosmosDB client
            self._client = CosmosClient(
                url=self._endpoint,
                credential=credential
            )
            
            # Get database
            self._database = self._client.get_database_client(self._database_name)
            
            logger.info("CosmosDB client initialized successfully with RBAC")
            
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB client: {str(e)}")
            raise
    
    def get_container(self, container_name: str):
        """Get a container client"""
        if not self._database:
            raise RuntimeError("CosmosDB client not initialized")
        
        return self._database.get_container_client(container_name)
    
    def get_database(self):
        """Get the database client"""
        return self._database
    
    def get_client(self):
        """Get the CosmosDB client"""
        return self._client


def get_cosmos_client() -> CosmosDBClient:
    """
    Get or create the singleton CosmosDB client instance
    
    Returns:
        CosmosDBClient: The singleton instance
    """
    global _cosmos_db_client
    
    if _cosmos_db_client is None:
        _cosmos_db_client = CosmosDBClient()
    
    return _cosmos_db_client
