# Documentación Técnica: ContextDesk

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
  - **OpenAI:** Soportado como alternativa de pago.
  - **Modo Mock:** Si no hay API Keys configuradas, el bot responde con el contexto recuperado del sistema, permitiendo validar la lógica de búsqueda sin coste.

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

- **Estructura:** Los archivos de configuración residen en `docker/files/` y los scripts de acción en `docker/actions/`.
- **Script `run.sh`:** Automatiza el arranque completo.
  - **Auto-Ingesta:** Comprueba el estado de la base de datos y lanza la ingesta si es la primera vez que se inicia.
  - **Configuración:** Permite seleccionar el dominio (`--domain`) y el proveedor de IA (`--provider`).
- **Script `down.sh`:** Detiene todos los servicios y permite limpiar volúmenes con `--volumes`.


## 6. Comportamiento Actual y Pruebas
El sistema está configurado y verificado con los siguientes comportamientos:

- **Modo Seguro por Defecto:** Si no detecta una clave de Groq o OpenAI, el sistema entra en modo "Mock". No inventará respuestas, sino que mostrará el contexto que ha sido capaz de recuperar.
- **Guardrails Estrictos:** El bloqueo de temas prohibidos (ej. consejos médicos) sucede *antes* de que la pregunta llegue a la IA, ahorrando recursos y garantizando seguridad.
- **Prioridad de Datos:** El orquestador prioriza el catálogo estructurado para consultas de stock/precio y usa el RAG para dudas generales/políticas.

## 7. Comprobaciones de Verificación
Para asegurar que el sistema está operativo, puedes ejecutar:
1. `curl http://localhost:8000/api/v1/health` -> Debe responder `{"status":"ok"}`.
2. `docker-compose logs api` -> Para ver qué proveedor de LLM está activo (Groq, OpenAI o Mock).

---
*Este documento refleja el estado actual del desarrollo a fecha del 15 de marzo de 2026.*
