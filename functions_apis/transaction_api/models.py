from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Transaction(BaseModel):
    id: str
    description: str
    type: str
    recipientName: str
    recipientBankReference: str
    accountId: str
    paymentType: str
    amount: float
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
