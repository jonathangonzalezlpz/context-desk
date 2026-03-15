#!/bin/bash

COMPOSE_FILE="docker/files/docker-compose.yml"

echo "🛑 Stopping ContextDesk..."
docker-compose -f $COMPOSE_FILE down

echo "🧹 Cleaning up volumes (optional, use --volumes to remove data)..."
if [[ "$*" == *"--volumes"* ]]; then
    docker-compose -f $COMPOSE_FILE down -v
    echo "🗑️ Volumes removed."
fi

echo "✅ System stopped."
