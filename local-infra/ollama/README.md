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

## Optimización para GPU (RTX 4060 Ti 16GB)
Esta configuración está refinada para una **NVIDIA RTX 4060 Ti con 16 GB de VRAM**:

### Criterios de Hardware
- **Aceleración**: El contenedor utiliza `nvidia-container-toolkit` para ejecutar inferencia en GPU.
- **Modelo Seguro**: Recomendamos `llama3:8b` o `mistral:7b`. En cuantización q8_0 ocupan ~8.5GB, permitiendo cargar el modelo íntegramente en VRAM.
- **Límite de VRAM**: Aunque tienes 16GB, el RAG y el contexto consumen memoria dinámica. No se recomienda usar modelos > 14B (como llama-3-70b o similares) sin cuantizaciones muy agresivas (q2/q3), ya que podrían saturar la VRAM y degradar al CPU.

### Parámetros de Control
- `OLLAMA_NUM_CTX`: Limitado a **4096** por defecto para garantizar estabilidad.
- `OLLAMA_KEEP_ALIVE`: Configurado en **24h** por defecto para evitar descargas/recargas constantes durante sesiones de desarrollo o demo.

