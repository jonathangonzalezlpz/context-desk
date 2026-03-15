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

---

## Añadir un nuevo dominio (negocio/local/aplicación)

Cada dominio representa un negocio o caso de uso independiente (una farmacia, una agencia de viajes, un restaurante, etc.). Para añadir uno nuevo:

### Estructura de carpetas requerida

```
knowledge/
  raw/<nombre_dominio>/         ← datos fuente sin procesar
    catalog.csv                 ← catálogo de productos/servicios consultables
    faq.md                      ← preguntas frecuentes
    services.md                 ← descripción de servicios
    policies.md                 ← políticas del negocio
    guardrails.md               ← temas prohibidos y comportamiento esperado
    [otros archivos relevantes]

  processed/<nombre_dominio>/   ← configuración y scripts de ingesta del dominio
    domain_config.json          ← configuración central del dominio (guardrails,
    |                              esquema del catálogo, rutas de knowledge, etc.)
    scripts/
      ingest_catalog.py         ← script para volcar el catálogo a PostgreSQL
      ingest_knowledge.py       ← script para indexar los Markdown en Qdrant
```

### 1. Sube los datos crudos

Añade los archivos de conocimiento en `knowledge/raw/<nombre_dominio>/`.

### 2. Crea `domain_config.json`

Define en `knowledge/processed/<nombre_dominio>/domain_config.json`:
- `domain_id`: identificador único del dominio.
- `guardrails.blocked_terms`: lista de términos a bloquear.
- `guardrails.blocked_response_message`: mensaje de respuesta cuando se bloquea.
- `catalog.source_csv`: ruta al CSV de productos.
- `catalog.column_map`: mapeo de columnas del CSV al esquema interno.
- `knowledge.files`: lista de archivos Markdown a indexar en Qdrant.
- `knowledge.chunk_size`: tamaño de chunk para el RAG.
- `knowledge.qdrant_collection`: nombre de la colección en Qdrant.

### 3. Adapta los scripts de ingesta

Copia los scripts de referencia desde `knowledge/processed/farmacia_demo/scripts/`
y ajústalos si la estructura del CSV u otras particularidades lo requieren.

### 4. Ejecuta la ingesta

```bash
python knowledge/processed/<nombre_dominio>/scripts/ingest_catalog.py
python knowledge/processed/<nombre_dominio>/scripts/ingest_knowledge.py
```

O bien, actualiza los targets del `Makefile` para apuntar al nuevo dominio activo.
