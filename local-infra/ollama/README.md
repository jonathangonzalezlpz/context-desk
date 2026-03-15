# Motor de IA Local: Ollama

Este directorio contiene la configuración para el servicio local de inferencia de modelos de lenguaje (LLM).

## Componentes
- **Dockerfile**: Basado en la imagen oficial, añade un script de auto-inicialización.
- **entrypoint.sh**: Script que automatiza el `ollama pull` del modelo configurado la primera vez que se levanta el entorno.

## Configuración
El servicio se configura mediante variables de entorno en el `docker-compose.yml`:
- `OLLAMA_MODEL`: El nombre del modelo a descargar (ej: `llama3`, `mistral`, `gemma`).

## Persistencia
Los modelos se almacenan en el volumen de Docker `ollama_data` para evitar re-descargas en arranques posteriores.
