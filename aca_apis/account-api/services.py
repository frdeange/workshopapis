from typing import List, Optional
from models import Account, PaymentMethod, PaymentMethodSummary, Beneficiary
from repositories import AccountRepository, PaymentMethodRepository, BeneficiaryRepository
import logging

logger = logging.getLogger(__name__)


class AccountService:
    """
    Business logic layer for Account operations.
    
    This service uses repositories to access data from CosmosDB
    and applies business rules and validations.
    """
    
    def __init__(self):
        """Initialize service with repository instances."""
        self.account_repo = AccountRepository()
        self.payment_method_repo = PaymentMethodRepository()
        self.beneficiary_repo = BeneficiaryRepository()
    
    def get_account_details(self, account_id: str) -> Optional[Account]:
        """
        Get account details with payment methods.
        
        Note: We need to query across partitions to find the account
        since we only have the account_id, not the userName.
        For better performance, consider passing userName as well.
        """
        logger.info("Request to get_account_details with account_id: %s", account_id)
        
        if not account_id:
            raise ValueError("AccountId is empty or null")
        if not account_id.isdigit():
            raise ValueError("AccountId is not a valid number")
        
        # Query to find account (cross-partition since we don't have userName)
        query = "SELECT * FROM c WHERE c.id = @accountId"
        parameters = [{"name": "@accountId", "value": account_id}]
        
        items = list(self.account_repo.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            logger.warning(f"Account not found: {account_id}")
            return None
        
        account = Account(**items[0])
        
        # Get payment methods for this account
        payment_methods = self.payment_method_repo.get_by_account_id(account_id)
        
        # Convert to summary format
        account.paymentMethods = [
            PaymentMethodSummary(
                id=pm.id,
                type=pm.type,
                activationDate=pm.activationDate,
                expirationDate=pm.expirationDate
            )
            for pm in payment_methods
        ]
        
        return account
    
    def get_payment_method_details(self, payment_method_id: str) -> Optional[PaymentMethod]:
        """
        Get payment method details.
        
        Note: We need to query across partitions since we only have payment_method_id,
        not the accountId (partition key).
        """
        logger.info("Request to get_payment_method_details with payment_method_id: %s", payment_method_id)
        
        if not payment_method_id:
            raise ValueError("PaymentMethodId is empty or null")
        if not payment_method_id.isdigit():
            raise ValueError("PaymentMethodId is not a valid number")
        
        # Query to find payment method (cross-partition)
        query = "SELECT * FROM c WHERE c.id = @paymentMethodId"
        parameters = [{"name": "@paymentMethodId", "value": payment_method_id}]
        
        items = list(self.payment_method_repo.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            logger.warning(f"Payment method not found: {payment_method_id}")
            return None
        
        return PaymentMethod(**items[0])
    
    def get_registered_beneficiary(self, account_id: str) -> List[Beneficiary]:
        """
        Get registered beneficiaries for an account.
        
        This is an efficient partition-scoped query since we have the accountId.
        """
        logger.info("Request to get_registered_beneficiary with account_id: %s", account_id)
        
        if not account_id:
            raise ValueError("AccountId is empty or null")
        if not account_id.isdigit():
            raise ValueError("AccountId is not a valid number")
        
        return self.beneficiary_repo.get_by_account_id(account_id)


class UserService:
    """
    Business logic layer for User-related Account operations.
    
    This service handles queries related to users and their accounts.
    """
    
    def __init__(self):
        """Initialize service with repository instance."""
        self.account_repo = AccountRepository()
    
    def get_accounts_by_user_name(self, user_name: str) -> List[Account]:
        """
        Get all accounts for a specific user.
        
        This is an efficient partition-scoped query since userName is the partition key.
        """
        logger.info(f"Request to get_accounts_by_user_name with user_name: {user_name}")
        return self.account_repo.get_by_user_name(user_name)
