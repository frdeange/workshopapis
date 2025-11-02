from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Transaction(BaseModel):
    """Transaction record for an account"""
    id: str = Field(..., description="Unique identifier of the transaction", example="11")
    description: str = Field(..., description="Description of the transaction", example="Payment of the bill 334398")
    type: str = Field(..., description="Type of transaction (income or outcome)", example="outcome")
    recipientName: str = Field(..., description="Name of the recipient/sender", example="acme")
    recipientBankReference: str = Field(..., description="Bank reference of the recipient", example="098734213")
    accountId: str = Field(..., description="ID of the account this transaction belongs to", example="1010")
    paymentType: str = Field(..., description="Payment method type used", example="BankTransfer")
    amount: float = Field(..., description="Transaction amount (negative for debits, positive for credits)", example=-120.00)
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO 8601 timestamp of the transaction", example="2023-06-15T09:15:00")

    class Config:
        json_schema_extra = {
            "example": {
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
        }
