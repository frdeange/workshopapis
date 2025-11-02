"""
Azure Function App - Payment API

HTTP Triggers for payment processing operations with CosmosDB integration.
Updated to use GitHub-hosted runners for deployment.
"""

import azure.functions as func
import logging
import os
import json
import requests
from datetime import datetime
from typing import Optional
from cosmos_client import get_cosmos_client
from models import PaymentRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Function App
app = func.FunctionApp()

# Environment variables
ACCOUNTS_CONTAINER = os.getenv("ACCOUNTS_CONTAINER_NAME", "accounts")
PAYMENT_METHODS_CONTAINER = os.getenv("PAYMENT_METHODS_CONTAINER_NAME", "payment-methods")
BENEFICIARIES_CONTAINER = os.getenv("BENEFICIARIES_CONTAINER_NAME", "beneficiaries")
TRANSACTION_API_URL = os.getenv("TRANSACTION_API_URL", "http://localhost:7072/api")


# Helper functions
def get_account_by_id(account_id: str) -> Optional[dict]:
    """Get account by ID"""
    try:
        container = get_cosmos_client().get_container(ACCOUNTS_CONTAINER)
        
        query = "SELECT * FROM c WHERE c.id = @accountId"
        parameters = [{"name": "@accountId", "value": account_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {str(e)}")
        raise


def get_payment_method_by_id(payment_method_id: str, account_id: str) -> Optional[dict]:
    """Get payment method by ID"""
    try:
        container = get_cosmos_client().get_container(PAYMENT_METHODS_CONTAINER)
        
        query = "SELECT * FROM c WHERE c.id = @paymentMethodId AND c.accountId = @accountId"
        parameters = [
            {"name": "@paymentMethodId", "value": payment_method_id},
            {"name": "@accountId", "value": account_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Error getting payment method {payment_method_id}: {str(e)}")
        raise


def get_beneficiary_by_id(beneficiary_id: str, account_id: str) -> Optional[dict]:
    """Get beneficiary by ID"""
    try:
        container = get_cosmos_client().get_container(BENEFICIARIES_CONTAINER)
        
        query = "SELECT * FROM c WHERE c.id = @beneficiaryId AND c.accountId = @accountId"
        parameters = [
            {"name": "@beneficiaryId", "value": beneficiary_id},
            {"name": "@accountId", "value": account_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Error getting beneficiary {beneficiary_id}: {str(e)}")
        raise


def update_account_balance(account_id: str, new_balance: float) -> dict:
    """Update account balance"""
    try:
        container = get_cosmos_client().get_container(ACCOUNTS_CONTAINER)
        
        # Get current account
        account = get_account_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Update balance
        account["balance"] = new_balance
        
        # Upsert account
        updated_account = container.upsert_item(account)
        
        return updated_account
    except Exception as e:
        logger.error(f"Error updating account balance: {str(e)}")
        raise


def create_transaction_via_api(account_id: str, transaction_data: dict) -> dict:
    """Create transaction via Transaction API"""
    try:
        url = f"{TRANSACTION_API_URL}/transactions/{account_id}"
        
        logger.info(f"Calling Transaction API: {url}")
        
        response = requests.post(url, json=transaction_data)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logger.error(f"Error calling Transaction API: {str(e)}")
        raise


def process_payment(payment_request: PaymentRequest) -> dict:
    """Process a payment"""
    try:
        # 1. Validate account exists
        account = get_account_by_id(payment_request.accountId)
        if not account:
            raise ValueError(f"Account {payment_request.accountId} not found")
        
        # 2. Validate payment method exists
        payment_method = get_payment_method_by_id(
            payment_request.paymentMethodId,
            payment_request.accountId
        )
        if not payment_method:
            raise ValueError(f"Payment method {payment_request.paymentMethodId} not found")
        
        # 3. Validate beneficiary exists
        beneficiary = get_beneficiary_by_id(
            payment_request.beneficiaryId,
            payment_request.accountId
        )
        if not beneficiary:
            raise ValueError(f"Beneficiary {payment_request.beneficiaryId} not found")
        
        # 4. Validate sufficient balance
        if account["balance"] < payment_request.amount:
            raise ValueError("Insufficient balance")
        
        # 5. Update account balance
        new_balance = account["balance"] - payment_request.amount
        update_account_balance(payment_request.accountId, new_balance)
        
        # 6. Create transaction
        transaction_data = {
            "id": f"txn-{datetime.utcnow().timestamp()}",
            "description": payment_request.description or f"Payment to {beneficiary['name']}",
            "type": "debit",
            "recipientName": beneficiary["name"],
            "recipientBankReference": beneficiary["bankReference"],
            "accountId": payment_request.accountId,
            "paymentType": payment_method["type"],
            "amount": payment_request.amount,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        transaction = create_transaction_via_api(payment_request.accountId, transaction_data)
        
        return {
            "success": True,
            "message": "Payment processed successfully",
            "transaction": transaction,
            "newBalance": new_balance
        }
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        raise


# HTTP Triggers

@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    
    Returns the health status of the Payment API service.
    
    Returns:
        200: Service is healthy
        - Response body: {"status": "healthy", "service": "payment-api"}
    
    Example:
        GET /api/health
        Response: {"status": "healthy", "service": "payment-api"}
    """
    logger.info("Health check requested")
    
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "payment-api"}),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="payments", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def process_payment_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Process a payment transaction
    
    Processes a payment from an account to a beneficiary using a specified payment method.
    Validates account, payment method, beneficiary, and sufficient balance before processing.
    Creates a transaction record via the Transaction API.
    
    Request Body:
        PaymentRequest object containing:
        - accountId (str): ID of the account making the payment
        - paymentMethodId (str): ID of the payment method to use
        - beneficiaryId (str): ID of the beneficiary receiving the payment
        - amount (float): Amount to transfer (must be positive)
        - description (str, optional): Description for the payment
    
    Returns:
        200: Payment processed successfully
        - Response body: PaymentResponse with transaction details and new balance
        400: Validation error (invalid data, insufficient balance, etc.)
        - Response body: {"error": "error message"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        POST /api/payments
        Request Body: {
            "accountId": "1010",
            "paymentMethodId": "345678",
            "beneficiaryId": "3",
            "amount": 120.50,
            "description": "Payment for consulting services"
        }
        Response: {
            "success": true,
            "message": "Payment processed successfully",
            "transaction": {
                "id": "txn-1234567890.123",
                "description": "Payment to Sarah TheAccountant",
                "type": "debit",
                "recipientName": "Sarah TheAccountant",
                "recipientBankReference": "555123456",
                "accountId": "1010",
                "paymentType": "BankTransfer",
                "amount": 120.50,
                "timestamp": "2023-11-01T10:30:00.000000"
            },
            "newBalance": 9879.50
        }
    """
    logger.info("POST /payments")
    
    try:
        # Parse request body
        payment_data = req.get_json()
        
        # Validate payment request
        payment_request = PaymentRequest(**payment_data)
        
        # Process payment
        result = process_payment(payment_request)
        
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
