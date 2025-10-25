# Banking APIs - Azure Functions Workshop

A complete banking API system built with Azure Functions and Azure Cosmos DB, featuring account management, transaction processing, and payment operations.

## 🏗️ Architecture

This project contains two implementations of the same banking APIs:

1. **FastAPI Applications** (in `aca_apis/`) - Original containerized APIs with Repository Pattern
2. **Azure Functions** (in `functions_apis/`) - Serverless implementation deployed to Azure

### Azure Functions Architecture

```
┌─────────────────┐
│  Account API    │ ──┐
│  (Function App) │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │    ┌──────────────────┐
│ Transaction API │ ──┼───▶│  Azure Cosmos DB │
│  (Function App) │   │    │   (NoSQL API)    │
└─────────────────┘   │    └──────────────────┘
                      │             
┌─────────────────┐   │             
│  Payment API    │ ──┘             
│  (Function App) │                 
└─────────────────┘                 
         │                          
         └──────────────────────────┘
            (calls Transaction API)
```

**Azure Resources:**
- **3 Function Apps** (Python 3.12, Flex Consumption Plan)
- **1 Cosmos DB Account** (NoSQL API, RBAC authentication)
- **4 Containers**: accounts, payment-methods, beneficiaries, transactions

## 📁 Project Structure

```
workshopapis/
├── aca_apis/                          # Original FastAPI implementations
│   ├── account-api/                   # Account management API (FastAPI)
│   ├── transaction-api/               # Transaction processing API (FastAPI)
│   └── payment-api/                   # Payment processing API (FastAPI)
│
├── functions_apis/                    # Azure Functions implementations
│   ├── account_api/                   # Account Function App
│   │   ├── function_app.py           # HTTP triggers
│   │   ├── cosmos_client.py          # CosmosDB client (RBAC)
│   │   ├── models.py                 # Pydantic models
│   │   ├── requirements.txt          # Python dependencies
│   │   ├── host.json                 # Function App config
│   │   └── local.settings.json       # Local environment variables
│   │
│   ├── transaction_api/               # Transaction Function App
│   │   ├── function_app.py
│   │   ├── cosmos_client.py
│   │   ├── models.py
│   │   ├── requirements.txt
│   │   ├── host.json
│   │   └── local.settings.json
│   │
│   └── payment_api/                   # Payment Function App
│       ├── function_app.py
│       ├── cosmos_client.py
│       ├── models.py
│       ├── requirements.txt
│       ├── host.json
│       └── local.settings.json
│
├── .github/
│   └── workflows/                     # GitHub Actions for CI/CD
│       ├── deploy-account-api.yml
│       ├── deploy-transaction-api.yml
│       └── deploy-payment-api.yml
│
├── seed_cosmosdb.py                   # Script to populate CosmosDB with test data
└── README.md                          # This file
```

## 🚀 Azure Functions Deployment

### Function Apps

| Function App | Purpose |
|-------------|---------|
| Account API | Account & beneficiary management |
| Transaction API | Transaction queries & creation |
| Payment API | Payment processing |

### Deployment Methods

#### Option 1: GitHub Actions (Recommended)

Automatic deployment on push to `main` branch:

```bash
# Make changes to any API
git add .
git commit -m "Update API"
git push origin main
```

GitHub Actions will automatically deploy only the changed Function App(s).

**Requirements:**
- Self-hosted GitHub Runner (running in Azure VNet)
- Configured GitHub Secrets:
  - `AZURE_CREDENTIALS` - Service Principal credentials JSON

#### Option 2: Manual Deployment (requires network access)

```bash
# From each function directory
cd functions_apis/account_api
func azure functionapp publish <your-function-app-name> --python
```

## 📡 API Endpoints

### Account API
- `GET /api/health` - Health check
- `GET /api/accounts/user/{user_name}` - Get accounts by username
- `GET /api/accounts/{account_id}` - Get account details with payment methods
- `GET /api/payment-methods/{payment_method_id}` - Get payment method details
- `GET /api/accounts/{account_id}/beneficiaries` - Get registered beneficiaries

### Transaction API
- `GET /api/health` - Health check
- `GET /api/transactions/{account_id}` - Get last N transactions (default 10)
- `GET /api/transactions/{account_id}/search?recipientName={name}` - Search by recipient
- `POST /api/transactions/{account_id}` - Create new transaction

### Payment API
- `GET /api/health` - Health check
- `POST /api/payments` - Process payment (validates account, updates balance, creates transaction)

## 🔧 Local Development

### Prerequisites

- Python 3.12
- Azure Functions Core Tools 4.x
- Azure CLI (authenticated)
- Access to Azure Cosmos DB

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/frdeange/workshopapis.git
   cd workshopapis
   ```

2. **Install dependencies for each Function App**
   ```bash
   cd functions_apis/account_api
   pip install -r requirements.txt
   
   cd ../transaction_api
   pip install -r requirements.txt
   
   cd ../payment_api
   pip install -r requirements.txt
   ```

3. **Configure local settings**
   
   Each Function App has a `local.settings.json` file with environment variables:
   
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "COSMOS_ENDPOINT": "https://<your-cosmos-account>.documents.azure.com:443/",
       "COSMOS_DATABASE_NAME": "BankingDB",
       "COSMOS_ACCOUNTS_CONTAINER_NAME": "accounts",
       "COSMOS_PAYMENT_METHODS_CONTAINER_NAME": "payment-methods",
       "COSMOS_BENEFICIARIES_CONTAINER_NAME": "beneficiaries",
       "COSMOS_TRANSACTIONS_CONTAINER_NAME": "transactions"
     }
   }
   ```

4. **Seed the database** (first time only)
   ```bash
   python seed_cosmosdb.py
   ```

5. **Run Functions locally**
   ```bash
   # In separate terminals:
   
   # Terminal 1 - Account API
   cd functions_apis/account_api
   func start --port 7071
   
   # Terminal 2 - Transaction API
   cd functions_apis/transaction_api
   func start --port 7072
   
   # Terminal 3 - Payment API
   cd functions_apis/payment_api
   func start --port 7073
   ```

6. **Test endpoints**
   ```bash
   # Health checks
   curl http://localhost:7071/api/health
   curl http://localhost:7072/api/health
   curl http://localhost:7073/api/health
   
   # Get account details
   curl http://localhost:7071/api/accounts/1000
   
   # Get transactions
   curl http://localhost:7072/api/transactions/1010
   ```

## 📝 Environment Variables

### Required for all Function Apps

| Variable | Description | Example |
|----------|-------------|---------|
| `COSMOS_ENDPOINT` | Cosmos DB endpoint URL | `https://<your-cosmos-account>.documents.azure.com:443/` |
| `COSMOS_DATABASE_NAME` | Database name | `BankingDB` |
| `ACCOUNTS_CONTAINER_NAME` | Accounts container | `accounts` |
| `PAYMENT_METHODS_CONTAINER_NAME` | Payment methods container | `payment-methods` |
| `BENEFICIARIES_CONTAINER_NAME` | Beneficiaries container | `beneficiaries` |
| `TRANSACTIONS_CONTAINER_NAME` | Transactions container | `transactions` |

### Payment API Additional

| Variable | Description | Example |
|----------|-------------|---------|
| `TRANSACTION_API_URL` | Transaction API base URL | `https://<your-transaction-api>.azurewebsites.net/api` |

## 🆚 FastAPI vs Azure Functions

This project contains both implementations for comparison:

| Feature | FastAPI (aca_apis/) | Azure Functions (functions_apis/) |
|---------|---------------------|-----------------------------------|
| **Pattern** | Repository Pattern | Direct CosmosDB queries |
| **Deployment** | Container Apps / Docker | Function Apps (serverless) |
| **Scaling** | Manual/auto scaling | Automatic (consumption plan) |
| **Cost** | Always-on containers | Pay-per-execution |
| **Route Prefix** | Custom routes | `/api` prefix (e.g., `/api/accounts`) |

## 📚 Additional Resources

- [Azure Functions Python Developer Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Azure Cosmos DB Python SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/sdk-python)
- [GitHub Actions for Azure](https://learn.microsoft.com/azure/developer/github/github-actions)

## 👥 Contributing

This is a workshop project. For questions or improvements, please open an issue or pull request.

## 📄 License

This project is created for educational purposes as part of an Azure workshop.
