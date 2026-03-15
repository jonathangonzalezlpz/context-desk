param (
    [string]$domain = "farmacia_demo",
    [string]$provider = "mock"
)

Write-Host "🚀 Starting ContextDesk..." -ForegroundColor Cyan
Write-Host "📍 Domain: $domain"
Write-Host "🤖 Provider: $provider"

# Load .env if exists
if (Test-Path ".env") {
    Get-Content .env | Where-Object { $_ -notmatch "^#" -and $_ -notmatch "^\s*$" } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
    }
}

# Export variables for docker-compose
$env:DOMAIN_ACTIVE = $domain
$env:PROVIDER_SELECTED = $provider
$env:OLLAMA_BASE_URL = if ($env:OLLAMA_BASE_URL) { $env:OLLAMA_BASE_URL } else { "http://host.docker.internal:11434" }
$env:OLLAMA_MODEL = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "llama3" }

# Select Docker Compose file
$COMPOSE_FILE = "docker/files/docker-compose.yml"

# 1. Start Database and Vector Store
docker-compose -f $COMPOSE_FILE up -d db qdrant

Write-Host "⏳ Waiting for database to be healthy..." -ForegroundColor Yellow
while ($(docker inspect -f {{.State.Health.Status}} context-desk-db-1) -ne "healthy") {
    Start-Sleep -Seconds 2
}

# 2. Check if ingestion is needed
Write-Host "🔍 Checking if data ingestion is required..." -ForegroundColor Cyan
$PRODUCT_COUNT = docker-compose -f $COMPOSE_FILE exec -T db psql -U user -d contextdesk_db -t -c "SELECT count(*) FROM products;"
$PRODUCT_COUNT = $PRODUCT_COUNT.Trim()

if ($PRODUCT_COUNT -eq "0") {
    Write-Host "📥 Ingesting catalog and knowledge..." -ForegroundColor Green
    docker-compose -f $COMPOSE_FILE up -d api
    docker-compose -f $COMPOSE_FILE exec -T api python knowledge/processed/$domain/scripts/ingest_catalog.py
    docker-compose -f $COMPOSE_FILE exec -T api python knowledge/processed/$domain/scripts/ingest_knowledge.py
} else {
    Write-Host "✅ Data already present ($PRODUCT_COUNT products). Skipping ingestion." -ForegroundColor Green
}

# 3. Start/Restart API
Write-Host "🌐 Starting API..." -ForegroundColor Cyan
docker-compose -f $COMPOSE_FILE up -d api

Write-Host "✨ ContextDesk is up and running!" -ForegroundColor Green
Write-Host "Health check: http://localhost:8000/api/v1/health"
