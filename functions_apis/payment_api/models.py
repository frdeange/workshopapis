from pydantic import BaseModel
from typing import Optional


class PaymentRequest(BaseModel):
    accountId: str
    paymentMethodId: str
    beneficiaryId: str
    amount: float
    description: Optional[str] = ""
