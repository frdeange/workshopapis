from typing import List
from models import Transaction
from repositories import TransactionRepository
import logging

logger = logging.getLogger(__name__)


class TransactionService:
    """
    Business logic layer for Transaction operations.
    
    This service uses repository to access data from CosmosDB
    and applies business rules and validations.
    """
    
    def __init__(self):
        """Initialize service with repository instance."""
        self.transaction_repo = TransactionRepository()
        
        # Configuration for "last transactions" limit
        self.last_transactions_limit = 10
    
    def get_last_transactions(self, account_id: str) -> List[Transaction]:
        """
        Get the last N transactions for an account.
        
        Args:
            account_id: The account ID to fetch transactions for
            
        Returns:
            List of recent Transaction objects
            
        Raises:
            ValueError: If account_id is invalid
        """
        logger.info("Request to get_last_transactions with account_id: %s", account_id)
        
        if not account_id:
            raise ValueError("AccountId is empty or null")
        if not account_id.isdigit():
            raise ValueError("AccountId is not a valid number")
        
        # Fetch transactions from CosmosDB with limit
        transactions = self.transaction_repo.get_by_account_id(
            account_id, 
            limit=self.last_transactions_limit
        )
        
        logger.info(f"Retrieved {len(transactions)} last transactions for account {account_id}")
        return transactions
    
    def get_transactions_by_recipient_name(self, account_id: str, recipient_name: str) -> List[Transaction]:
        """
        Search transactions by recipient name (case-insensitive).
        
        Args:
            account_id: The account ID to search within
            recipient_name: The recipient name to search for
            
        Returns:
            List of matching Transaction objects
            
        Raises:
            ValueError: If parameters are invalid
        """
        logger.info("Request to get_transactions_by_recipient_name with account_id: %s and recipient_name: %s", 
                   account_id, recipient_name)
        
        if not account_id:
            raise ValueError("AccountId is empty or null")
        if not account_id.isdigit():
            raise ValueError("AccountId is not a valid number")
        if not recipient_name:
            raise ValueError("RecipientName is empty or null")
        
        # Search in CosmosDB
        transactions = self.transaction_repo.search_by_recipient_name(
            account_id, 
            recipient_name
        )
        
        logger.info(f"Found {len(transactions)} transactions matching recipient name '{recipient_name}'")
        return transactions
    
    def notify_transaction(self, account_id: str, transaction: Transaction):
        """
        Store a new transaction notification.
        
        This method is called when a payment is processed to record
        the transaction in the database.
        
        Args:
            account_id: The account ID for the transaction
            transaction: The Transaction object to store
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If account doesn't exist (optional validation)
        """
        logger.info("Notifying new transaction for account: %s", account_id)
        
        if not account_id:
            raise ValueError("AccountId is empty or null")
        if not account_id.isdigit():
            raise ValueError("AccountId is not a valid number")
        
        # Ensure the transaction has the correct accountId
        transaction.accountId = account_id
        
        # Optional: Verify account exists by checking if there are any transactions
        # This is a business decision - you might want to skip this check
        # to allow transactions for new accounts
        try:
            existing_count = self.transaction_repo.count_by_account_id(account_id)
            logger.info(f"Account {account_id} has {existing_count} existing transactions")
        except Exception as e:
            logger.warning(f"Could not verify account existence: {e}")
            # Continue anyway - allow transactions for new accounts
        
        # Create the transaction in CosmosDB
        created_transaction = self.transaction_repo.create(transaction)
        
        logger.info("Transaction added successfully: %s", created_transaction.model_dump_json())
