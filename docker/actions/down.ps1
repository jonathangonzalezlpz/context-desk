param (
    [switch]$volumes = $false
)

$COMPOSE_FILE = "docker/files/docker-compose.yml"

Write-Host "🛑 Stopping ContextDesk..." -ForegroundColor Red
if ($volumes) {
    docker-compose -f $COMPOSE_FILE down -v
    Write-Host "🗑️ Volumes removed." -ForegroundColor Green
} else {
    docker-compose -f $COMPOSE_FILE down
}

Write-Host "✅ System stopped." -ForegroundColor Green
