import os
import logging
from fastapi import FastAPI, HTTPException, status
from typing import List
import uvicorn
from logging_config import configure_logging
from models import Account, PaymentMethod, Beneficiary
from services import AccountService, UserService

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)

# Initialize services
account_service = AccountService()
user_service = UserService()

# Create FastAPI app
app = FastAPI(
    title="Account API",
    description="Banking Account Management API",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/accounts/user/{user_name}", response_model=List[Account])
def get_accounts_by_user_name(user_name: str):
    """Get all accounts for a specific user"""
    logger.info("GET /accounts/user/%s", user_name)
    try:
        accounts = user_service.get_accounts_by_user_name(user_name)
        return accounts
    except Exception as e:
        logger.exception("Error getting accounts by user name")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/accounts/{account_id}", response_model=Account)
def get_account_details(account_id: str):
    """Get account details and available payment methods"""
    logger.info("GET /accounts/%s", account_id)
    try:
        account = account_service.get_account_details(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error getting account details")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/payment-methods/{payment_method_id}", response_model=PaymentMethod)
def get_payment_method_details(payment_method_id: str):
    """Get payment method details with available balance"""
    logger.info("GET /payment-methods/%s", payment_method_id)
    try:
        payment_method = account_service.get_payment_method_details(payment_method_id)
        if payment_method is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        return payment_method
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error getting payment method details")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/accounts/{account_id}/beneficiaries", response_model=List[Beneficiary])
def get_registered_beneficiary(account_id: str):
    """Get list of registered beneficiaries for a specific account"""
    logger.info("GET /accounts/%s/beneficiaries", account_id)
    try:
        beneficiaries = account_service.get_registered_beneficiary(account_id)
        return beneficiaries
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error getting beneficiaries")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    profile = os.environ.get("PROFILE", "prod")
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Starting Account API with profile: {profile}, port: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
