# Transaction API

Standalone Banking Transaction Management API built with FastAPI.

## Endpoints

- `GET /health` - Health check
- `GET /api/transactions/{account_id}` - Get last transactions for an account
- `GET /api/transactions/{account_id}/search?recipientName={name}` - Search transactions by recipient name
- `POST /api/transactions/{account_id}` - Notify a new transaction

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
docker build -t transaction-api .

# Run
docker run -p 8080:8080 transaction-api
```

## Environment Variables

- `PORT` - Port to run the API (default: 8080)
- `PROFILE` - Application profile (dev/prod, default: prod)

## Deployment to Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <your-registry> --image transaction-api:latest .

# Deploy to Container Apps
az containerapp create \
  --name transaction-api \
  --resource-group <your-rg> \
  --image <your-registry>.azurecr.io/transaction-api:latest \
  --target-port 8080 \
  --ingress external \
  --environment <your-environment>
```
