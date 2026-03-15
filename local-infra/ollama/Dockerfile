FROM ollama/ollama:latest

# Copiar el script de inicialización
COPY local-infra/ollama/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponer el puerto por defecto
EXPOSE 11434

ENTRYPOINT ["/entrypoint.sh"]
