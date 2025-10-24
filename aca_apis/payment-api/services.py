import logging
import os
from typing import Optional
import uuid
import requests

from models import Payment, Transaction

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, transaction_api_url: Optional[str] = None):
        # Prefer explicit constructor param. If not provided, read from env.
        env_url = os.environ.get("TRANSACTIONS_API_URL")
        if transaction_api_url:
            self.transaction_api_url = transaction_api_url
        elif env_url:
            self.transaction_api_url = env_url
        else:
            # Make it optional - just log a warning if not configured
            logger.warning(
                "TRANSACTIONS_API_URL is not configured. Transaction notifications will be skipped."
            )
            self.transaction_api_url = None

    def process_payment(self, payment: Payment):
        # validations similar to Java implementation
        if not payment.accountId:
            raise ValueError("AccountId is empty or null")
        if not payment.accountId.isdigit():
            raise ValueError("AccountId is not a valid number")

        if (payment.paymentType or "").lower() != "transfer" and (not payment.paymentMethodId):
            raise ValueError("paymentMethodId is empty or null")

        if payment.paymentMethodId and not payment.paymentMethodId.isdigit():
            raise ValueError("paymentMethodId is not a valid number")

        logger.info("Payment successful for: %s", payment.model_dump_json())

        # Only notify transaction if URL is configured
        if self.transaction_api_url:
            transaction = self._convert_payment_to_transaction(payment)
            logger.info("Notifying payment [%s] for account[%s]..", payment.description, transaction.accountId)

            try:
                url = f"{self.transaction_api_url}/transactions/{payment.accountId}"
                resp = requests.post(url, json=transaction.model_dump(), timeout=5)
                resp.raise_for_status()
                logger.info("Transaction notified for: %s", transaction.model_dump_json())
            except Exception as ex:
                logger.exception("Failed to notify transaction: %s", ex)
                # Don't fail the payment if notification fails
        else:
            logger.info("Transaction notification skipped (TRANSACTIONS_API_URL not configured)")

    def _convert_payment_to_transaction(self, payment: Payment) -> Transaction:
        return Transaction(
            id=str(uuid.uuid4()),
            description=payment.description,
            type="outcome",
            recipientName=payment.recipientName,
            recipientBankReference=payment.recipientBankCode,
            accountId=payment.accountId,
            paymentType=payment.paymentType,
            amount=payment.amount,
            timestamp=payment.timestamp,
        )
