# ContextDesk

**Plataforma de chatbot modular y segura para negocios locales.**

ContextDesk es una solución integral para implementar asistentes virtuales que garantizan la seguridad del dominio (Guardrails) y la privacidad de los datos mediante ejecución local (RAG híbrido).

**Este chatbot está diseñado para negocios con regulaciones o restricciones fuertes sobre los temas que su IA puede tratar, usando RAG híbrido y Guardrails duros, aislados de los Endpoints (Arquitectura Hexagonal Modular).**

📘 **[Lee la Documentación Técnica Detallada](./DOCUMENTATION.md)** para profundizar en el stack y configuración avanzada.

---

## 🏛️ Arquitectura y Decisiones Técnicas

El proyecto sigue una **Arquitectura Hexagonal (Puertos y Adaptadores)**, lo que permite que el núcleo lógico (el dominio) sea totalmente independiente de las herramientas externas (DB, Vector Store, LLMs).

### ¿Por qué estas tecnologías?

*   **FastAPI**: Elegido por su altísimo rendimiento y soporte nativo para `streaming`. Permite una construcción rápida de APIs en Python con validación automática y documentación interactiva.
*   **Ollama (Local-Infra)**: Proporciona una alternativa local a servicios como OpenAI. Garantiza **coste 0**, privacidad total y permite que el chatbot sea funcional incluso sin conexión a internet o APIs externas.
*   **Arquitectura Multi-Dominio**: El sistema es agnóstico al negocio. Toda la "inteligencia" y "restricciones" se inyectan mediante configuración, permitiendo escalar de una farmacia a una inmobiliaria en minutos.
*   **RAG (Retrieval Augmented Generation)**: Combina un catálogo estructurado (SQL) con una base de conocimiento (Vectorial) para dar respuestas precisas y verificables.

---

## 🏗️ Estructura de Componentes

### 1. `backend/` (El Núcleo)
Gestiona el ciclo de vida completo de la petición:
*   **Filtros y Guards**: Interceptores de entrada/salida que aseguran que el bot no se salga del tema permitido.
*   **Orquestación**: Coordina la búsqueda en el catálogo, la recuperación semántica (RAG) y la llamada al modelo de lenguaje.
*   **Persistencia**: Gestión de memoria de sesión en PostgreSQL.

### 2. `local-infra/` (IA Local)
Basado en **Ollama**, este componente actúa como el cerebro del sistema. Incluye una imagen Docker personalizada que descarga y configura automáticamente los modelos (Llama 3, Mistral) al arrancar.

### 3. `knowledge/` (Datos del Dominio)
*   `raw/`: Información en bruto del negocio (CSV de catálogo, MD de políticas).
*   `processed/`: Scripts de ingesta y archivos `domain_config.json` que definen la personalidad y reglas de cada caso de uso.

### 4. `frontend/` (Interfaz Web)
Una web de interacción premium diseñada con Vanilla JS/CSS. Enfocada en la simplicidad y la velocidad, procesando respuestas en streaming para una experiencia de usuario fluida.

### 5. `docker/` (Automatización)
Archivos de contenerización y scripts de acción:
*   `run.sh / run.ps1`: Orquestación de contenedores y auto-ingesta de datos.
*   `down.sh`: Limpieza de entorno.

---

## Requisitos de entorno
- Python 3.12
- Docker y Docker Compose
- GPU NVIDIA (Opcional, pero recomendada para Ollama)

## Inicialización y Uso

### 🚀 Lanzamiento Rápido (Recomendado)
Para levantar el sistema con auto-ingesta de datos:

**En Linux/macOS:**
```bash
bash docker/actions/run.sh --provider ollama
```

**En Windows (PowerShell):**
```powershell
.\docker\actions\run.ps1 -provider ollama
```

### 🛑 Parar el sistema (Windows/Linux)
Para detener todos los contenedores y limpiar el entorno:
```bash
# Linux/macOS
bash docker/actions/down.sh

# Windows (PowerShell)
.\docker\actions\down.ps1
```

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
