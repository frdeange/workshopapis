"""
Azure Function App - Account API

HTTP Triggers for account management operations with CosmosDB integration.
Updated to use GitHub-hosted runners for deployment.
"""

import azure.functions as func
import logging
import json
import os
from typing import Optional, List
from models import Account, PaymentMethod, Beneficiary, PaymentMethodSummary
from cosmos_client import get_cosmos_client
from azure.cosmos import exceptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Function App
app = func.FunctionApp()


def get_account_by_id(account_id: str) -> Optional[Account]:
    """Get account details with payment methods."""
    try:
        container_name = os.getenv("AZURE_COSMOSDB_ACCOUNT_CONTAINER", "accounts")
        account_container = get_cosmos_client().get_container(container_name)
        
        # Query to find account (cross-partition since we don't have userName)
        query = "SELECT * FROM c WHERE c.id = @accountId"
        parameters = [{"name": "@accountId", "value": account_id}]
        
        items = list(account_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return None
        
        account = Account(**items[0])
        
        # Get payment methods for this account
        pm_container_name = os.getenv("AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER", "payment-methods")
        pm_container = get_cosmos_client().get_container(pm_container_name)
        
        pm_query = "SELECT * FROM c WHERE c.accountId = @accountId"
        pm_parameters = [{"name": "@accountId", "value": account_id}]
        
        pm_items = list(pm_container.query_items(
            query=pm_query,
            parameters=pm_parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        # Convert to summary format
        account.paymentMethods = [
            PaymentMethodSummary(
                id=pm['id'],
                type=pm['type'],
                activationDate=pm.get('activationDate'),
                expirationDate=pm.get('expirationDate')
            )
            for pm in pm_items
        ]
        
        return account
        
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        raise


@app.function_name(name="health")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    
    Returns the health status of the Account API service.
    
    Returns:
        200: Service is healthy
        - Response body: {"status": "healthy"}
    
    Example:
        GET /api/health
        Response: {"status": "healthy"}
    """
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "account-api"}),
        mimetype="application/json",
        status_code=200
    )


@app.function_name(name="get_accounts_by_user")
@app.route(route="accounts/user/{user_name}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_accounts_by_user_name(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get all accounts for a specific user
    
    Retrieves all bank accounts associated with a given username.
    
    Path Parameters:
        user_name (str): Username of the account holder
    
    Returns:
        200: Successfully retrieved accounts
        - Response body: Array of Account objects
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/accounts/user/alice.user@contoso.com
        Response: [
            {
                "id": "1000",
                "userName": "alice.user@contoso.com",
                "accountHolderFullName": "Alice User",
                "currency": "USD",
                "balance": "5000",
                "activationDate": "2022-01-01",
                "paymentMethods": [
                    {
                        "id": "12345",
                        "type": "Visa",
                        "activationDate": "2022-01-01",
                        "expirationDate": "2025-01-01"
                    }
                ]
            }
        ]
    """
    try:
        user_name = req.route_params.get('user_name')
        logger.info(f"GET /accounts/user/{user_name}")
        
        container_name = os.getenv("AZURE_COSMOSDB_ACCOUNT_CONTAINER", "accounts")
        container = get_cosmos_client().get_container(container_name)
        
        # Query within partition for efficiency
        query = "SELECT * FROM c WHERE c.userName = @userName"
        parameters = [{"name": "@userName", "value": user_name}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=user_name,
            enable_cross_partition_query=False
        ))
        
        accounts = [Account(**item).model_dump() for item in items]
        
        return func.HttpResponse(
            json.dumps(accounts),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.exception("Error getting accounts by user name")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_account_details")
@app.route(route="accounts/{account_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_account_details(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get account details and available payment methods
    
    Retrieves complete information about a specific account, including associated payment methods.
    
    Path Parameters:
        account_id (str): Unique identifier of the account (must be numeric)
    
    Returns:
        200: Successfully retrieved account details
        - Response body: Account object with payment methods
        400: Invalid account ID format
        - Response body: {"error": "error message"}
        404: Account not found
        - Response body: {"error": "Account not found"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/accounts/1010
        Response: {
            "id": "1010",
            "userName": "bob.user@contoso.com",
            "accountHolderFullName": "Bob User",
            "currency": "EUR",
            "balance": "10000",
            "activationDate": "2022-01-01",
            "paymentMethods": [
                {
                    "id": "345678",
                    "type": "BankTransfer",
                    "activationDate": "2022-01-01",
                    "expirationDate": "9999-01-01"
                },
                {
                    "id": "55555",
                    "type": "Visa",
                    "activationDate": "2024-01-01",
                    "expirationDate": "2028-01-01"
                }
            ]
        }
    """
    try:
        account_id = req.route_params.get('account_id')
        logger.info(f"GET /accounts/{account_id}")
        
        if not account_id:
            return func.HttpResponse(
                json.dumps({"error": "AccountId is required"}),
                mimetype="application/json",
                status_code=400
            )
        
        if not account_id.isdigit():
            return func.HttpResponse(
                json.dumps({"error": "AccountId is not a valid number"}),
                mimetype="application/json",
                status_code=400
            )
        
        account = get_account_by_id(account_id)
        
        if account is None:
            return func.HttpResponse(
                json.dumps({"error": "Account not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        return func.HttpResponse(
            account.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as ve:
        logger.exception("Validation error")
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.exception("Error getting account details")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_payment_method_details")
@app.route(route="payment-methods/{payment_method_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_payment_method_details(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get payment method details with available balance
    
    Retrieves complete information about a specific payment method, including card details and available balance.
    
    Path Parameters:
        payment_method_id (str): Unique identifier of the payment method (must be numeric)
    
    Returns:
        200: Successfully retrieved payment method details
        - Response body: PaymentMethod object
        400: Invalid payment method ID format
        - Response body: {"error": "error message"}
        404: Payment method not found
        - Response body: {"error": "PaymentMethod not found"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/payment-methods/12345
        Response: {
            "id": "12345",
            "accountId": "1000",
            "type": "Visa",
            "activationDate": "2022-01-01",
            "expirationDate": "2025-01-01",
            "availableBalance": "500.00",
            "cardNumber": "1234567812345678"
        }
    """
    try:
        payment_method_id = req.route_params.get('payment_method_id')
        logger.info(f"GET /payment-methods/{payment_method_id}")
        
        if not payment_method_id:
            return func.HttpResponse(
                json.dumps({"error": "PaymentMethodId is required"}),
                mimetype="application/json",
                status_code=400
            )
        
        if not payment_method_id.isdigit():
            return func.HttpResponse(
                json.dumps({"error": "PaymentMethodId is not a valid number"}),
                mimetype="application/json",
                status_code=400
            )
        
        container_name = os.getenv("AZURE_COSMOSDB_PAYMENT_METHOD_CONTAINER", "payment-methods")
        container = get_cosmos_client().get_container(container_name)
        
        # Query to find payment method (cross-partition)
        query = "SELECT * FROM c WHERE c.id = @paymentMethodId"
        parameters = [{"name": "@paymentMethodId", "value": payment_method_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({"error": "Payment method not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        payment_method = PaymentMethod(**items[0])
        
        return func.HttpResponse(
            payment_method.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as ve:
        logger.exception("Validation error")
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.exception("Error getting payment method details")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.function_name(name="get_registered_beneficiary")
@app.route(route="accounts/{account_id}/beneficiaries", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_registered_beneficiary(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get list of registered beneficiaries for a specific account
    
    Retrieves all beneficiaries that have been registered for a given account. 
    These beneficiaries can be used as recipients for payments.
    
    Path Parameters:
        account_id (str): Unique identifier of the account (must be numeric)
    
    Returns:
        200: Successfully retrieved beneficiaries list
        - Response body: Array of Beneficiary objects
        400: Invalid account ID format
        - Response body: {"error": "error message"}
        500: Internal server error
        - Response body: {"error": "error message"}
    
    Example:
        GET /api/accounts/1000/beneficiaries
        Response: [
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
            }
        ]
    """
    try:
        account_id = req.route_params.get('account_id')
        logger.info(f"GET /accounts/{account_id}/beneficiaries")
        
        if not account_id:
            return func.HttpResponse(
                json.dumps({"error": "AccountId is required"}),
                mimetype="application/json",
                status_code=400
            )
        
        if not account_id.isdigit():
            return func.HttpResponse(
                json.dumps({"error": "AccountId is not a valid number"}),
                mimetype="application/json",
                status_code=400
            )
        
        container_name = os.getenv("AZURE_COSMOSDB_BENEFICIARY_CONTAINER", "beneficiaries")
        container = get_cosmos_client().get_container(container_name)
        
        # Query within partition for efficiency
        query = "SELECT * FROM c WHERE c.accountId = @accountId"
        parameters = [{"name": "@accountId", "value": account_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=account_id,
            enable_cross_partition_query=False
        ))
        
        beneficiaries = [Beneficiary(**item).model_dump() for item in items]
        
        return func.HttpResponse(
            json.dumps(beneficiaries),
            mimetype="application/json",
            status_code=200
        )
        
    except ValueError as ve:
        logger.exception("Validation error")
        return func.HttpResponse(
            json.dumps({"error": str(ve)}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        logger.exception("Error getting beneficiaries")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
