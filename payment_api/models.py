from pydantic import BaseModel, Field
from typing import Optional


class PaymentRequest(BaseModel):
    """Payment request for processing a transaction"""
    accountId: str = Field(..., description="ID of the account making the payment", example="1010")
    paymentMethodId: str = Field(..., description="ID of the payment method to use", example="345678")
    beneficiaryId: str = Field(..., description="ID of the beneficiary receiving the payment", example="3")
    amount: float = Field(..., description="Amount to transfer (must be positive)", example=120.50, gt=0)
    description: Optional[str] = Field("", description="Optional description for the payment", example="Payment for services")

    class Config:
        json_schema_extra = {
            "example": {
                "accountId": "1010",
                "paymentMethodId": "345678",
                "beneficiaryId": "3",
                "amount": 120.50,
                "description": "Payment for consulting services"
            }
        }


class PaymentResponse(BaseModel):
    """Response after successfully processing a payment"""
    success: bool = Field(..., description="Whether the payment was successful", example=True)
    message: str = Field(..., description="Status message", example="Payment processed successfully")
    transaction: dict = Field(..., description="Created transaction details")
    newBalance: float = Field(..., description="New account balance after payment", example=9879.50)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
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
        }
