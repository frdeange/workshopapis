from typing import List, Optional
from pydantic import BaseModel, Field


class PaymentMethodSummary(BaseModel):
    """Summary information for a payment method associated with an account"""
    id: str = Field(..., description="Unique identifier of the payment method", example="pm-123")
    type: str = Field(..., description="Type of payment method (card, bank_transfer, etc.)", example="card")
    activationDate: Optional[str] = Field(None, description="Date when the payment method was activated", example="2024-01-15T10:30:00Z")
    expirationDate: Optional[str] = Field(None, description="Expiration date of the payment method", example="2025-12-31T23:59:59Z")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345",
                "type": "Visa",
                "activationDate": "2022-01-01",
                "expirationDate": "2025-01-01"
            }
        }


class PaymentMethod(BaseModel):
    """Complete payment method information including card details"""
    id: str = Field(..., description="Unique identifier of the payment method", example="pm-123")
    accountId: Optional[str] = Field(None, description="ID of the account this payment method belongs to", example="acc-456")
    type: str = Field(..., description="Type of payment method", example="card")
    activationDate: Optional[str] = Field(None, description="Date when the payment method was activated", example="2024-01-15T10:30:00Z")
    expirationDate: Optional[str] = Field(None, description="Expiration date of the payment method", example="2025-12-31T23:59:59Z")
    availableBalance: Optional[str] = Field(None, description="Available balance for this payment method", example="5000.00")
    cardNumber: Optional[str] = Field(None, description="Masked card number (last 4 digits visible)", example="**** **** **** 1234")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345",
                "accountId": "1000",
                "type": "Visa",
                "activationDate": "2022-01-01",
                "expirationDate": "2025-01-01",
                "availableBalance": "500.00",
                "cardNumber": "1234567812345678"
            }
        }


class Beneficiary(BaseModel):
    """Beneficiary information for making payments"""
    id: str = Field(..., description="Unique identifier of the beneficiary", example="ben-789")
    accountId: Optional[str] = Field(None, description="ID of the account this beneficiary belongs to", example="acc-456")
    fullName: str = Field(..., description="Full name of the beneficiary", example="John Doe")
    bankCode: str = Field(..., description="Bank code or routing number", example="SWIFT123")
    bankName: str = Field(..., description="Name of the beneficiary's bank", example="Example Bank")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "accountId": "1000",
                "fullName": "Mike ThePlumber",
                "bankCode": "123456789",
                "bankName": "Intesa Sanpaolo"
            }
        }


class Account(BaseModel):
    """Bank account information with associated payment methods"""
    id: str = Field(..., description="Unique identifier of the account", example="acc-456")
    userName: str = Field(..., description="Username of the account holder", example="johndoe")
    accountHolderFullName: str = Field(..., description="Full name of the account holder", example="John Doe")
    currency: str = Field(..., description="Currency code (ISO 4217)", example="EUR")
    activationDate: Optional[str] = Field(None, description="Date when the account was activated", example="2024-01-01T00:00:00Z")
    balance: Optional[str] = Field(None, description="Current account balance", example="10000.50")
    paymentMethods: Optional[List[PaymentMethodSummary]] = Field(None, description="List of payment methods associated with this account")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1000",
                "userName": "alice.user@contoso.com",
                "accountHolderFullName": "Alice User",
                "currency": "USD",
                "activationDate": "2022-01-01",
                "balance": "5000",
                "paymentMethods": [
                    {
                        "id": "12345",
                        "type": "Visa",
                        "activationDate": "2022-01-01",
                        "expirationDate": "2025-01-01"
                    }
                ]
            }
        }
