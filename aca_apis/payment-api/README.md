# Payment API

Standalone Banking Payment Processing API built with FastAPI.

## Endpoints

- `GET /health` - Health check
- `POST /api/payments` - Process a payment

## Running Locally

```bash
# Install dependencies
pip install -e .

# Run the API (optionally set TRANSACTIONS_API_URL)
export TRANSACTIONS_API_URL=http://localhost:8082
python main.py
```

The API will be available at `http://localhost:8080`

## Docker

```bash
# Build
docker build -t payment-api .

# Run
docker run -p 8080:8080 -e TRANSACTIONS_API_URL=http://transaction-api:8080 payment-api
```

## Environment Variables

- `PORT` - Port to run the API (default: 8080)
- `PROFILE` - Application profile (dev/prod, default: prod)
- `TRANSACTIONS_API_URL` - URL of the Transaction API for notifications (optional)

## Deployment to Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <your-registry> --image payment-api:latest .

# Deploy to Container Apps
az containerapp create \
  --name payment-api \
  --resource-group <your-rg> \
  --image <your-registry>.azurecr.io/payment-api:latest \
  --target-port 8080 \
  --ingress external \
  --environment <your-environment> \
  --env-vars TRANSACTIONS_API_URL=https://transaction-api.your-domain.com
```
