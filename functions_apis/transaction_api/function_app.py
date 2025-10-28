"""
Azure Function App - Transaction API

HTTP Triggers for transaction management operations with CosmosDB integration.
Updated to use GitHub-hosted runners for deployment.
"""

import azure.functions as func
import logging
import os
import json
from datetime import datetime
from typing import List, Optional
from cosmos_client import get_cosmos_client
from models import Transaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Function App
app = func.FunctionApp()

# Environment variables
TRANSACTIONS_CONTAINER = os.getenv("TRANSACTIONS_CONTAINER_NAME", "transactions")


# Helper function to get transactions by account ID
def get_transactions_by_account_id(account_id: str, limit: int = 10) -> List[dict]:
    """Get last N transactions for an account, ordered by timestamp descending"""
    try:
        container = get_cosmos_client().get_container(TRANSACTIONS_CONTAINER)
        
        query = """
        SELECT * FROM c 
        WHERE c.accountId = @accountId 
        ORDER BY c.timestamp DESC 
        OFFSET 0 LIMIT @limit
        """
        
        parameters = [
            {"name": "@accountId", "value": account_id},
            {"name": "@limit", "value": limit}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        return items
    except Exception as e:
        logger.error(f"Error getting transactions for account {account_id}: {str(e)}")
        raise


def search_transactions_by_recipient(account_id: str, recipient_name: str) -> List[dict]:
    """Search transactions by recipient name (case-insensitive)"""
    try:
        container = get_cosmos_client().get_container(TRANSACTIONS_CONTAINER)
        
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
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        return items
    except Exception as e:
        logger.error(f"Error searching transactions: {str(e)}")
        raise


def create_transaction(account_id: str, transaction_data: dict) -> dict:
    """Create a new transaction"""
    try:
        container = get_cosmos_client().get_container(TRANSACTIONS_CONTAINER)
        
        # Ensure timestamp exists
        if "timestamp" not in transaction_data:
            transaction_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Ensure accountId matches
        transaction_data["accountId"] = account_id
        
        # Upsert the transaction
        created_item = container.upsert_item(transaction_data)
        
        return created_item
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise


# HTTP Triggers

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info("Health check requested")
    
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "transaction-api"}),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="transactions/{account_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_last_transactions(req: func.HttpRequest) -> func.HttpResponse:
    """Get last transactions for an account"""
    account_id = req.route_params.get('account_id')
    logger.info(f"GET /transactions/{account_id}")
    
    try:
        # Get limit from query params (default 10)
        limit = int(req.params.get('limit', 10))
        
        transactions = get_transactions_by_account_id(account_id, limit)
        
        return func.HttpResponse(
            json.dumps(transactions),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="transactions/{account_id}/search", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_transactions_by_recipient_name(req: func.HttpRequest) -> func.HttpResponse:
    """Search transactions by recipient name"""
    account_id = req.route_params.get('account_id')
    recipient_name = req.params.get('recipientName', '')
    
    logger.info(f"GET /transactions/{account_id}/search?recipientName={recipient_name}")
    
    if not recipient_name:
        return func.HttpResponse(
            json.dumps({"error": "recipientName query parameter is required"}),
            mimetype="application/json",
            status_code=400
        )
    
    try:
        transactions = search_transactions_by_recipient(account_id, recipient_name)
        
        return func.HttpResponse(
            json.dumps(transactions),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error searching transactions: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="transactions/{account_id}", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def notify_transaction(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new transaction"""
    account_id = req.route_params.get('account_id')
    logger.info(f"POST /transactions/{account_id}")
    
    try:
        # Parse request body
        transaction_data = req.get_json()
        
        # Create transaction
        created_transaction = create_transaction(account_id, transaction_data)
        
        return func.HttpResponse(
            json.dumps(created_transaction),
            mimetype="application/json",
            status_code=201
        )
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
