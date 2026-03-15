#!/bin/bash

COMPOSE_FILE="docker/files/docker-compose.yml"
PROJECT_NAME="context-desk"

echo "🛑 Stopping ContextDesk..."
docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down

echo "🧹 Cleaning up volumes (optional, use --volumes to remove data)..."
if [[ "$*" == *"--volumes"* ]]; then
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down -v
    echo "🗑️ Volumes removed."
fi

echo "✅ System stopped."
