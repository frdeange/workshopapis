import os
import logging
from fastapi import FastAPI, HTTPException, status
import uvicorn
from logging_config import configure_logging
from models import Payment
from services import PaymentService

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)

# Initialize service
payment_service = PaymentService()

# Create FastAPI app
app = FastAPI(
    title="Payment API",
    description="Banking Payment Processing API",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/payments", status_code=status.HTTP_200_OK)
def process_payment(payment: Payment):
    """Process a payment request"""
    logger.info("POST /payments - Processing payment for account: %s", payment.accountId)
    try:
        payment_service.process_payment(payment)
        return {"status": "success", "message": "Payment processed successfully"}
    except ValueError as ve:
        logger.exception("Validation error processing payment")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error processing payment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    profile = os.environ.get("PROFILE", "prod")
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Starting Payment API with profile: {profile}, port: {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
