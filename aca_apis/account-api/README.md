# Account API

Standalone Banking Account Management API built with FastAPI.

## Endpoints

- `GET /health` - Health check
- `GET /api/accounts/user/{user_name}` - Get all accounts for a user
- `GET /api/accounts/{account_id}` - Get account details
- `GET /api/payment-methods/{payment_method_id}` - Get payment method details
- `GET /api/accounts/{account_id}/beneficiaries` - Get registered beneficiaries

## Running Locally

```bash
# Install dependencies
pip install -e .

# Run the API
python main.py
```

The API will be available at `http://localhost:8080`

## Docker

```bash
# Build
docker build -t account-api .

# Run
docker run -p 8080:8080 account-api
```

## Environment Variables

- `PORT` - Port to run the API (default: 8080)
- `PROFILE` - Application profile (dev/prod, default: prod)

## Deployment to Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <your-registry> --image account-api:latest .

# Deploy to Container Apps
az containerapp create \
  --name account-api \
  --resource-group <your-rg> \
  --image <your-registry>.azurecr.io/account-api:latest \
  --target-port 8080 \
  --ingress external \
  --environment <your-environment>
```
