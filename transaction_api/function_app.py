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
    """
    Health check endpoint
    
    Returns the health status of the Transaction API service.
    
    Returns:
        200: Service is healthy
        - Response body: {"status": "healthy", "service": "transaction-api"}
    
    Example:
        GET /api/health
        Response: {"status": "healthy", "service": "transaction-api"}
    """
    logger.info("Health check requested")
    
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "transaction-api"}),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="transactions/{account_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_last_transactions(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get last transactions for an account
    
    Retrieves the most recent transactions for a specific account, ordered by timestamp descending.
    
    Path Parameters:
        account_id (str): Unique identifier of the account
    
    Query Parameters:
        limit (int, optional): Maximum number of transactions to return (default: 10)
    
    Returns:
        200: Successfully retrieved transactions
        - Response body: Array of Transaction objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/transactions/1010?limit=5
        Response: [
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
            }
        ]
    """
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
    """
    Search transactions by recipient name
    
    Searches for transactions of a specific account where the recipient name contains the search term (case-insensitive).
    
    Path Parameters:
        account_id (str): Unique identifier of the account
    
    Query Parameters:
        recipientName (str, required): Recipient name to search for (partial match, case-insensitive)
    
    Returns:
        200: Successfully retrieved matching transactions
        - Response body: Array of Transaction objects
        400: Missing required query parameter
        - Response body: {"error": "recipientName query parameter is required"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/transactions/1010/search?recipientName=acme
        Response: [
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
            }
        ]
    """
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
    """
    Create a new transaction
    
    Creates a new transaction record for a specific account. This endpoint is typically called
    by the Payment API after processing a payment. The timestamp is automatically added if not provided.
    
    Path Parameters:
        account_id (str): Unique identifier of the account
    
    Request Body:
        Transaction object (without timestamp, which is auto-generated):
        - id (str): Unique transaction identifier
        - description (str): Description of the transaction
        - type (str): Type (income/outcome)
        - recipientName (str): Recipient or sender name
        - recipientBankReference (str): Bank reference
        - paymentType (str): Payment method used
        - amount (float): Transaction amount (negative for debits)
    
    Returns:
        201: Transaction created successfully
        - Response body: Created Transaction object with timestamp
        400: Invalid request body format
        - Response body: {"error": "Invalid JSON in request body"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        POST /api/transactions/1010
        Request Body: {
            "id": "txn-123456",
            "description": "Payment for services",
            "type": "outcome",
            "recipientName": "Sarah TheAccountant",
            "recipientBankReference": "555123456",
            "paymentType": "BankTransfer",
            "amount": -120.50
        }
        Response: {
            "id": "txn-123456",
            "accountId": "1010",
            "description": "Payment for services",
            "type": "outcome",
            "recipientName": "Sarah TheAccountant",
            "recipientBankReference": "555123456",
            "paymentType": "BankTransfer",
            "amount": -120.50,
            "timestamp": "2023-11-01T10:30:00.000000"
        }
    """
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
