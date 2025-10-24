import os
import logging
from fastapi import FastAPI, HTTPException, status, Query
from typing import List
import uvicorn
from logging_config import configure_logging
from models import Transaction
from services import TransactionService

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)

# Initialize service
transaction_service = TransactionService()

# Create FastAPI app
app = FastAPI(
    title="Transaction API",
    description="Banking Transaction Management API",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/transactions/{account_id}", response_model=List[Transaction])
def get_last_transactions(account_id: str):
    """Get the last transactions for an account"""
    logger.info("GET /transactions/%s", account_id)
    try:
        transactions = transaction_service.get_last_transactions(account_id)
        return transactions
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error getting transactions")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/transactions/{account_id}/search", response_model=List[Transaction])
def get_transactions_by_recipient_name(
    account_id: str, 
    recipient_name: str = Query(..., alias="recipientName")
):
    """Get transactions by recipient name"""
    logger.info("GET /transactions/%s/search?recipientName=%s", account_id, recipient_name)
    try:
        transactions = transaction_service.get_transactions_by_recipient_name(account_id, recipient_name)
        return transactions
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error searching transactions")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/transactions/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def notify_transaction(account_id: str, transaction: Transaction):
    """Notify a new transaction for an account"""
    logger.info("POST /transactions/%s", account_id)
    try:
        transaction_service.notify_transaction(account_id, transaction)
    except ValueError as ve:
        logger.exception("Validation error while notifying transaction")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        logger.exception("Runtime error while notifying transaction")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(re))
    except Exception:
        logger.exception("Unexpected error while notifying transaction")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")

if __name__ == "__main__":
    profile = os.environ.get("PROFILE", "prod")
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Starting Transaction API with profile: {profile}, port: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
