# Dataset demo para farmacia en Madrid

Este conjunto de archivos contiene datos sintéticos y realistas para una demo de chatbot de farmacia orientado a:
- horario
- contacto
- servicios
- productos de parafarmacia
- FAQs del negocio

## Importante
- No representa una farmacia real.
- No debe usarse como fuente sanitaria real.
- No incluye medicamentos como catálogo consultable.
- Sí incluye términos bloqueados para detectar consultas que deben redirigirse a profesionales.

## Sugerencia de uso
- Indexar con embeddings: `faq.md`, `services.md`, `policies.md`, `guardrails.md`
- Guardar como configuración: `business_profile.json`, `contact.json`, `schedule.json`
- Guardar en base de datos estructurada: `catalog.csv`
- Usar para clasificación de bloqueo: `blocked_terms.txt`
- Usar para tests: `evaluation_questions.json`
