# ContextDesk

**Domain-safe chatbot platform for local businesses.** (Ejemplo base: Farmacia)

Este chatbot está diseñado para negocios con regulaciones o restricciones fuertes sobre los temas que su IA puede tratar, usando RAG híbrido y Guardrails duros, aislados de los Endpoints (Arquitectura Hexagonal Modular).

## Requisitos de entorno
- Python 3.12
- Docker y Docker Compose
- `uv` instalado (`curl -LsSf https://astral.sh/uv/install.sh | sh` o usando `pip install uv`)

## Inicialización local
1. Copiar `.env.example` a `.env`
2. Correr `make setup`
3. Correr `make docker-up` para levantar BD y dependencias
4. Correr `make dev` para usar la API en modo local con reload.
