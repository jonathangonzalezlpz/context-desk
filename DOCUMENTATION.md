# Documentación Técnica: ContextDesk

## Arquitectura Multi-Dominio

ContextDesk está diseñado para ser agnóstico al dominio. Toda la lógica de negocio y personalidad del bot se define en archivos de configuración JSON, permitiendo cambiar el comportamiento sin tocar el código Python.

### Configuración del Dominio (`domain_config.json`)
Cada dominio (ej. `farmacia_demo`) cuenta con un archivo de configuración que define:
- `system_prompt`: La personalidad y reglas del asistente.
- `guardrails`: Términos prohibidos y mensajes de bloqueo de seguridad.
- `relevancy_rules`: Reglas semánticas para evitar que el bot responda fuera de su dominio.
- `catalog_trigger_keywords`: Palabras clave que activan la búsqueda en el catálogo estructurado.

## Características Principales

### 1. Memoria de Sesión (Persistencia)
El sistema utiliza PostgreSQL para almacenar el historial de mensajes de cada `session_id`. El `ChatOrchestrator` recupera automáticamente el contexto previo para mantener conversaciones coherentes a lo largo del tiempo.

### 2. Streaming de Respuestas (Rendimiento)
Para optimizar la experiencia de usuario y aprovechar la aceleración por GPU (NVIDIA RTX 4060 Ti), el backend utiliza `StreamingResponse` de FastAPI. Esto permite que el frontend renderice la respuesta token a token conforme se genera, eliminando la latencia percibida.

### 3. Mecanismos de Seguridad y Contención

El sistema implementa múltiples capas de defensa para garantizar que el asistente opere exclusivamente dentro de los límites del negocio:

| Capa | Mecanismo | Vulnerabilidad que soluciona | Cómo lo hace |
| :--- | :--- | :--- | :--- |
| **Entrada** | Guardrails Duros (Regex) | Consultas directas sobre medicamentos o dosis. | Intercepta el mensaje buscando términos literales. |
| **Entrada** | Guardrails Fuzzy (Levenshtein) | Evasiones ortográficas o errores de tipeo (ej. 1buprof3n0). | Busca coincidencias difusas (similitud >85%) de términos prohibidos. |
| **Entrada** | Guardrails Semánticos (FastEmbed) | Intenciones sensibles o prohibidas encubiertas o parafraseadas. | Convierte el mensaje a vector y mide su distancia de coseno contra un clúster de frases prohibitivas usando BAAI/bge-small. Sin latencia ni uso de VRAM adicional. |
| **Dominio** | Filtro de Relevancia Semántica | Consultas fuera de dominio o intentos de desvío (Prompt Injection). | Aplica heurísticas y conteo de palabras clave para declinar temas no permitidos (ej. política, alcohol). |
| **Datos** | RAG e Ingesta Local | Fuga de datos sensibles o políticas internas a APIs de terceros. | Utiliza FastEmbed y Qdrant localmente para que la vectorización y búsqueda no salgan del servidor. |
| **Salida (Bloque)** | Validación Post-Generación | Alucinaciones del LLM en flujo no-streaming. | Re-evalúa la respuesta completa del LLM contra la lista de términos bloqueados antes de enviarla. |
| **Salida (Stream)** | StreamingGuard + Búfer de Seguridad | Contenido prohibido que el LLM emite token a token en tiempo real. | Acumula los primeros N caracteres en un búfer invisible, los valida y activa un kill-switch si detecta contenido prohibido antes de que llegue al cliente. |
| **Arquitectura** | Aislamiento Hexagonal | Mezcla de lógica de negocio con código de infraestructura. | Desacopla reglas de seguridad en `domain_config.json`, permitiendo auditorías sin cambiar el código. |

### 3.0. Validaciones Semánticas en la Entrada
El sistema aplica un pipeline de seguridad de 3 fases antes de activar el RAG o el LLM:
1. **Regex**: Alta velocidad, estricto.
2. **Fuzzy Matching**: Detecta variaciones ortográficas intencionadas como "am0xicilin4" o "paracetamolll".
3. **Clasificación Semántica por Vectores**: Soluciona consultas estructuradas donde el usuario solicita acciones o temas restringidos sin usar palabras bloqueadas explícitas (ej. dependiendo del dominio, podría interceptar diagnósticos encubiertos, asesoramiento financiero indebido o intenciones inapropiadas).
   * **Decisión Técnica**: En lugar de utilizar LLMs en la nube o cargar un segundo LLM local en memoria como juez (lo que añadiría fuerte latencia o colapsaría los 16GB de VRAM), se utiliza la biblioteca `FastEmbed` que ya acompaña al RAG local. Se ejecuta en milisegundos sobre la CPU utilizando el modelo `BAAI/bge-small-en-v1.5`, comparando matemáticamente la intención de la frase (distancia coseno > 0.82) contra un clúster de frases prohibidas inyectadas desde el `domain_config.json`.

### 3.1. Streaming Seguro: Modos de Operación (`StreamingGuard`)

El componente `StreamingGuard` (`backend/src/app/platform/guardrails/streaming_guard.py`) envuelve el flujo de tokens del LLM y aplica diferentes estrategias de seguridad según la sensibilidad del dominio. El modo activo se configura por dominio en `domain_config.json`.

#### Principio Fail-Closed
Cualquier excepción dentro del guardrail (timeout, error de clasificación, etc.) se trata como **contenido inseguro**. El sistema nunca falla en modo abierto.

#### Modo 1: `streaming_unrestricted`
**Para**: Entornos no sensibles (demos internas, pruebas de desarrollo).
**Comportamiento**: Los tokens fluyen directamente del LLM al cliente sin ningún filtro de salida.
**Latencia añadida**: 0ms.

#### Modo 2: `streaming_buffered_start` *(modo por defecto en Farmacia)*
**Para**: Dominios con alta sensibilidad como sanidad, legal o finanzas.
**Comportamiento**:
1. El cliente recibe un mensaje de espera seguro y predefinido (ej. *"Interpretando tu consulta..."*).
2. Los primeros `N` caracteres de la respuesta del LLM se acumulan en un búfer invisible.
3. Cuando el búfer alcanza el umbral:
   - Si es **seguro**: se libera el contenido acumulado y el resto de la respuesta fluye libremente.
   - Si es **inseguro**: se activa el **kill-switch**, se bloquea el generador y se devuelve la respuesta de seguridad predefinida. Nada del contenido original llega al cliente.
4. Si la respuesta completa es más corta que el búfer, se valida igualmente antes de enviarse.
**Latencia añadida**: baja (el tiempo que tarda el LLM en generar `buffer_chars` caracteres).

#### Modo 3: `streaming_full_guarded`
**Para**: Dominios de máxima sensibilidad donde la respuesta puede ser larga y compleja.
**Comportamiento**: Revisión por ventana deslizante a lo largo de **toda la respuesta**. Cada `N` caracteres, se re-valida el texto acumulado total. Si el guardrail detecta contenido prohibido en cualquier ventana, activa inmediatamente el kill-switch y corta el stream.
**Latencia añadida**: media-alta (pause each window).

#### Modo 4: `streaming_disabled`
**Para**: Dominios donde la prioridad es la seguridad absoluta sobre la velocidad de respuesta percibida.
**Comportamiento**: El servidor consume **todos** los tokens internamente, valida la respuesta completa y sólo entonces la envía al cliente en un único bloque. No hay streaming real.
**Latencia añadida**: alta (el usuario espera toda la generación antes de ver algo).

#### Configuración en `domain_config.json`
```json
"guardrails": {
  "streaming_mode": "streaming_buffered_start",
  "streaming_buffer_chars": 300,
  "streaming_ux_messages": [
    "Interpretando tu consulta...",
    "Preparando una respuesta segura..."
  ],
  "streaming_blocked_response": "Por seguridad, no puedo completar esta respuesta."
}
```

### 4. Robustez y Estabilidad
- **Migraciones Automáticas**: El backend ejecuta `Base.metadata.create_all` al arrancar, asegurando que tablas como `chat_messages` existan sin intervención manual.
- **Manejo de Errores en Streaming**: El generador de tokens está protegido con bloques `try-except` para evitar cortes abruptos (`ERR_INCOMPLETE_CHUNKED_ENCODING`) y reportar fallos técnicos de forma controlada.

## Mantenimiento y Logs
Para monitorear los servicios en tiempo real:
```bash
docker compose -p context-desk -f docker/files/docker-compose.yml logs -f
```
Para escalar a un nuevo dominio:
1. Crear carpeta en `knowledge/processed/<nuevo_dominio>/`.
2. Definir `domain_config.json` siguiendo el esquema de `farmacia_demo`.
3. Establecer `DOMAIN_ACTIVE=<nuevo_dominio>` en el archivo `.env`.

## 1. Visión General
ContextDesk es una plataforma de chatbot diseñada para negocios locales que requieren un control estricto sobre lo que su IA puede y no puede decir (Guardrails). Combina datos estructurados (Catálogo) con datos no estructurados (Base de Conocimiento/RAG).

## 2. Arquitectura del Sistema

### Backend (Modular Hexagonal)
- **FastAPI:** Punto de entrada de la API.
- **Domain:** Lógica de negocio pura (chat, catálogo, guardrails).
- **Platform/Infrastructure:** Implementaciones de servicios y adaptadores de base de datos.
- **Dependency Injection:** La configuración del dominio se carga dinámicamente según el negocio configurado.

### Almacenamiento
- **PostgreSQL:** Almacena el catálogo de productos (id, nombre, marca, precio, stock) y marca si un producto es apto para ser mencionado por el bot (`bot_allowed`).
- **Qdrant:** Base de datos vectorial para el RAG. Almacena fragmentos de texto (FAQs, políticas, servicios) convertidos en vectores.

### Frontend
- **Vanilla JS & CSS:** Interfaz premium con modo oscuro, glassmorphism y respuesta en tiempo real. Se comunica con el API vía REST.

## 3. El Stack AI Gratuito (Portfolio-Ready)
Para eliminar costes de desarrollo y facilitar la presentación en portfolio, ContextDesk utiliza:

- **Embeddings locales (FastEmbed):** No utiliza la API de OpenAI para vectorizar. Los vectores se generan dentro del contenedor Docker usando la CPU, lo que garantiza coste cero y privacidad.
- **Orquestador Multi-LLM:**
  - **Groq (Llama 3):** Recomendado para portfolio. Es gratuito, ultrarrápido y potente.
  - **Ollama (Local):** Soporte nativo para modelos locales (llama3, mistral, etc.). El sistema se comunica con tu instancia local de Ollama.
  - **OpenAI:** Soportado como alternativa de pago.
  - **Modo Mock:** Si no hay API Keys configuradas, el bot responde con el contexto recuperado del sistema.

## 4. Flujo de Procesamiento (RAG + Guardrails)

1. **Input Guardrail:** Se comprueba si el mensaje del usuario contiene términos prohibidos o patrones sospechosos.
2. **Clasificación de Intención:** Heurística rápida para detectar si el usuario busca productos del catálogo o información general.
3. **Construcción de Contexto:**
   - **Catalog Search:** Búsqueda difusa en PostgreSQL sobre productos permitidos.
   - **Vector Search:** Búsqueda semántica en Qdrant sobre la base de conocimiento cargada.
4. **Generación (LLM):** Se envía el contexto consolidado al LLM (Groq/OpenAI) con instrucciones estrictas de personalidad.
5. **Output Guardrail:** Validación final de la respuesta de la IA antes de enviarla al usuario para evitar alucinaciones con términos prohibidos.

## 5. Ingesta de Datos
El sistema es multi-dominio. Para activar un nuevo negocio, solo se requiere subir sus archivos `raw` y configurar el `domain_config.json`. Los scripts de ingesta automatizan el volcado a la DB y la base vectorial.

## 6. Orquestación y Automatización con Docker
Hemos profesionalizado la gestión de contenedores para facilitar el despliegue y las pruebas:

- **Estructura:** Los archivos de configuración residen en `docker/files/` y los scripts de acción en `docker/actions/`. El motor de IA local reside en `local-infra/ollama/`.
- **Nomenclatura Estandarizada:** Los contenedores se gestionan bajo el proyecto `context-desk`, lo que garantiza identificadores únicos (`context-desk-api-1`, `context-desk-db-1`, etc.) sin importar el directorio de ejecución.
- **Script `run.sh` / `run.ps1`:** Automatiza el arranque completo.
  - **Auto-Ingesta:** Comprueba el estado de la base de datos y lanza la ingesta si es la primera vez que se inicia.
  - **Configuración:** Permite seleccionar el dominio (`--domain`) y el proveedor de IA (`--provider`).
- **GPU Acceleration:** El sistema detecta automáticamente hardware NVIDIA y configura el passthrough para Ollama, permitiendo inferencia local de alto rendimiento.

## 7. Comprobaciones de Verificación
Para asegurar que el sistema está operativo, puedes ejecutar:
1. `curl http://localhost:8000/api/v1/health` -> Debe responder `{"status":"ok"}`.
2. `docker compose -p context-desk logs api` -> Para ver qué proveedor de LLM está activo y comprobar los logs de CORS.
3. `docker compose -p context-desk logs ollama` -> Para verificar la detección de la GPU NVIDIA.

---
*Este documento refleja el estado actual del desarrollo a fecha del 15 de marzo de 2026.*
