"""
Singleton Cosmos DB client for Maintenance API
"""
import os
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
import logging

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """Singleton Cosmos DB client"""
    _instance = None
    _client = None
    _database = None
    _technicians_container = None
    _jobs_container = None
    _schedule_slots_container = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CosmosDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Cosmos DB client with RBAC authentication"""
        try:
            cosmos_uri = os.environ.get("AZURE_COSMOSDB_URI")
            cosmos_key = os.environ.get("AZURE_COSMOSDB_KEY")
            database_name = os.environ.get("INDUSTRIAL_DATABASE_NAME", "IndustrialDB")
            technicians_container_name = os.environ.get("AZURE_COSMOSDB_TECHNICIANS_CONTAINER", "technicians")
            jobs_container_name = os.environ.get("AZURE_COSMOSDB_JOBS_CONTAINER", "maintenance-jobs")
            schedule_container_name = os.environ.get("AZURE_COSMOSDB_SCHEDULE_CONTAINER", "schedule-slots")

            if not cosmos_uri:
                raise ValueError("AZURE_COSMOSDB_URI environment variable not set")

            logger.info(f"Initializing Cosmos DB client for {cosmos_uri}")
            
            # Use KEY if available (local dev), otherwise RBAC (production)
            if cosmos_key:
                logger.info("Using Cosmos DB KEY authentication")
                self._client = CosmosClient(cosmos_uri, credential=cosmos_key)
            else:
                logger.info("Using DefaultAzureCredential (RBAC) authentication")
                credential = DefaultAzureCredential()
                self._client = CosmosClient(cosmos_uri, credential=credential)
            
            self._database = self._client.get_database_client(database_name)
            self._technicians_container = self._database.get_container_client(technicians_container_name)
            self._jobs_container = self._database.get_container_client(jobs_container_name)
            self._schedule_slots_container = self._database.get_container_client(schedule_container_name)
            
            logger.info("Cosmos DB client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB client: {str(e)}")
            raise

    @property
    def technicians_container(self):
        """Get technicians container"""
        return self._technicians_container

    @property
    def jobs_container(self):
        """Get maintenance jobs container"""
        return self._jobs_container

    @property
    def schedule_slots_container(self):
        """Get schedule slots container"""
        return self._schedule_slots_container
