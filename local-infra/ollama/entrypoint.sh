#!/bin/bash

# Iniciar Ollama en segundo plano
ollama serve &

# Esperar a que el servidor de Ollama esté listo
echo "⏳ Esperando a que el servidor de Ollama arranque..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    sleep 2
done

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

# Mantener el proceso en primer plano
echo "🚀 Ollama está listo para recibir peticiones."
wait
