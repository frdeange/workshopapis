# Banking APIs - Azure Functions Project

## Language Convention

**Code Language**: ALL code, including variable names, function names, comments, log messages, and error messages MUST be in English.
**Chat Language**: Follow the user's language preference in conversations.

## Architecture Overview

This project has **two implementations** of the same banking APIs:

1. **Azure Functions** (`functions_apis/`) - **PRIMARY/ACTIVE** - Serverless implementation deployed to production
2. **FastAPI** (`aca_apis/`) - **LEGACY** - Original containerized APIs with Repository Pattern (kept for reference/comparison)

**When to work on each:**
- Use `functions_apis/` for all active development and production deployments
- Use `aca_apis/` only for reference, learning comparisons, or if specifically requested

**Critical Architecture Decisions:**
- **RBAC Authentication Only**: No connection strings. All Cosmos DB access uses `DefaultAzureCredential` via Managed Identity (Azure) or Azure CLI (local).
- **Singleton Pattern for Cosmos Client**: Each Function App uses `cosmos_client.py` with `CosmosDBClient` singleton to reuse connections.
- **Cross-Service Communication**: Payment API makes HTTP calls to Transaction API (not Cosmos direct) - see `TRANSACTION_API_URL` env var.
- **Private Networking**: Function Apps run in VNet with Private Endpoints. Public access disabled except for Azure service tags.

## Service Boundaries

```
Account API → Cosmos DB (accounts, payment-methods, beneficiaries)
Transaction API → Cosmos DB (transactions only)
Payment API → Cosmos DB (accounts) + HTTP → Transaction API
```

**Why Payment calls Transaction API**: To maintain service boundaries and ensure transaction creation logic stays centralized.

## Environment Variables - CRITICAL

**Standard Variable Names** (use these consistently):
- `AZURE_COSMOSDB_URI` - Full URL with port (e.g., `https://<account>.documents.azure.com:443/`)
- `AZURE_COSMOSDB_DATABASE` - Default: `BankingDB`
- Container names vary by service (e.g., `AZURE_COSMOSDB_ACCOUNT_CONTAINER`)

**Payment API additionally needs:**
- `TRANSACTION_API_URL` - Base URL to deployed Transaction API (e.g., `https://<app>.azurewebsites.net/api`)

**Local Development**: Each function has `local.settings.json` (gitignored). Example structure:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_COSMOSDB_URI": "https://<account>.documents.azure.com:443/",
    "AZURE_COSMOSDB_DATABASE": "BankingDB",
    "AZURE_COSMOSDB_ACCOUNT_CONTAINER": "accounts"
  }
}
```

## CosmosDB Query Patterns

**Key Pattern**: Always use parameterized queries with `@paramName` syntax:
```python
query = "SELECT * FROM c WHERE c.id = @accountId"
parameters = [{"name": "@accountId", "value": account_id}]
container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True)
```

**Cross-Partition Queries**: Required when querying by `id` (not partition key). Set `enable_cross_partition_query=True`.

**Partition Keys**:
- `accounts`: `/userName`
- `payment-methods`, `beneficiaries`, `transactions`: `/accountId`

## Development Workflows

**Local Testing (3 terminals required):**
```bash
# Terminal 1 - Account API
cd functions_apis/account_api && func start --port 7071

# Terminal 2 - Transaction API  
cd functions_apis/transaction_api && func start --port 7072

# Terminal 3 - Payment API (depends on Transaction API)
cd functions_apis/payment_api && func start --port 7073
```

**Seeding Database:**
```bash
python seed_cosmosdb.py  # Requires Azure CLI auth: az login
```

**Testing Endpoints:**
- Health checks: `curl http://localhost:707X/api/health`
- All routes use `/api/` prefix (Azure Functions convention)

## CI/CD - GitHub Actions with Self-Hosted Runner

**Critical Setup**: Deployment uses a **self-hosted runner inside Azure VNet** because Function Apps have Private Endpoints enabled.

**Path-Based Triggers**: Each workflow only deploys when its folder changes:
- `functions_apis/account_api/**` → `deploy-account-api.yml`
- Similar for transaction and payment APIs

**Required Secret**: `AZURE_CREDENTIALS` (Service Principal JSON format):
```json
{"clientId":"...","clientSecret":"...","subscriptionId":"...","tenantId":"..."}
```

**Manual Deployment**:
```bash
cd functions_apis/<api_name>
func azure functionapp publish <function-app-name> --python
```
Note: Only works from VNet (e.g., self-hosted runner VM) due to Private Endpoints.

## Code Patterns

**Function App Structure** (each API follows this):
```
function_app.py     # HTTP triggers, route handlers
cosmos_client.py    # Singleton CosmosDB client
models.py           # Pydantic models for validation
requirements.txt    # Dependencies (pinned versions)
host.json           # Function runtime config
```

**Error Handling Convention**:
```python
try:
    # Cosmos operation
except exceptions.CosmosResourceNotFoundError:
    return func.HttpResponse("Not found", status_code=404)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return func.HttpResponse("Internal error", status_code=500)
```

**Pydantic Validation**: All request/response bodies use Pydantic models. Functions parse with:
```python
data = PaymentRequest(**json.loads(req.get_body()))
```

## Network & Security Constraints

**Access Restrictions**:
- Function Apps use `AzureCloud` service tag for inbound access (allows Azure Portal testing)
- CORS configured for `https://portal.azure.com` (for portal testing)
- Direct public internet access blocked

**Authentication Flow**:
1. Local dev: `DefaultAzureCredential` → Azure CLI credentials
2. Deployed: `DefaultAzureCredential` → Managed Identity
3. Managed Identities have `Cosmos DB Built-in Data Contributor` role

## Common Gotchas

1. **Environment variable standardization**: Always use `AZURE_COSMOSDB_URI` and `AZURE_COSMOSDB_DATABASE` (not `COSMOS_ENDPOINT`/`COSMOS_DATABASE_NAME`).
2. **Payment API needs Transaction API running**: Local dev requires Transaction API on port 7072 or set `TRANSACTION_API_URL`.
3. **Cross-partition queries are expensive**: Use partition key when possible (e.g., query by `userName` for accounts).
4. **Flex Consumption Plan limitations**: No traditional publish profiles. Deployment requires SCM access or GitHub Actions with self-hosted runner.
5. **Private Endpoints deployment constraint**: Cannot deploy from local machine directly - must use self-hosted runner in VNet or temporarily allow access.

## Adding New Endpoints

1. Add HTTP trigger in `function_app.py`:
```python
@app.route(route="my-endpoint", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def my_endpoint(req: func.HttpRequest) -> func.HttpResponse:
```
2. Add Pydantic model to `models.py` if needed
3. Test locally with `func start`
4. Push to `main` branch - GitHub Actions auto-deploys

## Debugging

**View logs locally**: `func start` outputs all logs to console.

**View deployed logs**:
```bash
az functionapp logs show --name <app-name> --resource-group <rg-name> --follow
```

**Common issues**:
- "Login failed" in GitHub Actions → Check `AZURE_CREDENTIALS` secret format
- "Cosmos DB access denied" → Verify Managed Identity has RBAC role assigned
- "IP Forbidden 403" → Ensure calling from VNet or Azure service tag allowed
