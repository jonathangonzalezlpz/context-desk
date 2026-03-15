param (
    [switch]$volumes = $false
)

$COMPOSE_FILE = "docker/files/docker-compose.yml"
$PROJECT_NAME = "context-desk"

Write-Host "🛑 Stopping ContextDesk..." -ForegroundColor Red
if ($volumes) {
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down -v
    Write-Host "🗑️ Volumes removed." -ForegroundColor Green
} else {
    docker compose -p $PROJECT_NAME -f $COMPOSE_FILE down
}

Write-Host "✅ System stopped." -ForegroundColor Green
