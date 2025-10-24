# Banking APIs - Azure Functions Workshop# Banking APIs Standalone



A complete banking API system built with Azure Functions and Azure Cosmos DB, featuring account management, transaction processing, and payment operations.Tres APIs REST independientes construidas con FastAPI para gestión bancaria, listas para desplegar en Azure Container Apps y gestionar con Azure API Management.



## 🏗️ Architecture## 📋 APIs Incluidas



This project contains two implementations of the same banking APIs:### 1. Account API (Puerto 8080)

Gestión de cuentas bancarias, métodos de pago y beneficiarios.

1. **FastAPI Applications** (in `aca_apis/`) - Original containerized APIs with Repository Pattern

2. **Azure Functions** (in `functions_apis/`) - Serverless implementation deployed to Azure**Endpoints:**

- `GET /health` - Health check

### Azure Functions Architecture- `GET /api/accounts/user/{user_name}` - Obtener cuentas de un usuario

- `GET /api/accounts/{account_id}` - Obtener detalles de una cuenta

```- `GET /api/payment-methods/{payment_method_id}` - Obtener detalles de método de pago

┌─────────────────┐- `GET /api/accounts/{account_id}/beneficiaries` - Obtener beneficiarios registrados

│  Account API    │ ──┐

│  (Function App) │   │### 2. Payment API (Puerto 8080)

└─────────────────┘   │Procesamiento de pagos bancarios.

                      │

┌─────────────────┐   │    ┌──────────────────┐**Endpoints:**

│ Transaction API │ ──┼───▶│  Azure Cosmos DB │- `GET /health` - Health check

│  (Function App) │   │    │   (NoSQL API)    │- `POST /api/payments` - Procesar un pago

└─────────────────┘   │    └──────────────────┘

                      │             │### 3. Transaction API (Puerto 8080)

┌─────────────────┐   │             │Gestión y consulta de transacciones bancarias.

│  Payment API    │ ──┘             │

│  (Function App) │                 │**Endpoints:**

└─────────────────┘                 │- `GET /health` - Health check

         │                          │- `GET /api/transactions/{account_id}` - Obtener últimas transacciones

         └──────────────────────────┘- `GET /api/transactions/{account_id}/search?recipientName={name}` - Buscar por destinatario

            (calls Transaction API)- `POST /api/transactions/{account_id}` - Notificar nueva transacción

```

## 🚀 Ejecución Local

**Azure Resources:**

- **3 Function Apps** (Python 3.12, Consumption Plan)Cada API puede ejecutarse independientemente:

- **1 Cosmos DB Account** (NoSQL API, RBAC authentication)

- **4 Containers**: accounts, payment-methods, beneficiaries, transactions```bash

# Navegar a la carpeta de la API

## 📁 Project Structurecd apis-standalone/account-api  # o payment-api, transaction-api



```# Instalar dependencias

workshopapis/pip install -e .

├── aca_apis/                          # Original FastAPI implementations

│   ├── account-api/                   # Account management API (FastAPI)# Ejecutar la API

│   ├── transaction-api/               # Transaction processing API (FastAPI)python main.py

│   └── payment-api/                   # Payment processing API (FastAPI)```

│

├── functions_apis/                    # Azure Functions implementationsLas APIs por defecto se ejecutan en el puerto 8080. Para ejecutarlas en paralelo localmente:

│   ├── account_api/                   # Account Function App

│   │   ├── function_app.py           # HTTP triggers```bash

│   │   ├── cosmos_client.py          # CosmosDB client (RBAC)# Terminal 1 - Account API

│   │   ├── models.py                 # Pydantic modelscd apis-standalone/account-api

│   │   ├── requirements.txt          # Python dependenciesPORT=8081 python main.py

│   │   ├── host.json                 # Function App config

│   │   └── local.settings.json       # Local environment variables# Terminal 2 - Payment API

│   │cd apis-standalone/payment-api

│   ├── transaction_api/               # Transaction Function AppPORT=8082 TRANSACTIONS_API_URL=http://localhost:8083 python main.py

│   │   ├── function_app.py

│   │   ├── cosmos_client.py# Terminal 3 - Transaction API

│   │   ├── models.pycd apis-standalone/transaction-api

│   │   ├── requirements.txtPORT=8083 python main.py

│   │   ├── host.json```

│   │   └── local.settings.json

│   │## 🐳 Docker

│   └── payment_api/                   # Payment Function App

│       ├── function_app.pyCada API tiene su propio Dockerfile. Para construir y ejecutar:

│       ├── cosmos_client.py

│       ├── models.py```bash

│       ├── requirements.txt# Construir imagen

│       ├── host.jsoncd apis-standalone/account-api

│       └── local.settings.jsondocker build -t account-api .

│

├── .github/# Ejecutar contenedor

│   └── workflows/                     # GitHub Actions for CI/CDdocker run -p 8080:8080 account-api

│       ├── deploy-account-api.yml```

│       ├── deploy-transaction-api.yml

│       └── deploy-payment-api.yml## ☁️ Despliegue en Azure Container Apps

│

├── seed_cosmosdb.py                   # Script to populate CosmosDB with test data### Paso 1: Crear Azure Container Registry (si no existe)

└── README.md                          # This file

``````bash

# Variables

## 🚀 Azure Functions DeploymentRESOURCE_GROUP="rg-banking-apis"

LOCATION="westeurope"

### Function AppsACR_NAME="acrbankingapis"  # debe ser único globalmente

ENVIRONMENT_NAME="env-banking-apis"

| Function App | Endpoint | Purpose |

|-------------|----------|---------|# Crear grupo de recursos

| `workshopenv-accountapi` | https://workshopenv-accountapi.azurewebsites.net | Account & beneficiary management |az group create --name $RESOURCE_GROUP --location $LOCATION

| `workshopenv-function-transactionapi` | https://workshopenv-function-transactionapi.azurewebsites.net | Transaction queries & creation |

| `workshopenv-function-paymentapi` | https://workshopenv-function-paymentapi.azurewebsites.net | Payment processing |# Crear Container Registry

az acr create \

### Deployment Methods  --resource-group $RESOURCE_GROUP \

  --name $ACR_NAME \

#### Option 1: GitHub Actions (Recommended)  --sku Basic \

  --admin-enabled true

Automatic deployment on push to `main` branch:

# Crear Container Apps Environment

```bashaz containerapp env create \

# Make changes to any API  --name $ENVIRONMENT_NAME \

git add .  --resource-group $RESOURCE_GROUP \

git commit -m "Update API"  --location $LOCATION

git push origin main```

```

### Paso 2: Construir y Subir Imágenes al Registry

GitHub Actions will automatically deploy only the changed Function App(s).

```bash

#### Option 2: Manual Deployment (requires network access)# Login en ACR

az acr login --name $ACR_NAME

```bash

# From each function directory# Construir y subir Account API

cd functions_apis/account_apicd apis-standalone/account-api

func azure functionapp publish workshopenv-accountapi --pythonaz acr build --registry $ACR_NAME --image account-api:latest .

```

# Construir y subir Payment API

## 📡 API Endpointscd ../payment-api

az acr build --registry $ACR_NAME --image payment-api:latest .

### Account API

- `GET /api/health` - Health check# Construir y subir Transaction API

- `GET /api/accounts/user/{user_name}` - Get accounts by usernamecd ../transaction-api

- `GET /api/accounts/{account_id}` - Get account details with payment methodsaz acr build --registry $ACR_NAME --image transaction-api:latest .

- `GET /api/payment-methods/{payment_method_id}` - Get payment method details```

- `GET /api/accounts/{account_id}/beneficiaries` - Get registered beneficiaries

### Paso 3: Desplegar Container Apps

### Transaction API

- `GET /api/health` - Health check```bash

- `GET /api/transactions/{account_id}` - Get last N transactions (default 10)# Obtener credenciales del ACR

- `GET /api/transactions/{account_id}/search?recipientName={name}` - Search by recipientACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)

- `POST /api/transactions/{account_id}` - Create new transactionACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

### Payment API

- `GET /api/health` - Health check# Desplegar Transaction API (primero, porque Payment depende de ella)

- `POST /api/payments` - Process payment (validates account, updates balance, creates transaction)az containerapp create \

  --name transaction-api \

## 🔧 Local Development  --resource-group $RESOURCE_GROUP \

  --environment $ENVIRONMENT_NAME \

### Prerequisites  --image $ACR_LOGIN_SERVER/transaction-api:latest \

  --target-port 8080 \

- Python 3.12  --ingress external \

- Azure Functions Core Tools 4.x  --registry-server $ACR_LOGIN_SERVER \

- Azure CLI (authenticated)  --registry-username $ACR_USERNAME \

- Access to Azure Cosmos DB  --registry-password $ACR_PASSWORD \

  --cpu 0.5 \

### Setup  --memory 1.0Gi



1. **Clone the repository**# Obtener URL de Transaction API

   ```bashTRANSACTION_API_URL=$(az containerapp show \

   git clone https://github.com/frdeange/workshops-apis.git  --name transaction-api \

   cd workshops-apis  --resource-group $RESOURCE_GROUP \

   ```  --query properties.configuration.ingress.fqdn -o tsv)

TRANSACTION_API_URL="https://$TRANSACTION_API_URL"

2. **Install dependencies for each Function App**

   ```bash# Desplegar Payment API

   cd functions_apis/account_apiaz containerapp create \

   pip install -r requirements.txt  --name payment-api \

     --resource-group $RESOURCE_GROUP \

   cd ../transaction_api  --environment $ENVIRONMENT_NAME \

   pip install -r requirements.txt  --image $ACR_LOGIN_SERVER/payment-api:latest \

     --target-port 8080 \

   cd ../payment_api  --ingress external \

   pip install -r requirements.txt  --registry-server $ACR_LOGIN_SERVER \

   ```  --registry-username $ACR_USERNAME \

  --registry-password $ACR_PASSWORD \

3. **Configure local settings**  --env-vars TRANSACTIONS_API_URL=$TRANSACTION_API_URL \

     --cpu 0.5 \

   Each Function App has a `local.settings.json` file with environment variables:  --memory 1.0Gi

   

   ```json# Desplegar Account API

   {az containerapp create \

     "IsEncrypted": false,  --name account-api \

     "Values": {  --resource-group $RESOURCE_GROUP \

       "AzureWebJobsStorage": "",  --environment $ENVIRONMENT_NAME \

       "FUNCTIONS_WORKER_RUNTIME": "python",  --image $ACR_LOGIN_SERVER/account-api:latest \

       "COSMOS_ENDPOINT": "https://workshopenv-cosmos.documents.azure.com:443/",  --target-port 8080 \

       "COSMOS_DATABASE_NAME": "BankingDB",  --ingress external \

       "ACCOUNTS_CONTAINER_NAME": "accounts",  --registry-server $ACR_LOGIN_SERVER \

       "PAYMENT_METHODS_CONTAINER_NAME": "payment-methods",  --registry-username $ACR_USERNAME \

       "BENEFICIARIES_CONTAINER_NAME": "beneficiaries",  --registry-password $ACR_PASSWORD \

       "TRANSACTIONS_CONTAINER_NAME": "transactions"  --cpu 0.5 \

     }  --memory 1.0Gi

   }

   ```# Obtener URLs de las APIs

echo "Account API: https://$(az containerapp show --name account-api --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"

4. **Seed the database** (first time only)echo "Payment API: https://$(az containerapp show --name payment-api --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"

   ```bashecho "Transaction API: $TRANSACTION_API_URL"

   python seed_cosmosdb.py```

   ```

## 🔄 Actualizar APIs Desplegadas

5. **Run Functions locally**

   ```bash

   In separate terminals:# Reconstruir y actualizar una imagen

   ```bashcd apis-standalone/account-api

   # Terminal 1 - Account APIaz acr build --registry $ACR_NAME --image account-api:latest .

   cd functions_apis/account_api

   func start --port 7071# Actualizar la Container App

   az containerapp update \

   # Terminal 2 - Transaction API  --name account-api \

   cd functions_apis/transaction_api  --resource-group $RESOURCE_GROUP \

   func start --port 7072  --image $ACR_LOGIN_SERVER/account-api:latest

   ```

   # Terminal 3 - Payment API

   cd functions_apis/payment_api## 🌐 Integración con Azure API Management

   func start --port 7073

   ```Una vez desplegadas las APIs en Container Apps, puedes importarlas en Azure API Management:



6. **Test endpoints**```bash

   ```bash# Crear instancia de API Management (puede tardar ~30-40 min)

   # Health checksAPIM_NAME="apim-banking"

   curl http://localhost:7071/api/healthPUBLISHER_EMAIL="admin@contoso.com"

   curl http://localhost:7072/api/healthPUBLISHER_NAME="Contoso Banking"

   curl http://localhost:7073/api/health

   az apim create \

   # Get account details  --name $APIM_NAME \

   curl http://localhost:7071/api/accounts/1000  --resource-group $RESOURCE_GROUP \

     --publisher-email $PUBLISHER_EMAIL \

   # Get transactions  --publisher-name "$PUBLISHER_NAME" \

   curl http://localhost:7072/api/transactions/1010  --sku-name Developer \

   ```  --location $LOCATION



## 🗄️ Database Schema# Las APIs se pueden importar desde el portal o mediante CLI

# añadiendo los backends de Container Apps

### Cosmos DB Containers```



#### accounts## 🧪 Pruebas

**Partition Key:** `/userName`

```json```bash

{# Probar Account API

  "id": "1000",curl https://<account-api-url>/health

  "userName": "alice",curl https://<account-api-url>/api/accounts/user/bob.user@contoso.com

  "balance": 5000.0

}# Probar Transaction API

```curl https://<transaction-api-url>/health

curl https://<transaction-api-url>/api/transactions/1010

#### payment-methods

**Partition Key:** `/accountId`# Probar Payment API

```jsoncurl -X POST https://<payment-api-url>/api/payments \

{  -H "Content-Type: application/json" \

  "id": "pm-001",  -d '{

  "accountId": "1000",    "description": "Test payment",

  "type": "credit_card",    "recipientName": "Test Recipient",

  "last4Digits": "4242",    "recipientBankCode": "123456",

  "expiryDate": "12/25"    "accountId": "1010",

}    "paymentMethodId": "345678",

```    "paymentType": "BankTransfer",

    "amount": 50.00,

#### beneficiaries    "timestamp": "2025-10-22T10:00:00"

**Partition Key:** `/accountId`  }'

```json```

{

  "id": "ben-001",## 📊 Monitoreo

  "accountId": "1000",

  "name": "Bob's Account",Las Container Apps incluyen Application Insights por defecto. Para ver logs:

  "bankReference": "ES1234567890"

}```bash

```# Ver logs de una Container App

az containerapp logs show \

#### transactions  --name account-api \

**Partition Key:** `/accountId`  --resource-group $RESOURCE_GROUP \

```json  --follow

{```

  "id": "txn-001",

  "accountId": "1000",## 🏗️ Arquitectura

  "description": "Payment to SuperMart",

  "type": "debit",```

  "recipientName": "SuperMart",┌─────────────────────┐

  "recipientBankReference": "ES9876543210",│  Azure API Management│

  "paymentType": "credit_card",│    (Opcional)       │

  "amount": 150.0,└──────────┬──────────┘

  "timestamp": "2025-10-24T10:30:00Z"           │

}    ┌──────┴──────┬───────────────┐

```    │             │               │

┌───▼────┐   ┌───▼─────┐   ┌────▼────┐

## 🔐 Authentication & Security│Account │   │ Payment │   │Transaction│

│  API   │   │   API   │───│   API   │

### Cosmos DB Access└────────┘   └─────────┘   └─────────┘

- **Authentication Method:** RBAC (Role-Based Access Control)    │             │              │

- **Credential Type:** DefaultAzureCredential (Managed Identity in Azure, Azure CLI locally)    └─────────────┴──────────────┘

- **Required Role:** `Cosmos DB Built-in Data Contributor`              │

    ┌─────────▼──────────┐

### Network Security    │ Container Apps Env │

- Function Apps use **Private Endpoints** (VNet integration)    │  + App Insights    │

- Deployment requires GitHub Actions or network access to VNet    └────────────────────┘

              │

## 🧪 Testing    ┌─────────▼──────────┐

    │ Container Registry │

### Sample Test Data    └────────────────────┘

```

After running `seed_cosmosdb.py`, you'll have:

## 📝 Notas

- **3 Accounts:** Alice (1000), Bob (1010), Charlie (1020)

- **5 Payment Methods:** Various cards and bank accounts- Cada API usa datos en memoria para pruebas (no hay persistencia)

- **5 Beneficiaries:** Registered recipients- Las APIs están diseñadas para ser stateless

- **8 Transactions:** Sample payment history- El Payment API puede notificar opcionalmente al Transaction API

- Todas las APIs exponen un endpoint `/health` para health checks

### Example Requests- Los Dockerfiles incluyen HEALTHCHECK para Container Apps



**Get Alice's account with payment methods:**## 🔐 Seguridad

```bash

curl https://workshopenv-accountapi.azurewebsites.net/api/accounts/1000Para producción, considera:

```- Usar Managed Identity en lugar de credenciales del ACR

- Implementar autenticación/autorización (Azure AD, API Keys)

**Search Bob's transactions to SuperMart:**- Configurar CORS según tus necesidades

```bash- Habilitar HTTPS only

curl "https://workshopenv-function-transactionapi.azurewebsites.net/api/transactions/1010/search?recipientName=SuperMart"- Implementar rate limiting en API Management

```

## 📚 Referencias

**Process a payment:**

```bash- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)

curl -X POST https://workshopenv-function-paymentapi.azurewebsites.net/api/payments \- [Azure Container Registry Documentation](https://learn.microsoft.com/azure/container-registry/)

  -H "Content-Type: application/json" \- [Azure API Management Documentation](https://learn.microsoft.com/azure/api-management/)

  -d '{- [FastAPI Documentation](https://fastapi.tiangolo.com/)

    "accountId": "1000",
    "paymentMethodId": "pm-001",
    "beneficiaryId": "ben-001",
    "amount": 100.0,
    "description": "Monthly payment"
  }'
```

## 📦 Dependencies

### Python Packages (all Function Apps)
- `azure-functions` - Azure Functions runtime
- `azure-cosmos==4.14.0` - Cosmos DB SDK
- `azure-identity==1.25.0` - Azure authentication
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

### Payment API Additional
- `requests` - HTTP client (to call Transaction API)

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

Each Function App has its own workflow that:
1. Triggers on push to `main` (only when its folder changes)
2. Allows manual execution
3. Sets up Python 3.12
4. Installs dependencies
5. Deploys to Azure Function App

**Path-based triggers:**
- Account API: `functions_apis/account_api/**`
- Transaction API: `functions_apis/transaction_api/**`
- Payment API: `functions_apis/payment_api/**`

## 📝 Environment Variables

### Required for all Function Apps

| Variable | Description | Example |
|----------|-------------|---------|
| `COSMOS_ENDPOINT` | Cosmos DB endpoint URL | `https://workshopenv-cosmos.documents.azure.com:443/` |
| `COSMOS_DATABASE_NAME` | Database name | `BankingDB` |
| `ACCOUNTS_CONTAINER_NAME` | Accounts container | `accounts` |
| `PAYMENT_METHODS_CONTAINER_NAME` | Payment methods container | `payment-methods` |
| `BENEFICIARIES_CONTAINER_NAME` | Beneficiaries container | `beneficiaries` |
| `TRANSACTIONS_CONTAINER_NAME` | Transactions container | `transactions` |

### Payment API Additional

| Variable | Description | Example |
|----------|-------------|---------|
| `TRANSACTION_API_URL` | Transaction API base URL | `https://workshopenv-function-transactionapi.azurewebsites.net/api` |

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

---

**Workshop Environment Details:**
- Resource Group: `RG-WorkshopEnvironment`
- Location: `Sweden Central`
- Subscription: `0acbc8a1-0f3e-498e-b86b-6fa5468730e2`
