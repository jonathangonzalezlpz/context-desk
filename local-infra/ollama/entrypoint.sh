#!/bin/bash

# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que el servidor de Ollama esté listo
echo "⏳ Esperando a que el servidor de Ollama arranque..."
until ollama list > /dev/null 2>&1; do
    sleep 2
done

# --- Observabilidad de Hardware ---
echo "--- Hardware Info ---"
if command -v nvidia-smi &> /dev/null; then
    echo "✅ GPU NVIDIA Detectada:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  No se detectó GPU NVIDIA. Ollama correrá en modo CPU (Lento)."
fi
echo "----------------------"

# Verificar si el modelo ya existe localmente
MODEL_NAME=${OLLAMA_MODEL:-llama3}
echo "🔍 Buscando el modelo: $MODEL_NAME"

if ollama list | grep -q "$MODEL_NAME"; then
    echo "✅ El modelo $MODEL_NAME ya está presente."
else
    echo "📥 Descargando el modelo $MODEL_NAME... (Esto puede tardar varios minutos)"
    ollama pull "$MODEL_NAME"
    echo "✅ Descarga completada."
fi

# --- Información del Modelo ---
echo "--- Model Details ---"
ollama show "$MODEL_NAME" --modelfile | grep -E "parameter_size|quantization_level" || echo "Detalles no disponibles."
echo "----------------------"

# Mantener el proceso en primer plano
echo "🚀 Ollama está listo para recibir peticiones (RTX 4060 Ti 16GB optimized)."
wait
