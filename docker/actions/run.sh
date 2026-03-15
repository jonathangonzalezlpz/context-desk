#!/bin/bash

# Default values
DOMAIN="farmacia_demo"
PROVIDER="mock"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift ;;
        --provider) PROVIDER="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "🚀 Starting ContextDesk..."
echo "📍 Domain: $DOMAIN"
echo "🤖 Provider: $PROVIDER"

# Export variables for docker-compose
export DOMAIN_ACTIVE=$DOMAIN
export PROVIDER_SELECTED=$PROVIDER

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Select Docker Compose file
COMPOSE_FILE="docker/files/docker-compose.yml"

# 1. Start Database and Vector Store
docker-compose -f $COMPOSE_FILE up -d db qdrant

echo "⏳ Waiting for database to be healthy..."
until [ "$(docker inspect -f {{.State.Health.Status}} context-desk-db-1)" == "healthy" ]; do
    sleep 2
done

# 2. Check if ingestion is needed (Simplified check: if products table is empty)
echo "🔍 Checking if data ingestion is required..."
PRODUCT_COUNT=$(docker-compose -f $COMPOSE_FILE exec -T db psql -U user -d contextdesk_db -t -c "SELECT count(*) FROM products;")

if [ "${PRODUCT_COUNT//[[:space:]]/}" == "0" ]; then
    echo "📥 Ingesting catalog and knowledge..."
    docker-compose -f $COMPOSE_FILE up -d api
    docker-compose -f $COMPOSE_FILE exec -T api python knowledge/processed/$DOMAIN/scripts/ingest_catalog.py
    docker-compose -f $COMPOSE_FILE exec -T api python knowledge/processed/$DOMAIN/scripts/ingest_knowledge.py
else
    echo "✅ Data already present. Skipping ingestion."
fi

# 3. Start/Restart API with correct ENV
echo "🌐 Starting API..."
docker-compose -f $COMPOSE_FILE up -d api

echo "✨ ContextDesk is up and running!"
echo "Health check: http://localhost:8000/api/v1/health"
